#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试店铺选择功能
验证FBA建议API与店铺选择的集成
"""

import requests
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_shop_selection_integration():
    """
    测试店铺选择功能集成
    """
    print("🏪 测试店铺选择功能集成")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    # 1. 获取店铺列表
    print("1. 获取店铺列表...")
    shop_response = requests.get(f"{base_url}/api/shop-list", timeout=30)
    
    if shop_response.status_code == 200:
        shop_result = shop_response.json()
        if shop_result.get('success'):
            shops = shop_result.get('data', {}).get('data', [])
            print(f"✅ 成功获取 {len(shops)} 个店铺")
            
            # 显示前5个店铺
            print("\n📋 店铺列表（前5个）:")
            for i, shop in enumerate(shops[:5], 1):
                sid = shop.get('sid')
                name = shop.get('name')
                country = shop.get('country')
                account = shop.get('account_name')
                print(f"  {i}. {name} ({country}) - ID: {sid} - 账户: {account}")
            
            # 2. 使用第一个店铺测试FBA建议API
            if shops:
                test_shop = shops[0]
                shop_id = str(test_shop.get('sid'))
                shop_name = test_shop.get('name')
                
                print(f"\n2. 使用店铺 '{shop_name}' (ID: {shop_id}) 测试FBA建议API...")
                
                # 从之前的测试中我们知道这些MSKU存在
                test_cases = [
                    {
                        "name": f"测试 {shop_name} - 真实MSKU",
                        "data": {
                            "shop_id": shop_id,
                            "msku": "R01500302JBK",  # 已知存在的MSKU
                            "mode": 0
                        }
                    },
                    {
                        "name": f"测试 {shop_name} - 真实ASIN",
                        "data": {
                            "shop_id": shop_id,
                            "asin": "B071L1HK76",  # 已知存在的ASIN
                            "mode": 0
                        }
                    }
                ]
                
                for test_case in test_cases:
                    print(f"\n   📋 {test_case['name']}")
                    print(f"   请求数据: {json.dumps(test_case['data'], ensure_ascii=False)}")
                    
                    try:
                        fba_response = requests.post(
                            f"{base_url}/api/fba-suggestion-info",
                            json=test_case['data'],
                            headers={'Content-Type': 'application/json'},
                            timeout=30
                        )
                        
                        if fba_response.status_code == 200:
                            fba_result = fba_response.json()
                            if fba_result.get('success'):
                                data = fba_result.get('data', {})
                                local_to_fba = data.get('quantity_sug_local_to_fba', 0)
                                print(f"   ✅ 成功! 建议本地发FBA量: {local_to_fba}")
                                print(f"   店铺: {shop_name} (ID: {shop_id})")
                                print(f"   MSKU: {data.get('msku', '未提供')}")
                                print(f"   ASIN: {data.get('asin', '未提供')}")
                            else:
                                error = fba_result.get('message', '未知错误')
                                print(f"   ❌ FBA API失败: {error}")
                        else:
                            print(f"   ❌ HTTP错误: {fba_response.status_code}")
                            
                    except Exception as e:
                        print(f"   ❌ 请求异常: {e}")
                
                # 3. 测试其他店铺
                print(f"\n3. 测试其他店铺...")
                for shop in shops[1:3]:  # 测试第2和第3个店铺
                    shop_id = str(shop.get('sid'))
                    shop_name = shop.get('name')
                    
                    print(f"\n   📋 测试店铺: {shop_name} (ID: {shop_id})")
                    
                    test_data = {
                        "shop_id": shop_id,
                        "msku": "R01500302JBK",  # 使用相同的MSKU测试
                        "mode": 0
                    }
                    
                    try:
                        fba_response = requests.post(
                            f"{base_url}/api/fba-suggestion-info",
                            json=test_data,
                            headers={'Content-Type': 'application/json'},
                            timeout=30
                        )
                        
                        if fba_response.status_code == 200:
                            fba_result = fba_response.json()
                            if fba_result.get('success'):
                                data = fba_result.get('data', {})
                                local_to_fba = data.get('quantity_sug_local_to_fba', 0)
                                print(f"   ✅ 成功! 建议本地发FBA量: {local_to_fba}")
                            else:
                                error = fba_result.get('message', '未知错误')
                                print(f"   ⚠️ 该店铺无此MSKU数据: {error}")
                        else:
                            print(f"   ❌ HTTP错误: {fba_response.status_code}")
                            
                    except Exception as e:
                        print(f"   ❌ 请求异常: {e}")
            
        else:
            print(f"❌ 获取店铺列表失败: {shop_result.get('message')}")
    else:
        print(f"❌ 店铺列表API HTTP错误: {shop_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🏁 店铺选择功能测试完成")
    print("\n💡 现在您可以访问以下页面测试:")
    print(f"   🌐 FBA建议测试页面: {base_url}/fba-suggestion-test")
    print("   📋 页面将自动加载店铺列表供选择")

if __name__ == "__main__":
    test_shop_selection_integration()
