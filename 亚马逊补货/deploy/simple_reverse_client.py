#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔌 简化反向代理客户端
使用WebSocket直接连接云服务器
"""

import websocket
import json
import threading
import time
import requests
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleReverseClient:
    """
    🔌 简化反向代理客户端
    使用WebSocket连接云服务器
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
        self.client_id = f"simple_client_{int(time.time())}"
        
        # WebSocket连接
        self.ws = None
        self.connected = False
        self.running = False
        
        # HTTP会话
        self.session = requests.Session()
        self.session.timeout = 15
        
        logger.info(f"🔌 简化反向代理客户端初始化完成")
        logger.info(f"🌐 云服务器: {self.cloud_server_url}")
        logger.info(f"🏠 本地服务器: {self.local_server_url}")
        logger.info(f"🆔 客户端ID: {self.client_id}")
    
    def on_message(self, ws, message):
        """
        处理WebSocket消息
        
        Args:
            ws: WebSocket连接
            message: 接收到的消息
        """
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            logger.info(f"📥 收到消息: {message_type}")
            
            if message_type == 'feishu_request':
                # 处理飞书请求
                threading.Thread(target=self.handle_feishu_request, args=(data,)).start()
            elif message_type == 'ping':
                # 响应ping
                pong_data = {'type': 'pong', 'timestamp': datetime.now().isoformat()}
                ws.send(json.dumps(pong_data))
                logger.debug("🏓 响应ping消息")
            else:
                logger.debug(f"📨 未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            logger.warning(f"⚠️ 无效JSON消息: {message}")
        except Exception as e:
            logger.error(f"❌ 消息处理异常: {str(e)}")
    
    def on_error(self, ws, error):
        """
        处理WebSocket错误
        
        Args:
            ws: WebSocket连接
            error: 错误信息
        """
        logger.error(f"❌ WebSocket错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """
        处理WebSocket关闭
        
        Args:
            ws: WebSocket连接
            close_status_code: 关闭状态码
            close_msg: 关闭消息
        """
        self.connected = False
        logger.warning(f"⚠️ WebSocket连接已关闭: {close_status_code} - {close_msg}")
    
    def on_open(self, ws):
        """
        处理WebSocket连接打开
        
        Args:
            ws: WebSocket连接
        """
        self.connected = True
        logger.info("✅ WebSocket连接建立成功")
        
        # 发送注册消息
        register_data = {
            'type': 'register',
            'client_id': self.client_id,
            'local_url': self.local_server_url,
            'timestamp': datetime.now().isoformat(),
            'service': 'feishu-webhook-handler'
        }
        
        ws.send(json.dumps(register_data))
        logger.info("📝 客户端注册消息已发送")
    
    def handle_feishu_request(self, data):
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

            # 调试信息
            logger.info(f"🔍 请求详情: method={method}, endpoint={endpoint}")
            logger.info(f"🔍 Headers: {headers}")
            logger.info(f"🔍 JSON数据: {json_data}")
            logger.info(f"🔍 Form数据: {form_data}")
            
            # 构建本地服务器URL
            target_url = f"{self.local_server_url}{endpoint}"
            
            # 准备请求参数
            # 强制设置正确的Content-Type
            fixed_headers = dict(headers)  # 创建副本
            if json_data:
                fixed_headers['Content-Type'] = 'application/json'
                fixed_headers['Accept'] = 'application/json'

            request_kwargs = {
                'headers': fixed_headers,
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
            response_message = {
                'type': 'response',
                'request_id': request_id,
                'response': response_info,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.ws and self.connected:
                self.ws.send(json.dumps(response_message))
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
    
    def send_error_response(self, request_id, error_message, status_code=500):
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
            
            response_message = {
                'type': 'response',
                'request_id': request_id,
                'response': error_response,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.ws and self.connected:
                self.ws.send(json.dumps(response_message))
            
        except Exception as e:
            logger.error(f"❌ 发送错误响应失败: {str(e)}")
    
    def start(self):
        """
        启动反向代理客户端
        """
        logger.info("🚀 启动简化反向代理客户端")
        self.running = True
        
        # 构建WebSocket URL
        ws_url = self.cloud_server_url.replace('http://', 'ws://').replace('https://', 'wss://') + '/socket.io/?EIO=4&transport=websocket'
        
        try:
            # 创建WebSocket连接
            websocket.enableTrace(False)
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            logger.info(f"🔗 连接到WebSocket: {ws_url}")
            
            # 运行WebSocket
            self.ws.run_forever()
            
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号")
        except Exception as e:
            logger.error(f"❌ 客户端运行异常: {str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """
        停止反向代理客户端
        """
        logger.info("🛑 停止简化反向代理客户端")
        self.running = False
        self.connected = False
        
        if self.ws:
            self.ws.close()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🔌 简化反向代理客户端')
    parser.add_argument('--cloud-server', default='http://175.178.183.96:8080', help='云服务器地址')
    parser.add_argument('--local-server', default='http://127.0.0.1:8000', help='本地服务器地址')
    
    args = parser.parse_args()
    
    # 创建客户端
    client = SimpleReverseClient(
        cloud_server_url=args.cloud_server,
        local_server_url=args.local_server
    )
    
    try:
        client.start()
    except Exception as e:
        logger.error(f"❌ 客户端运行异常: {str(e)}")

if __name__ == '__main__':
    main()
