#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速飞书诊断脚本
检查整个飞书机器人链路的状态
"""

import requests
import json
import time
from datetime import datetime

def test_cloud_proxy():
    """测试云代理服务器状态"""
    print("🌐 测试云代理服务器...")
    try:
        # 健康检查
        response = requests.get("http://175.178.183.96:8080/health", timeout=10)
        if response.status_code == 200:
            print("✅ 云代理服务器健康检查通过")
            print(f"📊 响应: {response.text}")
        else:
            print(f"❌ 云代理健康检查失败: {response.status_code}")
            return False
            
        # 测试飞书webhook转发
        test_data = {
            "type": "url_verification",
            "challenge": f"diagnostic_test_{int(time.time())}"
        }
        
        response = requests.post(
            "http://175.178.183.96:8080/feishu/webhook",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 云代理飞书webhook转发正常")
            print(f"📊 转发响应: {response.text}")
            return True
        else:
            print(f"❌ 云代理飞书webhook转发失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 云代理测试失败: {e}")
        return False

def test_local_server():
    """测试本地服务器状态"""
    print("\n🏠 测试本地服务器...")
    try:
        # 健康检查
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 本地服务器健康检查通过")
            print(f"📊 响应: {response.text}")
        else:
            print(f"❌ 本地服务器健康检查失败: {response.status_code}")
            return False
            
        # 测试状态接口
        response = requests.get("http://127.0.0.1:8000/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ 本地服务器状态接口正常")
            print(f"📊 状态: {response.text}")
            return True
        else:
            print(f"❌ 本地服务器状态接口失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 本地服务器测试失败: {e}")
        return False

def test_feishu_webhook_chain():
    """测试完整的飞书webhook链路"""
    print("\n🔗 测试完整飞书webhook链路...")
    try:
        # 模拟飞书发送消息到云代理
        test_message = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "message": {
                    "message_id": f"om_diagnostic_{int(time.time())}",
                    "chat_id": f"oc_diagnostic_{int(time.time())}",
                    "sender": {
                        "sender_id": {"open_id": f"ou_diagnostic_{int(time.time())}"},
                        "sender_type": "user"
                    },
                    "create_time": str(int(time.time() * 1000)),
                    "msg_type": "text",
                    "content": "{\"text\": \"@机器人 测试\"}"
                }
            }
        }
        
        print("📤 发送测试消息到云代理...")
        response = requests.post(
            "http://175.178.183.96:8080/feishu/webhook",
            json=test_message,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 云代理接收并转发测试消息成功")
            return True
        else:
            print(f"❌ 云代理转发测试消息失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 飞书webhook链路测试失败: {e}")
        return False

def check_feishu_config():
    """检查飞书配置要点"""
    print("\n⚙️ 飞书配置检查要点:")
    print("1. 事件订阅URL是否为: http://175.178.183.96:8080/feishu/webhook")
    print("2. 是否已添加事件: im.message.receive_v1")
    print("3. 是否已添加事件: im.chat.member.bot.added_v1")
    print("4. 机器人是否已加入测试群聊")
    print("5. 权限是否包含: 接收群聊中@机器人的消息")
    print("6. 权限是否包含: 获取与发送单聊、群聊消息")
    print("\n💡 如果以上都正确但仍无响应，可能需要:")
    print("   - 重新保存事件订阅配置")
    print("   - 机器人退群后重新加入")
    print("   - 等待5-10分钟让配置生效")

def main():
    """主函数"""
    print("🚀 开始飞书机器人快速诊断...")
    print(f"⏰ 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试云代理
    cloud_ok = test_cloud_proxy()
    
    # 测试本地服务器
    local_ok = test_local_server()
    
    # 测试完整链路
    chain_ok = test_feishu_webhook_chain()
    
    # 检查配置
    check_feishu_config()
    
    print("\n" + "=" * 60)
    print("📊 诊断结果汇总:")
    print(f"🌐 云代理服务器: {'✅ 正常' if cloud_ok else '❌ 异常'}")
    print(f"🏠 本地服务器: {'✅ 正常' if local_ok else '❌ 异常'}")
    print(f"🔗 完整链路: {'✅ 正常' if chain_ok else '❌ 异常'}")
    
    if cloud_ok and local_ok and chain_ok:
        print("\n🎉 技术层面一切正常！问题可能在飞书开放平台配置")
        print("💡 建议检查飞书开放平台的事件订阅配置")
    else:
        print("\n⚠️ 发现技术问题，需要优先解决")

if __name__ == "__main__":
    main() 