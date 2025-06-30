#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书应用权限和API版本
检查可能的权限或版本问题
"""

import json
import requests

def test_feishu_permissions():
    """
    测试飞书应用权限和可用的API
    """
    print("🔐 开始测试飞书应用权限...")
    
    # 配置
    app_id = 'cli_a8d7f7d671f6900d'
    app_secret = 'BFglaACx87kXkzboVThOWere05Oc21KI'
    
    # 1. 获取访问令牌
    print("\n1️⃣ 获取访问令牌...")
    token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    token_data = {'app_id': app_id, 'app_secret': app_secret}
    
    response = requests.post(token_url, json=token_data)
    result = response.json()
    
    if result.get('code') != 0:
        print(f"❌ 获取令牌失败: {result}")
        return
    
    access_token = result['tenant_access_token']
    print(f"✅ 获取访问令牌成功")
    print(f"Token过期时间: {result.get('expire', 'unknown')}秒")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # 2. 测试获取机器人信息
    print("\n2️⃣ 测试获取机器人信息...")
    bot_info_url = "https://open.feishu.cn/open-apis/bot/v3/info"
    
    try:
        response = requests.get(bot_info_url, headers=headers)
        result = response.json()
        
        print(f"机器人信息API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            bot = result.get('bot', {})
            print(f"✅ 机器人信息获取成功:")
            print(f"  - 机器人名称: {bot.get('app_name')}")
            print(f"  - 机器人ID: {bot.get('open_id')}")
            print(f"  - 状态: {bot.get('status')}")
        else:
            print(f"❌ 获取机器人信息失败: {result.get('msg')}")
            
    except Exception as e:
        print(f"❌ 获取机器人信息异常: {e}")
    
    # 3. 测试不同的消息API版本
    print("\n3️⃣ 测试不同的消息API版本...")
    
    api_versions = [
        {
            'name': 'v1版本',
            'url': 'https://open.feishu.cn/open-apis/im/v1/messages'
        },
        {
            'name': 'v2版本 (如果存在)',
            'url': 'https://open.feishu.cn/open-apis/im/v2/messages'
        },
        {
            'name': '旧版本消息API',
            'url': 'https://open.feishu.cn/open-apis/message/v4/send'
        }
    ]
    
    test_data = {
        'receive_id': 'oc_test_chat_123',
        'receive_id_type': 'chat_id',
        'msg_type': 'text',
        'content': '{"text": "版本测试消息"}'
    }
    
    for api in api_versions:
        print(f"\n测试 {api['name']}: {api['url']}")
        try:
            response = requests.post(api['url'], headers=headers, json=test_data)
            result = response.json()
            
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('code') == 0:
                print(f"✅ {api['name']} 成功!")
            else:
                print(f"❌ {api['name']} 失败: {result.get('msg')}")
                
        except Exception as e:
            print(f"❌ {api['name']} 异常: {e}")
    
    # 4. 测试获取应用权限范围
    print("\n4️⃣ 测试应用权限范围...")
    
    # 尝试获取应用的权限范围
    scope_urls = [
        "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
        "https://open.feishu.cn/open-apis/application/v6/app/visibility",
    ]
    
    for url in scope_urls:
        print(f"\n测试权限API: {url}")
        try:
            if 'app_access_token' in url:
                # 获取应用访问令牌
                response = requests.post(url, json={'app_id': app_id, 'app_secret': app_secret})
            else:
                response = requests.get(url, headers=headers)
                
            result = response.json()
            print(f"权限API响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            print(f"❌ 权限API异常: {e}")
    
    # 5. 测试使用query参数
    print("\n5️⃣ 测试使用Query参数...")
    
    query_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    query_data = {
        'receive_id': 'oc_test_chat_123',
        'msg_type': 'text',
        'content': '{"text": "Query参数测试"}'
    }
    
    try:
        response = requests.post(query_url, headers=headers, json=query_data)
        result = response.json()
        
        print(f"Query参数测试结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('code') == 0:
            print("✅ Query参数方式成功!")
        else:
            print(f"❌ Query参数方式失败: {result.get('msg')}")
            
    except Exception as e:
        print(f"❌ Query参数测试异常: {e}")
    
    print("\n🏁 权限测试完成")

if __name__ == "__main__":
    test_feishu_permissions() 