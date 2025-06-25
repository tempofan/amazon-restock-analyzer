#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试InfoMSKU API返回数据
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def debug_infomsku():
    """
    调试InfoMSKU API返回的完整数据结构
    """
    print("🔍 调试InfoMSKU API返回数据")
    print("=" * 60)
    
    # 初始化API
    api = LingxingAPINew()
    
    # 测试参数
    shop_id = "6151"
    msku = "RTEST01"
    mode = 0
    
    print(f"📦 测试参数:")
    print(f"   店铺ID: {shop_id}")
    print(f"   MSKU: {msku}")
    print(f"   模式: {mode}")
    
    # 直接调用API
    endpoint = api.endpoints['fba_suggestion_info_msku']
    post_data = {
        'sid': int(shop_id),
        'msku': msku,
        'mode': mode
    }
    
    print(f"\n📡 API调用:")
    print(f"   端点: {endpoint}")
    print(f"   数据: {post_data}")
    
    try:
        result = api.call_api(endpoint, method='POST', data=post_data)
        
        print(f"\n📊 完整API响应:")
        print(f"   成功状态: {result.get('success', False)}")
        
        if result.get('success'):
            data = result.get('data', {})
            print(f"   数据类型: {type(data)}")
            print(f"   数据内容:")
            
            # 美化打印JSON数据
            try:
                formatted_data = json.dumps(data, indent=2, ensure_ascii=False)
                print(formatted_data)
            except:
                print(f"   原始数据: {data}")
                
            # 分析数据结构
            if isinstance(data, dict):
                print(f"\n🔍 数据结构分析:")
                print(f"   顶级键: {list(data.keys())}")
                
                # 检查是否有嵌套的data字段
                if 'data' in data:
                    nested_data = data['data']
                    print(f"   嵌套data类型: {type(nested_data)}")
                    if isinstance(nested_data, dict):
                        print(f"   嵌套data键: {list(nested_data.keys())}")
                        
                        # 查找补货建议相关字段
                        suggestion_fields = [k for k in nested_data.keys() if 'sug' in k.lower() or 'quantity' in k.lower()]
                        if suggestion_fields:
                            print(f"   补货建议字段: {suggestion_fields}")
                            for field in suggestion_fields:
                                value = nested_data.get(field)
                                print(f"     {field}: {value}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"   错误: {error}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_infomsku()
