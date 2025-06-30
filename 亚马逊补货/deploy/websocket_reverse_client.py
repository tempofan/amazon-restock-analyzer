#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔌 原生WebSocket反向代理客户端
与云代理服务器的原生WebSocket接口兼容
"""

import asyncio
import websockets
import json
import logging
import time
import requests
from datetime import datetime
import signal
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('websocket_reverse_client.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebSocketReverseClient:
    """
    🔌 原生WebSocket反向代理客户端
    与云代理服务器建立WebSocket连接，处理飞书请求转发
    """
    
    def __init__(self, cloud_server_ws='ws://175.178.183.96:8081/ws', local_server_url='http://192.168.0.105:5000'):
        """
        初始化WebSocket反向代理客户端
        
        Args:
            cloud_server_ws: 云服务器WebSocket地址
            local_server_url: 本地服务器地址
        """
        self.cloud_server_ws = cloud_server_ws
        self.local_server_url = local_server_url
        self.client_id = f"ws_client_{int(time.time())}"
        
        # 连接状态
        self.websocket = None
        self.connected = False
        self.running = False
        
        # 创建HTTP会话
        self.session = requests.Session()
        self.session.timeout = 10
        
        # 统计信息
        self.stats = {
            'connected': False,
            'requests_processed': 0,
            'connection_attempts': 0,
            'start_time': time.time()
        }
        
        logger.info(f"🔌 WebSocket反向代理客户端初始化完成")
        logger.info(f"🌐 云服务器WebSocket: {self.cloud_server_ws}")
        logger.info(f"🏠 本地服务器: {self.local_server_url}")
        logger.info(f"🆔 客户端ID: {self.client_id}")
    
    async def register_client(self):
        """
        向云服务器注册客户端
        """
        try:
            registration_data = {
                'type': 'register',
                'client_id': self.client_id,
                'local_url': self.local_server_url,
                'timestamp': datetime.now().isoformat(),
                'service': 'feishu-webhook-reverse-proxy'
            }
            
            await self.websocket.send(json.dumps(registration_data))
            logger.info("✅ 客户端注册消息已发送")
            
        except Exception as e:
            logger.error(f"❌ 客户端注册失败: {str(e)}")
            return False
    
    async def process_feishu_request(self, request_data):
        """
        处理飞书请求
        
        Args:
            request_data: 飞书请求数据
        """
        try:
            request_id = request_data.get('request_id')
            endpoint = request_data.get('endpoint', '/feishu/webhook')
            method = request_data.get('method', 'POST')
            headers = request_data.get('headers', {})
            payload = request_data.get('data', {})
            query_params = request_data.get('query', {})
            
            logger.info(f"📥 处理飞书请求: {request_id} -> {endpoint}")
            
            # 构建本地服务器URL
            target_url = f"{self.local_server_url}{endpoint}"
            
            # 转发请求到本地服务器
            if method.upper() == 'POST':
                response = self.session.post(
                    target_url,
                    json=payload,
                    headers=headers,
                    params=query_params,
                    timeout=15
                )
            else:
                response = self.session.get(
                    target_url,
                    headers=headers,
                    params=query_params,
                    timeout=15
                )
            
            # 准备响应数据
            response_data = {
                'type': 'feishu_response',
                'request_id': request_id,
                'response': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送响应回云服务器
            await self.websocket.send(json.dumps(response_data))
            
            self.stats['requests_processed'] += 1
            logger.info(f"✅ 飞书请求处理完成: {request_id} - {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ 无法连接到本地服务器: {self.local_server_url}")
            await self.send_error_response(request_id, "本地服务器连接失败")
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ 本地服务器请求超时: {request_id}")
            await self.send_error_response(request_id, "本地服务器请求超时")
            
        except Exception as e:
            logger.error(f"❌ 处理飞书请求失败: {request_id} - {str(e)}")
            await self.send_error_response(request_id, f"处理请求失败: {str(e)}")
    
    async def send_error_response(self, request_id, error_message):
        """
        发送错误响应
        
        Args:
            request_id: 请求ID
            error_message: 错误消息
        """
        try:
            error_response = {
                'type': 'feishu_response',
                'request_id': request_id,
                'response': {
                    'status_code': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'data': {
                        'error': error_message,
                        'timestamp': datetime.now().isoformat()
                    }
                },
                'timestamp': datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(error_response))
            
        except Exception as e:
            logger.error(f"❌ 发送错误响应失败: {str(e)}")
    
    async def send_heartbeat(self):
        """
        发送心跳消息
        """
        try:
            heartbeat_data = {
                'type': 'heartbeat',
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            }
            
            await self.websocket.send(json.dumps(heartbeat_data))
            logger.debug("💓 心跳消息已发送")
            
        except Exception as e:
            logger.error(f"❌ 发送心跳失败: {str(e)}")
    
    async def heartbeat_loop(self):
        """
        心跳循环任务
        """
        while self.running and self.connected:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(30)  # 30秒心跳间隔
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 心跳循环异常: {str(e)}")
                await asyncio.sleep(30)
    
    async def message_handler(self):
        """
        消息处理循环
        """
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    if message_type == 'feishu_request':
                        # 处理飞书请求
                        await self.process_feishu_request(data)
                    elif message_type == 'ping':
                        # 响应ping消息
                        pong_data = {'type': 'pong', 'timestamp': datetime.now().isoformat()}
                        await self.websocket.send(json.dumps(pong_data))
                        logger.debug("🏓 响应ping消息")
                    elif message_type == 'registration_ack':
                        # 注册确认
                        logger.info("✅ 客户端注册确认收到")
                    else:
                        logger.debug(f"📨 收到未知消息类型: {message_type}")
                        
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ 收到无效JSON消息: {message}")
                except Exception as e:
                    logger.error(f"❌ 消息处理异常: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ WebSocket连接已关闭")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ 消息处理循环异常: {str(e)}")
            self.connected = False
    
    async def connect_and_run(self):
        """
        连接到云服务器并运行
        """
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(1, max_retries + 1):
            try:
                self.stats['connection_attempts'] += 1
                logger.info(f"🔗 尝试连接到云服务器 (尝试 {attempt}/{max_retries}): {self.cloud_server_ws}")
                
                # 建立WebSocket连接
                self.websocket = await websockets.connect(
                    self.cloud_server_ws,
                    ping_interval=20,
                    ping_timeout=10
                )
                
                self.connected = True
                self.stats['connected'] = True
                logger.info("✅ WebSocket连接建立成功")
                
                # 注册客户端
                await self.register_client()
                
                # 启动心跳任务
                heartbeat_task = asyncio.create_task(self.heartbeat_loop())
                
                try:
                    # 开始消息处理循环
                    await self.message_handler()
                finally:
                    # 取消心跳任务
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        pass
                
                # 如果到达这里，说明连接正常断开
                break
                
            except websockets.exceptions.InvalidHandshake as e:
                logger.error(f"❌ WebSocket握手失败 (尝试 {attempt}): {str(e)}")
                break
            except ConnectionRefusedError:
                logger.error(f"❌ 连接被拒绝 (尝试 {attempt}): 无法连接到 {self.cloud_server_ws}")
            except Exception as e:
                logger.error(f"❌ 连接异常 (尝试 {attempt}): {str(e)}")
            
            if attempt < max_retries:
                logger.info(f"⏳ {retry_delay}秒后重试...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # 指数退避，最大60秒
            else:
                logger.error("❌ 达到最大重试次数，连接失败")
                return False
        
        return True
    
    async def start(self):
        """
        启动反向代理客户端
        """
        logger.info("🚀 启动WebSocket反向代理客户端")
        self.running = True
        
        try:
            while self.running:
                success = await self.connect_and_run()
                if not success or not self.running:
                    break
                
                # 连接断开，等待重连
                logger.info("🔄 连接断开，5秒后重连...")
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号")
        finally:
            await self.stop()
    
    async def stop(self):
        """
        停止反向代理客户端
        """
        logger.info("🛑 停止WebSocket反向代理客户端")
        self.running = False
        self.connected = False
        self.stats['connected'] = False
        
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("✅ WebSocket连接已关闭")
            except Exception as e:
                logger.error(f"❌ 关闭WebSocket连接失败: {str(e)}")
    
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

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🔌 原生WebSocket反向代理客户端')
    parser.add_argument('--cloud-ws', default='ws://175.178.183.96:8081/ws', help='云服务器WebSocket地址')
    parser.add_argument('--local-server', default='http://192.168.0.105:5000', help='本地服务器地址')
    
    args = parser.parse_args()
    
    # 创建客户端
    client = WebSocketReverseClient(
        cloud_server_ws=args.cloud_ws,
        local_server_url=args.local_server
    )
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info("🛑 收到停止信号")
        client.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await client.start()
    except Exception as e:
        logger.error(f"❌ 客户端运行异常: {str(e)}")
        raise

if __name__ == '__main__':
    asyncio.run(main()) 