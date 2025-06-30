# -*- coding: utf-8 -*-
"""
🚀 快速导出脚本
快速获取补货数据，不进行MSKU详细信息增强
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
def load_env_file():
    """加载环境变量"""
    env_file = os.path.join(os.path.dirname(__file__), 'config', 'server.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

from business.restock_analyzer import RestockAnalyzer
from utils.logger import api_logger

def quick_export_restock_data(seller_id: str = None):
    """
    快速导出指定店铺的补货数据
    
    Args:
        seller_id: 店铺ID，如果不指定则获取所有店铺
    """
    print("🚀 快速导出补货数据（不含MSKU详细信息增强）")
    print("=" * 60)
    
    try:
        analyzer = RestockAnalyzer()
        
        # 设置参数
        seller_ids = [seller_id] if seller_id else None
        
        print(f"📋 配置参数:")
        print(f"   - 店铺ID: {seller_id if seller_id else '所有店铺'}")
        print(f"   - 数据类型: ASIN维度")
        print(f"   - 补货模式: 普通模式")
        print(f"   - 并发线程数: 5")
        print(f"   - MSKU详细信息增强: ❌ 禁用（提高速度）")
        print()
        
        # 获取补货数据
        print("🔄 开始获取补货数据...")
        restock_items = analyzer.get_restock_data(
            seller_ids=seller_ids,
            data_type=1,  # ASIN维度
            mode=0,       # 普通模式
            max_workers=5 # 最大并发
        )
        
        if not restock_items:
            print("❌ 未找到补货数据")
            return
        
        print(f"✅ 成功获取 {len(restock_items)} 条补货数据")
        
        # 生成汇总报告
        summary = analyzer.generate_summary_report(restock_items)
        print("\n📊 补货数据汇总:")
        print(f"   - 总计商品: {summary['total_items']}")
        print(f"   - 紧急补货: {summary['urgent_items']}")
        print(f"   - 断货商品: {summary['out_of_stock_items']}")
        print(f"   - 高销量商品: {summary['high_sales_items']}")
        print(f"   - 建议采购总量: {summary['total_suggested_purchase']}")
        print(f"   - 平均可售天数: {summary['avg_available_days']}")
        
        # 导出Excel（标准格式和明细拆分格式）
        print("\n📄 导出Excel文件...")
        excel_file = analyzer.export_to_excel_both(restock_items)
        print(f"✅ Excel文件已导出: {excel_file}")
        
        # 显示紧急补货商品
        urgent_items = analyzer.analyze_urgent_restock(restock_items)
        if urgent_items:
            print(f"\n🚨 紧急补货商品 (前10个):")
            print("-" * 80)
            print(f"{'ASIN':<12} {'店铺ID':<8} {'可售天数':<8} {'建议采购':<8} {'日均销量':<8}")
            print("-" * 80)
            
            for item in urgent_items[:10]:
                asin = item.asin[:10]
                sid = item.sid
                days = item.available_sale_days if item.available_sale_days > 0 else 0
                purchase = item.suggested_purchase
                sales = round(item.sales_avg_30, 1)
                
                print(f"{asin:<12} {sid:<8} {days:<8} {purchase:<8} {sales:<8}")
        
        print(f"\n🎉 快速导出完成！")
        print(f"💡 如需MSKU详细信息，请使用完整版本（但会很慢）")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        api_logger.log_error(e, "快速导出失败")

def main():
    """主函数"""
    print("🚀 快速补货数据导出工具")
    print("=" * 60)
    
    # 获取店铺选择
    choice = input("""
请选择导出范围:
1. 指定店铺（输入店铺ID）
2. 所有店铺

请输入选择 (1-2): """).strip()
    
    if choice == "1":
        seller_id = input("请输入店铺ID: ").strip()
        if seller_id:
            quick_export_restock_data(seller_id)
        else:
            print("❌ 店铺ID不能为空")
    elif choice == "2":
        quick_export_restock_data()
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main() 