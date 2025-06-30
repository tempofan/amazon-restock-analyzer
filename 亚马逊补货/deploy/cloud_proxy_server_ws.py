#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 支持WebSocket的云代理服务器
支持反向代理架构，解决本地公网IP不固定问题
"""

import logging
import time
import json
import traceback
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import argparse
import threading
import websockets
from websockets.server import serve

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proxy_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloudProxyServerWS:
    """
    🚀 支持WebSocket的云代理服务器类
    支持传统HTTP代理和反向代理WebSocket连接
    """
    
    def __init__(self, host='0.0.0.0', port=8080, ws_port=8081, debug=False):
        """
        初始化代理服务器
        
        Args:
            host: 服务器监听地址
            port: HTTP服务器监听端口
            ws_port: WebSocket服务器监听端口
            debug: 是否开启调试模式
        """
        self.app = Flask(__name__)
        CORS(self.app)  # 允许跨域请求
        
        self.host = host
        self.port = port
        self.ws_port = ws_port
        self.debug = debug
        
        # 领星API配置
        self.lingxing_base_url = "https://openapi.lingxing.com"
        
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
        
        # 创建HTTP会话
        self.session = self._create_session()
        
        # 注册路由
        self._register_routes()
        
        logger.info(f"🌐 云代理服务器初始化完成 - HTTP:{host}:{port}, WS:{host}:{ws_port}")
    
    def _create_session(self) -> requests.Session:
        """
        创建HTTP会话，配置重试策略
        
        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _register_routes(self):
        """注册所有HTTP路由"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """🔍 健康检查接口"""
            return jsonify({
                'status': 'healthy',
                'server': f'cloud-server:{self.port}',
                'service': 'feishu-webhook-ws',
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
                'active_ws_connections': len(self.ws_clients)
            })
        
        @self.app.route('/api/proxy/<path:endpoint>', methods=['GET', 'POST'])
        def proxy_api(endpoint):
            """
            🔄 API代理转发接口
            将请求转发到领星API服务器
            """
            return self._handle_proxy_request(endpoint)
        
        @self.app.route('/feishu/webhook', methods=['POST'])
        def feishu_webhook():
            """🤖 飞书webhook接口 - 通过WebSocket转发"""
            return self._handle_feishu_request_ws()
        
        @self.app.route('/feishu/command', methods=['POST'])
        def feishu_command():
            """🎯 飞书命令接口 - 通过WebSocket转发"""
            return self._handle_feishu_request_ws('/feishu/command')
        
        @self.app.route('/test', methods=['GET'])
        def test_connection():
            """🧪 测试与领星API的连接"""
            try:
                # 尝试访问领星API根路径
                response = self.session.get(
                    f"{self.lingxing_base_url}",
                    timeout=10
                )
                
                return jsonify({
                    'status': 'success',
                    'message': '与领星API连接正常',
                    'response_code': response.status_code,
                    'ws_connections': len(self.ws_clients),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"连接测试失败: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'连接测试失败: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }), 500
    
    def _handle_proxy_request(self, endpoint: str) -> Response:
        """
        处理代理请求的核心逻辑
        
        Args:
            endpoint: API端点路径
            
        Returns:
            Response: Flask响应对象
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # 构建目标URL
            target_url = f"{self.lingxing_base_url}/{endpoint}"
            
            # 获取原始请求信息
            method = request.method
            headers = dict(request.headers)
            params = request.args.to_dict()
            
            # 移除代理相关的头部
            headers_to_remove = ['Host', 'Content-Length']
            for header in headers_to_remove:
                headers.pop(header, None)
            
            # 设置User-Agent
            headers['User-Agent'] = 'LingXing-Cloud-Proxy/1.0'
            
            logger.info(f"🔄 代理请求: {method} {target_url}")
            
            # 发送请求
            if method == 'GET':
                response = self.session.get(
                    target_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
            elif method == 'POST':
                if request.is_json:
                    response = self.session.post(
                        target_url,
                        json=request.get_json(),
                        params=params,
                        headers=headers,
                        timeout=30
                    )
                else:
                    response = self.session.post(
                        target_url,
                        data=request.get_data(),
                        params=params,
                        headers=headers,
                        timeout=30
                    )
            else:
                return jsonify({'error': f'不支持的HTTP方法: {method}'}), 405
            
            # 记录响应时间
            response_time = time.time() - start_time
            
            # 处理响应
            if response.status_code == 200:
                self.stats['success_requests'] += 1
                logger.info(f"✅ 请求成功: {response.status_code} - {response_time:.2f}s")
            else:
                self.stats['failed_requests'] += 1
                logger.warning(f"⚠️ 请求失败: {response.status_code} - {response_time:.2f}s")
            
            # 构建响应
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # 添加代理信息到响应头
            flask_response = jsonify(response_data)
            flask_response.status_code = response.status_code
            flask_response.headers['X-Proxy-Server'] = 'LingXing-Cloud-Proxy-WS'
            flask_response.headers['X-Response-Time'] = str(response_time)
            
            return flask_response
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            error_msg = str(e)
            logger.error(f"❌ 代理请求异常: {error_msg}\n{traceback.format_exc()}")
            return jsonify({
                'error': f'代理服务器内部错误: {error_msg}',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def _handle_feishu_request_ws(self, endpoint: str = '/feishu/webhook') -> Response:
        """
        通过WebSocket处理飞书请求转发
        
        Args:
            endpoint: 飞书端点路径
            
        Returns:
            Response: Flask响应对象
        """
        start_time = time.time()
        self.stats['feishu_requests'] += 1
        
        try:
            # 检查是否有活跃的WebSocket连接
            if not self.ws_clients:
                logger.warning("⚠️ 没有活跃的WebSocket连接")
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
                
                # 返回响应
                flask_response = jsonify(response.get('data', {}))
                flask_response.status_code = response.get('status_code', 200)
                flask_response.headers['X-Feishu-Proxy'] = 'Cloud-Proxy-WS'
                flask_response.headers['X-Response-Time'] = str(response_time)
                
                return flask_response
            else:
                return jsonify({
                    'error': '请求超时或连接断开',
                    'timestamp': datetime.now().isoformat()
                }), 504
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 飞书请求异常: {error_msg}\n{traceback.format_exc()}")
            return jsonify({
                'error': f'飞书代理服务器内部错误: {error_msg}',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 500
    
    async def _send_and_wait_response(self, websocket, request_data, request_id, timeout=30):
        """
        发送请求并等待响应
        
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
                    response = self.pending_requests.pop(request_id)
                    return response.get('response')
                await asyncio.sleep(0.1)
            
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
                        logger.info(f"📝 客户端注册: {client_id} - {data.get('local_url')}")
                    
                    elif data.get('type') == 'feishu_response':
                        request_id = data.get('request_id')
                        if request_id:
                            self.pending_requests[request_id] = data
                            logger.info(f"📨 收到响应: {request_id}")
                    
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
        logger.info(f"📊 统计信息接口: http://{self.host}:{self.port}/stats")
        logger.info(f"🔍 健康检查接口: http://{self.host}:{self.port}/health")
        logger.info(f"🧪 连接测试接口: http://{self.host}:{self.port}/test")
        logger.info(f"🔄 代理接口: http://{self.host}:{self.port}/api/proxy/{{endpoint}}")
        logger.info(f"🤖 飞书webhook接口: http://{self.host}:{self.port}/feishu/webhook")
        logger.info(f"🎯 飞书命令接口: http://{self.host}:{self.port}/feishu/command")
        logger.info(f"🔌 WebSocket接口: ws://{self.host}:{self.ws_port}/ws")
        
        # 启动WebSocket服务器
        self.start_websocket_server()
        
        # 启动HTTP服务器
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
            threaded=True
        )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='支持WebSocket的云代理服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8080, help='HTTP服务器监听端口')
    parser.add_argument('--ws-port', type=int, default=8081, help='WebSocket服务器监听端口')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    
    args = parser.parse_args()
    
    # 创建并启动代理服务器
    proxy_server = CloudProxyServerWS(
        host=args.host,
        port=args.port,
        ws_port=args.ws_port,
        debug=args.debug
    )
    
    try:
        proxy_server.run()
    except KeyboardInterrupt:
        logger.info("👋 代理服务器已停止")
    except Exception as e:
        logger.error(f"❌ 代理服务器启动失败: {str(e)}")

if __name__ == '__main__':
    main() 