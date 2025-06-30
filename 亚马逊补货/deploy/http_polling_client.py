#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 HTTP轮询客户端
通过HTTP轮询方式连接云服务器，模拟WebSocket功能
"""

import requests
import json
import time
import threading
import logging
from datetime import datetime
import signal
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HTTPPollingClient:
    """
    🔄 HTTP轮询客户端
    通过HTTP轮询方式处理飞书请求
    """
    
    def __init__(self, cloud_server_url='http://175.178.183.96:8080', local_server_url='http://127.0.0.1:8000'):
        """
        初始化客户端
        
        Args:
            cloud_server_url: 云服务器地址
            local_server_url: 本地服务器地址
        """
        self.cloud_server_url = cloud_server_url
        self.local_server_url = local_server_url
        self.client_id = f"http_client_{int(time.time())}"
        
        # 运行状态
        self.running = False
        
        # HTTP会话
        self.session = requests.Session()
        self.session.timeout = 10
        
        # 统计信息
        self.stats = {
            'requests_processed': 0,
            'start_time': time.time(),
            'last_poll_time': None,
            'errors': 0
        }
        
        logger.info(f"🔄 HTTP轮询客户端初始化完成")
        logger.info(f"🌐 云服务器: {self.cloud_server_url}")
        logger.info(f"🏠 本地服务器: {self.local_server_url}")
        logger.info(f"🆔 客户端ID: {self.client_id}")
    
    def register_client(self):
        """
        向云服务器注册客户端
        """
        try:
            register_data = {
                'client_id': self.client_id,
                'local_url': self.local_server_url,
                'timestamp': datetime.now().isoformat(),
                'service': 'http-polling-client'
            }
            
            response = self.session.post(
                f"{self.cloud_server_url}/register_client",
                json=register_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ 客户端注册成功")
                return True
            else:
                logger.warning(f"⚠️ 客户端注册失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 客户端注册异常: {str(e)}")
            return False
    
    def poll_for_requests(self):
        """
        轮询云服务器获取待处理请求
        """
        try:
            response = self.session.get(
                f"{self.cloud_server_url}/poll_requests",
                params={'client_id': self.client_id},
                timeout=5
            )
            
            self.stats['last_poll_time'] = datetime.now().isoformat()
            
            if response.status_code == 200:
                data = response.json()
                requests_list = data.get('requests', [])
                
                if requests_list:
                    logger.info(f"📥 收到 {len(requests_list)} 个待处理请求")
                    
                    for request_data in requests_list:
                        threading.Thread(
                            target=self.handle_feishu_request,
                            args=(request_data,)
                        ).start()
                
                return True
            elif response.status_code == 204:
                # 没有待处理请求
                return True
            else:
                logger.warning(f"⚠️ 轮询失败: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            # 超时是正常的，继续轮询
            return True
        except Exception as e:
            logger.error(f"❌ 轮询异常: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def handle_feishu_request(self, request_data):
        """
        处理飞书请求
        
        Args:
            request_data: 飞书请求数据
        """
        try:
            request_id = request_data.get('request_id')
            data = request_data.get('data', {})
            
            logger.info(f"📥 处理飞书请求: {request_id}")
            
            # 提取请求信息
            method = data.get('method', 'POST')
            headers = data.get('headers', {})
            json_data = data.get('json_data')
            form_data = data.get('form_data')
            query_params = data.get('args', {})
            endpoint = data.get('endpoint', '/feishu/webhook')
            
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
            self.send_response(request_id, response_info)
            
            self.stats['requests_processed'] += 1
            logger.info(f"✅ 飞书请求处理完成: {request_id} - {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接到本地服务器: {self.local_server_url}")
            self.send_error_response(request_id, "本地服务器连接失败", 503)
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ 本地服务器请求超时: {request_id}")
            self.send_error_response(request_id, "本地服务器请求超时", 408)
            
        except Exception as e:
            logger.error(f"❌ 处理飞书请求失败: {request_id} - {str(e)}")
            self.send_error_response(request_id, f"处理请求失败: {str(e)}", 500)
    
    def send_response(self, request_id, response_info):
        """
        发送响应到云服务器
        
        Args:
            request_id: 请求ID
            response_info: 响应信息
        """
        try:
            response_data = {
                'request_id': request_id,
                'response': response_info,
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.session.post(
                f"{self.cloud_server_url}/submit_response",
                json=response_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"✅ 响应已发送: {request_id}")
            else:
                logger.warning(f"⚠️ 响应发送失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 发送响应异常: {str(e)}")
    
    def send_error_response(self, request_id, error_message, status_code=500):
        """
        发送错误响应
        
        Args:
            request_id: 请求ID
            error_message: 错误消息
            status_code: HTTP状态码
        """
        error_response = {
            'status_code': status_code,
            'headers': {'Content-Type': 'application/json'},
            'data': {
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        self.send_response(request_id, error_response)
    
    def send_heartbeat(self):
        """
        发送心跳到云服务器
        """
        try:
            heartbeat_data = {
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            }
            
            response = self.session.post(
                f"{self.cloud_server_url}/heartbeat",
                json=heartbeat_data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug("💓 心跳已发送")
            
        except Exception as e:
            logger.debug(f"❌ 心跳发送失败: {str(e)}")
    
    def start(self):
        """
        启动HTTP轮询客户端
        """
        logger.info("🚀 启动HTTP轮询客户端")
        self.running = True
        
        # 注册客户端
        self.register_client()
        
        # 轮询循环
        poll_interval = 2  # 2秒轮询间隔
        heartbeat_interval = 30  # 30秒心跳间隔
        last_heartbeat = time.time()
        
        try:
            while self.running:
                # 轮询请求
                self.poll_for_requests()
                
                # 发送心跳
                current_time = time.time()
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.send_heartbeat()
                    last_heartbeat = current_time
                
                # 等待下次轮询
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号")
        except Exception as e:
            logger.error(f"❌ 客户端运行异常: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """
        停止HTTP轮询客户端
        """
        logger.info("🛑 停止HTTP轮询客户端")
        self.running = False
        
        # 发送注销消息
        try:
            unregister_data = {
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.session.post(
                f"{self.cloud_server_url}/unregister_client",
                json=unregister_data,
                timeout=5
            )
            
        except Exception as e:
            logger.debug(f"注销客户端失败: {str(e)}")
    
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
    
    parser = argparse.ArgumentParser(description='🔄 HTTP轮询客户端')
    parser.add_argument('--cloud-server', default='http://175.178.183.96:8080', help='云服务器地址')
    parser.add_argument('--local-server', default='http://127.0.0.1:8000', help='本地服务器地址')
    
    args = parser.parse_args()
    
    # 创建客户端
    client = HTTPPollingClient(
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

if __name__ == '__main__':
    main()
