#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找有效的MSKU用于测试InfoMSKU API
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def find_valid_msku():
    """
    从GetSummaryList API中查找有补货建议的MSKU
    """
    print("🔍 查找有效的MSKU用于测试")
    print("=" * 60)
    
    # 初始化API
    api = LingxingAPINew()
    
    # 获取店铺列表
    print("🏪 获取店铺列表...")
    shop_result = api.get_shop_list()
    if not shop_result.get('success'):
        print(f"❌ 获取店铺列表失败: {shop_result.get('error')}")
        return
    
    shops = shop_result.get('data', {}).get('data', [])
    if not shops:
        print("❌ 没有可用的店铺")
        return
    
    print(f"✅ 找到 {len(shops)} 个店铺")
    
    # 遍历店铺查找有补货建议的MSKU
    valid_mskus = []
    
    for shop in shops[:3]:  # 只检查前3个店铺
        shop_id = str(shop.get('sid', ''))
        shop_name = shop.get('name', '')
        
        print(f"\n🎯 检查店铺: {shop_name} (ID: {shop_id})")
        
        # 获取该店铺的补货建议列表
        try:
            result = api.get_replenishment_suggestions(
                page=1,
                page_size=20,
                shop_id=shop_id,
                data_type=2  # MSKU维度
            )
            
            if result.get('success'):
                data = result.get('data', {})
                items = data.get('data', []) if isinstance(data, dict) else data
                
                print(f"   📋 找到 {len(items)} 个补货项目")
                
                # 查找有补货建议的MSKU
                for item in items:
                    basic_info = item.get('basic_info', {})
                    msku_list = basic_info.get('msku_fnsku_list', [])
                    suggest_info = item.get('suggest_info', {})
                    
                    if msku_list:
                        msku = msku_list[0].get('msku', '')
                        purchase_sug = suggest_info.get('quantity_sug_purchase', 0)
                        local_fba_sug = suggest_info.get('quantity_sug_local_to_fba', 0)
                        oversea_fba_sug = suggest_info.get('quantity_sug_oversea_to_fba', 0)
                        
                        # 如果有任何补货建议
                        if purchase_sug > 0 or local_fba_sug > 0 or oversea_fba_sug > 0:
                            valid_msku = {
                                'shop_id': shop_id,
                                'shop_name': shop_name,
                                'msku': msku,
                                'asin': basic_info.get('asin', ''),
                                'quantity_sug_purchase': purchase_sug,
                                'quantity_sug_local_to_fba': local_fba_sug,
                                'quantity_sug_oversea_to_fba': oversea_fba_sug,
                            }
                            valid_mskus.append(valid_msku)
                            print(f"   ✅ 找到有效MSKU: {msku} (采购:{purchase_sug}, 本地FBA:{local_fba_sug}, 海外FBA:{oversea_fba_sug})")
                
            else:
                print(f"   ❌ 获取补货建议失败: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 测试找到的有效MSKU
    print(f"\n📊 测试有效MSKU的InfoMSKU API")
    print("=" * 60)
    
    if not valid_mskus:
        print("❌ 没有找到有效的MSKU")
        return
    
    print(f"✅ 找到 {len(valid_mskus)} 个有效MSKU")
    
    # 测试前3个有效MSKU
    for i, msku_info in enumerate(valid_mskus[:3], 1):
        print(f"\n🧪 测试 {i}: {msku_info['msku']} (店铺: {msku_info['shop_name']})")
        print(f"   GetSummaryList数据: 采购={msku_info['quantity_sug_purchase']}, 本地FBA={msku_info['quantity_sug_local_to_fba']}, 海外FBA={msku_info['quantity_sug_oversea_to_fba']}")
        
        # 调用InfoMSKU API
        endpoint = api.endpoints['fba_suggestion_info_msku']
        post_data = {
            'sid': int(msku_info['shop_id']),
            'msku': msku_info['msku'],
            'mode': 0
        }
        
        try:
            result = api.call_api(endpoint, method='POST', data=post_data)
            
            if result.get('success'):
                data = result.get('data', {})
                
                if data and isinstance(data, dict) and data.get('code') == 0:
                    info_data = data.get('data', {})
                    if info_data:
                        purchase = info_data.get('quantity_sug_purchase', 0)
                        local_fba = info_data.get('quantity_sug_local_to_fba', 0)
                        oversea_fba = info_data.get('quantity_sug_oversea_to_fba', 0)
                        
                        print(f"   InfoMSKU数据:     采购={purchase}, 本地FBA={local_fba}, 海外FBA={oversea_fba}")
                        
                        # 对比差异
                        purchase_diff = purchase - msku_info['quantity_sug_purchase']
                        local_fba_diff = local_fba - msku_info['quantity_sug_local_to_fba']
                        oversea_fba_diff = oversea_fba - msku_info['quantity_sug_oversea_to_fba']
                        
                        print(f"   数量差异:         采购={purchase_diff:+d}, 本地FBA={local_fba_diff:+d}, 海外FBA={oversea_fba_diff:+d}")
                        
                        if purchase_diff != 0 or local_fba_diff != 0 or oversea_fba_diff != 0:
                            print(f"   🎯 发现数量差异! 这证实了两个API返回的数据确实不同")
                        else:
                            print(f"   ✅ 数量一致")
                    else:
                        print(f"   ❌ InfoMSKU返回空数据")
                else:
                    error_msg = data.get('message', '未知错误') if data else '空响应'
                    print(f"   ❌ InfoMSKU API错误: {error_msg}")
            else:
                print(f"   ❌ InfoMSKU API调用失败: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ InfoMSKU API异常: {e}")

if __name__ == "__main__":
    find_valid_msku()
