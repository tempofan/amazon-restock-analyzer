#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 简单HTTP轮询云代理服务器
集成飞书webhook转发功能，使用HTTP轮询机制
"""

import logging
import time
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response
import requests
import threading
from collections import defaultdict, deque
import asyncio
import traceback
from websockets.server import serve
import websockets.exceptions

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/lingxing-proxy/cloud_proxy.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局状态管理
class ProxyState:
    """代理服务器状态管理"""
    
    def __init__(self):
        # 客户端管理
        self.clients = {}  # {client_id: {info, last_heartbeat}}
        self.pending_requests = defaultdict(deque)  # {client_id: [requests]}
        self.responses = {}  # {request_id: response_data}
        
        # 统计信息
        self.stats = {
            'start_time': time.time(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'active_clients': 0,
            'feishu_requests': 0,
            'ws_connections': 0
        }
        
        # 线程锁
        self.lock = threading.RLock()
        
        # 启动清理线程
        self.start_cleanup_thread()
    
    def start_cleanup_thread(self):
        """启动定期清理线程"""
        def cleanup():
            while True:
                try:
                    self.cleanup_expired_data()
                    time.sleep(60)  # 每分钟清理一次
                except Exception as e:
                    logger.error(f"❌ 清理线程异常: {str(e)}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
        logger.info("🧹 清理线程已启动")
    
    def cleanup_expired_data(self):
        """清理过期数据"""
        with self.lock:
            current_time = time.time()
            
            # 清理过期客户端
            expired_clients = []
            for client_id, client_info in self.clients.items():
                if current_time - client_info['last_heartbeat'] > 300:  # 5分钟无心跳
                    expired_clients.append(client_id)
            
            for client_id in expired_clients:
                logger.warning(f"⚠️ 清理过期客户端: {client_id}")
                del self.clients[client_id]
                if client_id in self.pending_requests:
                    del self.pending_requests[client_id]
            
            # 清理过期响应
            expired_responses = []
            for request_id, response_data in self.responses.items():
                response_time = datetime.fromisoformat(response_data['timestamp'])
                if datetime.now() - response_time > timedelta(hours=1):  # 1小时过期
                    expired_responses.append(request_id)
            
            for request_id in expired_responses:
                del self.responses[request_id]
            
            # 更新统计信息
            self.stats['active_clients'] = len(self.clients)
    
    def register_client(self, client_id, client_info):
        """注册客户端"""
        with self.lock:
            self.clients[client_id] = {
                **client_info,
                'last_heartbeat': time.time(),
                'registered_at': time.time()
            }
            logger.info(f"✅ 客户端注册: {client_id}")
    
    def unregister_client(self, client_id):
        """注销客户端"""
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
                if client_id in self.pending_requests:
                    del self.pending_requests[client_id]
                logger.info(f"✅ 客户端注销: {client_id}")
    
    def update_heartbeat(self, client_id, stats=None):
        """更新客户端心跳"""
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id]['last_heartbeat'] = time.time()
                if stats:
                    self.clients[client_id]['stats'] = stats
                return True
            return False
    
    def add_request(self, client_id, request_data):
        """添加待处理请求"""
        with self.lock:
            if client_id not in self.clients:
                return False
            
            self.pending_requests[client_id].append(request_data)
            self.stats['total_requests'] += 1
            logger.info(f"📥 添加请求到队列: {client_id} - {request_data['request_id']}")
            return True
    
    def get_requests(self, client_id):
        """获取客户端的待处理请求"""
        with self.lock:
            if client_id not in self.clients:
                return []
            
            requests_list = list(self.pending_requests[client_id])
            self.pending_requests[client_id].clear()
            return requests_list
    
    def store_response(self, request_id, response_data):
        """存储响应数据"""
        with self.lock:
            self.responses[request_id] = response_data
            self.stats['successful_requests'] += 1
            logger.info(f"✅ 存储响应: {request_id}")
    
    def get_response(self, request_id, timeout=30):
        """获取响应数据（带超时）"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.lock:
                if request_id in self.responses:
                    response_data = self.responses.pop(request_id)
                    return response_data
            
            time.sleep(0.1)  # 100ms检查间隔
        
        # 超时处理
        self.stats['failed_requests'] += 1
        logger.warning(f"⚠️ 响应超时: {request_id}")
        return None
    
    def get_available_client(self):
        """获取可用的客户端"""
        with self.lock:
            for client_id, client_info in self.clients.items():
                if time.time() - client_info['last_heartbeat'] < 60:  # 1分钟内有心跳
                    return client_id
            return None

# 创建全局状态实例
proxy_state = ProxyState()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - proxy_state.stats['start_time'],
        'stats': proxy_state.stats
    })

@app.route('/register_client', methods=['POST'])
def register_client():
    """客户端注册接口"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'error': '客户端ID不能为空'}), 400
        
        proxy_state.register_client(client_id, data)
        
        return jsonify({
            'status': 'success',
            'message': '客户端注册成功',
            'client_id': client_id
        })
        
    except Exception as e:
        logger.error(f"❌ 客户端注册失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/unregister_client', methods=['POST'])
def unregister_client():
    """客户端注销接口"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'error': '客户端ID不能为空'}), 400
        
        proxy_state.unregister_client(client_id)
        
        return jsonify({
            'status': 'success',
            'message': '客户端注销成功'
        })
        
    except Exception as e:
        logger.error(f"❌ 客户端注销失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    """心跳检测接口"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        stats = data.get('stats')
        
        if not client_id:
            return jsonify({'error': '客户端ID不能为空'}), 400
        
        if proxy_state.update_heartbeat(client_id, stats):
            return jsonify({
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': '客户端未注册'}), 404
            
    except Exception as e:
        logger.error(f"❌ 心跳检测失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/poll_requests', methods=['GET'])
def poll_requests():
    """轮询请求接口"""
    try:
        client_id = request.args.get('client_id')
        
        if not client_id:
            return jsonify({'error': '客户端ID不能为空'}), 400
        
        requests_list = proxy_state.get_requests(client_id)
        
        return jsonify({
            'status': 'success',
            'requests': requests_list,
            'count': len(requests_list)
        })
        
    except Exception as e:
        logger.error(f"❌ 轮询请求失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/submit_response', methods=['POST'])
def submit_response():
    """提交响应接口"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({'error': '请求ID不能为空'}), 400
        
        proxy_state.store_response(request_id, data)
        
        return jsonify({
            'status': 'success',
            'message': '响应提交成功'
        })
        
    except Exception as e:
        logger.error(f"❌ 提交响应失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feishu/webhook', methods=['POST'])
def feishu_webhook():
    """飞书webhook接口"""
    try:
        proxy_state.stats['feishu_requests'] += 1
        
        # 获取可用客户端
        client_id = proxy_state.get_available_client()
        if not client_id:
            logger.error("❌ 没有可用的客户端处理飞书请求")
            return jsonify({
                'error': '服务暂时不可用，请稍后重试',
                'code': 'NO_AVAILABLE_CLIENT'
            }), 503
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 构建请求数据
        request_data = {
            'request_id': request_id,
            'endpoint': '/feishu/webhook',
            'method': request.method,
            'headers': dict(request.headers),
            'data': request.get_json() if request.is_json else {},
            'args': dict(request.args),
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加到请求队列
        if not proxy_state.add_request(client_id, request_data):
            return jsonify({
                'error': '客户端不可用',
                'code': 'CLIENT_UNAVAILABLE'
            }), 503
        
        logger.info(f"📤 飞书请求已转发: {request_id} -> {client_id}")
        
        # 等待响应
        response_data = proxy_state.get_response(request_id, timeout=30)
        
        if response_data:
            # 构建Flask响应
            status_code = response_data.get('status_code', 200)
            headers = response_data.get('headers', {})
            content = response_data.get('content', '')
            
            # 过滤响应头
            filtered_headers = {}
            for key, value in headers.items():
                if key.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                    filtered_headers[key] = value
            
            logger.info(f"✅ 飞书请求处理完成: {request_id} - {status_code}")
            
            return Response(
                content,
                status=status_code,
                headers=filtered_headers
            )
        else:
            # 超时响应
            logger.error(f"❌ 飞书请求处理超时: {request_id}")
            return jsonify({
                'error': '请求处理超时',
                'code': 'REQUEST_TIMEOUT',
                'request_id': request_id
            }), 504
            
    except Exception as e:
        logger.error(f"❌ 飞书webhook处理异常: {str(e)}")
        return jsonify({
            'error': '服务器内部错误',
            'code': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    try:
        uptime = time.time() - proxy_state.stats['start_time']
        
        stats = {
            **proxy_state.stats,
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'clients': {}
        }
        
        # 添加客户端信息
        with proxy_state.lock:
            for client_id, client_info in proxy_state.clients.items():
                stats['clients'][client_id] = {
                    'local_server': client_info.get('local_server'),
                    'last_heartbeat': client_info['last_heartbeat'],
                    'registered_at': client_info['registered_at'],
                    'stats': client_info.get('stats', {})
                }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 原有的领星API代理功能保持不变
@app.route('/api/lingxing/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_to_lingxing(path):
    """代理到领星API"""
    try:
        target_url = f"https://openapi.lingxing.com/{path}"
        
        # 获取请求数据
        headers = dict(request.headers)
        data = request.get_data()
        params = dict(request.args)
        
        # 发送请求到领星API
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            params=params,
            timeout=30
        )
        
        # 构建响应
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.raw.headers.items()
                  if name.lower() not in excluded_headers]
        
        return Response(response.content, response.status_code, headers)
        
    except Exception as e:
        logger.error(f"❌ 领星API代理失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
                    self.stats['successful_requests'] / max(self.stats['total_requests'], 1) * 100
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
                
                self.stats['successful_requests'] += 1
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