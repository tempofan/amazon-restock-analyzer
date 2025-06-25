#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用真实数据测试FBA建议API
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.lingxing_api_new import LingxingAPINew

def test_real_fba_api():
    """
    使用真实数据测试FBA建议API
    """
    print("🎯 使用真实数据测试FBA建议API")
    print("=" * 50)
    
    # 创建API客户端
    api = LingxingAPINew()
    
    # 真实测试数据（从补货建议列表中获取）
    test_cases = [
        {
            "name": "真实MSKU测试 - 普通模式",
            "shop_id": "6194",
            "msku": "R01500302JBK",
            "asin": "",
            "mode": 0
        },
        {
            "name": "真实ASIN测试 - 普通模式", 
            "shop_id": "6194",
            "msku": "",
            "asin": "B071L1HK76",
            "mode": 0
        },
        {
            "name": "真实MSKU测试 - 海外仓中转模式",
            "shop_id": "6194",
            "msku": "R01500302JBK",
            "asin": "",
            "mode": 1
        },
        {
            "name": "另一个真实MSKU测试",
            "shop_id": "6197",
            "msku": "3DB-SJ02-2-0001584",
            "asin": "",
            "mode": 0
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            # 调用FBA建议API
            result = api.get_fba_suggestion_info(
                shop_id=test_case['shop_id'],
                msku=test_case['msku'],
                asin=test_case['asin'],
                mode=test_case['mode']
            )
            
            print(f"📤 请求参数:")
            print(f"   店铺ID: {test_case['shop_id']}")
            print(f"   MSKU: {test_case['msku'] or '未提供'}")
            print(f"   ASIN: {test_case['asin'] or '未提供'}")
            print(f"   模式: {test_case['mode']} ({'普通模式' if test_case['mode'] == 0 else '海外仓中转模式'})")
            
            if result.get('success'):
                print("✅ API调用成功!")
                
                data = result.get('data', {})
                
                # 提取关键字段
                local_to_fba = data.get('quantity_sug_local_to_fba', 0)
                purchase = data.get('quantity_sug_purchase', 0)
                oversea_to_fba = data.get('quantity_sug_oversea_to_fba', 0)
                local_to_oversea = data.get('quantity_sug_local_to_oversea', 0)
                
                print(f"🎯 核心建议数据:")
                print(f"   建议本地发FBA量（普通模式）: {local_to_fba}")
                print(f"   建议采购量: {purchase}")
                print(f"   建议海外仓发FBA量: {oversea_to_fba}")
                print(f"   建议本地发海外仓量: {local_to_oversea}")
                
                # 销售数据
                sales_3 = data.get('sales_avg_3', 0)
                sales_7 = data.get('sales_avg_7', 0)
                sales_14 = data.get('sales_avg_14', 0)
                sales_30 = data.get('sales_avg_30', 0)
                
                print(f"📈 销售数据:")
                print(f"   3天日均: {sales_3}")
                print(f"   7天日均: {sales_7}")
                print(f"   14天日均: {sales_14}")
                print(f"   30天日均: {sales_30}")
                
                # 建议日期
                sug_date_purchase = data.get('sug_date_purchase', '')
                sug_date_local = data.get('sug_date_send_local', '')
                sug_date_oversea = data.get('sug_date_send_oversea', '')
                
                print(f"📅 建议日期:")
                print(f"   建议采购日: {sug_date_purchase or '未设置'}")
                print(f"   建议本地发货日: {sug_date_local or '未设置'}")
                print(f"   建议海外仓发货日: {sug_date_oversea or '未设置'}")
                
                # 检查是否有建议
                if local_to_fba > 0:
                    print(f"🎉 成功获取到建议本地发FBA量: {local_to_fba} 件")
                elif purchase > 0:
                    print(f"💡 建议采购: {purchase} 件")
                elif oversea_to_fba > 0:
                    print(f"🚢 建议海外仓发FBA: {oversea_to_fba} 件")
                else:
                    print("ℹ️ 当前没有补货建议")
                    
            else:
                error = result.get('error', '未知错误')
                print(f"❌ API调用失败: {error}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 真实数据FBA建议API测试完成")

if __name__ == "__main__":
    test_real_fba_api()
