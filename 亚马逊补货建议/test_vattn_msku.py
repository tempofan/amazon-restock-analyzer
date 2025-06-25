#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试VATTN店铺的特定MSKU
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def test_vattn_msku():
    """
    专门测试VATTN店铺的MSKU: 3DB-SJ10-0-0000091
    """
    print("🔍 测试VATTN店铺的特定MSKU")
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
    
    # 查找VATTN店铺
    vattn_shops = []
    for shop in shops:
        shop_name = shop.get('name', '').upper()
        if 'VATTN' in shop_name:
            vattn_shops.append(shop)
    
    if not vattn_shops:
        print("❌ 未找到VATTN店铺")
        print("📋 所有店铺列表:")
        for shop in shops:
            print(f"   {shop.get('name', 'N/A')} (ID: {shop.get('sid', 'N/A')})")
        return
    
    print(f"✅ 找到 {len(vattn_shops)} 个VATTN店铺:")
    for shop in vattn_shops:
        print(f"   {shop.get('name', 'N/A')} (ID: {shop.get('sid', 'N/A')})")
    
    # 测试每个VATTN店铺
    print(f"\n🚀 测试VATTN店铺的InfoMSKU API")
    print("-" * 60)
    
    success_count = 0
    
    for shop in vattn_shops:
        shop_id = str(shop.get('sid', ''))
        shop_name = shop.get('name', '')
        
        print(f"\n🧪 测试店铺: {shop_name} (ID: {shop_id})")
        
        # 测试不同模式
        test_modes = [
            {"mode": 0, "name": "普通模式"},
            {"mode": 1, "name": "海外仓中转模式"},
        ]
        
        for mode_info in test_modes:
            mode = mode_info['mode']
            mode_name = mode_info['name']
            
            print(f"\n   🔬 {mode_name} (mode={mode})")
            
            try:
                # 直接调用InfoMSKU API
                result = api.call_api('/erp/sc/routing/fbaSug/msku/getInfo', 
                                     method='POST', 
                                     data={
                                         'sid': int(shop_id),
                                         'msku': target_msku,
                                         'mode': mode
                                     })
                
                if result.get('success'):
                    api_data = result.get('data', {})
                    response_code = api_data.get('code', -1)
                    response_message = api_data.get('message', '')
                    
                    print(f"      状态: code={response_code}, message={response_message}")
                    
                    if response_code == 0:
                        # 成功获取数据
                        suggestion_data = api_data.get('data', {})
                        if suggestion_data:
                            success_count += 1
                            print(f"      🎉 成功获取InfoMSKU数据!")
                            
                            # 显示关键补货建议字段
                            purchase = suggestion_data.get('quantity_sug_purchase', 0)
                            local_fba = suggestion_data.get('quantity_sug_local_to_fba', 0)
                            oversea_fba = suggestion_data.get('quantity_sug_oversea_to_fba', 0)
                            local_oversea = suggestion_data.get('quantity_sug_local_to_oversea', 0)
                            
                            print(f"         📦 补货建议:")
                            print(f"            采购建议: {purchase}")
                            print(f"            本地发FBA: {local_fba}")
                            print(f"            海外发FBA: {oversea_fba}")
                            print(f"            本地发海外仓: {local_oversea}")
                            
                            # 显示库存和销量信息
                            fba_valid = suggestion_data.get('quantity_fba_valid', 0)
                            local_valid = suggestion_data.get('quantity_local_valid', 0)
                            oversea_valid = suggestion_data.get('quantity_oversea_valid', 0)
                            sales_30 = suggestion_data.get('sales_total_30', 0)
                            sales_avg_30 = suggestion_data.get('sales_avg_30', 0)
                            
                            print(f"         📊 库存信息:")
                            print(f"            FBA可售: {fba_valid}")
                            print(f"            本地库存: {local_valid}")
                            print(f"            海外库存: {oversea_valid}")
                            print(f"            30天销量: {sales_30}")
                            print(f"            日均销量: {sales_avg_30}")
                            
                            # 显示运输方式建议
                            suggest_sm_list = suggestion_data.get('suggest_sm_list', [])
                            if suggest_sm_list:
                                print(f"         🚚 运输方式建议 ({len(suggest_sm_list)} 个):")
                                for sm in suggest_sm_list:
                                    name = sm.get('name', 'N/A')
                                    sm_purchase = sm.get('quantity_sug_purchase', 0)
                                    sm_local_fba = sm.get('quantity_sug_local_to_fba', 0)
                                    print(f"            {name}: 采购={sm_purchase}, 本地发FBA={sm_local_fba}")
                            
                            print(f"\n         📋 完整原始数据:")
                            try:
                                formatted_data = json.dumps(suggestion_data, indent=8, ensure_ascii=False)
                                print(formatted_data)
                            except:
                                print(f"            {suggestion_data}")
                                
                        else:
                            print(f"      ⚠️  返回空数据")
                    else:
                        # API返回错误
                        error_details = api_data.get('error_details', response_message)
                        print(f"      ❌ 错误: {error_details}")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"      ❌ HTTP错误: {error}")
                    
            except Exception as e:
                print(f"      ❌ 异常: {e}")
    
    # 如果成功获取到数据，也测试GetSummaryList进行对比
    if success_count > 0:
        print(f"\n📊 对比GetSummaryList数据")
        print("-" * 60)
        
        for shop in vattn_shops:
            shop_id = str(shop.get('sid', ''))
            shop_name = shop.get('name', '')
            
            print(f"\n🔍 获取 {shop_name} 的GetSummaryList数据")
            
            try:
                # 调用GetSummaryList API
                result = api.call_api('/erp/sc/routing/restocking/analysis/getSummaryList', 
                                     method='POST', 
                                     data={
                                         "data_type": 2,  # MSKU维度
                                         "offset": 0,
                                         "length": 100,
                                         "sid_list": [shop_id]
                                     })
                
                if result.get('success'):
                    api_data = result.get('data', {})
                    if api_data.get('code') == 0:
                        items = api_data.get('data', [])
                        
                        # 查找目标MSKU
                        target_item = None
                        for item in items:
                            basic_info = item.get('basic_info', {})
                            msku_list = basic_info.get('msku_fnsku_list', [])
                            if msku_list:
                                msku = msku_list[0].get('msku', '')
                                if msku == target_msku:
                                    target_item = item
                                    break
                        
                        if target_item:
                            suggest_info = target_item.get('suggest_info', {})
                            summary_purchase = suggest_info.get('quantity_sug_purchase', 0)
                            summary_local_fba = suggest_info.get('quantity_sug_local_to_fba', 0)
                            summary_oversea_fba = suggest_info.get('quantity_sug_oversea_to_fba', 0)
                            
                            print(f"   ✅ 在GetSummaryList中找到目标MSKU")
                            print(f"      GetSummaryList数据:")
                            print(f"         采购建议: {summary_purchase}")
                            print(f"         本地发FBA: {summary_local_fba}")
                            print(f"         海外发FBA: {summary_oversea_fba}")
                            
                            print(f"\n      🎯 现在可以对比InfoMSKU和GetSummaryList的数据差异!")
                        else:
                            print(f"   ❌ 在GetSummaryList的 {len(items)} 个MSKU中未找到目标MSKU")
                    else:
                        error_msg = api_data.get('message', '未知错误')
                        print(f"   ❌ GetSummaryList错误: {error_msg}")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"   ❌ GetSummaryList HTTP错误: {error}")
                    
            except Exception as e:
                print(f"   ❌ GetSummaryList异常: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 测试总结:")
    print(f"   目标MSKU: {target_msku}")
    print(f"   VATTN店铺数: {len(vattn_shops)}")
    print(f"   成功获取InfoMSKU数据次数: {success_count}")
    
    if success_count > 0:
        print(f"   ✅ 成功! InfoMSKU API在VATTN店铺中返回了有效数据!")
        print(f"   🎯 这证明API工作正常，可以获取到准确的补货建议")
        print(f"   💡 现在可以用这个数据进行GetSummaryList的对比测试")
    else:
        print(f"   ❌ 即使在VATTN店铺中也未获取到数据")
        print(f"   💡 可能需要检查:")
        print(f"      1. 店铺ID是否正确")
        print(f"      2. API权限配置")
        print(f"      3. 补货规则的具体配置")

if __name__ == "__main__":
    test_vattn_msku()
