# -*- coding: utf-8 -*-
"""
领星ERP补货数据获取主程序
"""

import os
import sys
import argparse
from datetime import datetime
from typing import List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.client import APIClient, APIException
from business.restock_analyzer import RestockAnalyzer
from utils.logger import api_logger
from config.config import APIConfig

def get_data_type_choice() -> int:
    """
    获取用户选择的数据类型
    
    Returns:
        int: 数据类型（1: ASIN, 2: MSKU）
    """
    print("\n请选择查询维度:")
    print("1. ASIN维度")
    print("2. MSKU维度")
    
    while True:
        try:
            choice = input("请输入选择 (1-2): ").strip()
            if choice == '1':
                return 1
            elif choice == '2':
                return 2
            else:
                print("❌ 无效选择，请输入 1 或 2")
        except KeyboardInterrupt:
            print("\n👋 用户取消操作")
            exit(0)
        except Exception as e:
            print(f"❌ 输入错误: {e}，请重新输入")
            continue

def get_mode_choice() -> int:
    """
    获取用户选择的补货模式（已设置默认值）
    
    Returns:
        int: 补货模式（0: 普通模式, 1: 海外仓中转模式）
    """
    # 默认使用普通模式
    return 0

def get_max_pages_choice() -> Optional[int]:
    """
    获取用户选择的最大页数（已设置默认值）
    
    Returns:
        Optional[int]: 最大页数限制
    """
    # 默认不限制页数
    return None

def get_max_workers_choice() -> int:
    """
    获取用户选择的最大并发数（已设置默认值）
    
    Returns:
        int: 最大并发数（1-5）
    """
    # 默认使用最大并发数5
    return 5

def get_export_format_choice() -> str:
    """
    获取用户选择的导出格式（已设置默认值）
    
    Returns:
        str: 导出格式类型（'both': 两种格式都有, 'standard': 标准格式, 'detail': 明细格式）
    """
    # 默认使用两种格式都有的导出方式
    return 'both'

def get_msku_enhancement_choice() -> bool:
    """
    获取用户是否启用MSKU详细信息增强（已设置默认值）
    
    Returns:
        bool: True表示启用MSKU详细信息增强，False表示不启用
    """
    # 默认启用MSKU详细信息增强
    return True

def test_connection():
    """
    测试API连接
    """
    print("正在测试API连接...")
    
    try:
        client = APIClient()
        result = client.test_connection()
        
        if result.get('success', False):
            print("✓ API连接测试成功")
            print(f"  - Token状态: {result.get('token_status', 'unknown')}")
            print(f"  - 店铺数量: {result.get('seller_count', 0)}")
            return True
        else:
            print(f"✗ API连接测试失败: {result.get('message', '未知错误')}")
            return False
            
    except APIException as e:
        print(f"✗ API连接测试失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 连接测试异常: {e}")
        return False

def get_sellers_info():
    """
    获取店铺信息
    """
    print("正在获取店铺信息...")
    
    try:
        analyzer = RestockAnalyzer()
        sellers = analyzer.get_sellers()
        
        print(f"\n找到 {len(sellers)} 个店铺:")
        print("-" * 80)
        print(f"{'店铺ID':<15} {'店铺名称':<30} {'地区':<10} {'状态':<10}")
        print("-" * 80)
        
        for seller in sellers:
            sid = seller.get('sid', '')
            name = seller.get('name', '')[:28]  # 限制长度
            region = seller.get('region', '')
            status = '正常' if seller.get('status') == 1 else '异常'
            
            print(f"{sid:<15} {name:<30} {region:<10} {status:<10}")
        
        return sellers
        
    except Exception as e:
        print(f"✗ 获取店铺信息失败: {e}")
        return []

def get_restock_data(seller_ids: List[str] = None,
                  data_type: int = 1,
                  asin_list: List[str] = None,
                  msku_list: List[str] = None,
                  mode: int = 0,
                  max_pages: int = None,
                  max_workers: int = 3,
                  export_excel: bool = True,
                  export_json: bool = False,
                  export_format: str = 'both',
                  enhance_with_msku_details: bool = False):
    """
    获取补货数据
    
    Args:
        seller_ids: 店铺ID列表
        data_type: 查询维度（1: asin, 2: msku）
        asin_list: ASIN列表
        msku_list: MSKU列表
        mode: 补货建议模式（0: 普通模式, 1: 海外仓中转模式）
        max_pages: 最大页数
        max_workers: 并发线程数
        export_excel: 是否导出Excel
        export_json: 是否导出JSON
        export_format: 导出格式（'both': 两种格式都有, 'standard': 标准格式, 'detail': 明细格式）
        enhance_with_msku_details: 是否使用MSKU详细信息接口增强数据
    """
    print("正在获取补货数据...")
    
    try:
        analyzer = RestockAnalyzer()
        
        # 获取补货数据
        restock_items = analyzer.get_restock_data(
            seller_ids=seller_ids,
            data_type=data_type,
            asin_list=asin_list,
            msku_list=msku_list,
            mode=mode,
            max_pages=max_pages,
            max_workers=max_workers
        )
        
        if not restock_items:
            print("未找到补货数据")
            return
        
        print(f"\n成功获取 {len(restock_items)} 条补货数据")
        
        # 如果启用了MSKU详细信息增强
        if enhance_with_msku_details:
            print("正在使用MSKU详细信息接口增强数据...")
            try:
                restock_items = analyzer.enhance_restock_items_with_details(restock_items)
                print("✓ MSKU详细信息增强完成")
            except Exception as e:
                print(f"⚠ MSKU详细信息增强失败: {e}")
                api_logger.log_error(e, "MSKU详细信息增强失败")
                # 继续使用原始数据
        
        # 生成汇总报告
        summary = analyzer.generate_summary_report(restock_items)
        print("\n=== 补货数据汇总 ===")
        print(f"总计商品: {summary['total_items']}")
        print(f"紧急补货: {summary['urgent_items']}")
        print(f"断货商品: {summary['out_of_stock_items']}")
        print(f"高销量商品: {summary['high_sales_items']}")
        print(f"建议采购总量: {summary['total_suggested_purchase']}")
        print(f"平均可售天数: {summary['avg_available_days']}")
        
        # 分析紧急补货
        urgent_items = analyzer.analyze_urgent_restock(restock_items)
        if urgent_items:
            print(f"\n=== 紧急补货商品 (前10个) ===")
            print("-" * 100)
            print(f"{'ASIN':<12} {'店铺ID':<10} {'可售天数':<8} {'断货日期':<12} {'建议采购':<8} {'日均销量':<8}")
            print("-" * 100)
            
            for item in urgent_items[:10]:
                asin = item.asin[:10]
                sid = item.sid
                days = item.available_sale_days if item.available_sale_days > 0 else '断货'
                out_date = item.out_stock_date[:10] if item.out_stock_date else '-'
                purchase = item.suggested_purchase
                sales = round(item.sales_avg_30, 1)
                
                print(f"{asin:<12} {sid:<10} {str(days):<8} {out_date:<12} {purchase:<8} {sales:<8}")
        
        # 分析高销量商品
        high_sales_items = analyzer.analyze_high_sales_items(restock_items)
        if high_sales_items:
            print(f"\n=== 高销量商品 (前10个) ===")
            print("-" * 100)
            print(f"{'ASIN':<12} {'店铺ID':<10} {'30天日均':<8} {'FBA可售':<8} {'建议采购':<8} {'可售天数':<8}")
            print("-" * 100)
            
            for item in high_sales_items[:10]:
                asin = item.asin[:10]
                sid = item.sid
                sales = round(item.sales_avg_30, 1)
                fba = item.fba_available
                purchase = item.suggested_purchase
                days = item.available_sale_days if item.available_sale_days > 0 else '断货'
                
                print(f"{asin:<12} {sid:<10} {sales:<8} {fba:<8} {purchase:<8} {str(days):<8}")
        
        # 导出数据
        exported_files = []
        
        if export_excel:
            try:
                if export_format == 'both':
                    excel_file = analyzer.export_to_excel_both(restock_items)
                    print(f"\n✓ Excel文件已导出（包含标准格式和明细拆分格式）: {excel_file}")
                elif export_format == 'detail':
                    excel_file = analyzer.export_to_excel_detail(restock_items)
                    print(f"\n✓ Excel文件已导出（明细拆分格式）: {excel_file}")
                else:  # 'standard'
                    excel_file = analyzer.export_to_excel(restock_items)
                    print(f"\n✓ Excel文件已导出（标准格式）: {excel_file}")
                exported_files.append(excel_file)
            except Exception as e:
                print(f"✗ Excel导出失败: {e}")
        
        if export_json:
            try:
                json_file = analyzer.save_to_json(restock_items)
                exported_files.append(json_file)
                print(f"✓ JSON文件已保存: {json_file}")
            except Exception as e:
                print(f"✗ JSON保存失败: {e}")
        
        if exported_files:
            print(f"\n数据已导出到以下文件:")
            for file in exported_files:
                print(f"  - {file}")
        
        return restock_items
        
    except Exception as e:
        print(f"✗ 获取补货数据失败: {e}")
        api_logger.log_error(e, "获取补货数据失败")
        return None

def interactive_mode():
    """
    交互式模式
    """
    print("\n=== 领星ERP补货数据获取工具 ===")
    print("1. 测试API连接")
    print("2. 获取店铺信息")
    print("3. 获取所有店铺补货数据")
    print("4. 获取指定店铺补货数据")
    print("5. 获取指定ASIN补货数据")
    print("6. 获取指定MSKU补货数据")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请选择操作 (0-6): ").strip()
            
            if choice == '0':
                print("再见！")
                break
            elif choice == '1':
                test_connection()
            elif choice == '2':
                get_sellers_info()
            elif choice == '3':
                print("\n=== 获取所有店铺的补货数据 ===")
                print("📋 使用默认设置:")
                print("  - 补货模式: 普通模式")
                print("  - 最大页数: 不限制")
                print("  - 并发线程数: 5（最大）")
                print("  - 导出格式: 标准格式和明细拆分格式（两个工作表）")
                print("  - MSKU详细信息增强: 启用")
                data_type = get_data_type_choice()
                mode = get_mode_choice()
                max_pages = get_max_pages_choice()
                max_workers = get_max_workers_choice()
                export_format = get_export_format_choice()
                enhance_with_msku_details = get_msku_enhancement_choice()
                get_restock_data(data_type=data_type, mode=mode, max_pages=max_pages, max_workers=max_workers, export_format=export_format, enhance_with_msku_details=enhance_with_msku_details)
            elif choice == '4':
                # 先获取店铺列表
                sellers = get_sellers_info()
                if sellers:
                    print("\n请输入要查询的店铺ID（多个用逗号分隔）:")
                    sid_input = input().strip()
                    if sid_input:
                        seller_ids = [sid.strip() for sid in sid_input.split(',')]
                        print("📋 使用默认设置:")
                        print("  - 补货模式: 普通模式")
                        print("  - 最大页数: 不限制")
                        print("  - 并发线程数: 5（最大）")
                        print("  - 导出格式: 标准格式和明细拆分格式（两个工作表）")
                        print("  - MSKU详细信息增强: 启用")
                        data_type = get_data_type_choice()
                        mode = get_mode_choice()
                        max_pages = get_max_pages_choice()
                        max_workers = get_max_workers_choice()
                        export_format = get_export_format_choice()
                        enhance_with_msku_details = get_msku_enhancement_choice()
                        get_restock_data(seller_ids=seller_ids, data_type=data_type, mode=mode, max_pages=max_pages, max_workers=max_workers, export_format=export_format, enhance_with_msku_details=enhance_with_msku_details)
            elif choice == '5':
                print("\n=== 获取指定ASIN补货数据 ===")
                print("请输入要查询的ASIN（多个用逗号分隔）:")
                asin_input = input().strip()
                if asin_input:
                    asin_list = [asin.strip().upper() for asin in asin_input.split(',')]
                    print("📋 使用默认设置:")
                    print("  - 补货模式: 普通模式")
                    print("  - 最大页数: 不限制")
                    print("  - 并发线程数: 5（最大）")
                    print("  - 导出格式: 标准格式和明细拆分格式（两个工作表）")
                    print("  - MSKU详细信息增强: 启用")
                    mode = get_mode_choice()
                    max_pages = get_max_pages_choice()
                    max_workers = get_max_workers_choice()
                    export_format = get_export_format_choice()
                    enhance_with_msku_details = get_msku_enhancement_choice()
                    get_restock_data(asin_list=asin_list, data_type=1, mode=mode, max_pages=max_pages, max_workers=max_workers, export_format=export_format, enhance_with_msku_details=enhance_with_msku_details)
            elif choice == '6':
                print("\n=== 获取指定MSKU补货数据 ===")
                print("请输入要查询的MSKU（多个用逗号分隔）:")
                msku_input = input().strip()
                if msku_input:
                    msku_list = [msku.strip().upper() for msku in msku_input.split(',')]
                    print("📋 使用默认设置:")
                    print("  - 补货模式: 普通模式")
                    print("  - 最大页数: 不限制")
                    print("  - 并发线程数: 5（最大）")
                    print("  - 导出格式: 标准格式和明细拆分格式（两个工作表）")
                    print("  - MSKU详细信息增强: 启用")
                    mode = get_mode_choice()
                    max_pages = get_max_pages_choice()
                    max_workers = get_max_workers_choice()
                    export_format = get_export_format_choice()
                    enhance_with_msku_details = get_msku_enhancement_choice()
                    get_restock_data(msku_list=msku_list, data_type=2, mode=mode, max_pages=max_pages, max_workers=max_workers, export_format=export_format, enhance_with_msku_details=enhance_with_msku_details)
            else:
                print("无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            break
        except Exception as e:
            print(f"操作失败: {e}")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='领星ERP补货数据获取工具')
    parser.add_argument('--test', action='store_true', help='测试API连接')
    parser.add_argument('--sellers', action='store_true', help='获取店铺信息')
    parser.add_argument('--restock', action='store_true', help='获取补货数据')
    parser.add_argument('--sid', type=str, help='指定店铺ID（多个用逗号分隔）')
    parser.add_argument('--asin', type=str, help='指定ASIN（多个用逗号分隔）')
    parser.add_argument('--msku', type=str, help='指定MSKU（多个用逗号分隔）')
    parser.add_argument('--data-type', type=int, choices=[1, 2], default=1, 
                       help='查询维度（1: asin, 2: msku）')
    parser.add_argument('--mode', type=int, choices=[0, 1], default=0,
                       help='补货建议模式（0: 普通模式, 1: 海外仓中转模式）')
    parser.add_argument('--max-pages', type=int, help='最大页数限制')
    parser.add_argument('--max-workers', type=int, default=3, help='并发线程数（默认3，范围1-5）')
    parser.add_argument('--no-excel', action='store_true', help='不导出Excel文件')
    parser.add_argument('--json', action='store_true', help='导出JSON文件')
    parser.add_argument('--export-format', type=str, choices=['standard', 'detail', 'both'], default='both',
                       help='导出格式（standard: 标准格式, detail: 明细拆分格式, both: 两种格式都有）')
    parser.add_argument('--enhance-msku-details', action='store_true', help='使用MSKU详细信息接口增强数据（会增加API调用次数）')
    parser.add_argument('--interactive', action='store_true', help='交互式模式')
    
    args = parser.parse_args()
    
    # 确保必要的目录存在
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    try:
        if args.interactive:
            interactive_mode()
        elif args.test:
            test_connection()
        elif args.sellers:
            get_sellers_info()
        elif args.restock:
            # 解析参数
            seller_ids = None
            if args.sid:
                seller_ids = [sid.strip() for sid in args.sid.split(',')]
            
            asin_list = None
            if args.asin:
                asin_list = [asin.strip().upper() for asin in args.asin.split(',')]
            
            msku_list = None
            if args.msku:
                msku_list = [msku.strip().upper() for msku in args.msku.split(',')]
            
            # 获取补货数据
            get_restock_data(
                seller_ids=seller_ids,
                data_type=args.data_type,
                asin_list=asin_list,
                msku_list=msku_list,
                mode=args.mode,
                max_pages=args.max_pages,
                max_workers=args.max_workers,
                export_excel=not args.no_excel,
                export_json=args.json,
                export_format=args.export_format,
                enhance_with_msku_details=args.enhance_msku_details
            )
        else:
            # 默认进入交互式模式
            interactive_mode()
            
    except KeyboardInterrupt:
        print("\n程序已中断")
    except Exception as e:
        print(f"程序执行失败: {e}")
        api_logger.log_error(e, "程序执行失败")
        sys.exit(1)

if __name__ == '__main__':
    main()