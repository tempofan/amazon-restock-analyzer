#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GetSummaryList API的不同模式，寻找更准确的数据
"""

import sys
import os
import json
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew

def test_getsummarylist_modes():
    """
    测试GetSummaryList API的不同模式和参数组合
    """
    print("🔍 测试GetSummaryList API的不同模式")
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
    
    test_shop = shops[0]
    shop_id = str(test_shop.get('sid', ''))
    shop_name = test_shop.get('name', '')
    
    print(f"🎯 使用测试店铺: {shop_name} (ID: {shop_id})")
    
    # 测试不同的模式和参数组合
    test_cases = [
        {
            "name": "普通模式 (mode=0)",
            "params": {
                "data_type": 2,
                "offset": 0,
                "length": 5,
                "sid_list": [shop_id],
                "mode": 0
            }
        },
        {
            "name": "海外仓中转模式 (mode=1)",
            "params": {
                "data_type": 2,
                "offset": 0,
                "length": 5,
                "sid_list": [shop_id],
                "mode": 1
            }
        },
        {
            "name": "不指定模式",
            "params": {
                "data_type": 2,
                "offset": 0,
                "length": 5,
                "sid_list": [shop_id]
            }
        },
        {
            "name": "ASIN维度",
            "params": {
                "data_type": 1,  # ASIN维度
                "offset": 0,
                "length": 5,
                "sid_list": [shop_id],
                "mode": 0
            }
        }
    ]
    
    print(f"\n🧪 开始测试不同模式...")
    print("=" * 60)
    
    results = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 测试 {i}: {test_case['name']}")
        params = test_case['params']
        print(f"   参数: {json.dumps(params, indent=2)}")
        
        try:
            result = api.call_api('/erp/sc/routing/restocking/analysis/getSummaryList', 
                                 method='POST', 
                                 data=params)
            
            print(f"   HTTP状态: {'✅ 成功' if result.get('success') else '❌ 失败'}")
            
            if result.get('success'):
                api_data = result.get('data', {})
                response_code = api_data.get('code', -1)
                response_message = api_data.get('message', '')
                
                print(f"   业务状态: code={response_code}, message={response_message}")
                
                if response_code == 0:
                    items = api_data.get('data', [])
                    total = api_data.get('total', 0)
                    
                    print(f"   📊 获取到 {len(items)} 个项目 (总计: {total})")
                    
                    if items:
                        # 分析第一个项目的补货建议数据
                        first_item = items[0]
                        basic_info = first_item.get('basic_info', {})
                        suggest_info = first_item.get('suggest_info', {})
                        
                        msku_list = basic_info.get('msku_fnsku_list', [])
                        msku = msku_list[0].get('msku', 'N/A') if msku_list else 'N/A'
                        
                        purchase = suggest_info.get('quantity_sug_purchase', 0)
                        local_fba = suggest_info.get('quantity_sug_local_to_fba', 0)
                        oversea_fba = suggest_info.get('quantity_sug_oversea_to_fba', 0)
                        local_oversea = suggest_info.get('quantity_sug_local_to_oversea', 0)
                        
                        print(f"   📦 示例MSKU: {msku}")
                        print(f"      采购建议: {purchase}")
                        print(f"      本地发FBA: {local_fba}")
                        print(f"      海外发FBA: {oversea_fba}")
                        print(f"      本地发海外仓: {local_oversea}")
                        
                        # 保存结果用于对比
                        results[test_case['name']] = {
                            'msku': msku,
                            'purchase': purchase,
                            'local_fba': local_fba,
                            'oversea_fba': oversea_fba,
                            'local_oversea': local_oversea
                        }
                        
                        # 显示更多详细信息
                        amazon_info = first_item.get('amazon_quantity_info', {})
                        scm_info = first_item.get('scm_quantity_info', {})
                        sales_info = first_item.get('sales_info', {})
                        
                        print(f"      FBA可售: {amazon_info.get('amazon_quantity_valid', 0)}")
                        print(f"      本地库存: {scm_info.get('sc_quantity_local_valid', 0)}")
                        print(f"      30天销量: {sales_info.get('sales_total_30', 0)}")
                        print(f"      日均销量: {sales_info.get('sales_avg_30', 0)}")
                    else:
                        print(f"   ⚠️  返回空数据列表")
                        results[test_case['name']] = None
                else:
                    print(f"   ❌ 业务错误: {response_message}")
                    results[test_case['name']] = None
            else:
                error = result.get('error', 'Unknown error')
                print(f"   ❌ HTTP错误: {error}")
                results[test_case['name']] = None
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            results[test_case['name']] = None
        
        print(f"   " + "-" * 50)
    
    # 对比不同模式的结果
    print(f"\n📊 模式对比分析:")
    print("=" * 60)
    
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if len(valid_results) > 1:
        print(f"✅ 发现不同模式返回不同的补货建议数量!")
        
        # 找到第一个有效结果作为基准
        base_name, base_data = next(iter(valid_results.items()))
        print(f"\n📋 以 '{base_name}' 为基准进行对比:")
        print(f"   MSKU: {base_data['msku']}")
        print(f"   采购建议: {base_data['purchase']}")
        print(f"   本地发FBA: {base_data['local_fba']}")
        print(f"   海外发FBA: {base_data['oversea_fba']}")
        
        # 对比其他模式
        for name, data in valid_results.items():
            if name != base_name and data['msku'] == base_data['msku']:
                purchase_diff = data['purchase'] - base_data['purchase']
                local_fba_diff = data['local_fba'] - base_data['local_fba']
                oversea_fba_diff = data['oversea_fba'] - base_data['oversea_fba']
                
                print(f"\n🔍 '{name}' 与基准的差异:")
                print(f"   采购建议差异: {purchase_diff:+d}")
                print(f"   本地发FBA差异: {local_fba_diff:+d}")
                print(f"   海外发FBA差异: {oversea_fba_diff:+d}")
                
                if purchase_diff != 0 or local_fba_diff != 0 or oversea_fba_diff != 0:
                    print(f"   🎯 发现数量差异! 不同模式确实返回不同数据")
                else:
                    print(f"   ✅ 数量一致")
    else:
        print(f"⚠️  只有一个或没有有效结果，无法进行对比")
    
    print(f"\n💡 建议:")
    if any(results.values()):
        print(f"   1. 使用 '普通模式 (mode=0)' 作为默认模式")
        print(f"   2. 如果需要海外仓中转，使用 '海外仓中转模式 (mode=1)'")
        print(f"   3. 对比领星ERP界面，确认哪个模式的数据更准确")
        print(f"   4. 考虑在应用中提供模式切换选项")
    else:
        print(f"   1. 检查补货规则配置")
        print(f"   2. 确认是否有需要补货的产品")
        print(f"   3. 联系领星技术支持确认API使用方法")

if __name__ == "__main__":
    test_getsummarylist_modes()
