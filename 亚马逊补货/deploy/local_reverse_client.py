#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔌 本地反向代理客户端
连接到云代理服务器，处理飞书请求转发
"""

import socketio
import requests
import json
import logging
import time
import asyncio
from datetime import datetime
import signal
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('local_reverse_client.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LocalReverseClient:
    """
    🔌 本地反向代理客户端
    与云代理服务器建立SocketIO连接，处理飞书请求转发
    """
    
    def __init__(self, cloud_server_url='http://175.178.183.96:8080', local_server_url='http://192.168.0.99:8000'):
        """
        初始化本地反向代理客户端
        
        Args:
            cloud_server_url: 云服务器地址
            local_server_url: 本地服务器地址
        """
        self.cloud_server_url = cloud_server_url
        self.local_server_url = local_server_url
        self.client_id = f"local_client_{int(time.time())}"
        
        # 创建SocketIO客户端
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=0,  # 无限重连
            reconnection_delay=1,
            reconnection_delay_max=60
        )
        
        # 创建HTTP会话
        self.session = requests.Session()
        self.session.timeout = 15
        
        # 运行状态
        self.running = False
        self.connected = False
        
        # 统计信息
        self.stats = {
            'connected': False,
            'requests_processed': 0,
            'connection_attempts': 0,
            'start_time': time.time(),
            'last_request_time': None
        }
        
        # 注册事件处理器
        self._register_events()
        
        logger.info(f"🔌 本地反向代理客户端初始化完成")
        logger.info(f"🌐 云服务器: {self.cloud_server_url}")
        logger.info(f"🏠 本地服务器: {self.local_server_url}")
        logger.info(f"🆔 客户端ID: {self.client_id}")
    
    def _register_events(self):
        """注册SocketIO事件处理器"""
        
        @self.sio.event
        def connect():
            """连接成功事件"""
            self.connected = True
            self.stats['connected'] = True
            logger.info("✅ 已连接到云代理服务器")
            
            # 注册为本地服务器客户端
            self.sio.emit('register', {
                'type': 'local_server',
                'client_id': self.client_id,
                'local_url': self.local_server_url,
                'timestamp': datetime.now().isoformat(),
                'service': 'feishu-webhook-handler'
            })
        
        @self.sio.event
        def disconnect():
            """断开连接事件"""
            self.connected = False
            self.stats['connected'] = False
            logger.warning("⚠️ 与云代理服务器断开连接")
        
        @self.sio.event
        def registered(data):
            """注册确认事件"""
            logger.info(f"✅ 客户端注册成功: {data}")
        
        @self.sio.event
        def feishu_request(data):
            """处理飞书请求事件"""
            asyncio.create_task(self._handle_feishu_request(data))
        
        @self.sio.event
        def connect_error(data):
            """连接错误事件"""
            logger.error(f"❌ 连接错误: {data}")
            self.stats['connection_attempts'] += 1
    
    async def _handle_feishu_request(self, data):
        """
        处理飞书请求
        
        Args:
            data: 飞书请求数据
        """
        try:
            request_id = data.get('request_id')
            request_data = data.get('data', {})
            
            logger.info(f"📥 处理飞书请求: {request_id}")
            
            # 提取请求信息
            method = request_data.get('method', 'POST')
            headers = request_data.get('headers', {})
            json_data = request_data.get('json_data')
            form_data = request_data.get('form_data')
            query_params = request_data.get('args', {})
            endpoint = request_data.get('endpoint', '/feishu/webhook')
            
            # 构建本地服务器URL
            target_url = f"{self.local_server_url}{endpoint}"
            
            # 准备请求参数
            request_kwargs = {
                'headers': headers,
                'params': query_params,
                'timeout': 15
            }
            
            # 根据数据类型设置请求体
            if json_data:
                request_kwargs['json'] = json_data
            elif form_data:
                request_kwargs['data'] = form_data
            
            # 发送请求到本地服务器
            if method.upper() == 'POST':
                response = self.session.post(target_url, **request_kwargs)
            else:
                response = self.session.get(target_url, **request_kwargs)
            
            # 准备响应数据
            try:
                # 尝试解析JSON响应
                response_data = response.json()
            except:
                # 如果不是JSON，使用文本
                response_data = response.text
            
            response_info = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response_data
            }
            
            # 发送响应回云服务器
            self.sio.emit('response', {
                'request_id': request_id,
                'response': response_info,
                'timestamp': datetime.now().isoformat()
            })
            
            self.stats['requests_processed'] += 1
            self.stats['last_request_time'] = datetime.now().isoformat()
            logger.info(f"✅ 飞书请求处理完成: {request_id} - {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接到本地服务器: {self.local_server_url}")
            await self._send_error_response(request_id, "本地服务器连接失败", 503)
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ 本地服务器请求超时: {request_id}")
            await self._send_error_response(request_id, "本地服务器请求超时", 408)
            
        except Exception as e:
            logger.error(f"❌ 处理飞书请求失败: {request_id} - {str(e)}")
            await self._send_error_response(request_id, f"处理请求失败: {str(e)}", 500)
    
    async def _send_error_response(self, request_id, error_message, status_code=500):
        """
        发送错误响应
        
        Args:
            request_id: 请求ID
            error_message: 错误消息
            status_code: HTTP状态码
        """
        try:
            error_response = {
                'status_code': status_code,
                'headers': {'Content-Type': 'application/json'},
                'data': {
                    'error': error_message,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            self.sio.emit('response', {
                'request_id': request_id,
                'response': error_response,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ 发送错误响应失败: {str(e)}")
    
    def start(self):
        """
        启动反向代理客户端
        """
        logger.info("🚀 启动本地反向代理客户端")
        self.running = True
        
        try:
            # 连接到云服务器
            logger.info(f"🔗 连接到云代理服务器: {self.cloud_server_url}")
            self.sio.connect(self.cloud_server_url)
            
            # 保持连接
            while self.running:
                time.sleep(1)
                
                # 定期发送心跳（可选）
                if self.connected and int(time.time()) % 30 == 0:
                    self._send_heartbeat()
                    
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号")
        except Exception as e:
            logger.error(f"❌ 客户端运行异常: {str(e)}")
        finally:
            self.stop()
    
    def _send_heartbeat(self):
        """发送心跳消息"""
        try:
            heartbeat_data = {
                'type': 'heartbeat',
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            }
            
            self.sio.emit('heartbeat', heartbeat_data)
            logger.debug("💓 心跳消息已发送")
            
        except Exception as e:
            logger.error(f"❌ 发送心跳失败: {str(e)}")
    
    def stop(self):
        """
        停止反向代理客户端
        """
        logger.info("🛑 停止本地反向代理客户端")
        self.running = False
        self.connected = False
        self.stats['connected'] = False
        
        try:
            if self.sio.connected:
                self.sio.disconnect()
                logger.info("✅ 已断开与云服务器的连接")
        except Exception as e:
            logger.error(f"❌ 断开连接失败: {str(e)}")
    
    def get_stats(self):
        """
        获取统计信息
        
        Returns:
            dict: 统计信息
        """
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600
        }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🔌 本地反向代理客户端')
    parser.add_argument('--cloud-server', default='http://175.178.183.96:8080', help='云服务器地址')
    parser.add_argument('--local-server', default='http://192.168.0.99:8000', help='本地服务器地址')
    
    args = parser.parse_args()
    
    # 创建客户端
    client = LocalReverseClient(
        cloud_server_url=args.cloud_server,
        local_server_url=args.local_server
    )
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info("🛑 收到停止信号")
        client.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        client.start()
    except Exception as e:
        logger.error(f"❌ 客户端运行异常: {str(e)}")
        raise

if __name__ == '__main__':
    main()
