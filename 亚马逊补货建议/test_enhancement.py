#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据增强功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from api.lingxing_api_new import LingxingAPINew
from config import Config

def test_enhancement():
    """
    测试数据增强功能
    """
    print("🔍 开始测试数据增强功能...")
    
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
    print("🏪 获取店铺列表...")
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
    
    # 检查配置
    print(f"⚙️ 数据增强配置: {Config.DATA_PROCESSING_CONFIG.get('enable_fba_enhancement', False)}")
    
    # 获取补货建议数据（不增强）
    print("📊 获取原始补货建议数据...")
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
    
    # 获取补货建议数据（增强）
    print("🚀 获取增强补货建议数据...")
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
    
    # 对比数据
    print("\n📊 数据对比分析:")
    print("=" * 80)
    
    for i, (original_item, enhanced_item) in enumerate(zip(original_items, enhanced_items)):
        print(f"\n🔍 项目 {i+1}:")
        
        # 基础信息
        basic_info = original_item.get('basic_info', {})
        msku_list = basic_info.get('msku_fnsku_list', [])
        msku = msku_list[0].get('msku', '') if msku_list else ''
        asin = basic_info.get('asin', '')
        
        print(f"   MSKU: {msku}")
        print(f"   ASIN: {asin}")
        
        # 原始建议数量
        original_suggest = original_item.get('suggest_info', {})
        original_purchase = original_suggest.get('quantity_sug_purchase', 0)
        original_local_fba = original_suggest.get('quantity_sug_local_to_fba', 0)
        original_oversea_fba = original_suggest.get('quantity_sug_oversea_to_fba', 0)
        
        print(f"   原始数据:")
        print(f"     采购建议: {original_purchase}")
        print(f"     本地发FBA: {original_local_fba}")
        print(f"     海外发FBA: {original_oversea_fba}")
        
        # 增强建议数量
        enhanced_suggest = enhanced_item.get('suggest_info', {})
        enhanced_purchase = enhanced_suggest.get('quantity_sug_purchase', 0)
        enhanced_local_fba = enhanced_suggest.get('quantity_sug_local_to_fba', 0)
        enhanced_oversea_fba = enhanced_suggest.get('quantity_sug_oversea_to_fba', 0)
        enhanced_flag = enhanced_item.get('_enhanced_with_fba', False)
        
        print(f"   增强数据:")
        print(f"     采购建议: {enhanced_purchase}")
        print(f"     本地发FBA: {enhanced_local_fba}")
        print(f"     海外发FBA: {enhanced_oversea_fba}")
        print(f"     增强标记: {enhanced_flag}")
        
        # 差异分析
        purchase_diff = enhanced_purchase - original_purchase
        local_fba_diff = enhanced_local_fba - original_local_fba
        oversea_fba_diff = enhanced_oversea_fba - original_oversea_fba
        
        if purchase_diff != 0 or local_fba_diff != 0 or oversea_fba_diff != 0:
            print(f"   🔄 数量差异:")
            if purchase_diff != 0:
                print(f"     采购建议差异: {purchase_diff:+d}")
            if local_fba_diff != 0:
                print(f"     本地发FBA差异: {local_fba_diff:+d}")
            if oversea_fba_diff != 0:
                print(f"     海外发FBA差异: {oversea_fba_diff:+d}")
        else:
            print(f"   ✅ 数量无差异")
    
    print("\n" + "=" * 80)
    print("🎯 测试完成!")

if __name__ == "__main__":
    test_enhancement()
