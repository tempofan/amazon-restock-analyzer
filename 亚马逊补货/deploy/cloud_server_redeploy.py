#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 云服务器重新部署脚本
解决云服务器代码缺陷，重新部署完整的飞书机器人系统
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# 配置日志 - 使用可写目录
log_dir = '/opt/feishu-cloud-server/logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'feishu_cloud_server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloudFeishuServer:
    """
    🤖 云服务器飞书机器人处理器
    直接在云服务器上处理飞书请求，不再转发到本地
    """
    
    def __init__(self):
        """初始化云服务器飞书处理器"""
        self.app = Flask(__name__)
        CORS(self.app)
        
        # 飞书配置 - 需要在云服务器上配置
        self.app_id = os.getenv('FEISHU_APP_ID', '')
        self.app_secret = os.getenv('FEISHU_APP_SECRET', '')
        self.verification_token = os.getenv('FEISHU_VERIFICATION_TOKEN', '')
        
        # 领星API配置
        self.lingxing_base_url = "https://openapi.lingxing.com"
        self.lingxing_app_id = os.getenv('LINGXING_APP_ID', '')
        self.lingxing_app_secret = os.getenv('LINGXING_APP_SECRET', '')
        
        # 访问令牌缓存
        self.access_token = None
        self.token_expire_time = 0
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'success_requests': 0,
            'failed_requests': 0,
            'feishu_requests': 0,
            'start_time': time.time()
        }
        
        # 注册路由
        self._register_routes()
        
        logger.info("🚀 云服务器飞书机器人初始化完成")
    
    def _register_routes(self):
        """注册Flask路由"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """健康检查接口"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'server': 'Cloud Feishu Server v2.0',
                'uptime': time.time() - self.stats['start_time']
            })
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """获取统计信息"""
            return jsonify({
                'stats': self.stats,
                'timestamp': datetime.now().isoformat(),
                'server_info': {
                    'version': '2.0',
                    'type': 'cloud_direct',
                    'features': ['飞书机器人', '领星API', '直接处理']
                }
            })
        
        @self.app.route('/feishu/webhook', methods=['POST'])
        def feishu_webhook():
            """飞书Webhook处理接口"""
            return self._handle_feishu_webhook()
        
        @self.app.route('/test', methods=['GET'])
        def test_endpoint():
            """测试接口"""
            return jsonify({
                'message': '云服务器运行正常',
                'timestamp': datetime.now().isoformat(),
                'config_status': {
                    'feishu_app_id': bool(self.app_id),
                    'feishu_app_secret': bool(self.app_secret),
                    'lingxing_app_id': bool(self.lingxing_app_id),
                    'lingxing_app_secret': bool(self.lingxing_app_secret)
                }
            })
    
    def _handle_feishu_webhook(self):
        """
        处理飞书Webhook请求
        直接在云服务器上处理，不再转发
        """
        try:
            self.stats['total_requests'] += 1
            self.stats['feishu_requests'] += 1
            
            # 获取请求数据
            data = request.get_json()
            if not data:
                logger.error("❌ 收到空的请求数据")
                self.stats['failed_requests'] += 1
                return jsonify({'error': 'No data received'}), 400
            
            logger.info(f"🤖 收到飞书请求: {json.dumps(data, ensure_ascii=False)}")
            
            # 处理URL验证
            if data.get('type') == 'url_verification':
                challenge = data.get('challenge', '')
                logger.info(f"✅ URL验证成功: {challenge}")
                self.stats['success_requests'] += 1
                return jsonify({'challenge': challenge})
            
            # 处理消息事件
            if data.get('type') == 'event_callback':
                result = self._process_message_event(data)
                if result:
                    self.stats['success_requests'] += 1
                    return jsonify({'status': 'success', 'message': 'Message processed'})
                else:
                    self.stats['failed_requests'] += 1
                    return jsonify({'status': 'failed', 'message': 'Message processing failed'}), 500
            
            # 未知请求类型
            logger.warning(f"⚠️ 未知请求类型: {data.get('type')}")
            self.stats['success_requests'] += 1
            return jsonify({'status': 'ignored', 'type': data.get('type', 'unknown')})
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 处理飞书请求异常: {error_msg}\n{traceback.format_exc()}")
            self.stats['failed_requests'] += 1
            return jsonify({'error': f'Server error: {error_msg}'}), 500
    
    def _process_message_event(self, event_data):
        """
        处理飞书消息事件
        
        Args:
            event_data: 飞书事件数据
            
        Returns:
            bool: 处理结果
        """
        try:
            event = event_data.get('event', {})
            message = event.get('message', {})
            
            # 获取消息信息
            msg_type = message.get('msg_type')
            chat_id = message.get('chat_id')
            content = message.get('content')
            
            logger.info(f"📝 处理消息: 类型={msg_type}, 聊天ID={chat_id}")
            
            # 只处理文本消息
            if msg_type != 'text':
                logger.info(f"⏭️ 跳过非文本消息: {msg_type}")
                return True
            
            # 解析消息内容
            if content:
                try:
                    content_data = json.loads(content)
                    text = content_data.get('text', '').strip()
                except:
                    text = str(content).strip()
            else:
                text = ''
            
            logger.info(f"💬 消息内容: {text}")
            
            # 处理命令
            if text:
                response = self._process_command(text)
                
                # 发送回复
                if response and chat_id:
                    success = self._send_message(chat_id, response)
                    logger.info(f"📤 发送回复结果: {success}")
                    return success
                else:
                    logger.info("📝 无需回复或缺少聊天ID")
                    return True
            else:
                logger.info("📝 消息内容为空")
                return True
                
        except Exception as e:
            logger.error(f"❌ 处理消息事件异常: {str(e)}\n{traceback.format_exc()}")
            return False
    
    def _process_command(self, text):
        """
        处理用户命令
        
        Args:
            text: 用户输入文本
            
        Returns:
            str: 回复内容
        """
        logger.info(f"🎯 处理命令: {text}")
        
        # 解析命令
        parts = text.split()
        if not parts:
            return self._get_help_message()
        
        command = parts[0].lower()
        
        # 命令映射
        if command in ['帮助', 'help']:
            return self._get_help_message()
        elif command in ['测试', 'test']:
            return self._test_api_connection()
        elif command in ['状态', 'status']:
            return self._get_server_status()
        elif command in ['店铺', 'sellers']:
            return self._get_sellers_info()
        elif command in ['补货', 'restock']:
            seller_id = parts[1] if len(parts) > 1 else None
            return self._get_restock_data(seller_id)
        elif command in ['紧急', 'urgent']:
            seller_id = parts[1] if len(parts) > 1 else None
            return self._get_urgent_restock(seller_id)
        else:
            return f"❓ 未知命令: {command}\n\n{self._get_help_message()}"
    
    def _get_help_message(self):
        """获取帮助信息"""
        return """🤖 领星数据机器人帮助

📋 可用命令：
• 帮助 / help - 显示此帮助信息
• 测试 / test - 测试API连接状态
• 状态 / status - 查看服务器状态
• 店铺 / sellers - 获取店铺列表
• 补货 [店铺ID] - 获取补货数据
• 紧急 [店铺ID] - 获取紧急补货商品

💡 使用示例：
• @机器人 帮助
• @机器人 测试
• @机器人 补货
• @机器人 补货 12345

🔧 服务器版本: Cloud Direct v2.0"""
    
    def _test_api_connection(self):
        """测试API连接"""
        try:
            # 测试获取访问令牌
            token = self._get_access_token()
            if token:
                return "✅ API连接测试成功\n🔑 访问令牌获取正常\n🌐 网络连接正常"
            else:
                return "❌ API连接测试失败\n🔑 无法获取访问令牌\n请检查配置"
        except Exception as e:
            return f"❌ API连接测试异常\n错误信息: {str(e)}"
    
    def _get_server_status(self):
        """获取服务器状态"""
        uptime = time.time() - self.stats['start_time']
        uptime_hours = uptime / 3600
        
        return f"""📊 云服务器状态报告

🚀 服务器信息:
• 版本: Cloud Direct v2.0
• 运行时间: {uptime_hours:.1f} 小时
• 状态: 正常运行

📈 请求统计:
• 总请求数: {self.stats['total_requests']}
• 成功请求: {self.stats['success_requests']}
• 失败请求: {self.stats['failed_requests']}
• 飞书请求: {self.stats['feishu_requests']}

⚙️ 配置状态:
• 飞书配置: {'✅' if self.app_id and self.app_secret else '❌'}
• 领星配置: {'✅' if self.lingxing_app_id and self.lingxing_app_secret else '❌'}
• 访问令牌: {'✅' if self.access_token else '❌'}

🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    def _get_sellers_info(self):
        """获取店铺信息"""
        try:
            # 这里应该调用领星API获取店铺信息
            # 由于需要实际的API调用，这里返回示例信息
            return """🏪 店铺信息

📋 可用店铺列表:
• 店铺ID: 12345 - 主店铺
• 店铺ID: 67890 - 分店铺

💡 使用方法:
• 查看所有店铺补货: 补货
• 查看指定店铺: 补货 12345

⚠️ 注意: 需要配置领星API才能获取实际数据"""
        except Exception as e:
            return f"❌ 获取店铺信息失败: {str(e)}"
    
    def _get_restock_data(self, seller_id=None):
        """获取补货数据"""
        try:
            if seller_id:
                return f"""📦 店铺 {seller_id} 补货数据

⚠️ 功能开发中...
需要配置领星API连接才能获取实际补货数据

💡 当前可用功能:
• 帮助 - 查看所有命令
• 测试 - 测试系统状态
• 状态 - 查看服务器状态"""
            else:
                return """📦 全部店铺补货数据

⚠️ 功能开发中...
需要配置领星API连接才能获取实际补货数据

💡 使用方法:
• 补货 - 查看所有店铺
• 补货 12345 - 查看指定店铺"""
        except Exception as e:
            return f"❌ 获取补货数据失败: {str(e)}"
    
    def _get_urgent_restock(self, seller_id=None):
        """获取紧急补货数据"""
        try:
            return """🚨 紧急补货提醒

⚠️ 功能开发中...
需要配置领星API连接才能获取实际紧急补货数据

💡 当前状态:
• 系统运行正常
• 等待API配置完成
• 可使用基础命令测试"""
        except Exception as e:
            return f"❌ 获取紧急补货数据失败: {str(e)}"
    
    def _get_access_token(self):
        """
        获取飞书访问令牌
        
        Returns:
            str: 访问令牌
        """
        try:
            # 检查令牌是否有效
            if self.access_token and time.time() < self.token_expire_time:
                return self.access_token
            
            # 获取新令牌
            if not self.app_id or not self.app_secret:
                logger.error("❌ 飞书配置不完整")
                return None
            
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.access_token = result.get('tenant_access_token')
                    self.token_expire_time = time.time() + result.get('expire', 7200) - 300
                    logger.info("✅ 获取访问令牌成功")
                    return self.access_token
                else:
                    logger.error(f"❌ 获取访问令牌失败: {result}")
                    return None
            else:
                logger.error(f"❌ 访问令牌请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取访问令牌异常: {str(e)}")
            return None
    
    def _send_message(self, chat_id, text):
        """
        发送消息到飞书
        
        Args:
            chat_id: 聊天ID
            text: 消息内容
            
        Returns:
            bool: 发送结果
        """
        try:
            # 获取访问令牌
            token = self._get_access_token()
            if not token:
                logger.error("❌ 无法获取访问令牌")
                return False
            
            # 发送消息
            url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            data = {
                'receive_id': chat_id,
                'msg_type': 'text',
                'content': json.dumps({'text': text}, ensure_ascii=False)
            }
            
            logger.info(f"📤 发送消息到 {chat_id}: {text[:50]}...")
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info("✅ 消息发送成功")
                    return True
                else:
                    logger.error(f"❌ 消息发送失败: {result}")
                    return False
            else:
                logger.error(f"❌ 消息发送HTTP错误: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送消息异常: {str(e)}")
            return False
    
    def run(self, host='0.0.0.0', port=8080):
        """启动云服务器"""
        logger.info(f"🚀 启动云服务器飞书机器人: http://{host}:{port}")
        logger.info(f"🤖 飞书Webhook地址: http://{host}:{port}/feishu/webhook")
        logger.info(f"💊 健康检查地址: http://{host}:{port}/health")
        logger.info(f"📊 统计信息地址: http://{host}:{port}/stats")
        
        self.app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True
        )

def main():
    """主函数"""
    print("🚀 云服务器飞书机器人重新部署")
    print("=" * 50)
    
    # 检查环境变量
    required_vars = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请设置以下环境变量:")
        for var in missing_vars:
            print(f"  export {var}=your_value")
        print()
    
    # 创建并启动服务器
    server = CloudFeishuServer()
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {str(e)}")
        logger.error(f"服务器启动异常: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
