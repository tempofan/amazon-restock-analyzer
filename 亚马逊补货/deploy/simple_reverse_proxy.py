#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 简单HTTP轮询反向代理客户端
使用HTTP轮询机制连接云服务器，无需WebSocket依赖
"""

import logging
import time
import json
import requests
from datetime import datetime
import threading
import queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_reverse_proxy.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleReverseProxyClient:
    """
    🔄 简单HTTP轮询反向代理客户端
    通过HTTP轮询方式处理云服务器的飞书请求转发
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
        self.client_id = f"client_{int(time.time())}"
        
        # 创建HTTP会话
        self.session = requests.Session()
        self.session.timeout = 10
        
        # 控制运行状态
        self.running = False
        self.poll_interval = 2  # 轮询间隔（秒）
        
        # 统计信息
        self.stats = {
            'connected': False,
            'requests_processed': 0,
            'poll_attempts': 0,
            'start_time': time.time()
        }
        
        logger.info(f"🔄 简单反向代理客户端初始化完成")
        logger.info(f"🌐 云服务器: {self.cloud_server_url}")
        logger.info(f"🏠 本地服务器: {self.local_server_url}")
        logger.info(f"🆔 客户端ID: {self.client_id}")
    
    def register_client(self):
        """
        向云服务器注册客户端
        
        Returns:
            bool: 注册是否成功
        """
        try:
            response = self.session.post(
                f"{self.cloud_server_url}/register_client",
                json={
                    'client_id': self.client_id,
                    'local_server': self.local_server_url,
                    'timestamp': datetime.now().isoformat()
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ 客户端注册成功")
                self.stats['connected'] = True
                return True
            else:
                logger.warning(f"⚠️ 客户端注册失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 客户端注册异常: {str(e)}")
            return False
    
    def poll_requests(self):
        """
        轮询云服务器获取待处理的请求
        
        Returns:
            list: 待处理的请求列表
        """
        try:
            self.stats['poll_attempts'] += 1
            
            response = self.session.get(
                f"{self.cloud_server_url}/poll_requests",
                params={'client_id': self.client_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                requests_list = data.get('requests', [])
                
                if requests_list:
                    logger.info(f"📥 获取到 {len(requests_list)} 个待处理请求")
                
                return requests_list
            else:
                logger.debug(f"轮询响应: {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            logger.debug("轮询超时")
            return []
        except Exception as e:
            logger.error(f"❌ 轮询请求异常: {str(e)}")
            return []
    
    def process_request(self, request_data):
        """
        处理单个飞书请求
        
        Args:
            request_data: 请求数据
        """
        try:
            request_id = request_data.get('request_id')
            endpoint = request_data.get('endpoint', '/feishu/webhook')
            method = request_data.get('method', 'POST')
            headers = request_data.get('headers', {})
            payload = request_data.get('data', {})
            params = request_data.get('args', {})
            
            logger.info(f"📥 处理飞书请求: {request_id} -> {endpoint}")
            
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
                'request_id': request_id,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送响应回云服务器
            self.send_response(response_data)
            
            self.stats['requests_processed'] += 1
            logger.info(f"✅ 请求处理完成: {request_id} - {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接到本地服务器: {self.local_server_url}")
            self.send_error_response(request_id, "本地服务器连接失败")
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ 本地服务器请求超时: {request_id}")
            self.send_error_response(request_id, "本地服务器请求超时")
            
        except Exception as e:
            logger.error(f"❌ 处理飞书请求失败: {request_id} - {str(e)}")
            self.send_error_response(request_id, f"处理请求失败: {str(e)}")
    
    def send_response(self, response_data):
        """
        发送响应到云服务器
        
        Args:
            response_data: 响应数据
        """
        try:
            response = self.session.post(
                f"{self.cloud_server_url}/submit_response",
                json=response_data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"✅ 响应发送成功: {response_data['request_id']}")
            else:
                logger.warning(f"⚠️ 响应发送失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 发送响应异常: {str(e)}")
    
    def send_error_response(self, request_id, error_message):
        """
        发送错误响应
        
        Args:
            request_id: 请求ID
            error_message: 错误消息
        """
        try:
            response_data = {
                'request_id': request_id,
                'status_code': 500,
                'headers': {'Content-Type': 'application/json'},
                'content': json.dumps({
                    'error': error_message,
                    'timestamp': datetime.now().isoformat()
                }),
                'timestamp': datetime.now().isoformat()
            }
            
            self.send_response(response_data)
            
        except Exception as e:
            logger.error(f"❌ 发送错误响应失败: {str(e)}")
    
    def heartbeat_loop(self):
        """
        心跳检测循环
        """
        while self.running:
            try:
                response = self.session.post(
                    f"{self.cloud_server_url}/heartbeat",
                    json={
                        'client_id': self.client_id,
                        'timestamp': datetime.now().isoformat(),
                        'stats': self.stats
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.debug("💓 心跳检测正常")
                else:
                    logger.warning(f"⚠️ 心跳检测异常: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ 心跳检测失败: {str(e)}")
            
            time.sleep(30)  # 30秒心跳间隔
    
    def polling_loop(self):
        """
        主轮询循环
        """
        logger.info("🔄 开始轮询循环")
        
        while self.running:
            try:
                # 轮询获取请求
                requests_list = self.poll_requests()
                
                # 处理每个请求
                for request_data in requests_list:
                    if not self.running:
                        break
                    self.process_request(request_data)
                
                # 等待下次轮询
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 收到停止信号")
                break
            except Exception as e:
                logger.error(f"❌ 轮询循环异常: {str(e)}")
                time.sleep(5)  # 异常后等待5秒再继续
    
    def start(self):
        """
        启动反向代理客户端
        """
        logger.info("🚀 启动简单反向代理客户端")
        
        # 注册客户端
        if not self.register_client():
            logger.error("❌ 客户端注册失败，无法启动")
            return
        
        self.running = True
        
        # 启动心跳检测线程
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        logger.info("💓 心跳检测线程已启动")
        
        try:
            # 开始主轮询循环
            self.polling_loop()
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号")
        finally:
            self.stop()
    
    def stop(self):
        """
        停止反向代理客户端
        """
        logger.info("🛑 停止反向代理客户端")
        self.running = False
        self.stats['connected'] = False
        
        # 注销客户端
        try:
            self.session.post(
                f"{self.cloud_server_url}/unregister_client",
                json={'client_id': self.client_id},
                timeout=5
            )
            logger.info("✅ 客户端注销成功")
        except Exception as e:
            logger.error(f"❌ 客户端注销失败: {str(e)}")
    
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
    
    parser = argparse.ArgumentParser(description='🔄 简单HTTP轮询反向代理客户端')
    parser.add_argument('--cloud-server', default='http://175.178.183.96:8080', help='云服务器地址')
    parser.add_argument('--local-server', default='http://192.168.0.105:5000', help='本地服务器地址')
    parser.add_argument('--poll-interval', type=int, default=2, help='轮询间隔（秒）')
    
    args = parser.parse_args()
    
    # 创建并启动客户端
    client = SimpleReverseProxyClient(
        cloud_server_url=args.cloud_server,
        local_server_url=args.local_server
    )
    
    client.poll_interval = args.poll_interval
    
    try:
        client.start()
    except KeyboardInterrupt:
        logger.info("🛑 收到停止信号")
    except Exception as e:
        logger.error(f"❌ 客户端运行异常: {str(e)}")
        raise

if __name__ == '__main__':
    main() 