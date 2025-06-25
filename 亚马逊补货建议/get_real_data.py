#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取真实的补货建议数据
用于测试FBA建议API
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.lingxing_api_new import LingxingAPINew

def get_real_replenishment_data():
    """
    获取真实的补货建议数据
    """
    print("🔍 获取真实的补货建议数据")
    print("=" * 50)
    
    # 创建API客户端
    api = LingxingAPINew()
    
    # 获取补货建议列表
    print("1. 获取补货建议列表...")
    result = api.get_replenishment_suggestions(page=1, page_size=5)
    
    if result.get('success'):
        data = result.get('data', {})
        print(f"数据类型: {type(data)}")
        
        if result.get('is_mock'):
            print("⚠️ 使用的是模拟数据")
            mock_data = data
            
            # 从模拟数据中提取MSKU和ASIN
            if isinstance(mock_data, dict) and 'data' in mock_data:
                items = mock_data['data']
                if items and len(items) > 0:
                    print(f"\n2. 找到 {len(items)} 条模拟数据:")
                    for i, item in enumerate(items[:3], 1):
                        msku = item.get('msku', '')
                        asin = item.get('asin', '')
                        shop_id = item.get('shop_id', '136')
                        print(f"  {i}. MSKU: {msku}, ASIN: {asin}, 店铺ID: {shop_id}")
                        
                        # 测试FBA建议API
                        if msku:
                            print(f"     测试FBA建议API (MSKU: {msku})...")
                            test_fba_api(api, shop_id, msku=msku)
                        elif asin:
                            print(f"     测试FBA建议API (ASIN: {asin})...")
                            test_fba_api(api, shop_id, asin=asin)
                        print()
        else:
            print("✅ 使用的是真实API数据")
            # 处理真实API数据
            if isinstance(data, dict) and 'data' in data:
                items = data['data']
                print(f"找到 {len(items)} 条真实数据")
                # 类似处理...
    else:
        print(f"❌ 获取补货建议列表失败: {result.get('error')}")

def test_fba_api(api, shop_id, msku='', asin=''):
    """
    测试FBA建议API
    """
    try:
        result = api.get_fba_suggestion_info(
            shop_id=str(shop_id),
            msku=msku,
            asin=asin,
            mode=0
        )
        
        if result.get('success'):
            data = result.get('data', {})
            local_to_fba = data.get('quantity_sug_local_to_fba', 0)
            print(f"       ✅ 成功! 建议本地发FBA量: {local_to_fba}")
        else:
            error = result.get('error', '未知错误')
            print(f"       ❌ 失败: {error}")
    except Exception as e:
        print(f"       ❌ 异常: {e}")

if __name__ == "__main__":
    get_real_replenishment_data()
