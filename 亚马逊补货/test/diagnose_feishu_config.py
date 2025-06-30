#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书配置诊断脚本
帮助找出配置问题
"""

import json
import requests
import time

def diagnose_feishu_config():
    """
    诊断飞书配置问题
    """
    print("🔍 飞书配置诊断...")
    
    # 飞书应用配置
    app_id = 'cli_a8d7f7d671f6900d'
    app_secret = 'BFglaACx87kXkzboVThOWere05Oc21KI'
    
    # 1. 获取应用访问令牌
    print("\n1️⃣ 检查应用访问令牌...")
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token_data = {'app_id': app_id, 'app_secret': app_secret}
    
    try:
        response = requests.post(token_url, json=token_data)
        result = response.json()
        
        if result.get('code') == 0:
            access_token = result['tenant_access_token']
            print(f"✅ 访问令牌获取成功")
        else:
            print(f"❌ 访问令牌获取失败: {result}")
            return
    except Exception as e:
        print(f"❌ 访问令牌获取异常: {e}")
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # 2. 检查机器人信息
    print("\n2️⃣ 检查机器人信息...")
    bot_info_url = "https://open.feishu.cn/open-apis/bot/v3/info"
    
    try:
        response = requests.get(bot_info_url, headers=headers)
        result = response.json()
        
        if result.get('code') == 0:
            bot = result.get('bot', {})
            print(f"✅ 机器人信息:")
            print(f"  - 名称: {bot.get('app_name')}")
            print(f"  - 机器人ID: {bot.get('open_id')}")
            print(f"  - 激活状态: {bot.get('activate_status')}")
            print(f"  - 头像: {bot.get('avatar_url')}")
        else:
            print(f"❌ 获取机器人信息失败: {result}")
    except Exception as e:
        print(f"❌ 获取机器人信息异常: {e}")
    
    # 3. 检查webhook配置
    print("\n3️⃣ 检查webhook配置...")
    webhook_url = "http://175.178.183.96:8080/feishu/webhook"
    
    # 验证webhook URL是否可访问
    try:
        test_data = {
            "type": "url_verification",
            "challenge": f"config_test_{int(time.time())}"
        }
        
        response = requests.post(webhook_url, json=test_data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Webhook URL可访问: {webhook_url}")
            print(f"响应: {response.text}")
        else:
            print(f"❌ Webhook URL访问异常: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook URL连接失败: {e}")
    
    # 4. 可能的问题和解决方案
    print("\n4️⃣ 可能的问题和解决方案...")
    
    problems_and_solutions = [
        {
            "问题": "事件订阅配置问题",
            "检查": "确认飞书开放平台中事件订阅的状态",
            "解决": [
                "重新保存事件订阅配置",
                "确认URL验证通过",
                "检查事件类型是否正确选择"
            ]
        },
        {
            "问题": "机器人权限不足",
            "检查": "检查机器人在群聊中的权限",
            "解决": [
                "确认机器人有发送消息权限",
                "检查群聊设置是否允许机器人",
                "尝试重新添加机器人到群聊"
            ]
        },
        {
            "问题": "网络连通性问题", 
            "检查": "飞书服务器是否能访问你的webhook",
            "解决": [
                "检查防火墙设置",
                "确认端口8080对外开放",
                "测试从外网访问云服务器"
            ]
        },
        {
            "问题": "应用发布状态",
            "检查": "应用是否已正确发布",
            "解决": [
                "检查应用发布状态",
                "确认应用已通过审核",
                "检查应用可用范围"
            ]
        }
    ]
    
    for i, item in enumerate(problems_and_solutions, 1):
        print(f"\n问题 {i}: {item['问题']}")
        print(f"检查: {item['检查']}")
        print("解决方案:")
        for solution in item['解决']:
            print(f"  - {solution}")
    
    # 5. 立即行动建议
    print("\n5️⃣ 立即行动建议...")
    print("""
🔧 推荐检查步骤：

1. 重新配置事件订阅：
   - 进入飞书开放平台 → 事件与回调
   - 删除现有的事件订阅
   - 重新添加 'im.message.receive_v1' 事件
   - 重新验证URL

2. 检查机器人状态：
   - 确认机器人在群聊中有管理员权限
   - 尝试移除后重新添加机器人

3. 测试网络连通性：
   - 从手机热点测试访问 http://175.178.183.96:8080/health
   - 确认外网可以访问

4. 检查应用设置：
   - 确认应用已发布且状态正常
   - 检查应用权限范围

💡 如果以上步骤都正常，可能是飞书平台的缓存问题，
   建议等待5-10分钟后再次测试。
""")

if __name__ == "__main__":
    diagnose_feishu_config() 