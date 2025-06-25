#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定MSKU的InfoMSKU API数据
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def test_specific_msku():
    """
    测试特定MSKU: 3DB-SJ10-0-0000091
    """
    print("🔍 测试特定MSKU的InfoMSKU API数据")
    print("=" * 60)
    
    # 目标MSKU
    target_msku = "3DB-SJ10-0-0000091"
    print(f"🎯 目标MSKU: {target_msku}")
    
    # 初始化API
    api = LingxingAPINew()
    
    # 获取店铺列表
    print("\n🏪 获取店铺列表...")
    shop_result = api.get_shop_list()
    if not shop_result.get('success'):
        print(f"❌ 获取店铺列表失败: {shop_result.get('error')}")
        return
    
    shops = shop_result.get('data', {}).get('data', [])
    if not shops:
        print("❌ 没有可用的店铺")
        return
    
    print(f"✅ 找到 {len(shops)} 个店铺")
    
    # 步骤1: 先在GetSummaryList中查找该MSKU
    print(f"\n📋 步骤1: 在GetSummaryList中查找MSKU {target_msku}")
    print("-" * 60)
    
    found_in_shops = []
    
    for shop in shops[:5]:  # 检查前5个店铺
        shop_id = str(shop.get('sid', ''))
        shop_name = shop.get('name', '')
        
        print(f"\n🔍 检查店铺: {shop_name} (ID: {shop_id})")
        
        try:
            # 使用msku_list参数直接查询特定MSKU
            result = api.call_api('/erp/sc/routing/restocking/analysis/getSummaryList', 
                                 method='POST', 
                                 data={
                                     "data_type": 2,  # MSKU维度
                                     "offset": 0,
                                     "length": 50,
                                     "sid_list": [shop_id],
                                     "msku_list": [target_msku]  # 直接查询目标MSKU
                                 })
            
            if result.get('success'):
                api_data = result.get('data', {})
                if api_data.get('code') == 0:
                    items = api_data.get('data', [])
                    total = api_data.get('total', 0)
                    
                    if items:
                        print(f"   ✅ 找到MSKU! 共 {len(items)} 个记录")
                        found_in_shops.append({
                            'shop_id': shop_id,
                            'shop_name': shop_name,
                            'items': items
                        })
                        
                        # 显示找到的数据
                        for item in items:
                            basic_info = item.get('basic_info', {})
                            suggest_info = item.get('suggest_info', {})
                            
                            msku_list = basic_info.get('msku_fnsku_list', [])
                            found_msku = msku_list[0].get('msku', '') if msku_list else ''
                            asin = basic_info.get('asin', '')
                            
                            purchase = suggest_info.get('quantity_sug_purchase', 0)
                            local_fba = suggest_info.get('quantity_sug_local_to_fba', 0)
                            oversea_fba = suggest_info.get('quantity_sug_oversea_to_fba', 0)
                            
                            print(f"      MSKU: {found_msku}")
                            print(f"      ASIN: {asin}")
                            print(f"      采购建议: {purchase}")
                            print(f"      本地发FBA: {local_fba}")
                            print(f"      海外发FBA: {oversea_fba}")
                    else:
                        print(f"   ❌ 未找到MSKU")
                else:
                    error_msg = api_data.get('message', '未知错误')
                    print(f"   ❌ GetSummaryList错误: {error_msg}")
            else:
                error = result.get('error', 'Unknown error')
                print(f"   ❌ API调用失败: {error}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
    
    # 步骤2: 对找到的MSKU测试InfoMSKU API
    print(f"\n🚀 步骤2: 测试InfoMSKU API")
    print("-" * 60)
    
    if not found_in_shops:
        print(f"❌ 在所有店铺中都未找到MSKU {target_msku}")
        print(f"💡 建议:")
        print(f"   1. 检查MSKU是否正确")
        print(f"   2. 确认该MSKU是否在这些店铺中存在")
        print(f"   3. 尝试其他MSKU进行测试")
        return
    
    print(f"✅ 在 {len(found_in_shops)} 个店铺中找到了该MSKU")
    
    # 对每个找到的店铺测试InfoMSKU API
    for shop_data in found_in_shops:
        shop_id = shop_data['shop_id']
        shop_name = shop_data['shop_name']
        
        print(f"\n🧪 测试店铺: {shop_name} (ID: {shop_id})")
        
        # 测试不同模式
        test_modes = [
            {"mode": 0, "name": "普通模式"},
            {"mode": 1, "name": "海外仓中转模式"},
        ]
        
        for mode_info in test_modes:
            mode = mode_info['mode']
            mode_name = mode_info['name']
            
            print(f"\n   🔬 测试 {mode_name} (mode={mode})")
            
            try:
                # 直接调用InfoMSKU API
                result = api.call_api('/erp/sc/routing/fbaSug/msku/getInfo', 
                                     method='POST', 
                                     data={
                                         'sid': int(shop_id),
                                         'msku': target_msku,
                                         'mode': mode
                                     })
                
                print(f"      HTTP状态: {'✅ 成功' if result.get('success') else '❌ 失败'}")
                
                if result.get('success'):
                    api_data = result.get('data', {})
                    response_code = api_data.get('code', -1)
                    response_message = api_data.get('message', '')
                    
                    print(f"      业务状态: code={response_code}, message={response_message}")
                    
                    if response_code == 0:
                        # 成功获取数据
                        suggestion_data = api_data.get('data', {})
                        if suggestion_data:
                            print(f"      🎉 成功获取InfoMSKU数据!")
                            
                            # 显示关键补货建议字段
                            purchase = suggestion_data.get('quantity_sug_purchase', 0)
                            local_fba = suggestion_data.get('quantity_sug_local_to_fba', 0)
                            oversea_fba = suggestion_data.get('quantity_sug_oversea_to_fba', 0)
                            local_oversea = suggestion_data.get('quantity_sug_local_to_oversea', 0)
                            
                            print(f"         采购建议: {purchase}")
                            print(f"         本地发FBA: {local_fba}")
                            print(f"         海外发FBA: {oversea_fba}")
                            print(f"         本地发海外仓: {local_oversea}")
                            
                            # 显示其他重要字段
                            fba_valid = suggestion_data.get('quantity_fba_valid', 0)
                            sales_30 = suggestion_data.get('sales_total_30', 0)
                            sales_avg_30 = suggestion_data.get('sales_avg_30', 0)
                            
                            print(f"         FBA可售库存: {fba_valid}")
                            print(f"         30天销量: {sales_30}")
                            print(f"         日均销量: {sales_avg_30}")
                            
                            # 显示运输方式建议
                            suggest_sm_list = suggestion_data.get('suggest_sm_list', [])
                            if suggest_sm_list:
                                print(f"         运输方式建议 ({len(suggest_sm_list)} 个):")
                                for sm in suggest_sm_list[:3]:
                                    name = sm.get('name', 'N/A')
                                    sm_purchase = sm.get('quantity_sug_purchase', 0)
                                    sm_local_fba = sm.get('quantity_sug_local_to_fba', 0)
                                    print(f"           {name}: 采购={sm_purchase}, 本地发FBA={sm_local_fba}")
                            
                            # 对比GetSummaryList的数据
                            print(f"\n      📊 与GetSummaryList数据对比:")
                            for item in shop_data['items']:
                                suggest_info = item.get('suggest_info', {})
                                summary_purchase = suggest_info.get('quantity_sug_purchase', 0)
                                summary_local_fba = suggest_info.get('quantity_sug_local_to_fba', 0)
                                summary_oversea_fba = suggest_info.get('quantity_sug_oversea_to_fba', 0)
                                
                                purchase_diff = purchase - summary_purchase
                                local_fba_diff = local_fba - summary_local_fba
                                oversea_fba_diff = oversea_fba - summary_oversea_fba
                                
                                print(f"         GetSummaryList: 采购={summary_purchase}, 本地FBA={summary_local_fba}, 海外FBA={summary_oversea_fba}")
                                print(f"         InfoMSKU:       采购={purchase}, 本地FBA={local_fba}, 海外FBA={oversea_fba}")
                                print(f"         差异:           采购={purchase_diff:+d}, 本地FBA={local_fba_diff:+d}, 海外FBA={oversea_fba_diff:+d}")
                                
                                if purchase_diff != 0 or local_fba_diff != 0 or oversea_fba_diff != 0:
                                    print(f"         🎯 发现数量差异! 这证实了两个API返回不同数据")
                                else:
                                    print(f"         ✅ 数量一致")
                        else:
                            print(f"      ⚠️  InfoMSKU返回空数据")
                    else:
                        # API返回错误
                        error_details = api_data.get('error_details', response_message)
                        print(f"      ❌ InfoMSKU错误: {error_details}")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"      ❌ HTTP错误: {error}")
                    
            except Exception as e:
                print(f"      ❌ 异常: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 测试总结:")
    print(f"   目标MSKU: {target_msku}")
    print(f"   找到店铺数: {len(found_in_shops)}")
    print(f"   如果InfoMSKU API返回有效数据，说明API工作正常")
    print(f"   如果仍然返回'该补货建议数据不存在'，可能需要:")
    print(f"     1. 在领星ERP中配置该MSKU的补货规则")
    print(f"     2. 确认该MSKU有实际的补货需求")
    print(f"     3. 联系领星技术支持确认API使用条件")

if __name__ == "__main__":
    test_specific_msku()
