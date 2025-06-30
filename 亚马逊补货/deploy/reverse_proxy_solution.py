#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 反向代理解决方案
解决本地公网IP不固定的问题，让本地服务器主动连接云服务器
"""

import asyncio
import websockets
import json
import requests
import threading
import time
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReverseProxyClient:
    """
    🔄 反向代理客户端
    运行在本地，主动连接云服务器，接收并处理飞书请求
    """
    
    def __init__(self, cloud_server_ws_url, local_server_url):
        """
        初始化反向代理客户端
        
        Args:
            cloud_server_ws_url: 云服务器WebSocket地址
            local_server_url: 本地服务器地址
        """
        self.cloud_server_ws_url = cloud_server_ws_url
        self.local_server_url = local_server_url
        self.websocket = None
        self.running = False
        
    async def connect_and_listen(self):
        """连接云服务器并监听请求"""
        logger.info(f"🔗 连接到云服务器: {self.cloud_server_ws_url}")
        
        try:
            async with websockets.connect(self.cloud_server_ws_url) as websocket:
                self.websocket = websocket
                self.running = True
                logger.info("✅ 成功连接到云服务器")
                
                # 发送注册消息
                register_msg = {
                    "type": "register",
                    "client_id": "local_feishu_server",
                    "local_url": self.local_server_url,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(register_msg))
                
                # 监听消息
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.handle_request(data)
                    except Exception as e:
                        logger.error(f"❌ 处理消息异常: {e}")
                        
        except Exception as e:
            logger.error(f"❌ WebSocket连接异常: {e}")
            self.running = False
    
    async def handle_request(self, request_data):
        """
        处理来自云服务器的请求
        
        Args:
            request_data: 请求数据
        """
        try:
            if request_data.get('type') == 'feishu_request':
                # 转发飞书请求到本地服务器
                response = await self.forward_to_local(request_data)
                
                # 将响应发送回云服务器
                response_msg = {
                    "type": "feishu_response",
                    "request_id": request_data.get('request_id'),
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
                
                if self.websocket:
                    await self.websocket.send(json.dumps(response_msg))
                    
        except Exception as e:
            logger.error(f"❌ 处理请求异常: {e}")
    
    async def forward_to_local(self, request_data):
        """
        将请求转发到本地服务器
        
        Args:
            request_data: 请求数据
            
        Returns:
            dict: 本地服务器响应
        """
        try:
            method = request_data.get('method', 'POST')
            endpoint = request_data.get('endpoint', '/feishu/webhook')
            headers = request_data.get('headers', {})
            data = request_data.get('data', {})
            
            url = f"{self.local_server_url}{endpoint}"
            
            logger.info(f"🔄 转发请求到本地: {method} {url}")
            
            if method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, params=data, headers=headers, timeout=30)
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            logger.info(f"✅ 本地响应: {response.status_code}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 转发请求异常: {e}")
            return {
                "status_code": 500,
                "data": {"error": str(e)}
            }
    
    def start(self):
        """启动反向代理客户端"""
        logger.info("🚀 启动反向代理客户端...")
        
        while True:
            try:
                asyncio.run(self.connect_and_listen())
            except KeyboardInterrupt:
                logger.info("👋 反向代理客户端已停止")
                break
            except Exception as e:
                logger.error(f"❌ 连接异常: {e}")
                logger.info("⏰ 5秒后重新连接...")
                time.sleep(5)

def main():
    """主函数"""
    # 配置
    CLOUD_SERVER_WS_URL = "ws://175.178.183.96:8081/ws"  # WebSocket地址
    LOCAL_SERVER_URL = "http://127.0.0.1:5000"  # 本地服务器地址
    
    # 创建并启动反向代理客户端
    client = ReverseProxyClient(CLOUD_SERVER_WS_URL, LOCAL_SERVER_URL)
    client.start()

if __name__ == '__main__':
    main() 