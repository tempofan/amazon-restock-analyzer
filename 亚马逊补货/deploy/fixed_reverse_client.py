#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 修复版反向代理客户端
专门解决数据传输问题
"""

import socketio
import requests
import json
import logging
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedReverseClient:
    """
    修复版反向代理客户端
    """
    
    def __init__(self, cloud_server_url, local_server_url):
        """初始化客户端"""
        self.cloud_server_url = cloud_server_url
        self.local_server_url = local_server_url
        self.client_id = f"fixed_client_{int(datetime.now().timestamp())}"
        
        # 创建SocketIO客户端
        self.sio = socketio.Client()
        self.setup_events()
        
        # 创建HTTP会话
        self.session = requests.Session()
        
        logger.info("🔧 修复版反向代理客户端初始化完成")
        logger.info(f"🌐 云服务器: {cloud_server_url}")
        logger.info(f"🏠 本地服务器: {local_server_url}")
        logger.info(f"🆔 客户端ID: {self.client_id}")
    
    def setup_events(self):
        """设置SocketIO事件处理"""
        
        @self.sio.event
        def connect():
            logger.info("✅ WebSocket连接建立成功")
            # 注册客户端
            self.sio.emit('register_client', {'client_id': self.client_id})
            logger.info("📝 客户端注册消息已发送")
        
        @self.sio.event
        def disconnect():
            logger.info("❌ WebSocket连接断开")
        
        @self.sio.on('registration_ack')
        def on_registration_ack(data):
            logger.info(f"📥 收到注册确认: {data}")
        
        @self.sio.on('feishu_request')
        def on_feishu_request(data):
            logger.info("📥 收到飞书请求")
            self.handle_feishu_request(data)
    
    def handle_feishu_request(self, data):
        """
        处理飞书请求 - 修复版
        """
        try:
            request_id = data.get('request_id')
            request_data = data.get('request_data', {})
            
            logger.info(f"📥 处理飞书请求: {request_id}")
            
            # 详细调试信息
            logger.info(f"🔍 原始数据: {json.dumps(data, ensure_ascii=False)[:200]}...")
            
            # 提取请求信息
            method = request_data.get('method', 'POST')
            headers = request_data.get('headers', {})
            body_data = request_data.get('data')  # 原始请求体
            json_data = request_data.get('json_data')
            form_data = request_data.get('form_data')
            query_params = request_data.get('args', {})
            endpoint = request_data.get('endpoint', '/feishu/webhook')
            
            logger.info(f"🔍 方法: {method}")
            logger.info(f"🔍 端点: {endpoint}")
            logger.info(f"🔍 Headers: {headers}")
            logger.info(f"🔍 Body数据: {body_data}")
            logger.info(f"🔍 JSON数据: {json_data}")
            logger.info(f"🔍 Form数据: {form_data}")
            
            # 构建本地服务器URL
            target_url = f"{self.local_server_url}{endpoint}"
            
            # 准备请求参数 - 修复版
            fixed_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'FeishuBot/1.0'
            }
            
            # 添加飞书特有的头信息
            for key, value in headers.items():
                if key.lower().startswith('x-lark-'):
                    fixed_headers[key] = value
            
            # 准备请求体数据
            request_body = None
            if json_data:
                request_body = json_data
                logger.info("✅ 使用JSON数据")
            elif body_data:
                try:
                    # 尝试解析原始请求体
                    if isinstance(body_data, str):
                        request_body = json.loads(body_data)
                    else:
                        request_body = body_data
                    logger.info("✅ 使用原始请求体数据")
                except:
                    logger.warning("⚠️ 无法解析原始请求体，使用空数据")
                    request_body = {}
            else:
                logger.warning("⚠️ 没有找到请求体数据")
                request_body = {}
            
            logger.info(f"🔍 最终请求体: {json.dumps(request_body, ensure_ascii=False)[:200]}...")
            
            # 发送请求到本地服务器
            try:
                if method.upper() == 'POST':
                    response = self.session.post(
                        target_url,
                        json=request_body,
                        headers=fixed_headers,
                        params=query_params,
                        timeout=15
                    )
                else:
                    response = self.session.get(
                        target_url,
                        headers=fixed_headers,
                        params=query_params,
                        timeout=15
                    )
                
                logger.info(f"📊 本地服务器响应: {response.status_code}")
                logger.info(f"📄 响应内容: {response.text[:200]}...")
                
                # 准备响应数据
                try:
                    response_data = response.json()
                except:
                    response_data = {"message": response.text}
                
                # 发送响应回云服务器
                self.sio.emit('feishu_response', {
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'data': response_data,
                    'headers': dict(response.headers)
                })
                
                logger.info(f"✅ 飞书请求处理完成: {request_id} - {response.status_code}")
                
            except Exception as e:
                logger.error(f"❌ 本地服务器请求失败: {str(e)}")
                # 发送错误响应
                self.sio.emit('feishu_response', {
                    'request_id': request_id,
                    'status_code': 500,
                    'data': {'error': str(e)},
                    'headers': {}
                })
                
        except Exception as e:
            logger.error(f"❌ 处理飞书请求异常: {str(e)}")
    
    def connect(self):
        """连接到云服务器"""
        try:
            logger.info("🚀 启动修复版反向代理客户端")
            
            # 解析WebSocket URL
            if self.cloud_server_url.startswith('ws://'):
                ws_url = self.cloud_server_url
            else:
                ws_url = self.cloud_server_url.replace('http://', 'ws://')
            
            # 添加SocketIO路径
            if not ws_url.endswith('/socket.io/'):
                if ws_url.endswith('/'):
                    ws_url += 'socket.io/'
                else:
                    ws_url += '/socket.io/'
            
            # 添加SocketIO参数
            ws_url += '?EIO=4&transport=websocket'
            
            logger.info(f"🔗 连接到WebSocket: {ws_url}")
            
            # 连接到云服务器
            self.sio.connect(ws_url)
            
            # 保持连接
            logger.info("🔄 保持连接运行...")
            self.sio.wait()
            
        except Exception as e:
            logger.error(f"❌ 连接失败: {str(e)}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='修复版反向代理客户端')
    parser.add_argument('--cloud-server', required=True, help='云服务器URL')
    parser.add_argument('--local-server', required=True, help='本地服务器URL')
    
    args = parser.parse_args()
    
    # 创建并启动客户端
    client = FixedReverseClient(args.cloud_server, args.local_server)
    
    try:
        client.connect()
    except KeyboardInterrupt:
        logger.info("👋 用户中断，正在退出...")
    except Exception as e:
        logger.error(f"❌ 客户端运行失败: {str(e)}")

if __name__ == '__main__':
    main()
