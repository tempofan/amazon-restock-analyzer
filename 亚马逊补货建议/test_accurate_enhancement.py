#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试精确数据增强功能
基于InfoMSKU API的准确补货建议数量获取
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew
from config import Config

def test_accurate_enhancement():
    """
    测试基于InfoMSKU API的精确数据增强功能
    """
    print("🎯 测试精确数据增强功能")
    print("=" * 80)
    print("📋 基于API文档分析:")
    print("   - InfoMSKU API: 提供精确的单个MSKU补货建议")
    print("   - GetSummaryList API: 提供概览性数据，可能不够准确")
    print("   - 解决方案: 使用InfoMSKU API增强GetSummaryList的数据")
    print("=" * 80)
    
    # 初始化API
    api = LingxingAPINew()
    
    # 测试连接
    print("📡 测试API连接...")
    connection_result = api.test_connection()
    if not connection_result.get('success'):
        print(f"❌ API连接失败: {connection_result.get('error')}")
        return
    print("✅ API连接成功")
    
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
    
    # 选择第一个店铺进行测试
    test_shop = shops[0]
    shop_id = str(test_shop.get('sid', ''))
    shop_name = test_shop.get('name', '')
    print(f"🎯 使用测试店铺: {shop_name} (ID: {shop_id})")
    
    # 启用数据增强
    print(f"\n⚙️ 启用数据增强功能...")
    Config.DATA_PROCESSING_CONFIG['enable_fba_enhancement'] = True
    
    # 获取原始数据（GetSummaryList API）
    print(f"\n📊 步骤1: 获取原始数据 (GetSummaryList API)...")
    Config.DATA_PROCESSING_CONFIG['enable_fba_enhancement'] = False
    original_result = api.get_replenishment_suggestions(
        page=1,
        page_size=3,
        shop_id=shop_id,
        data_type=2
    )
    
    if not original_result.get('success'):
        print(f"❌ 获取原始数据失败: {original_result.get('error')}")
        return
    
    original_data = original_result.get('data', {})
    original_items = original_data.get('data', []) if isinstance(original_data, dict) else original_data
    print(f"📋 原始数据项目数: {len(original_items)}")
    
    # 获取增强数据（GetSummaryList + InfoMSKU API）
    print(f"\n🚀 步骤2: 获取增强数据 (GetSummaryList + InfoMSKU API)...")
    Config.DATA_PROCESSING_CONFIG['enable_fba_enhancement'] = True
    enhanced_result = api.get_replenishment_suggestions(
        page=1,
        page_size=3,
        shop_id=shop_id,
        data_type=2
    )
    
    if not enhanced_result.get('success'):
        print(f"❌ 获取增强数据失败: {enhanced_result.get('error')}")
        return
    
    enhanced_data = enhanced_result.get('data', {})
    enhanced_items = enhanced_data.get('data', []) if isinstance(enhanced_data, dict) else enhanced_data
    print(f"📋 增强数据项目数: {len(enhanced_items)}")
    
    # 详细对比分析
    print(f"\n📊 步骤3: 详细对比分析")
    print("=" * 80)
    
    total_differences = 0
    enhanced_count = 0
    
    for i, (original_item, enhanced_item) in enumerate(zip(original_items, enhanced_items)):
        print(f"\n🔍 项目 {i+1}:")
        
        # 基础信息
        basic_info = original_item.get('basic_info', {})
        msku_list = basic_info.get('msku_fnsku_list', [])
        msku = msku_list[0].get('msku', '') if msku_list else ''
        asin = basic_info.get('asin', '')
        
        print(f"   📦 MSKU: {msku}")
        print(f"   🏷️  ASIN: {asin}")
        
        # 原始建议数量
        original_suggest = original_item.get('suggest_info', {})
        original_purchase = original_suggest.get('quantity_sug_purchase', 0)
        original_local_fba = original_suggest.get('quantity_sug_local_to_fba', 0)
        original_oversea_fba = original_suggest.get('quantity_sug_oversea_to_fba', 0)
        
        # 增强建议数量
        enhanced_suggest = enhanced_item.get('suggest_info', {})
        enhanced_purchase = enhanced_suggest.get('quantity_sug_purchase', 0)
        enhanced_local_fba = enhanced_suggest.get('quantity_sug_local_to_fba', 0)
        enhanced_oversea_fba = enhanced_suggest.get('quantity_sug_oversea_to_fba', 0)
        enhanced_flag = enhanced_item.get('_enhanced_with_fba', False)
        
        print(f"   📈 数据增强状态: {'✅ 已增强' if enhanced_flag else '❌ 未增强'}")
        
        if enhanced_flag:
            enhanced_count += 1
            
            # 显示增强信息
            enhancement_info = enhanced_item.get('_enhancement_info', {})
            differences = enhancement_info.get('differences', {})
            
            print(f"   📊 数量对比:")
            print(f"      采购建议:    {original_purchase:>6} → {enhanced_purchase:>6} (差异: {differences.get('purchase_diff', 0):+d})")
            print(f"      本地发FBA:   {original_local_fba:>6} → {enhanced_local_fba:>6} (差异: {differences.get('local_fba_diff', 0):+d})")
            print(f"      海外发FBA:   {original_oversea_fba:>6} → {enhanced_oversea_fba:>6} (差异: {differences.get('oversea_fba_diff', 0):+d})")
            
            # 统计差异
            purchase_diff = abs(differences.get('purchase_diff', 0))
            local_fba_diff = abs(differences.get('local_fba_diff', 0))
            oversea_fba_diff = abs(differences.get('oversea_fba_diff', 0))
            
            if purchase_diff > 0 or local_fba_diff > 0 or oversea_fba_diff > 0:
                total_differences += 1
                print(f"   ⚠️  发现数量差异!")
            else:
                print(f"   ✅ 数量一致")
        else:
            print(f"   📊 数量对比:")
            print(f"      采购建议:    {original_purchase:>6}")
            print(f"      本地发FBA:   {original_local_fba:>6}")
            print(f"      海外发FBA:   {original_oversea_fba:>6}")
            print(f"   ℹ️  未进行数据增强")
    
    # 总结报告
    print(f"\n" + "=" * 80)
    print(f"📋 测试总结报告:")
    print(f"   📊 总测试项目: {len(original_items)}")
    print(f"   ✅ 成功增强项目: {enhanced_count}")
    print(f"   ⚠️  发现差异项目: {total_differences}")
    print(f"   📈 增强成功率: {(enhanced_count/len(original_items)*100):.1f}%")
    
    if total_differences > 0:
        print(f"\n🎯 关键发现:")
        print(f"   ✅ 成功发现并修正了 {total_differences} 个项目的数量差异")
        print(f"   📊 这证明了GetSummaryList API的数据确实不够准确")
        print(f"   🚀 InfoMSKU API提供了更精确的补货建议数量")
        print(f"\n💡 建议:")
        print(f"   1. 启用数据增强功能以获得准确的补货建议")
        print(f"   2. 使用数据对比工具验证更多MSKU的数据")
        print(f"   3. 考虑将InfoMSKU API作为主要数据源")
    else:
        print(f"\n📊 结果分析:")
        if enhanced_count == 0:
            print(f"   ⚠️  没有项目被成功增强，可能存在API权限或配置问题")
        else:
            print(f"   ✅ 所有增强的项目数量都一致，数据质量良好")
    
    print(f"\n🎉 测试完成!")

if __name__ == "__main__":
    test_accurate_enhancement()
