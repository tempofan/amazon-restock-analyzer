#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试InfoMSKU API的不同参数组合
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def test_infomsku_params():
    """
    测试InfoMSKU API的不同参数组合，找到有效的调用方式
    """
    print("🔍 测试InfoMSKU API的不同参数组合")
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
    
    # 从GetSummaryList获取一些MSKU用于测试
    print("\n📋 从GetSummaryList获取MSKU列表...")
    test_shop = shops[0]
    shop_id = str(test_shop.get('sid', ''))
    shop_name = test_shop.get('name', '')
    
    print(f"🎯 使用测试店铺: {shop_name} (ID: {shop_id})")
    
    # 获取该店铺的MSKU列表
    summary_result = api.call_api('/erp/sc/routing/restocking/analysis/getSummaryList', 
                                 method='POST', 
                                 data={
                                     "data_type": 2,  # MSKU维度
                                     "offset": 0,
                                     "length": 10,
                                     "sid": [shop_id]
                                 })
    
    if not summary_result.get('success'):
        print(f"❌ 获取GetSummaryList失败: {summary_result.get('error')}")
        return
    
    summary_data = summary_result.get('data', {})
    if summary_data.get('code') != 0:
        print(f"❌ GetSummaryList业务错误: {summary_data.get('message')}")
        return
    
    items = summary_data.get('data', [])
    if not items:
        print("❌ 没有找到MSKU数据")
        return
    
    print(f"✅ 找到 {len(items)} 个MSKU")
    
    # 提取MSKU列表
    test_mskus = []
    for item in items[:5]:  # 只测试前5个
        basic_info = item.get('basic_info', {})
        msku_list = basic_info.get('msku_fnsku_list', [])
        if msku_list:
            msku = msku_list[0].get('msku', '')
            if msku:
                test_mskus.append(msku)
    
    print(f"📦 测试MSKU列表: {test_mskus}")
    
    # 测试不同的参数组合
    test_cases = [
        # 基本参数
        {"name": "基本参数", "params": {"sid": int(shop_id), "msku": test_mskus[0], "mode": 0}},
        {"name": "模式1", "params": {"sid": int(shop_id), "msku": test_mskus[0], "mode": 1}},
        
        # 不同店铺
        {"name": "其他店铺", "params": {"sid": int(shops[1].get('sid', shop_id)), "msku": test_mskus[0], "mode": 0}},
        
        # 不同MSKU
        {"name": "其他MSKU", "params": {"sid": int(shop_id), "msku": test_mskus[1] if len(test_mskus) > 1 else test_mskus[0], "mode": 0}},
        
        # 字符串格式的sid
        {"name": "字符串sid", "params": {"sid": shop_id, "msku": test_mskus[0], "mode": 0}},
        
        # 不传mode参数
        {"name": "无mode参数", "params": {"sid": int(shop_id), "msku": test_mskus[0]}},
    ]
    
    print(f"\n🧪 开始测试不同参数组合...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 测试 {i}: {test_case['name']}")
        params = test_case['params']
        print(f"   参数: {params}")
        
        try:
            # 直接调用InfoMSKU API
            result = api.call_api('/erp/sc/routing/fbaSug/msku/getInfo', 
                                 method='POST', 
                                 data=params)
            
            print(f"   HTTP状态: {'✅ 成功' if result.get('success') else '❌ 失败'}")
            
            if result.get('success'):
                api_data = result.get('data', {})
                response_code = api_data.get('code', -1)
                response_message = api_data.get('message', '')
                
                print(f"   业务状态: code={response_code}, message={response_message}")
                
                if response_code == 0:
                    # 成功获取数据
                    suggestion_data = api_data.get('data', {})
                    if suggestion_data:
                        purchase = suggestion_data.get('quantity_sug_purchase', 0)
                        local_fba = suggestion_data.get('quantity_sug_local_to_fba', 0)
                        oversea_fba = suggestion_data.get('quantity_sug_oversea_to_fba', 0)
                        
                        print(f"   🎉 成功获取补货建议!")
                        print(f"      采购建议: {purchase}")
                        print(f"      本地发FBA: {local_fba}")
                        print(f"      海外发FBA: {oversea_fba}")
                        
                        # 显示更多字段
                        other_fields = ['sales_avg_30', 'sales_total_30', 'quantity_fba_valid']
                        for field in other_fields:
                            value = suggestion_data.get(field, 'N/A')
                            print(f"      {field}: {value}")
                            
                        # 显示运输方式建议
                        suggest_sm_list = suggestion_data.get('suggest_sm_list', [])
                        if suggest_sm_list:
                            print(f"      运输方式建议 ({len(suggest_sm_list)} 个):")
                            for sm in suggest_sm_list[:2]:
                                name = sm.get('name', 'N/A')
                                sm_purchase = sm.get('quantity_sug_purchase', 0)
                                print(f"        {name}: {sm_purchase}")
                    else:
                        print(f"   ⚠️  返回空数据")
                elif response_code == 500:
                    error_details = api_data.get('error_details', response_message)
                    print(f"   ❌ 业务错误: {error_details}")
                else:
                    print(f"   ❌ 未知业务错误: {response_message}")
            else:
                error = result.get('error', 'Unknown error')
                print(f"   ❌ HTTP错误: {error}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
        
        print(f"   " + "-" * 50)
    
    print(f"\n📊 测试总结:")
    print(f"   如果所有测试都返回'该补货建议数据不存在'，可能的原因:")
    print(f"   1. 需要在领星ERP中先配置补货规则")
    print(f"   2. 当前MSKU没有库存不足的情况")
    print(f"   3. API权限或账户配置问题")
    print(f"   4. 需要特定的业务条件才能生成补货建议")

if __name__ == "__main__":
    test_infomsku_params()
