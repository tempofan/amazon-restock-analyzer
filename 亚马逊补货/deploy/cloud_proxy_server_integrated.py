#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 集成云代理服务器
在8080端口上同时支持HTTP和WebSocket连接
"""

import logging
import time
import json
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import argparse
import threading

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

class CloudProxyServerIntegrated:
    """
    🚀 集成云代理服务器类
    在同一端口上同时支持HTTP和WebSocket连接
    """
    
    def __init__(self, host='0.0.0.0', port=8080, debug=False):
        """
        初始化代理服务器
        
        Args:
            host: 服务器监听地址
            port: 服务器监听端口
            debug: 是否开启调试模式
        """
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'lingxing-proxy-secret-key'
        CORS(self.app)  # 允许跨域请求
        
        # 初始化SocketIO
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False
        )
        
        self.host = host
        self.port = port
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
        self._register_socketio_events()
        
        logger.info(f"🌐 集成云代理服务器初始化完成 - {host}:{port}")
    
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
                'service': 'feishu-webhook-integrated',
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
    
    def _register_socketio_events(self):
        """注册SocketIO事件处理器"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """客户端连接事件"""
            client_id = request.sid
            self.ws_clients[client_id] = {
                'connected_at': datetime.now().isoformat(),
                'last_ping': time.time()
            }
            self.stats['ws_connections'] += 1
            
            logger.info(f"🔗 WebSocket客户端连接: {client_id}")
            
            # 发送连接确认
            emit('connected', {
                'client_id': client_id,
                'message': '连接成功',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """客户端断开连接事件"""
            client_id = request.sid
            if client_id in self.ws_clients:
                del self.ws_clients[client_id]
            
            logger.info(f"🔌 WebSocket客户端断开: {client_id}")
        
        @self.socketio.on('ping')
        def handle_ping(data):
            """处理心跳检测"""
            client_id = request.sid
            if client_id in self.ws_clients:
                self.ws_clients[client_id]['last_ping'] = time.time()
            
            emit('pong', {
                'timestamp': datetime.now().isoformat(),
                'message': 'pong'
            })
        
        @self.socketio.on('register')
        def handle_register(data):
            """处理客户端注册"""
            client_id = request.sid
            logger.info(f"✅ 客户端 {client_id} 注册成功")
            
            emit('registered', {
                'client_id': client_id,
                'message': '注册成功',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('response')
        def handle_response(data):
            """处理来自本地服务器的响应"""
            client_id = request.sid
            request_id = data.get('request_id')
            
            if request_id and request_id in self.pending_requests:
                # 将响应数据存储，供HTTP请求使用
                self.pending_requests[request_id]['response'] = data.get('data', {})
                self.pending_requests[request_id]['completed'] = True
                logger.info(f"✅ 收到请求 {request_id} 的响应")
    
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
            
            # 准备请求数据
            if request.method == 'POST':
                data = request.get_json() if request.is_json else request.form.to_dict()
                headers = dict(request.headers)
                
                # 发送POST请求
                response = self.session.post(
                    target_url,
                    json=data if request.is_json else None,
                    data=None if request.is_json else data,
                    headers=headers,
                    timeout=30
                )
            else:
                # 发送GET请求
                params = request.args.to_dict()
                headers = dict(request.headers)
                
                response = self.session.get(
                    target_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
            
            # 记录成功
            self.stats['success_requests'] += 1
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            logger.info(f"✅ 代理请求成功: {endpoint} - {response.status_code} - {response_time:.2f}s")
            
            # 返回响应
            return Response(
                response.content,
                status=response.status_code,
                headers=dict(response.headers)
            )
            
        except requests.exceptions.Timeout:
            self.stats['failed_requests'] += 1
            logger.error(f"❌ 请求超时: {endpoint}")
            return jsonify({
                'error': '请求超时',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 408
            
        except requests.exceptions.RequestException as e:
            self.stats['failed_requests'] += 1
            logger.error(f"❌ 请求失败: {endpoint} - {str(e)}")
            return jsonify({
                'error': f'请求失败: {str(e)}',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 502
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"❌ 代理请求异常: {endpoint} - {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': f'内部服务器错误: {str(e)}',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def _handle_feishu_request_ws(self, endpoint: str = '/feishu/webhook') -> Response:
        """
        通过WebSocket处理飞书请求
        
        Args:
            endpoint: 飞书接口端点
            
        Returns:
            Response: Flask响应对象
        """
        self.stats['feishu_requests'] += 1
        
        try:
            # 检查是否有可用的WebSocket连接
            if not self.ws_clients:
                logger.error("❌ 没有可用的WebSocket连接")
                return jsonify({
                    'error': '本地服务器未连接',
                    'message': '请确保本地反向代理客户端正在运行',
                    'timestamp': datetime.now().isoformat()
                }), 503
            
            # 准备转发数据
            request_data = {
                'endpoint': endpoint,
                'method': request.method,
                'headers': dict(request.headers),
                'data': request.get_json() if request.is_json else request.form.to_dict(),
                'args': request.args.to_dict()
            }
            
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 存储待处理请求
            self.pending_requests[request_id] = {
                'created_at': time.time(),
                'completed': False,
                'response': None
            }
            
            # 构建WebSocket消息
            ws_message = {
                'type': 'feishu_request',
                'request_id': request_id,
                'data': request_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送到所有连接的客户端
            self.socketio.emit('feishu_request', ws_message)
            logger.info(f"📤 已通过WebSocket转发飞书请求: {endpoint}")
            
            # 等待响应（简化版本，实际应用中可能需要异步处理）
            timeout = 30  # 30秒超时
            start_wait = time.time()
            
            while time.time() - start_wait < timeout:
                if self.pending_requests[request_id]['completed']:
                    response_data = self.pending_requests[request_id]['response']
                    del self.pending_requests[request_id]
                    
                    return jsonify({
                        'status': 'success',
                        'message': '请求处理完成',
                        'data': response_data,
                        'request_id': request_id,
                        'timestamp': datetime.now().isoformat()
                    })
                
                time.sleep(0.1)  # 短暂等待
            
            # 超时处理
            del self.pending_requests[request_id]
            return jsonify({
                'error': '请求处理超时',
                'message': '本地服务器响应超时',
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            }), 408
            
        except Exception as e:
            logger.error(f"❌ 处理飞书请求失败: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': f'处理飞书请求失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def run(self):
        """
        🚀 启动代理服务器
        """
        logger.info(f"🚀 启动集成云代理服务器: http://{self.host}:{self.port}")
        logger.info(f"📊 统计信息接口: http://{self.host}:{self.port}/stats")
        logger.info(f"🔍 健康检查接口: http://{self.host}:{self.port}/health")
        logger.info(f"🧪 连接测试接口: http://{self.host}:{self.port}/test")
        logger.info(f"🔄 代理接口: http://{self.host}:{self.port}/api/proxy/{{endpoint}}")
        logger.info(f"🤖 飞书webhook接口: http://{self.host}:{self.port}/feishu/webhook")
        logger.info(f"🎯 飞书命令接口: http://{self.host}:{self.port}/feishu/command")
        logger.info(f"🔌 WebSocket接口: ws://{self.host}:{self.port}/socket.io/")
        
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                allow_unsafe_werkzeug=True
            )
        except KeyboardInterrupt:
            logger.info("🛑 服务器已停止")
        except Exception as e:
            logger.error(f"❌ 服务器启动失败: {str(e)}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='🌐 集成云代理服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器监听端口')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    
    args = parser.parse_args()
    
    # 创建并启动服务器
    server = CloudProxyServerIntegrated(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    server.run()

if __name__ == '__main__':
    main() 