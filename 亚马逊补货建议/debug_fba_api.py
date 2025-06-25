#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试FBA建议API
检查API响应的详细信息
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.lingxing_api_new import LingxingAPINew

def debug_fba_api():
    """
    调试FBA建议API调用
    """
    print("🔍 调试FBA建议API")
    print("=" * 50)
    
    # 创建API客户端
    api = LingxingAPINew()
    
    # 测试认证
    print("1. 测试认证...")
    auth_result = api.get_access_token()
    print(f"认证结果: {auth_result}")
    if auth_result:
        print(f"Access Token: {api.access_token[:20]}...")
    else:
        print("❌ 认证失败，无法继续测试")
        return
    
    print("\n2. 测试FBA建议API调用...")
    
    # 测试参数
    shop_id = "136"
    msku = "CNxxxx"
    mode = 0
    
    print(f"测试参数: shop_id={shop_id}, msku={msku}, mode={mode}")
    
    # 直接调用底层API方法
    endpoint = '/erp/sc/routing/fbaSug/msku/getInfo'
    post_data = {
        'sid': int(shop_id),
        'msku': msku,
        'mode': mode
    }
    
    print(f"API端点: {endpoint}")
    print(f"请求数据: {json.dumps(post_data, ensure_ascii=False)}")
    
    # 调用API
    result = api.call_api(endpoint, method='POST', data=post_data)
    
    print(f"\n3. API响应结果:")
    print(f"成功状态: {result.get('success')}")
    print(f"状态码: {result.get('status_code')}")
    
    if result.get('success'):
        api_data = result.get('data', {})
        print(f"响应数据: {json.dumps(api_data, ensure_ascii=False, indent=2)}")
        
        # 检查响应格式
        if isinstance(api_data, dict):
            code = api_data.get('code')
            message = api_data.get('message')
            print(f"\nAPI返回码: {code}")
            print(f"API消息: {message}")
            
            if code == 0:
                print("✅ API调用成功")
                data = api_data.get('data', {})
                local_to_fba = data.get('quantity_sug_local_to_fba', 0)
                print(f"建议本地发FBA量: {local_to_fba}")
            else:
                print(f"❌ API返回错误: {message}")
        else:
            print(f"⚠️ 意外的响应格式: {type(api_data)}")
    else:
        print(f"❌ API调用失败: {result.get('error')}")
    
    print("\n4. 测试其他可能的端点...")
    
    # 尝试其他可能的端点
    alternative_endpoints = [
        '/erp/sc/routing/restocking/info/msku',  # 原有端点
        '/erp/sc/routing/fbaSug/msku/getSummaryList',  # 可能的列表端点
    ]
    
    for alt_endpoint in alternative_endpoints:
        print(f"\n测试端点: {alt_endpoint}")
        alt_result = api.call_api(alt_endpoint, method='POST', data=post_data)
        
        if alt_result.get('success'):
            alt_data = alt_result.get('data', {})
            if isinstance(alt_data, dict):
                code = alt_data.get('code')
                message = alt_data.get('message', 'No message')
                print(f"  返回码: {code}, 消息: {message}")
            else:
                print(f"  响应类型: {type(alt_data)}")
        else:
            print(f"  失败: {alt_result.get('error')}")

if __name__ == "__main__":
    debug_fba_api()
