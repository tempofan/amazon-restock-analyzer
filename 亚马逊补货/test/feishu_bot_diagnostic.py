#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书机器人全面诊断脚本 🤖
检查飞书机器人无法响应的所有可能原因
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv('config/server.env')

def check_environment_variables():
    """检查环境变量配置"""
    print("🔍 检查环境变量配置...")
    print("-" * 50)
    
    required_vars = {
        'FEISHU_APP_ID': os.getenv('FEISHU_APP_ID'),
        'FEISHU_APP_SECRET': os.getenv('FEISHU_APP_SECRET'),
        'FEISHU_VERIFICATION_TOKEN': os.getenv('FEISHU_VERIFICATION_TOKEN'),
        'FEISHU_ENCRYPT_KEY': os.getenv('FEISHU_ENCRYPT_KEY', '可选')
    }
    
    all_configured = True
    for var_name, value in required_vars.items():
        if value and value != '未设置':
            if var_name == 'FEISHU_APP_SECRET':
                print(f"✅ {var_name}: {value[:10]}...")
            else:
                print(f"✅ {var_name}: {value}")
        else:
            print(f"❌ {var_name}: 未配置")
            if var_name != 'FEISHU_ENCRYPT_KEY':
                all_configured = False
    
    return all_configured

def check_feishu_token():
    """检查飞书访问令牌获取"""
    print("\n🎯 检查飞书访问令牌...")
    print("-" * 50)
    
    app_id = os.getenv('FEISHU_APP_ID')
    app_secret = os.getenv('FEISHU_APP_SECRET')
    
    if not app_id or not app_secret:
        print("❌ App ID 或 App Secret 未配置")
        return False
    
    try:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {'Content-Type': 'application/json'}
        data = {'app_id': app_id, 'app_secret': app_secret}
        
        print(f"📡 请求URL: {url}")
        print(f"📝 请求数据: {{'app_id': '{app_id}', 'app_secret': '***'}}")
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        result = response.json()
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print("✅ 访问令牌获取成功")
            return True
        else:
            print(f"❌ 访问令牌获取失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def check_webhook_server():
    """检查Webhook服务器状态"""
    print("\n🌐 检查Webhook服务器...")
    print("-" * 50)
    
    from config.config import ServerConfig
    host = ServerConfig.HOST
    port = ServerConfig.PORT
    
    # 检查主服务器
    main_url = f"http://{host}:{port}/health"
    print(f"📡 检查主服务器: {main_url}")
    
    try:
        response = requests.get(main_url, timeout=5)
        print(f"✅ 主服务器响应: {response.status_code}")
        print(f"📄 响应内容: {response.json()}")
    except Exception as e:
        print(f"❌ 主服务器无响应: {e}")
    
    # 检查飞书专用服务器
    feishu_url = f"http://{host}:5000/health"
    print(f"\n📡 检查飞书服务器: {feishu_url}")
    
    try:
        response = requests.get(feishu_url, timeout=5)
        print(f"✅ 飞书服务器响应: {response.status_code}")
        print(f"📄 响应内容: {response.json()}")
    except Exception as e:
        print(f"❌ 飞书服务器无响应: {e}")

def check_feishu_bot_initialization():
    """检查飞书机器人初始化"""
    print("\n🤖 检查飞书机器人初始化...")
    print("-" * 50)
    
    try:
        from feishu.feishu_bot import FeishuBot
        bot = FeishuBot()
        
        print(f"✅ FeishuBot实例化成功")
        print(f"📱 App ID: {bot.app_id}")
        print(f"🔑 App Secret: {bot.app_secret[:10]}..." if bot.app_secret else "未配置")
        print(f"🎫 Verification Token: {bot.verification_token}")
        print(f"🔐 Encrypt Key: {'已配置' if bot.encrypt_key else '未配置'}")
        
        # 测试获取访问令牌
        print("\n🎯 测试获取访问令牌...")
        token = bot.get_access_token()
        if token:
            print(f"✅ 访问令牌获取成功: {token[:20]}...")
        else:
            print("❌ 访问令牌获取失败")
            
        return True
        
    except Exception as e:
        print(f"❌ FeishuBot初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_command_processing():
    """检查命令处理功能"""
    print("\n⚙️ 检查命令处理功能...")
    print("-" * 50)
    
    try:
        from feishu.feishu_bot import FeishuBot
        bot = FeishuBot()
        
        # 测试命令处理
        test_commands = ['帮助', 'help', '测试', 'test', '未知命令']
        
        for command in test_commands:
            try:
                response = bot._process_command(command, 'test_user')
                print(f"✅ 命令 '{command}': 处理成功")
                print(f"   响应长度: {len(response)} 字符")
            except Exception as e:
                print(f"❌ 命令 '{command}': 处理失败 - {e}")
                
    except Exception as e:
        print(f"❌ 命令处理测试失败: {e}")

def simulate_webhook_request():
    """模拟webhook请求"""
    print("\n📨 模拟webhook请求...")
    print("-" * 50)
    
    # 模拟飞书消息事件
    mock_event = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "message": {
                "msg_type": "text",
                "content": '{"text": "帮助"}',
                "chat_id": "oc_test_chat_id",
                "message_id": "om_test_message_id"
            },
            "sender": {
                "sender_id": {
                    "open_id": "ou_test_user_id"
                }
            }
        }
    }
    
    try:
        from feishu.feishu_bot import FeishuBot
        bot = FeishuBot()
        
        print(f"📝 模拟事件: {json.dumps(mock_event, ensure_ascii=False, indent=2)}")
        
        result = bot.process_message(mock_event)
        print(f"✅ 消息处理成功")
        print(f"📊 处理结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ 消息处理失败: {e}")
        import traceback
        traceback.print_exc()

def check_network_connectivity():
    """检查网络连接"""
    print("\n🌍 检查网络连接...")
    print("-" * 50)
    
    # 检查飞书API连接
    test_urls = [
        "https://open.feishu.cn",
        "https://www.baidu.com",
        "https://api.github.com"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {url}: 连接正常 (状态码: {response.status_code})")
        except Exception as e:
            print(f"❌ {url}: 连接失败 - {e}")

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    print("-" * 50)
    
    required_packages = [
        'requests',
        'flask',
        'python-dotenv'
    ]
    
    optional_packages = [
        'pycryptodome'  # 用于消息加密
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}: 已安装")
        except ImportError:
            print(f"❌ {package}: 未安装")
    
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_').replace('pycryptodome', 'Crypto'))
            print(f"✅ {package}: 已安装")
        except ImportError:
            print(f"⚠️ {package}: 未安装（可选）")

def provide_solutions():
    """提供解决方案建议"""
    print("\n💡 常见问题解决方案...")
    print("=" * 50)
    
    solutions = [
        "1. 确保飞书开放平台配置正确:",
        "   • 应用类型选择'企业自建应用'",
        "   • 获取正确的App ID和App Secret",
        "   • 配置事件订阅URL",
        "   • 添加机器人权限",
        "",
        "2. 检查网络配置:",
        "   • 确保服务器可以访问飞书API",
        "   • 检查防火墙设置",
        "   • 确认端口是否开放",
        "",
        "3. 验证Webhook配置:",
        "   • URL格式: http://你的IP:端口/feishu/webhook", 
        "   • 确保服务器正在运行",
        "   • 检查飞书事件订阅配置",
        "",
        "4. 机器人权限设置:",
        "   • 接收群聊中@机器人消息",
        "   • 获取与发送单聊、群聊消息",
        "   • 以应用的身份发送消息",
        "",
        "5. 常用调试命令:",
        "   • python test/feishu_bot_diagnostic.py",
        "   • python feishu/start_feishu_server.py",
        "   • 检查logs目录下的错误日志",
    ]
    
    for solution in solutions:
        print(solution)

def main():
    """主诊断流程"""
    print("🔧 飞书机器人全面诊断工具")
    print("=" * 60)
    print(f"📅 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行各项检查
    checks = [
        check_environment_variables,
        check_dependencies,
        check_network_connectivity,
        check_feishu_token,
        check_feishu_bot_initialization,
        check_command_processing,
        simulate_webhook_request,
        check_webhook_server,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            results.append(False)
        print()
    
    # 输出总结
    print("📊 诊断总结")
    print("=" * 60)
    passed = sum(1 for r in results if r is True)
    total = len([r for r in results if r is not None])
    
    if passed == total:
        print("🎉 所有检查都通过了！机器人应该能正常工作。")
        print("💡 如果仍有问题，请检查：")
        print("   • 飞书开放平台的事件订阅配置")
        print("   • 服务器的公网访问权限")
        print("   • 机器人是否被正确添加到群聊中")
    else:
        print(f"⚠️ 发现问题: {total - passed}/{total} 项检查未通过")
        print("请根据上述诊断结果修复相关问题。")
    
    provide_solutions()

if __name__ == '__main__':
    main() 