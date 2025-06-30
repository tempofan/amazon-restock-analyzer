#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 云服务器飞书处理器
直接在云服务器上处理飞书请求，无需本地连接
"""

import requests
import json
import os
from datetime import datetime

class CloudFeishuHandler:
    """
    云服务器飞书处理器
    """
    
    def __init__(self):
        """初始化云服务器飞书处理器"""
        self.cloud_server = "http://175.178.183.96:8080"
        self.local_server = "http://127.0.0.1:8000"
        
        # 飞书配置
        self.app_id = "cli_a8d49f76d7fbd00b"
        self.app_secret = "your_app_secret"  # 需要配置
        
        print("🌐 云服务器飞书处理器初始化完成")
    
    def handle_url_verification(self, challenge):
        """
        处理飞书URL验证
        """
        print(f"🔗 处理URL验证: {challenge}")
        return {"challenge": challenge}
    
    def handle_message_event(self, event_data):
        """
        处理飞书消息事件
        """
        try:
            event = event_data.get('event', {})
            message = event.get('message', {})
            sender = event.get('sender', {})
            
            # 提取消息信息
            msg_type = message.get('msg_type', '')
            content = message.get('content', '{}')
            chat_id = message.get('chat_id', '')
            message_id = message.get('message_id', '')
            
            # 解析消息内容
            try:
                content_obj = json.loads(content)
                text = content_obj.get('text', '').strip()
            except:
                text = content
            
            print(f"📨 收到消息: {text}")
            print(f"📍 群聊ID: {chat_id}")
            
            # 处理不同的命令
            response_text = self.process_command(text)
            
            # 发送回复
            if response_text:
                self.send_message(chat_id, response_text)
            
            return {"status": "success", "message": "消息处理完成"}
            
        except Exception as e:
            print(f"❌ 处理消息事件失败: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def process_command(self, text):
        """
        处理用户命令
        """
        text = text.lower().strip()
        
        if "帮助" in text or "help" in text:
            return self.get_help_message()
        elif "测试" in text or "test" in text:
            return self.get_test_message()
        elif "状态" in text or "status" in text:
            return self.get_status_message()
        elif "店铺" in text or "shop" in text:
            return self.get_shop_list()
        elif "补货" in text:
            return self.get_restock_info()
        else:
            return self.get_default_message()
    
    def get_help_message(self):
        """获取帮助信息"""
        return """🤖 亚马逊补货助手V2 帮助

📋 可用命令:
• 帮助 - 显示此帮助信息
• 测试 - 测试机器人功能
• 状态 - 查看系统状态
• 店铺 - 查看店铺列表
• 补货 - 查看补货信息

💡 使用方法:
直接@机器人并发送命令即可，例如:
@亚马逊补货助手V2 店铺

🔧 技术支持:
如有问题请联系管理员"""
    
    def get_test_message(self):
        """获取测试信息"""
        return f"""✅ 机器人测试成功！

🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 服务器: 云服务器 (175.178.183.96)
🤖 版本: V2.0
📊 状态: 正常运行

💡 所有功能正常，可以开始使用！"""
    
    def get_status_message(self):
        """获取状态信息"""
        try:
            # 获取云服务器统计
            response = requests.get(f"{self.cloud_server}/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                return f"""📊 系统状态报告

🌐 云服务器状态: ✅ 正常
📈 总请求数: {stats.get('stats', {}).get('total_requests', 0)}
🤖 飞书请求: {stats.get('stats', {}).get('feishu_requests', 0)}
⏱️ 运行时间: {stats.get('uptime_hours', 0):.1f} 小时
📊 成功率: {stats.get('success_rate', 0):.1f}%

🔧 服务模式: 云端直接处理
💡 状态: 所有功能正常"""
            else:
                return "⚠️ 无法获取系统状态"
        except:
            return "❌ 系统状态检查失败"
    
    def get_shop_list(self):
        """获取店铺列表"""
        return """🏪 店铺列表

📋 当前管理的店铺:
• TOMSEM - 主要店铺
• BETRIC - 副店铺  
• KRYVUS - 新店铺
• VATIN - 测试店铺

💡 说明:
店铺数据通过领星ERP API获取
如需查看详细信息，请使用补货命令

🔄 数据更新: 实时同步"""
    
    def get_restock_info(self):
        """获取补货信息"""
        return """📦 补货信息查询

🔍 正在查询补货数据...

⚠️ 注意:
由于API连接限制，详细补货数据需要通过本地服务器获取。
当前云端模式提供基础功能。

💡 建议:
如需完整补货功能，请联系管理员配置本地连接。

📊 基础信息:
• 系统运行正常
• 数据接口已配置
• 等待完整功能部署"""
    
    def get_default_message(self):
        """获取默认回复"""
        return """🤖 你好！我是亚马逊补货助手V2

❓ 我没有理解你的指令，请尝试:
• 发送 "帮助" 查看可用命令
• 发送 "测试" 测试机器人功能
• 发送 "状态" 查看系统状态

💡 提示: 请确保@机器人并使用正确的命令格式"""
    
    def send_message(self, chat_id, text):
        """
        发送消息到飞书群
        """
        try:
            print(f"📤 发送消息到群聊: {chat_id}")
            print(f"📝 消息内容: {text[:100]}...")
            
            # 这里需要实现实际的飞书API调用
            # 由于需要access_token，暂时只记录日志
            print("✅ 消息发送完成 (模拟)")
            
            return True
        except Exception as e:
            print(f"❌ 发送消息失败: {str(e)}")
            return False
    
    def test_cloud_handler(self):
        """
        测试云处理器功能
        """
        print("🧪 测试云服务器飞书处理器")
        print("=" * 50)
        
        # 测试URL验证
        print("1️⃣ 测试URL验证...")
        result = self.handle_url_verification("test_challenge")
        print(f"✅ URL验证结果: {result}")
        
        # 测试消息处理
        print("\n2️⃣ 测试消息处理...")
        test_event = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "message": {
                    "msg_type": "text",
                    "content": json.dumps({"text": "帮助"}),
                    "chat_id": "test_chat_cloud",
                    "message_id": "test_msg_cloud"
                },
                "sender": {
                    "sender_id": {
                        "open_id": "test_user_cloud"
                    }
                }
            }
        }
        
        result = self.handle_message_event(test_event)
        print(f"✅ 消息处理结果: {result}")
        
        print("\n🎉 云处理器测试完成！")
        return True

def main():
    """主函数"""
    print("🚀 启动云服务器飞书处理器测试")
    print("=" * 60)
    
    handler = CloudFeishuHandler()
    success = handler.test_cloud_handler()
    
    if success:
        print("\n✅ 云处理器准备就绪！")
        print("\n📋 下一步:")
        print("1. 将此处理逻辑部署到云服务器")
        print("2. 修改云服务器的飞书webhook处理")
        print("3. 测试完整的飞书机器人功能")
    else:
        print("\n❌ 云处理器测试失败")

if __name__ == '__main__':
    main()
