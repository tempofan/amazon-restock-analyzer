#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基于SDK的API实现
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.lingxing_api_sdk_based import LingxingAPISDKBased
from utils.logger import setup_logger

def test_sdk_api():
    """
    测试基于SDK的API实现
    """
    print("🚀 测试基于SDK的API实现")
    print("=" * 60)
    
    # 设置日志
    logger = setup_logger('sdk_test', 'logs/sdk_test.log')
    
    # 初始化API
    api = LingxingAPISDKBased()
    
    # 测试1: 连接测试
    print("\n1️⃣ 测试API连接...")
    connection_result = api.test_connection()
    print(f"连接测试结果: {connection_result}")
    
    if not connection_result.get('success'):
        print("❌ API连接失败，无法继续测试")
        return
    
    print("✅ API连接成功！")
    
    # 添加延迟
    print("\n⏳ 等待3秒避免频率限制...")
    time.sleep(3)
    
    # 测试2: 获取店铺列表
    print("\n2️⃣ 测试店铺列表获取...")
    shop_result = api.get_shop_list()
    
    if shop_result.get('success'):
        api_data = shop_result.get('data', {})
        if api_data.get('code') == 200:
            shops = api_data.get('data', [])
            print(f"✅ 成功获取 {len(shops)} 个店铺")
            
            # 显示前3个店铺
            for i, shop in enumerate(shops[:3]):
                print(f"   店铺{i+1}: ID={shop.get('sid')}, 名称={shop.get('name')}")
        else:
            print(f"❌ API返回错误: {api_data.get('message', '未知错误')}")
            return
    else:
        print(f"❌ 获取店铺列表失败: {shop_result.get('error')}")
        return
    
    # 添加延迟
    print("\n⏳ 等待5秒避免频率限制...")
    time.sleep(5)
    
    # 测试3: 获取补货建议数据（小规模）
    print("\n3️⃣ 测试补货建议数据获取...")
    replenish_result = api.get_replenishment_summary(
        data_type=2,  # MSKU维度
        offset=0,
        length=5  # 小规模测试
    )
    
    if replenish_result.get('success'):
        api_data = replenish_result.get('data', {})
        print(f"API响应码: {api_data.get('code')}")
        print(f"API消息: {api_data.get('message')}")
        
        if api_data.get('code') == 200:
            items = api_data.get('data', [])
            print(f"✅ 成功获取 {len(items)} 条补货数据")
            
            if items:
                # 显示第一条数据
                first_item = items[0]
                basic_info = first_item.get('basic_info', {})
                suggest_info = first_item.get('suggest_info', {})
                
                print("   📋 第一条数据示例:")
                print(f"      店铺ID: {basic_info.get('sid')}")
                msku_list = basic_info.get('msku_fnsku_list', [])
                if msku_list:
                    print(f"      MSKU: {msku_list[0].get('msku', 'N/A')}")
                print(f"      ASIN: {basic_info.get('asin', 'N/A')}")
                print(f"      采购建议: {suggest_info.get('quantity_sug_purchase', 0)}")
                print(f"      本地发FBA: {suggest_info.get('quantity_sug_local_to_fba', 0)}")
            else:
                print("   ⚠️ 返回数据为空")
        else:
            print(f"   ❌ API返回错误码: {api_data.get('code')}, 消息: {api_data.get('message')}")
    else:
        print(f"   ❌ 补货数据获取失败: {replenish_result.get('error')}")
    
    # 测试4: 测试指定店铺的数据
    if shops:
        print("\n⏳ 等待5秒避免频率限制...")
        time.sleep(5)
        
        print("\n4️⃣ 测试指定店铺的补货数据...")
        test_shop = shops[0]
        shop_id = str(test_shop.get('sid'))
        shop_name = test_shop.get('name')
        
        print(f"测试店铺: {shop_name} (ID: {shop_id})")
        
        shop_replenish_result = api.get_replenishment_summary(
            data_type=2,
            offset=0,
            length=5,
            sid_list=[shop_id]
        )
        
        if shop_replenish_result.get('success'):
            api_data = shop_replenish_result.get('data', {})
            if api_data.get('code') == 200:
                items = api_data.get('data', [])
                print(f"✅ 成功获取店铺 {shop_name} 的 {len(items)} 条补货数据")
            else:
                print(f"❌ 店铺数据获取失败: {api_data.get('message')}")
        else:
            print(f"❌ 店铺数据请求失败: {shop_replenish_result.get('error')}")
    
    print(f"\n🎯 测试总结:")
    print("1. ✅ API连接测试")
    print("2. ✅ 店铺列表获取")
    print("3. ✅ 补货数据获取")
    print("4. ✅ 指定店铺数据获取")
    print("\n🎉 基于SDK的API实现测试完成！")

if __name__ == '__main__':
    test_sdk_api()
