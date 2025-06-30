# -*- coding: utf-8 -*-
"""
飞书机器人测试脚本
用于测试机器人的各种功能
"""

import requests
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import ServerConfig

def test_health_check():
    """
    测试健康检查接口
    """
    print("🔍 测试健康检查接口...")
    
    try:
        url = f"http://{ServerConfig.HOST}:{ServerConfig.PORT}/health"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 健康检查通过")
            print(f"   状态: {data.get('status')}")
            print(f"   时间: {data.get('timestamp')}")
            print(f"   服务器: {data.get('server')}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_api_status():
    """
    测试API状态接口
    """
    print("\n🔍 测试API状态接口...")
    
    try:
        url = f"http://{ServerConfig.HOST}:{ServerConfig.PORT}/api/status"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API状态检查通过")
            
            # 飞书机器人状态
            feishu_bot = data.get('feishu_bot', {})
            print(f"   飞书App ID: {feishu_bot.get('app_id')}")
            print(f"   令牌状态: {'有效' if feishu_bot.get('has_token') else '无效'}")
            
            # API连接状态
            api_conn = data.get('api_connection', {})
            print(f"   API连接: {'✅ 成功' if api_conn.get('success') else '❌ 失败'}")
            
            return True
        else:
            print(f"❌ API状态检查失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API状态检查异常: {e}")
        return False

def test_command_execution():
    """
    测试命令执行接口
    """
    print("\n🔍 测试命令执行接口...")
    
    commands = [
        "帮助",
        "测试", 
        "状态",
        "店铺"
    ]
    
    for command in commands:
        try:
            url = f"http://{ServerConfig.HOST}:{ServerConfig.PORT}/feishu/command"
            data = {
                "command": command
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 命令 '{command}' 执行成功")
                print(f"   响应长度: {len(result.get('response', ''))}")
            else:
                print(f"❌ 命令 '{command}' 执行失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 命令 '{command}' 执行异常: {e}")

def test_webhook_simulation():
    """
    模拟飞书webhook请求
    """
    print("\n🔍 模拟飞书webhook请求...")
    
    # 模拟URL验证请求
    print("   测试URL验证...")
    try:
        url = f"http://{ServerConfig.HOST}:{ServerConfig.PORT}/feishu/webhook"
        data = {
            "type": "url_verification",
            "challenge": "test_challenge_123456"
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('challenge') == 'test_challenge_123456':
                print("   ✅ URL验证通过")
            else:
                print("   ❌ URL验证失败：挑战码不匹配")
        else:
            print(f"   ❌ URL验证失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ URL验证异常: {e}")
    
    # 模拟消息事件
    print("   测试消息事件...")
    try:
        data = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "message": {
                    "msg_type": "text",
                    "content": json.dumps({"text": "帮助"}),
                    "chat_id": "test_chat_id"
                },
                "sender": {
                    "sender_id": {
                        "open_id": "test_user_id"
                    }
                }
            }
        }
        
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("   ✅ 消息事件处理成功")
            else:
                print(f"   ⚠️ 消息事件处理状态: {result.get('status')}")
        else:
            print(f"   ❌ 消息事件处理失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 消息事件处理异常: {e}")

def run_all_tests():
    """
    运行所有测试
    """
    print("🧪 开始飞书机器人功能测试...\n")
    
    tests = [
        test_health_check,
        test_api_status,
        test_command_execution,
        test_webhook_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！飞书机器人功能正常！")
    else:
        print("⚠️ 部分测试失败，请检查配置和服务状态")

def interactive_test():
    """
    交互式测试模式
    """
    print("🤖 飞书机器人交互式测试\n")
    
    while True:
        print("请选择测试项目：")
        print("1. 健康检查")
        print("2. API状态")
        print("3. 命令执行")
        print("4. Webhook模拟")
        print("5. 运行所有测试")
        print("0. 退出")
        
        try:
            choice = input("\n请输入选择 (0-5): ").strip()
            
            if choice == '0':
                print("👋 测试结束")
                break
            elif choice == '1':
                test_health_check()
            elif choice == '2':
                test_api_status()
            elif choice == '3':
                test_command_execution()
            elif choice == '4':
                test_webhook_simulation()
            elif choice == '5':
                run_all_tests()
            else:
                print("❌ 无效选择，请重新输入")
                
            input("\n按Enter键继续...")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 测试中断")
            break
        except Exception as e:
            print(f"❌ 操作异常: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='飞书机器人测试工具')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    parser.add_argument('--interactive', action='store_true', help='交互式测试模式')
    parser.add_argument('--health', action='store_true', help='健康检查测试')
    parser.add_argument('--status', action='store_true', help='API状态测试')
    parser.add_argument('--command', action='store_true', help='命令执行测试')
    parser.add_argument('--webhook', action='store_true', help='Webhook模拟测试')
    
    args = parser.parse_args()
    
    if args.all:
        run_all_tests()
    elif args.interactive:
        interactive_test()
    elif args.health:
        test_health_check()
    elif args.status:
        test_api_status()
    elif args.command:
        test_command_execution()
    elif args.webhook:
        test_webhook_simulation()
    else:
        # 默认交互式模式
        interactive_test() 