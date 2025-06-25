#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试InfoMSKU API，不依赖GetSummaryList
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def test_direct_infomsku():
    """
    直接测试特定MSKU的InfoMSKU API
    """
    print("🔍 直接测试InfoMSKU API")
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
    
    # 直接测试InfoMSKU API
    print(f"\n🚀 直接测试InfoMSKU API")
    print("-" * 60)
    
    success_count = 0
    
    # 测试前10个店铺
    for i, shop in enumerate(shops[:10], 1):
        shop_id = str(shop.get('sid', ''))
        shop_name = shop.get('name', '')
        
        print(f"\n🧪 测试 {i}: {shop_name} (ID: {shop_id})")
        
        # 测试不同模式
        test_modes = [
            {"mode": 0, "name": "普通模式"},
            {"mode": 1, "name": "海外仓中转模式"},
        ]
        
        for mode_info in test_modes:
            mode = mode_info['mode']
            mode_name = mode_info['name']
            
            print(f"   🔬 {mode_name} (mode={mode})")
            
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
                                for sm in suggest_sm_list[:3]:
                                    name = sm.get('name', 'N/A')
                                    sm_purchase = sm.get('quantity_sug_purchase', 0)
                                    sm_local_fba = sm.get('quantity_sug_local_to_fba', 0)
                                    print(f"            {name}: 采购={sm_purchase}, 本地发FBA={sm_local_fba}")
                            
                            # 显示完整的原始数据
                            print(f"         📋 完整原始数据:")
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
    
    print(f"\n" + "=" * 60)
    print(f"🎯 测试总结:")
    print(f"   目标MSKU: {target_msku}")
    print(f"   测试店铺数: {min(10, len(shops))}")
    print(f"   成功获取数据次数: {success_count}")
    
    if success_count > 0:
        print(f"   ✅ InfoMSKU API工作正常，成功获取到补货建议数据!")
        print(f"   🎯 这证明API本身没有问题，可以正常返回数据")
        print(f"   💡 建议将此MSKU用于进一步的数据对比测试")
    else:
        print(f"   ❌ 所有测试都未获取到有效数据")
        print(f"   💡 可能的原因:")
        print(f"      1. 该MSKU在所有店铺中都没有配置补货规则")
        print(f"      2. 该MSKU当前不需要补货")
        print(f"      3. 需要特定的业务条件才能生成补货建议")
        print(f"      4. MSKU不存在或已停用")

if __name__ == "__main__":
    test_direct_infomsku()
