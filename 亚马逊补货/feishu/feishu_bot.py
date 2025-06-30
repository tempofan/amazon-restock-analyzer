# -*- coding: utf-8 -*-
"""
飞书机器人集成模块
用于将亚马逊补货工具集成到飞书平台
"""

import json
import hashlib
import hmac
import base64
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import sys
import requests

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from business.restock_analyzer import RestockAnalyzer
from utils.logger import api_logger
from config.config import ServerConfig

class FeishuBot:
    """
    飞书机器人类
    处理飞书消息接收和发送
    """
    
    def __init__(self):
        """
        初始化飞书机器人
        """
        # 飞书机器人配置 (新应用)
        self.app_id = os.getenv('FEISHU_APP_ID', 'cli_a8d49f76d7fbd00b')
        self.app_secret = os.getenv('FEISHU_APP_SECRET', 'ivQKKw0UsCHC2spYjrssvb0Hx4AdLxE6')
        self.verification_token = os.getenv('FEISHU_VERIFICATION_TOKEN', '')
        self.encrypt_key = os.getenv('FEISHU_ENCRYPT_KEY', '')
        
        # 飞书API地址
        self.base_url = "https://open.feishu.cn"
        self.token_url = f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        self.message_url = f"{self.base_url}/open-apis/im/v1/messages"
        
        # 访问令牌
        self.access_token = None
        self.token_expire_time = 0
        
        # 业务分析器
        self.analyzer = RestockAnalyzer()
        
        # 命令处理器映射
        self.command_handlers = {
            '帮助': self._handle_help,
            'help': self._handle_help,
            '测试': self._handle_test_connection,
            'test': self._handle_test_connection,
            '店铺': self._handle_get_sellers,
            'sellers': self._handle_get_sellers,
            '补货': self._handle_get_restock_data,
            'restock': self._handle_get_restock_data,
            '紧急': self._handle_urgent_restock,
            'urgent': self._handle_urgent_restock,
            '状态': self._handle_server_status,
            'status': self._handle_server_status,
        }
    
    def get_access_token(self) -> str:
        """
        获取飞书访问令牌
        
        Returns:
            str: 访问令牌
        """
        # 检查令牌是否过期
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
        
        # 获取新令牌
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'app_id': self.app_id,
            'app_secret': self.app_secret
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, json=data)
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result['tenant_access_token']
                self.token_expire_time = time.time() + result['expire'] - 300  # 提前5分钟过期
                api_logger.log_info(f"飞书访问令牌获取成功，过期时间: {datetime.fromtimestamp(self.token_expire_time)}")
                return self.access_token
            else:
                api_logger.log_error(f"获取飞书访问令牌失败: {result}")
                return None
                
        except Exception as e:
            api_logger.log_error(e, "获取飞书访问令牌异常")
            return None
    
    def verify_signature(self, timestamp: str, nonce: str, encrypt: str, signature: str) -> bool:
        """
        验证飞书请求签名
        
        Args:
            timestamp: 时间戳
            nonce: 随机数
            encrypt: 加密字符串
            signature: 签名
            
        Returns:
            bool: 验证结果
        """
        if not self.verification_token:
            return True  # 如果没有配置验证令牌，则跳过验证
        
        # 构造签名字符串
        sign_str = timestamp + nonce + self.verification_token + encrypt
        
        # 计算签名
        calculated_signature = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()
        
        return calculated_signature == signature
    
    def decrypt_data(self, encrypt: str) -> Optional[Dict]:
        """
        解密飞书数据
        
        Args:
            encrypt: 加密数据
            
        Returns:
            Dict: 解密后的数据
        """
        if not self.encrypt_key:
            return None
        
        try:
            from Crypto.Cipher import AES
            
            # Base64解码
            encrypt_data = base64.b64decode(encrypt)
            
            # AES解密
            cipher = AES.new(self.encrypt_key.encode('utf-8'), AES.MODE_CBC, encrypt_data[:16])
            decrypted = cipher.decrypt(encrypt_data[16:])
            
            # 去除填充
            padding_length = decrypted[-1]
            decrypted = decrypted[:-padding_length]
            
            # 解析JSON
            return json.loads(decrypted.decode('utf-8'))
            
        except Exception as e:
            api_logger.log_error(e, "飞书数据解密失败")
            return None
    
    def send_message(self, receive_id: str, msg_type: str, content: Dict) -> bool:
        """
        发送飞书消息
        
        Args:
            receive_id: 接收者ID
            msg_type: 消息类型
            content: 消息内容
            
        Returns:
            bool: 发送结果
        """
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        # 根据receive_id格式自动判断类型
        if receive_id.startswith('oc_'):
            id_type = 'chat_id'
        elif receive_id.startswith('ou_'):
            id_type = 'open_id'
        elif receive_id.startswith('om_'):
            id_type = 'user_id'
        else:
            # 默认使用chat_id，这是最常见的情况
            id_type = 'chat_id'
        
        # 根据receive_id格式构建URL，将receive_id_type作为查询参数
        message_url_with_params = f"{self.message_url}?receive_id_type={id_type}"
        
        data = {
            'receive_id': receive_id,
            'msg_type': msg_type,
            'content': content  # content可能是字符串或对象，直接使用
        }
        
        # 调试：记录发送的数据
        api_logger.log_info(f"发送消息API URL: {message_url_with_params}")
        api_logger.log_info(f"发送消息Headers: {headers}")
        api_logger.log_info(f"发送消息数据: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = requests.post(message_url_with_params, headers=headers, json=data)
            result = response.json()
            
            if result.get('code') == 0:
                return True
            else:
                api_logger.log_error(f"发送飞书消息失败: {result}")
                return False
                
        except Exception as e:
            api_logger.log_error(e, "发送飞书消息异常")
            return False
    
    def send_text_message(self, receive_id: str, text: str) -> bool:
        """
        发送文本消息
        
        Args:
            receive_id: 接收者ID
            text: 文本内容
            
        Returns:
            bool: 发送结果
        """
        api_logger.log_info(f"发送文本消息: receive_id={receive_id}, text={text[:50]}...")
        # 对于文本消息，content需要是JSON字符串
        content = json.dumps({'text': text}, ensure_ascii=False)
        return self.send_message(receive_id, 'text', content)
    
    def send_rich_text_message(self, receive_id: str, title: str, content: List[List[Dict]]) -> bool:
        """
        发送富文本消息
        
        Args:
            receive_id: 接收者ID
            title: 标题
            content: 富文本内容
            
        Returns:
            bool: 发送结果
        """
        rich_content = {
            'title': title,
            'content': content
        }
        return self.send_message(receive_id, 'post', rich_content)
    
    def process_message(self, event_data: Dict) -> Dict:
        """
        处理接收到的消息
        
        Args:
            event_data: 事件数据
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 调试：记录完整事件数据
            api_logger.log_info(f"处理消息事件: {json.dumps(event_data, ensure_ascii=False)}")
            
            # 提取消息信息
            event = event_data.get('event', {})
            message = event.get('message', {})
            sender = event.get('sender', {})
            
            # 获取消息内容
            msg_type = message.get('msg_type')
            content = message.get('content')
            chat_id = message.get('chat_id')
            sender_id = sender.get('sender_id', {}).get('open_id')
            
            # 调试：记录提取的信息
            api_logger.log_info(f"消息类型: {msg_type}, 聊天ID: {chat_id}, 发送者: {sender_id}")
            api_logger.log_info(f"消息内容: {content}")
            
            if msg_type == 'text' and content and chat_id:
                # 解析文本消息
                try:
                    text_content = json.loads(content)
                    text = text_content.get('text', '').strip()
                    api_logger.log_info(f"解析出的文本: {text}")
                except:
                    # 如果解析失败，直接使用content
                    text = content.strip() if isinstance(content, str) else str(content)
                    api_logger.log_info(f"直接使用的文本: {text}")
                
                # 处理@机器人的消息（飞书格式为@_user_1）
                if '@_user_1' in text or '@机器人' in text:
                    text = text.replace('@_user_1', '').replace('@机器人', '').strip()
                    api_logger.log_info(f"移除@mention后的文本: {text}")
                
                # 处理命令
                if text:
                    response = self._process_command(text, sender_id or 'anonymous')
                    
                    # 发送回复
                    if response and chat_id:
                        success = self.send_text_message(chat_id, response)
                        api_logger.log_info(f"发送回复结果: {success}")
                    
                    return {'status': 'success', 'message': 'Message processed', 'message_type': msg_type}
                else:
                    api_logger.log_info("消息为空，忽略处理")
                    return {'status': 'ignored', 'message': 'Empty message', 'message_type': msg_type}
            else:
                # 不支持的消息类型或缺少必要信息
                api_logger.log_info(f"不支持的消息或缺少信息 - 类型: {msg_type}, 聊天ID: {chat_id}")
                if chat_id:
                    self.send_text_message(chat_id, "抱歉，我目前只支持文本消息。请发送文本命令获取帮助。")
                return {'status': 'ignored', 'message': 'Unsupported message type or missing info', 'message_type': msg_type or ''}
                
        except Exception as e:
            api_logger.log_error(e, "处理飞书消息异常")
            return {'status': 'error', 'message': str(e), 'message_type': ''}
    
    def _process_command(self, text: str, sender_id: str) -> str:
        """
        处理用户命令
        
        Args:
            text: 用户输入文本
            sender_id: 发送者ID
            
        Returns:
            str: 回复内容
        """
        # 记录用户命令
        api_logger.log_info(f"收到用户命令: {text} (用户ID: {sender_id})")
        
        # 解析命令
        parts = text.split()
        if not parts:
            return self._handle_help()
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # 查找命令处理器
        handler = self.command_handlers.get(command)
        if handler:
            try:
                return handler(args, sender_id)
            except Exception as e:
                api_logger.log_error(e, f"执行命令失败: {command}")
                return f"执行命令失败: {str(e)}"
        else:
            return self._handle_unknown_command(text)
    
    def _handle_help(self, args: List[str] = None, sender_id: str = None) -> str:
        """
        处理帮助命令
        """
        help_text = """
🤖 亚马逊补货助手 - 命令帮助

📋 可用命令：
• 帮助 / help - 显示此帮助信息
• 测试 / test - 测试API连接状态
• 店铺 / sellers - 获取店铺列表
• 补货 [店铺ID] - 获取补货数据
• 紧急 [店铺ID] - 获取紧急补货商品
• 状态 / status - 查看服务器状态

💡 使用示例：
• 补货 - 获取所有店铺补货数据
• 补货 12345 - 获取指定店铺补货数据
• 紧急 - 获取所有紧急补货商品
• 紧急 12345 - 获取指定店铺紧急补货商品

🔗 服务器地址: http://192.168.0.99:8000
⏰ 当前时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return help_text
    
    def _handle_test_connection(self, args: List[str], sender_id: str) -> str:
        """
        处理测试连接命令
        """
        try:
            from api.client import APIClient
            client = APIClient()
            result = client.test_connection()
            
            if result.get('success', False):
                return f"""
✅ API连接测试成功！

📊 连接状态：
• Token状态: {result.get('token_status', 'unknown')}
• 店铺数量: {result.get('seller_count', 0)}
• 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            else:
                return f"❌ API连接测试失败: {result.get('message', '未知错误')}"
                
        except Exception as e:
            return f"❌ 连接测试异常: {str(e)}"
    
    def _handle_get_sellers(self, args: List[str], sender_id: str) -> str:
        """
        处理获取店铺信息命令
        """
        try:
            sellers = self.analyzer.get_sellers()
            
            if not sellers:
                return "❌ 未找到店铺信息"
            
            response = f"📋 找到 {len(sellers)} 个店铺：\n\n"
            response += "店铺ID | 店铺名称 | 地区 | 状态\n"
            response += "--- | --- | --- | ---\n"
            
            for seller in sellers[:10]:  # 限制显示前10个
                sid = seller.get('sid', '')
                name = seller.get('name', '')[:20]  # 限制长度
                region = seller.get('region', '')
                status = '正常' if seller.get('status') == 1 else '异常'
                response += f"{sid} | {name} | {region} | {status}\n"
            
            if len(sellers) > 10:
                response += f"\n... 还有 {len(sellers) - 10} 个店铺"
            
            response += f"\n⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return response
            
        except Exception as e:
            return f"❌ 获取店铺信息失败: {str(e)}"
    
    def _handle_get_restock_data(self, args: List[str], sender_id: str) -> str:
        """
        处理获取补货数据命令
        """
        try:
            # 解析参数
            seller_ids = None
            if args:
                seller_ids = [arg.strip() for arg in args]
            
            # 获取补货数据（限制数量，避免消息过长）
            restock_items = self.analyzer.get_restock_data(
                seller_ids=seller_ids,
                data_type=1,  # ASIN维度
                max_pages=2,  # 限制页数
                max_workers=3
            )
            
            if not restock_items:
                return "❌ 未找到补货数据"
            
            # 生成汇总报告
            summary = self.analyzer.generate_summary_report(restock_items)
            
            response = f"""
📊 补货数据汇总报告

📈 统计数据：
• 总计商品: {summary['total_items']}
• 紧急补货: {summary['urgent_items']}
• 断货商品: {summary['out_of_stock_items']}
• 高销量商品: {summary['high_sales_items']}
• 建议采购总量: {summary['total_suggested_purchase']}
• 平均可售天数: {summary['avg_available_days']}

🔥 前5个紧急补货商品：
"""
            
            # 分析紧急补货商品
            urgent_items = self.analyzer.analyze_urgent_restock(restock_items)
            if urgent_items:
                response += "\nASIN | 可售天数 | 建议采购 | 日均销量\n"
                response += "--- | --- | --- | ---\n"
                
                for item in urgent_items[:5]:
                    asin = item.asin[:10]
                    days = item.available_sale_days if item.available_sale_days > 0 else '断货'
                    purchase = item.suggested_purchase
                    sales = round(item.sales_avg_30, 1)
                    
                    response += f"{asin} | {days} | {purchase} | {sales}\n"
            else:
                response += "\n✅ 暂无紧急补货商品"
            
            # 导出Excel文件
            try:
                excel_file = self.analyzer.export_to_excel(restock_items)
                response += f"\n📄 详细数据已导出: {excel_file}"
            except Exception as e:
                response += f"\n⚠️ 导出失败: {str(e)}"
            
            response += f"\n⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return response
            
        except Exception as e:
            return f"❌ 获取补货数据失败: {str(e)}"
    
    def _handle_urgent_restock(self, args: List[str], sender_id: str) -> str:
        """
        处理紧急补货命令
        """
        try:
            # 解析参数
            seller_ids = None
            if args:
                seller_ids = [arg.strip() for arg in args]
            
            # 获取补货数据
            restock_items = self.analyzer.get_restock_data(
                seller_ids=seller_ids,
                data_type=1,
                max_pages=3,
                max_workers=3
            )
            
            if not restock_items:
                return "❌ 未找到补货数据"
            
            # 分析紧急补货商品
            urgent_items = self.analyzer.analyze_urgent_restock(restock_items)
            
            if not urgent_items:
                return "✅ 暂无紧急补货商品！"
            
            response = f"""
🚨 紧急补货提醒！

发现 {len(urgent_items)} 个紧急补货商品：

ASIN | 店铺ID | 可售天数 | 断货日期 | 建议采购
--- | --- | --- | --- | ---
"""
            
            for item in urgent_items[:10]:  # 限制显示前10个
                asin = item.asin[:10]
                sid = item.sid
                days = item.available_sale_days if item.available_sale_days > 0 else '断货'
                out_date = item.out_stock_date[:10] if item.out_stock_date else '-'
                purchase = item.suggested_purchase
                
                response += f"{asin} | {sid} | {days} | {out_date} | {purchase}\n"
            
            if len(urgent_items) > 10:
                response += f"\n... 还有 {len(urgent_items) - 10} 个紧急补货商品"
            
            response += f"\n⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            response += "\n💡 建议立即处理这些商品的补货！"
            
            return response
            
        except Exception as e:
            return f"❌ 获取紧急补货数据失败: {str(e)}"
    
    def _handle_server_status(self, args: List[str], sender_id: str) -> str:
        """
        处理服务器状态命令
        """
        try:
            import psutil
            import shutil
            
            # 获取系统信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = shutil.disk_usage('.')
            
            # 网络状态检查
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            port_status = "✅ 可用" if sock.connect_ex((ServerConfig.HOST, ServerConfig.PORT)) != 0 else "⚠️ 占用"
            sock.close()
            
            response = f"""
🖥️ 服务器状态报告

💻 系统信息：
• 服务器IP: {ServerConfig.HOST}
• 服务端口: {ServerConfig.PORT} ({port_status})
• CPU使用率: {cpu_percent}%
• 内存使用率: {memory.percent}%
• 可用磁盘: {disk.free // (1024**3)}GB

📊 服务状态：
• 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• 数据库类型: {os.getenv('DB_TYPE', 'sqlite')}
• 日志级别: {os.getenv('LOG_LEVEL', 'INFO')}

🔗 访问地址: http://{ServerConfig.HOST}:{ServerConfig.PORT}
"""
            
            return response
            
        except Exception as e:
            return f"❌ 获取服务器状态失败: {str(e)}"
    
    def _handle_unknown_command(self, text: str) -> str:
        """
        处理未知命令
        """
        return f"""
❓ 未知命令: {text}

请发送 "帮助" 或 "help" 查看可用命令列表。

💡 常用命令：
• 测试 - 检查API连接
• 店铺 - 查看店铺列表  
• 补货 - 获取补货数据
• 紧急 - 查看紧急补货
"""