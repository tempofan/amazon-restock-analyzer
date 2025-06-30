#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 领星API云代理服务器
用于将本机的API请求转发到领星API服务器，解决IP白名单问题

部署说明：
1. 将此文件上传到有固定公网IP的云服务器
2. 在领星ERP后台将云服务器IP添加到白名单
3. 启动代理服务: python cloud_proxy_server.py
4. 修改本机项目配置，将API请求指向此代理服务器
"""

import logging
import time
import json
import traceback
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

class CloudProxyServer:
    """
    🚀 云代理服务器类
    负责转发API请求并提供监控功能
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
        
        # 本地服务器配置（飞书webhook转发目标）
        self.local_server_url = "http://192.168.0.99:8000"
        
        # 请求统计
        self.stats = {
            'total_requests': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'feishu_requests': 0,
            'start_time': time.time()
        }
        
        # 创建HTTP会话
        self.session = self._create_session()
        
        # 注册路由
        self._register_routes()
        
        logger.info(f"🌐 云代理服务器初始化完成 - {host}:{port}")
    
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
        """注册所有路由"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """🔍 健康检查接口"""
            return jsonify({
                'status': 'healthy',
                'server': f'cloud-server:{self.port}',
                'service': 'feishu-webhook',
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
                )
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
            """🤖 飞书webhook转发接口"""
            return self._handle_feishu_request()
        
        @self.app.route('/feishu/command', methods=['POST'])
        def feishu_command():
            """🎯 飞书命令转发接口"""
            return self._handle_feishu_request('/feishu/command')
        
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
            
            logger.info(f"🔄 转发请求: {method} {target_url}")
            
            # 根据请求方法处理
            if method == 'GET':
                response = self.session.get(
                    target_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
            elif method == 'POST':
                # 处理POST请求数据
                if request.is_json:
                    json_data = request.get_json()
                    response = self.session.post(
                        target_url,
                        params=params,
                        json=json_data,
                        headers=headers,
                        timeout=30
                    )
                else:
                    response = self.session.post(
                        target_url,
                        params=params,
                        data=request.get_data(),
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
            flask_response.headers['X-Proxy-Server'] = 'LingXing-Cloud-Proxy'
            flask_response.headers['X-Response-Time'] = str(response_time)
            
            return flask_response
            
        except requests.exceptions.Timeout:
            self.stats['failed_requests'] += 1
            logger.error(f"⏰ 请求超时: {endpoint}")
            return jsonify({
                'error': '请求超时',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 504
            
        except requests.exceptions.ConnectionError:
            self.stats['failed_requests'] += 1
            logger.error(f"🔌 连接错误: {endpoint}")
            return jsonify({
                'error': '连接领星API失败',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 502
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            error_msg = str(e)
            logger.error(f"❌ 代理请求异常: {error_msg}\n{traceback.format_exc()}")
            return jsonify({
                'error': f'代理服务器内部错误: {error_msg}',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
                            }), 500
    
    def _handle_feishu_request(self, endpoint: str = '/feishu/webhook') -> Response:
        """
        处理飞书请求转发的核心逻辑
        
        Args:
            endpoint: 飞书端点路径
            
        Returns:
            Response: Flask响应对象
        """
        start_time = time.time()
        self.stats['feishu_requests'] += 1
        
        try:
            # 构建目标URL
            target_url = f"{self.local_server_url}{endpoint}"
            
            # 获取原始请求信息
            method = request.method
            headers = dict(request.headers)
            
            # 移除代理相关的头部
            headers_to_remove = ['Host', 'Content-Length']
            for header in headers_to_remove:
                headers.pop(header, None)
            
            # 设置User-Agent
            headers['User-Agent'] = 'Feishu-Cloud-Proxy/1.0'
            
            logger.info(f"🤖 转发飞书请求: {method} {target_url}")
            
            # 处理POST请求数据
            if request.is_json:
                json_data = request.get_json()
                logger.info(f"📝 飞书请求内容: {json.dumps(json_data, ensure_ascii=False)}")
                
                response = self.session.post(
                    target_url,
                    json=json_data,
                    headers=headers,
                    timeout=30
                )
            else:
                response = self.session.post(
                    target_url,
                    data=request.get_data(),
                    headers=headers,
                    timeout=30
                )
            
            # 记录响应时间
            response_time = time.time() - start_time
            
            # 处理响应
            logger.info(f"🤖 飞书请求响应: {response.status_code} - {response_time:.2f}s")
            
            # 构建响应
            try:
                response_data = response.json()
                logger.info(f"📄 飞书响应内容: {json.dumps(response_data, ensure_ascii=False)}")
            except:
                response_data = response.text
                logger.info(f"📄 飞书响应文本: {response_data}")
            
            # 构建Flask响应
            flask_response = jsonify(response_data)
            flask_response.status_code = response.status_code
            flask_response.headers['X-Feishu-Proxy'] = 'Cloud-Proxy'
            flask_response.headers['X-Response-Time'] = str(response_time)
            
            return flask_response
            
        except requests.exceptions.Timeout:
            logger.error(f"⏰ 飞书请求超时: {endpoint}")
            return jsonify({
                'error': '请求超时',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 504
            
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 飞书连接错误: {endpoint}")
            return jsonify({
                'error': '连接本地服务器失败',
                'endpoint': endpoint,
                'local_server': self.local_server_url,
                'timestamp': datetime.now().isoformat()
            }), 502
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 飞书请求异常: {error_msg}\n{traceback.format_exc()}")
            return jsonify({
                'error': f'飞书代理服务器内部错误: {error_msg}',
                'endpoint': endpoint,
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def run(self):
        """🚀 启动代理服务器"""
        logger.info(f"🚀 启动云代理服务器: http://{self.host}:{self.port}")
        logger.info(f"📊 统计信息接口: http://{self.host}:{self.port}/stats")
        logger.info(f"🔍 健康检查接口: http://{self.host}:{self.port}/health")
        logger.info(f"🧪 连接测试接口: http://{self.host}:{self.port}/test")
        logger.info(f"🔄 代理接口: http://{self.host}:{self.port}/api/proxy/{{endpoint}}")
        logger.info(f"🤖 飞书webhook接口: http://{self.host}:{self.port}/feishu/webhook")
        logger.info(f"🎯 飞书命令接口: http://{self.host}:{self.port}/feishu/command")
        logger.info(f"🏠 本地服务器转发目标: {self.local_server_url}")
        
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
            threaded=True
        )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='领星API云代理服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器监听地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器监听端口')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    
    args = parser.parse_args()
    
    # 创建并启动代理服务器
    proxy_server = CloudProxyServer(
        host=args.host,
        port=args.port,
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