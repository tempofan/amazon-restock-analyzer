#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟数据生成器
当API不可用时提供模拟数据用于演示
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

class MockDataGenerator:
    """
    模拟数据生成器类
    """
    
    def __init__(self):
        """初始化模拟数据生成器"""
        self.product_names = [
            "无线蓝牙耳机 TWS降噪耳机",
            "智能手机保护壳 透明防摔壳",
            "USB-C数据线 快充线材",
            "便携式充电宝 20000mAh",
            "蓝牙音箱 防水音响",
            "智能手表表带 硅胶表带",
            "手机支架 桌面支架",
            "车载充电器 双USB接口",
            "无线充电器 快充无线充",
            "笔记本电脑包 防震包"
        ]
        
        self.shop_names = [
            "亚马逊美国店铺",
            "亚马逊欧洲店铺", 
            "亚马逊日本店铺",
            "亚马逊加拿大店铺"
        ]
    
    def generate_asin(self) -> str:
        """生成模拟ASIN"""
        return 'B' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
    
    def generate_msku(self) -> str:
        """生成模拟MSKU"""
        return 'MSKU-' + ''.join([chr(random.randint(65, 90)) for _ in range(3)]) + str(random.randint(100, 999))
    
    def generate_replenishment_item(self) -> Dict[str, Any]:
        """生成单个补货建议项目"""
        # 基础信息
        asin = self.generate_asin()
        msku = self.generate_msku()
        product_name = random.choice(self.product_names)
        shop_name = random.choice(self.shop_names)
        
        # 库存数据
        current_stock = random.randint(0, 500)
        reserved_stock = random.randint(0, min(50, current_stock))
        available_stock = current_stock - reserved_stock
        
        # 销售数据
        daily_sales_avg = round(random.uniform(1, 20), 1)
        
        # 财务数据
        unit_cost = round(random.uniform(5, 100), 2)
        selling_price = round(unit_cost * random.uniform(1.5, 3.0), 2)
        
        # 补货计算
        days_of_stock = round(available_stock / daily_sales_avg if daily_sales_avg > 0 else 999, 1)
        
        # 计算建议补货量
        if days_of_stock < 30:
            suggested_quantity = random.randint(50, 200)
        else:
            suggested_quantity = 0
        
        # 紧急程度评分
        if days_of_stock <= 7:
            urgency_score = random.randint(80, 100)
            urgency_level = 'urgent'
            stock_status = 'critical'
        elif days_of_stock <= 14:
            urgency_score = random.randint(60, 79)
            urgency_level = 'high'
            stock_status = 'low'
        elif days_of_stock <= 30:
            urgency_score = random.randint(40, 59)
            urgency_level = 'medium'
            stock_status = 'low'
        else:
            urgency_score = random.randint(0, 39)
            urgency_level = 'low'
            stock_status = 'normal'
        
        # 投资和利润计算
        suggested_investment = suggested_quantity * unit_cost
        expected_revenue = suggested_quantity * selling_price
        expected_profit = expected_revenue - suggested_investment
        
        # 生成建议文本
        if urgency_level == 'urgent':
            recommendation = f"🚨 紧急补货！当前库存仅够 {days_of_stock} 天，建议立即补货 {suggested_quantity} 件"
        elif urgency_level == 'high':
            recommendation = f"⚠️ 需要补货，当前库存 {days_of_stock} 天，建议补货 {suggested_quantity} 件"
        else:
            recommendation = f"✅ 库存充足，当前库存 {days_of_stock} 天"
        
        return {
            'id': f"item_{random.randint(10000, 99999)}",
            'asin': asin,
            'msku': msku,
            'sku': f"SKU-{random.randint(1000, 9999)}",
            'product_name': product_name,
            'shop_id': f"shop_{random.randint(1, 4)}",
            'shop_name': shop_name,
            'image_url': f"https://via.placeholder.com/150x150?text={asin}",
            'current_stock': current_stock,
            'available_stock': available_stock,
            'reserved_stock': reserved_stock,
            'daily_sales_avg': daily_sales_avg,
            'weekly_sales_avg': daily_sales_avg * 7,
            'monthly_sales_avg': daily_sales_avg * 30,
            'suggested_quantity': suggested_quantity,
            'min_stock_days': 30,
            'max_stock_days': 90,
            'unit_cost': unit_cost,
            'selling_price': selling_price,
            'suggested_investment': suggested_investment,
            'expected_revenue': expected_revenue,
            'expected_profit': expected_profit,
            'days_of_stock': days_of_stock,
            'urgency_score': urgency_score,
            'urgency_level': urgency_level,
            'stock_status': stock_status,
            'recommendation': recommendation,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }
    
    def generate_replenishment_list(self, count: int = 50) -> Dict[str, Any]:
        """生成补货建议列表"""
        items = [self.generate_replenishment_item() for _ in range(count)]
        
        # 计算汇总信息
        total_items = len(items)
        urgent_count = len([item for item in items if item['urgency_level'] == 'urgent'])
        
        total_investment = sum(item['suggested_investment'] for item in items)
        total_profit = sum(item['expected_profit'] for item in items)
        
        # 状态分布
        status_distribution = {}
        urgency_distribution = {}
        
        for item in items:
            status = item['stock_status']
            urgency = item['urgency_level']
            
            status_distribution[status] = status_distribution.get(status, 0) + 1
            urgency_distribution[urgency] = urgency_distribution.get(urgency, 0) + 1
        
        return {
            'items': items,
            'summary': {
                'total_items': total_items,
                'status_distribution': status_distribution,
                'urgency_distribution': urgency_distribution,
                'financial_summary': {
                    'total_investment': round(total_investment, 2),
                    'total_profit': round(total_profit, 2),
                    'average_roi': round((total_profit / total_investment * 100) if total_investment > 0 else 0, 2)
                }
            },
            'processed_at': datetime.now().isoformat(),
            'success': True
        }
    
    def generate_shop_list(self) -> List[Dict[str, Any]]:
        """生成店铺列表"""
        return [
            {'id': f'shop_{i+1}', 'name': shop_name}
            for i, shop_name in enumerate(self.shop_names)
        ]
    
    def generate_analytics_data(self) -> Dict[str, Any]:
        """生成分析数据"""
        return {
            'overview': {
                'total_products': 100,
                'urgent_replenishment': 8,
                'high_priority_items': 15,
                'total_investment_needed': 25000,
                'expected_profit': 8500,
                'average_roi': 34.0
            },
            'trends': {
                'stock_trend': 'stable',
                'sales_trend': 'growing',
                'profit_trend': 'positive'
            },
            'categories': {
                'by_shop': {
                    shop_name: {
                        'count': random.randint(10, 30),
                        'investment': random.randint(5000, 20000),
                        'profit': random.randint(1000, 8000)
                    }
                    for shop_name in self.shop_names
                }
            },
            'recommendations': {
                'top_urgent_items': [
                    {
                        'asin': self.generate_asin(),
                        'product_name': random.choice(self.product_names),
                        'urgency_score': random.randint(80, 100),
                        'days_of_stock': random.randint(1, 7),
                        'suggested_quantity': random.randint(50, 200)
                    }
                    for _ in range(10)
                ]
            },
            'generated_at': datetime.now().isoformat(),
            'success': True
        }
