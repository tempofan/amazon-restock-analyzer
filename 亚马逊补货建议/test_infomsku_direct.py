#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试InfoMSKU API
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def test_infomsku_direct():
    """
    直接测试InfoMSKU API调用
    """
    print("🔍 直接测试InfoMSKU API")
    print("=" * 60)
    
    # 初始化API
    api = LingxingAPINew()
    
    # 测试参数
    test_cases = [
        {"shop_id": "6149", "msku": "RTEST01", "mode": 0},
        {"shop_id": "6151", "msku": "RTEST01", "mode": 0},
        {"shop_id": "6149", "msku": "CN0001", "mode": 0},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}:")
        print(f"   店铺ID: {test_case['shop_id']}")
        print(f"   MSKU: {test_case['msku']}")
        print(f"   模式: {test_case['mode']}")
        
        # 直接调用API
        endpoint = api.endpoints['fba_suggestion_info_msku']
        post_data = {
            'sid': int(test_case['shop_id']),
            'msku': test_case['msku'],
            'mode': test_case['mode']
        }
        
        print(f"   📡 API端点: {endpoint}")
        print(f"   📦 请求数据: {post_data}")
        
        try:
            result = api.call_api(endpoint, method='POST', data=post_data)
            print(f"   📊 API响应:")
            print(f"      成功: {result.get('success', False)}")
            
            if result.get('success'):
                data = result.get('data', {})
                print(f"      数据类型: {type(data)}")
                
                if isinstance(data, dict):
                    # 显示关键字段
                    key_fields = [
                        'quantity_sug_purchase',
                        'quantity_sug_local_to_fba', 
                        'quantity_sug_oversea_to_fba',
                        'quantity_sug_local_to_oversea'
                    ]
                    
                    print(f"      关键字段:")
                    for field in key_fields:
                        value = data.get(field, 'N/A')
                        print(f"        {field}: {value}")
                    
                    # 显示运输方式建议
                    suggest_sm_list = data.get('suggest_sm_list', [])
                    if suggest_sm_list:
                        print(f"      运输方式建议 ({len(suggest_sm_list)} 个):")
                        for sm in suggest_sm_list[:3]:  # 只显示前3个
                            name = sm.get('name', 'N/A')
                            purchase = sm.get('quantity_sug_purchase', 0)
                            local_fba = sm.get('quantity_sug_local_to_fba', 0)
                            print(f"        {name}: 采购={purchase}, 本地发FBA={local_fba}")
                else:
                    print(f"      原始数据: {data}")
            else:
                error = result.get('error', 'Unknown error')
                print(f"      错误: {error}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
        
        print(f"   " + "-" * 50)

if __name__ == "__main__":
    test_infomsku_direct()
