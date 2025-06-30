#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 单端口云代理服务器
同时支持HTTP和WebSocket连接，解决端口开放问题
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

class CloudProxyServerSinglePort:
    """
    🚀 单端口云代理服务器类
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
        CORS(self.app)  # 允许跨域请求
        
        self.host = host
        self.port = port
        self.debug = debug
        
        # 领星API配置
        self.lingxing_base_url = "https://openapi.lingxing.com"
        
        # WebSocket连接管理（暂时使用简化版本）
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
        
        logger.info(f"🌐 单端口云代理服务器初始化完成 - {host}:{port}")
    
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
                'service': 'feishu-webhook-single-port',
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
            """🤖 飞书webhook接口 - 直接转发到本地服务器"""
            return self._handle_feishu_request_direct()
        
        @self.app.route('/feishu/command', methods=['POST'])
        def feishu_command():
            """🎯 飞书命令接口 - 直接转发到本地服务器"""
            return self._handle_feishu_request_direct('/feishu/command')
        
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
    
    def _handle_feishu_request_direct(self, endpoint: str = '/feishu/webhook') -> Response:
        """
        直接转发飞书请求到本地服务器（固定IP方案）
        
        Args:
            endpoint: 飞书接口端点
            
        Returns:
            Response: Flask响应对象
        """
        self.stats['feishu_requests'] += 1
        
        try:
            # 本地服务器地址
            local_server_url = "http://192.168.0.105:5000"
            target_url = f"{local_server_url}{endpoint}"
            
            # 准备请求数据
            if request.method == 'POST':
                data = request.get_json() if request.is_json else request.form.to_dict()
                headers = dict(request.headers)
                
                # 转发POST请求
                response = self.session.post(
                    target_url,
                    json=data if request.is_json else None,
                    data=None if request.is_json else data,
                    headers=headers,
                    timeout=10
                )
            else:
                # 转发GET请求
                params = request.args.to_dict()
                headers = dict(request.headers)
                
                response = self.session.get(
                    target_url,
                    params=params,
                    headers=headers,
                    timeout=10
                )
            
            logger.info(f"✅ 飞书请求转发成功: {endpoint} - {response.status_code}")
            
            # 返回响应
            return Response(
                response.content,
                status=response.status_code,
                headers=dict(response.headers)
            )
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接到本地服务器: {endpoint}")
            return jsonify({
                'error': '本地服务器连接失败',
                'message': '请确保本地飞书服务器正在运行',
                'local_server': '192.168.0.105:5000',
                'timestamp': datetime.now().isoformat()
            }), 503
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ 本地服务器请求超时: {endpoint}")
            return jsonify({
                'error': '本地服务器请求超时',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 408
            
        except Exception as e:
            logger.error(f"❌ 处理飞书请求失败: {endpoint} - {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': f'处理飞书请求失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def run(self):
        """
        🚀 启动代理服务器
        """
        logger.info(f"🚀 启动单端口云代理服务器: http://{self.host}:{self.port}")
        logger.info(f"📊 统计信息接口: http://{self.host}:{self.port}/stats")
        logger.info(f"🔍 健康检查接口: http://{self.host}:{self.port}/health")
        logger.info(f"🧪 连接测试接口: http://{self.host}:{self.port}/test")
        logger.info(f"🔄 代理接口: http://{self.host}:{self.port}/api/proxy/{{endpoint}}")
        logger.info(f"🤖 飞书webhook接口: http://{self.host}:{self.port}/feishu/webhook")
        logger.info(f"🎯 飞书命令接口: http://{self.host}:{self.port}/feishu/command")
        logger.info(f"📡 本地服务器: http://192.168.0.105:5000")
        
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=self.debug,
                threaded=True
            )
        except KeyboardInterrupt:
            logger.info("🛑 服务器已停止")
        except Exception as e:
            logger.error(f"❌ 服务器启动失败: {str(e)}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='🌐 单端口云代理服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器监听端口')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    
    args = parser.parse_args()
    
    # 创建并启动服务器
    server = CloudProxyServerSinglePort(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    server.run()

if __name__ == '__main__':
    main() 