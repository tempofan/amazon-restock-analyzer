#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 SocketIO反向代理客户端
连接到集成云代理服务器，处理飞书请求转发
"""

import logging
import time
import json
import requests
import socketio
from datetime import datetime
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reverse_proxy_client.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReverseProxyClientSocketIO:
    """
    🔄 SocketIO反向代理客户端类
    连接到云服务器，处理飞书请求转发
    """
    
    def __init__(self, cloud_server_url='http://175.178.183.96:8080', local_server_url='http://192.168.0.105:5000'):
        """
        初始化反向代理客户端
        
        Args:
            cloud_server_url: 云服务器地址
            local_server_url: 本地服务器地址
        """
        self.cloud_server_url = cloud_server_url
        self.local_server_url = local_server_url
        
        # 创建SocketIO客户端
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=0,  # 无限重连
            reconnection_delay=1,
            reconnection_delay_max=5
        )
        
        # 创建HTTP会话
        self.session = requests.Session()
        self.session.timeout = 10
        
        # 注册SocketIO事件处理器
        self._register_events()
        
        # 统计信息
        self.stats = {
            'connected': False,
            'requests_processed': 0,
            'connection_attempts': 0,
            'start_time': time.time()
        }
        
        logger.info(f"🔄 反向代理客户端初始化完成")
        logger.info(f"🌐 云服务器: {self.cloud_server_url}")
        logger.info(f"🏠 本地服务器: {self.local_server_url}")
    
    def _register_events(self):
        """注册SocketIO事件处理器"""
        
        @self.sio.event
        def connect():
            """连接成功事件"""
            self.stats['connected'] = True
            logger.info("🔗 成功连接到云服务器")
            
            # 发送注册消息
            self.sio.emit('register', {
                'client_type': 'reverse_proxy',
                'local_server': self.local_server_url,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.sio.event
        def disconnect():
            """断开连接事件"""
            self.stats['connected'] = False
            logger.warning("🔌 与云服务器断开连接")
        
        @self.sio.event
        def connected(data):
            """连接确认事件"""
            logger.info(f"✅ 连接确认: {data}")
        
        @self.sio.event
        def registered(data):
            """注册确认事件"""
            logger.info(f"✅ 注册成功: {data}")
        
        @self.sio.event
        def feishu_request(data):
            """处理飞书请求事件"""
            self._handle_feishu_request(data)
        
        @self.sio.event
        def pong(data):
            """心跳响应事件"""
            logger.debug(f"💓 收到心跳响应: {data}")
    
    def _handle_feishu_request(self, data):
        """
        处理飞书请求
        
        Args:
            data: 请求数据
        """
        try:
            request_id = data.get('request_id')
            request_data = data.get('data', {})
            
            logger.info(f"📥 收到飞书请求: {request_id}")
            
            # 提取请求信息
            endpoint = request_data.get('endpoint', '/feishu/webhook')
            method = request_data.get('method', 'POST')
            headers = request_data.get('headers', {})
            payload = request_data.get('data', {})
            params = request_data.get('args', {})
            
            # 构建本地服务器URL
            target_url = f"{self.local_server_url}{endpoint}"
            
            # 转发请求到本地服务器
            if method.upper() == 'POST':
                response = self.session.post(
                    target_url,
                    json=payload,
                    headers=headers,
                    params=params,
                    timeout=10
                )
            else:
                response = self.session.get(
                    target_url,
                    headers=headers,
                    params=params,
                    timeout=10
                )
            
            # 准备响应数据
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送响应回云服务器
            self.sio.emit('response', {
                'request_id': request_id,
                'data': response_data
            })
            
            self.stats['requests_processed'] += 1
            logger.info(f"✅ 请求处理完成: {request_id} - {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接到本地服务器: {self.local_server_url}")
            self._send_error_response(request_id, "本地服务器连接失败")
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ 本地服务器请求超时: {request_id}")
            self._send_error_response(request_id, "本地服务器请求超时")
            
        except Exception as e:
            logger.error(f"❌ 处理飞书请求失败: {request_id} - {str(e)}")
            self._send_error_response(request_id, f"处理请求失败: {str(e)}")
    
    def _send_error_response(self, request_id, error_message):
        """
        发送错误响应
        
        Args:
            request_id: 请求ID
            error_message: 错误消息
        """
        try:
            self.sio.emit('response', {
                'request_id': request_id,
                'data': {
                    'status_code': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'content': json.dumps({
                        'error': error_message,
                        'timestamp': datetime.now().isoformat()
                    }),
                    'timestamp': datetime.now().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"❌ 发送错误响应失败: {str(e)}")
    
    def _start_heartbeat(self):
        """启动心跳检测"""
        def heartbeat():
            while True:
                try:
                    if self.sio.connected:
                        self.sio.emit('ping', {
                            'timestamp': datetime.now().isoformat()
                        })
                    time.sleep(30)  # 30秒心跳间隔
                except Exception as e:
                    logger.error(f"❌ 心跳检测失败: {str(e)}")
                    time.sleep(5)
        
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
        logger.info("💓 心跳检测已启动")
    
    def connect(self):
        """连接到云服务器"""
        max_retries = 0  # 无限重试
        retry_count = 0
        
        while max_retries == 0 or retry_count < max_retries:
            try:
                self.stats['connection_attempts'] += 1
                logger.info(f"🔗 尝试连接到云服务器: {self.cloud_server_url}")
                
                self.sio.connect(self.cloud_server_url)
                
                # 启动心跳检测
                self._start_heartbeat()
                
                logger.info("🚀 反向代理客户端启动成功")
                
                # 保持连接
                self.sio.wait()
                
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ 连接失败 (尝试 {retry_count}): {str(e)}")
                
                if max_retries == 0 or retry_count < max_retries:
                    wait_time = min(5, retry_count)
                    logger.info(f"⏳ {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error("❌ 达到最大重试次数，停止连接")
                    break
    
    def disconnect(self):
        """断开连接"""
        if self.sio.connected:
            self.sio.disconnect()
            logger.info("🔌 已断开连接")
    
    def get_stats(self):
        """获取统计信息"""
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600
        }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🔄 SocketIO反向代理客户端')
    parser.add_argument('--cloud-server', default='http://175.178.183.96:8080', help='云服务器地址')
    parser.add_argument('--local-server', default='http://192.168.0.105:5000', help='本地服务器地址')
    
    args = parser.parse_args()
    
    # 创建并启动客户端
    client = ReverseProxyClientSocketIO(
        cloud_server_url=args.cloud_server,
        local_server_url=args.local_server
    )
    
    try:
        client.connect()
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
        client.disconnect()
    except Exception as e:
        logger.error(f"❌ 客户端运行异常: {str(e)}")
        raise

if __name__ == '__main__':
    main() 