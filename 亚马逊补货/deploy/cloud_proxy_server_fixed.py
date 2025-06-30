#!/usr/bin/env python3
"""
修复版云代理服务器 - 解决WebSocket响应处理bug
"""

import asyncio
import json
import time
import uuid
import logging
import threading
import traceback
from datetime import datetime
from typing import Dict, Any

import requests
from flask import Flask, request, jsonify, Response
from websockets.server import serve
import websockets.exceptions

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudProxyServer:
    """
    云代理服务器 - 支持WebSocket反向代理
    """
    
    def __init__(self, host='0.0.0.0', port=8080, ws_port=8081):
        """
        初始化云代理服务器
        
        Args:
            host: 服务器主机地址
            port: HTTP服务端口
            ws_port: WebSocket服务端口
        """
        self.host = host
        self.port = port
        self.ws_port = ws_port
        
        # Flask应用
        self.app = Flask(__name__)
        
        # WebSocket连接管理
        self.ws_clients = {}  # 存储WebSocket连接
        self.pending_requests = {}  # 存储待处理的请求
        
        # 请求统计
        self.stats = {
            'total_requests': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'feishu_requests': 0,
            'ws_connections': 0,
            'start_time': time.time()
        }
        
        # 注册路由
        self._register_routes()
        
        logger.info(f"🌐 云代理服务器初始化完成 - HTTP:{host}:{port}, WS:{host}:{ws_port}")
    
    def _register_routes(self):
        """注册所有HTTP路由"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """🔍 健康检查接口"""
            return jsonify({
                'status': 'healthy',
                'server': f'cloud-server:{self.port}',
                'service': 'feishu-webhook-ws-fixed',
                'ws_port': self.ws_port,
                'active_connections': len(self.ws_clients),
                'message': '代理服务器运行正常',
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            })
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """📊 获取服务器统计信息"""
            uptime = time.time() - self.stats['start_time']
            return jsonify({
                'stats': self.stats,
                'uptime_seconds': uptime,
                'uptime_hours': uptime / 3600,
                'success_rate': (
                    self.stats['success_requests'] / max(self.stats['total_requests'], 1) * 100
                ),
                'active_ws_connections': len(self.ws_clients),
                'clients': list(self.ws_clients.keys())
            })
        
        @self.app.route('/feishu/webhook', methods=['POST'])
        def feishu_webhook():
            """🤖 飞书webhook接口 - 通过WebSocket转发"""
            return self._handle_feishu_request_ws()
        
        @self.app.route('/feishu/command', methods=['POST'])
        def feishu_command():
            """🎯 飞书命令接口 - 通过WebSocket转发"""
            return self._handle_feishu_request_ws('/feishu/command')
    
    def _handle_feishu_request_ws(self, endpoint: str = '/feishu/webhook') -> Response:
        """
        通过WebSocket处理飞书请求转发
        
        Args:
            endpoint: 目标端点路径
            
        Returns:
            Response: Flask响应对象
        """
        start_time = time.time()
        self.stats['feishu_requests'] += 1
        self.stats['total_requests'] += 1
        
        try:
            # 检查是否有活跃的WebSocket连接
            if not self.ws_clients:
                logger.warning("⚠️ 没有活跃的WebSocket连接")
                self.stats['failed_requests'] += 1
                return jsonify({
                    'error': '没有活跃的本地服务器连接',
                    'timestamp': datetime.now().isoformat()
                }), 503
            
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 构建请求数据
            request_data = {
                'type': 'feishu_request',
                'request_id': request_id,
                'method': request.method,
                'endpoint': endpoint,
                'headers': dict(request.headers),
                'data': request.get_json() if request.is_json else {},
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送到第一个可用的WebSocket连接
            client_id = list(self.ws_clients.keys())[0]
            websocket = self.ws_clients[client_id]
            
            logger.info(f"🤖 通过WebSocket转发飞书请求: {request_id}")
            
            # 发送请求并等待响应
            response = asyncio.run(self._send_and_wait_response(websocket, request_data, request_id))
            
            if response:
                response_time = time.time() - start_time
                logger.info(f"✅ 飞书请求完成: {response_time:.2f}s")
                
                # 正确解析响应数据
                response_data = response.get('response', {})
                status_code = response_data.get('status_code', 200)
                headers = response_data.get('headers', {})
                data = response_data.get('data', {})
                
                # 返回响应
                flask_response = jsonify(data)
                flask_response.status_code = status_code
                flask_response.headers['X-Feishu-Proxy'] = 'Cloud-Proxy-WS-Fixed'
                flask_response.headers['X-Response-Time'] = str(response_time)
                
                # 添加原始响应头（如果需要）
                for key, value in headers.items():
                    if key.lower() not in ['content-length', 'content-encoding']:
                        flask_response.headers[key] = value
                
                self.stats['success_requests'] += 1
                return flask_response
            else:
                logger.warning(f"⏰ 飞书请求超时: {request_id}")
                self.stats['failed_requests'] += 1
                return jsonify({
                    'error': '请求超时或连接断开',
                    'timestamp': datetime.now().isoformat()
                }), 504
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 飞书请求异常: {error_msg}\n{traceback.format_exc()}")
            self.stats['failed_requests'] += 1
            return jsonify({
                'error': f'飞书代理服务器内部错误: {error_msg}',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 500
    
    async def _send_and_wait_response(self, websocket, request_data, request_id, timeout=30):
        """
        发送请求并等待响应 - 修复了响应处理bug
        
        Args:
            websocket: WebSocket连接
            request_data: 请求数据
            request_id: 请求ID
            timeout: 超时时间
            
        Returns:
            dict: 响应数据
        """
        try:
            # 发送请求
            await websocket.send(json.dumps(request_data))
            
            # 等待响应
            start_time = time.time()
            while time.time() - start_time < timeout:
                if request_id in self.pending_requests:
                    # 🔧 修复bug: 正确获取并移除响应数据
                    response = self.pending_requests.pop(request_id)
                    logger.debug(f"📨 获取到响应数据: {response}")
                    return response
                await asyncio.sleep(0.1)
            
            logger.warning(f"⏰ 请求超时: {request_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ 发送请求异常: {e}")
            return None
    
    async def handle_websocket(self, websocket, path):
        """
        处理WebSocket连接
        
        Args:
            websocket: WebSocket连接
            path: 连接路径
        """
        client_id = f"client_{len(self.ws_clients)}_{int(time.time())}"
        self.ws_clients[client_id] = websocket
        self.stats['ws_connections'] += 1
        
        logger.info(f"🔗 新的WebSocket连接: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('type') == 'register':
                        local_url = data.get('local_url')
                        logger.info(f"📝 客户端注册: {client_id} - {local_url}")
                        
                        # 发送注册确认
                        ack_data = {
                            'type': 'registration_ack',
                            'client_id': client_id,
                            'timestamp': datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(ack_data))
                        
                    elif data.get('type') == 'feishu_response':
                        request_id = data.get('request_id')
                        if request_id:
                            # 🔧 修复bug: 直接存储完整的响应数据
                            self.pending_requests[request_id] = data
                            logger.info(f"📨 收到响应: {request_id}")
                    
                    elif data.get('type') == 'heartbeat':
                        # 响应心跳
                        pong_data = {
                            'type': 'heartbeat_ack',
                            'timestamp': datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(pong_data))
                        logger.debug(f"💓 心跳响应: {client_id}")
                        
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ 收到无效JSON消息: {message}")
                except Exception as e:
                    logger.error(f"❌ 处理WebSocket消息异常: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 WebSocket连接断开: {client_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket异常: {e}")
        finally:
            # 清理连接
            if client_id in self.ws_clients:
                del self.ws_clients[client_id]
            logger.info(f"🧹 清理WebSocket连接: {client_id}")
    
    def start_websocket_server(self):
        """启动WebSocket服务器"""
        logger.info(f"🔌 启动WebSocket服务器: ws://{self.host}:{self.ws_port}")
        
        async def websocket_server():
            async with serve(self.handle_websocket, self.host, self.ws_port):
                await asyncio.Future()  # 永远运行
        
        # 在新线程中运行WebSocket服务器
        def run_ws():
            asyncio.run(websocket_server())
        
        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()
    
    def run(self):
        """🚀 启动代理服务器"""
        logger.info(f"🚀 启动云代理服务器: http://{self.host}:{self.port}")
        
        # 启动WebSocket服务器
        self.start_websocket_server()
        
        # 启动Flask应用
        self.app.run(
            host=self.host,
            port=self.port,
            debug=False,
            threaded=True
        )

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='云代理服务器 - 修复版')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8080, help='HTTP服务端口')
    parser.add_argument('--ws-port', type=int, default=8081, help='WebSocket服务端口')
    
    args = parser.parse_args()
    
    # 创建并启动服务器
    server = CloudProxyServer(
        host=args.host,
        port=args.port,
        ws_port=args.ws_port
    )
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("🛑 服务器已停止")

if __name__ == "__main__":
    main() 