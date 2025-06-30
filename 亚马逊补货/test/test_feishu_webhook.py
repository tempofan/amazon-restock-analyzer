#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书机器人Webhook测试脚本 🧪
用于测试机器人是否能正确处理消息
"""

import json
import requests
from datetime import datetime

def test_webhook_url_verification():
    """测试URL验证"""
    print("🔗 测试URL验证...")
    
    url = "http://192.168.0.99:5000/feishu/webhook"
    
    # 飞书URL验证请求
    verification_data = {
        "type": "url_verification",
        "challenge": "test_challenge_12345"
    }
    
    try:
        response = requests.post(url, json=verification_data, timeout=10)
        result = response.json()
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('challenge') == verification_data['challenge']:
            print("✅ URL验证测试通过")
            return True
        else:
            print("❌ URL验证测试失败")
            return False
            
    except Exception as e:
        print(f"❌ URL验证测试异常: {e}")
        return False

def test_message_processing():
    """测试消息处理"""
    print("\n💬 测试消息处理...")
    
    url = "http://192.168.0.99:5000/feishu/webhook"
    
    # 模拟飞书消息事件
    message_data = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "message": {
                "msg_type": "text",
                "content": '{"text": "帮助"}',
                "chat_id": "oc_test_chat_id_123456",
                "message_id": "om_test_message_id_123456"
            },
            "sender": {
                "sender_id": {
                    "open_id": "ou_test_user_id_123456"
                }
            }
        }
    }
    
    try:
        response = requests.post(url, json=message_data, timeout=10)
        result = response.json()
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('status') == 'success':
            print("✅ 消息处理测试通过")
            return True
        else:
            print("❌ 消息处理测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 消息处理测试异常: {e}")
        return False

def test_command_endpoint():
    """测试命令端点"""
    print("\n⚙️ 测试命令端点...")
    
    url = "http://192.168.0.99:5000/feishu/command"
    
    test_commands = [
        {"command": "帮助"},
        {"command": "测试"},
        {"command": "状态"}
    ]
    
    success_count = 0
    for cmd_data in test_commands:
        try:
            response = requests.post(url, json=cmd_data, timeout=10)
            result = response.json()
            
            command = cmd_data['command']
            status = result.get('status', 'error')
            response_text = result.get('response', '')
            
            print(f"🎯 命令 '{command}': {status}")
            print(f"   响应长度: {len(response_text)} 字符")
            
            if status == 'success':
                success_count += 1
                
        except Exception as e:
            print(f"❌ 命令 '{cmd_data['command']}' 测试异常: {e}")
    
    print(f"\n📊 命令测试结果: {success_count}/{len(test_commands)} 成功")
    return success_count == len(test_commands)

def test_health_check():
    """测试健康检查"""
    print("\n💊 测试健康检查...")
    
    url = "http://192.168.0.99:5000/health"
    
    try:
        response = requests.get(url, timeout=5)
        result = response.json()
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 健康状态: {result.get('status', 'unknown')}")
        print(f"🤖 机器人状态: {result.get('feishu_bot_status', 'unknown')}")
        
        if result.get('status') == 'healthy':
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def main():
    """主测试流程"""
    print("🧪 飞书机器人Webhook测试")
    print("=" * 50)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行各项测试
    tests = [
        ("健康检查", test_health_check),
        ("URL验证", test_webhook_url_verification),
        ("消息处理", test_message_processing),
        ("命令端点", test_command_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试总结
    print("\n📊 测试总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！机器人可以正常工作。")
        print("\n💡 接下来的步骤:")
        print("1. 在飞书开放平台配置事件订阅URL:")
        print("   http://你的公网IP:5000/feishu/webhook")
        print("2. 确保机器人已添加到群聊中")
        print("3. 在群聊中@机器人发送消息测试")
    else:
        print("⚠️ 部分测试失败，请检查相关配置。")
    
    print(f"\n⏰ 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main() 