#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接返回InfoMSKU API的原始数据
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def test_infomsku_raw():
    """
    直接返回InfoMSKU API的原始数据，供进一步确认问题
    """
    print("🔍 直接返回InfoMSKU API原始数据")
    print("=" * 60)
    
    # 初始化API
    api = LingxingAPINew()
    
    # 测试参数
    test_cases = [
        {"shop_id": "6149", "msku": "RTEST01", "mode": 0},
        {"shop_id": "6151", "msku": "RTEST01", "mode": 0},
        {"shop_id": "6149", "msku": "CN0001", "mode": 0},
        {"shop_id": "6149", "msku": "3DB-SJ14-1-0000044", "mode": 0},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试用例 {i}:")
        print(f"   店铺ID: {test_case['shop_id']}")
        print(f"   MSKU: {test_case['msku']}")
        print(f"   模式: {test_case['mode']}")
        
        try:
            # 调用修改后的InfoMSKU API方法
            result = api._get_accurate_fba_suggestion(
                shop_id=test_case['shop_id'],
                msku=test_case['msku'],
                mode=test_case['mode']
            )
            
            print(f"   📊 API调用结果:")
            print(f"      成功: {result.get('success', False)}")
            print(f"      消息: {result.get('message', 'N/A')}")
            
            if result.get('success'):
                raw_data = result.get('data', {})
                print(f"      原始数据类型: {type(raw_data)}")
                
                # 美化打印原始数据
                try:
                    formatted_data = json.dumps(raw_data, indent=2, ensure_ascii=False)
                    print(f"      原始数据内容:")
                    print(formatted_data)
                except:
                    print(f"      原始数据内容: {raw_data}")
            else:
                error = result.get('error', 'Unknown error')
                print(f"      错误: {error}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
        
        print(f"   " + "-" * 50)
    
    print(f"\n📋 说明:")
    print(f"   现在API会直接返回InfoMSKU的原始响应数据")
    print(f"   包括错误信息和状态码，供您进一步分析")
    print(f"   请检查返回的数据结构和内容")

if __name__ == "__main__":
    test_infomsku_raw()
