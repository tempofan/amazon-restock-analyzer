# -*- coding: utf-8 -*-
"""
补货分析模块
负责补货数据的分析和处理
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from api.client import APIClient
from utils.logger import api_logger
from config.config import APIConfig

@dataclass
class RestockItem:
    """补货项目数据类"""
    hash_id: str
    asin: str
    sid: str
    data_type: int
    node_type: int
    
    # MSKU信息（用于MSKU维度）
    msku_list: List[str] = None
    fnsku_list: List[str] = None
    
    # 库存信息
    fba_available: int = 0
    fba_shipping: int = 0
    fba_shipping_plan: int = 0
    
    # 供应链信息
    local_available: int = 0
    oversea_available: int = 0
    oversea_shipping: int = 0
    purchase_plan: int = 0
    
    # 销量信息
    sales_avg_7: float = 0.0
    sales_avg_30: float = 0.0
    sales_total_7: int = 0
    sales_total_30: int = 0
    
    # 建议信息
    out_stock_flag: int = 0
    out_stock_date: str = ""
    suggested_purchase: int = 0
    suggested_local_to_fba: int = 0
    suggested_oversea_to_fba: int = 0
    available_sale_days: int = 0
    
    # 其他信息
    listing_opentime: str = ""
    sync_time: str = ""
    remark: str = ""
    star: int = 0
    
    # MSKU详细信息增强字段（来自MSKU详细信息API）
    # 详细销量统计
    sales_avg_3: float = 0.0
    sales_avg_14: float = 0.0
    sales_avg_60: float = 0.0
    sales_avg_90: float = 0.0
    sales_total_3: int = 0
    sales_total_14: int = 0
    sales_total_60: int = 0
    sales_total_90: int = 0
    
    # 详细建议信息
    quantity_sug_replenishment: int = 0
    quantity_sug_send: int = 0
    quantity_sug_local_to_oversea: int = 0
    quantity_sug_oversea_to_fba: int = 0
    
    # 建议日期
    sug_date_send_local: str = ""
    sug_date_send_oversea: str = ""
    sug_date_purchase: str = ""
    
    # 详细库存信息
    quantity_fba_valid: int = 0
    reserved_fc_transfers: int = 0
    reserved_fc_processing: int = 0
    
    # 运输方式建议列表
    suggest_sm_list: List[Dict[str, Any]] = None
    
    # 建议的发货方式列表
    shipping_method_suggestions: List[Dict[str, Any]] = None
    # MSKU详细信息原始数据（用于存储完整的API响应）
    msku_detail_raw_data: Dict[str, Any] = None
    
    @property
    def primary_msku(self) -> str:
        """获取主要的MSKU（第一个MSKU）"""
        if self.msku_list and len(self.msku_list) > 0:
            return self.msku_list[0]
        return ""
    
    @property
    def primary_fnsku(self) -> str:
        """获取主要的FNSKU（第一个FNSKU）"""
        if self.fnsku_list and len(self.fnsku_list) > 0:
            return self.fnsku_list[0]
        return ""
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'RestockItem':
        """从API数据创建RestockItem对象"""
        basic_info = data.get('basic_info', {})
        amazon_qty = data.get('amazon_quantity_info', {})
        scm_qty = data.get('scm_quantity_info', {})
        sales_info = data.get('sales_info', {})
        suggest_info = data.get('suggest_info', {})
        ext_info = data.get('ext_info', {})
        
        # 解析MSKU和FNSKU信息
        msku_fnsku_list = basic_info.get('msku_fnsku_list', [])
        msku_list = [item.get('msku', '') for item in msku_fnsku_list if item.get('msku')]
        fnsku_list = [item.get('fnsku', '') for item in msku_fnsku_list if item.get('fnsku')]
        
        # 创建RestockItem对象
        item = cls(
            hash_id=basic_info.get('hash_id', ''),
            asin=basic_info.get('asin', ''),
            sid=basic_info.get('sid', ''),
            data_type=basic_info.get('data_type', 0),
            node_type=basic_info.get('node_type', 0),
            
            msku_list=msku_list if msku_list else None,
            fnsku_list=fnsku_list if fnsku_list else None,
            
            fba_available=amazon_qty.get('amazon_quantity_valid', 0),
            fba_shipping=amazon_qty.get('amazon_quantity_shipping', 0),
            fba_shipping_plan=amazon_qty.get('amazon_quantity_shipping_plan', 0),
            
            local_available=scm_qty.get('sc_quantity_local_valid', 0),
            oversea_available=scm_qty.get('sc_quantity_oversea_valid', 0),
            oversea_shipping=scm_qty.get('sc_quantity_oversea_shipping', 0),
            purchase_plan=scm_qty.get('sc_quantity_purchase_plan', 0),
            
            sales_avg_7=sales_info.get('sales_avg_7', 0.0),
            sales_avg_30=sales_info.get('sales_avg_30', 0.0),
            sales_total_7=sales_info.get('sales_total_7', 0),
            sales_total_30=sales_info.get('sales_total_30', 0),
            
            out_stock_flag=suggest_info.get('out_stock_flag', 0),
            out_stock_date=suggest_info.get('out_stock_date', ''),
            suggested_purchase=suggest_info.get('quantity_sug_purchase', 0),
            suggested_local_to_fba=suggest_info.get('quantity_sug_local_to_fba', 0),
            suggested_oversea_to_fba=suggest_info.get('quantity_sug_oversea_to_fba', 0),
            available_sale_days=suggest_info.get('available_sale_days', 0),
            
            # 建议补货量和建议发货量
            quantity_sug_replenishment=suggest_info.get('quantity_sug_replenishment', 0),
            quantity_sug_send=suggest_info.get('quantity_sug_send', 0),
            
            listing_opentime=basic_info.get('listing_opentime_list', [''])[0],
            sync_time=basic_info.get('sync_time', ''),
            remark=ext_info.get('remark', ''),
            star=ext_info.get('star', 0)
        )
        
        # 存储item_list数据以供明细拆分使用
        item.item_list = data.get('item_list', [])
        
        return item
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        # 格式化MSKU/FNSKU列表为换行分隔的字符串
        msku_display = '\n'.join(self.msku_list) if self.msku_list else ''
        fnsku_display = '\n'.join(self.fnsku_list) if self.fnsku_list else ''
        
        # 将数据类型转换为中文显示
        data_type_display = {
            1: 'ASIN维度',
            2: 'MSKU维度'
        }.get(self.data_type, f'类型{self.data_type}')
        
        return {
            'hash_id': self.hash_id,
            'asin': self.asin,
            'sid': self.sid,
            'data_type': data_type_display,
            'node_type': self.node_type,
            'msku_fnsku': f'{msku_display}\n{fnsku_display}' if msku_display and fnsku_display else msku_display or fnsku_display,
            'msku_list': msku_display,
            'fnsku_list': fnsku_display,
            'primary_msku': self.primary_msku,
            'primary_fnsku': self.primary_fnsku,
            'fba_available': self.fba_available,
            'fba_shipping': self.fba_shipping,
            'fba_shipping_plan': self.fba_shipping_plan,
            'local_available': self.local_available,
            'oversea_available': self.oversea_available,
            'oversea_shipping': self.oversea_shipping,
            'purchase_plan': self.purchase_plan,
            'sales_avg_7': self.sales_avg_7,
            'sales_avg_30': self.sales_avg_30,
            'sales_total_7': self.sales_total_7,
            'sales_total_30': self.sales_total_30,
            'out_stock_flag': self.out_stock_flag,
            'out_stock_date': self.out_stock_date,
            'suggested_purchase': self.suggested_purchase,
            'suggested_local_to_fba': self.suggested_local_to_fba,
            'suggested_oversea_to_fba': self.suggested_oversea_to_fba,
            'available_sale_days': self.available_sale_days,
            'listing_opentime': self.listing_opentime,
            'sync_time': self.sync_time,
            'remark': self.remark,
            'star': self.star
        }
    
    def to_detail_dicts(self) -> List[Dict[str, Any]]:
        """转换为明细字典格式列表，每个MSKU/FNSKU组合生成一行"""
        detail_dicts = []
        
        # 如果有item_list数据，使用每个MSKU的独立数据
        if hasattr(self, 'item_list') and self.item_list:
            for item_data in self.item_list:
                # 从item_data创建RestockItem对象
                item = RestockItem.from_api_data(item_data)
                
                # 为每个MSKU/FNSKU组合创建详细记录
                if item.msku_list and item.fnsku_list:
                    min_length = min(len(item.msku_list), len(item.fnsku_list))
                    for i in range(min_length):
                        detail_dict = {
                            'hash_id': item.hash_id,
                            'asin': item.asin,
                            'msku': item.msku_list[i],
                            'fnsku': item.fnsku_list[i],
                            'data_type': 'MSKU维度',
                            'node_type': item.node_type,
                            'fba_available': item.fba_available,
                            'local_available': item.local_available,
                            'oversea_available': item.oversea_available,
                            'fba_shipping': item.fba_shipping,
                            'oversea_shipping': item.oversea_shipping,
                            'fba_shipping_plan': item.fba_shipping_plan,
                            'purchase_plan': item.purchase_plan,
                            'sales_avg_7': item.sales_avg_7,
                            'sales_avg_30': item.sales_avg_30,
                            'sales_total_7': item.sales_total_7,
                            'sales_total_30': item.sales_total_30,
                            'suggested_purchase': item.suggested_purchase,
                            'suggested_local_to_fba': item.suggested_local_to_fba,
                            'suggested_oversea_to_fba': item.suggested_oversea_to_fba,
                            'available_sale_days': item.available_sale_days,
                            'out_stock_flag': item.out_stock_flag,
                            'out_stock_date': item.out_stock_date,
                            'listing_opentime': item.listing_opentime,
                            'sync_time': item.sync_time,
                            'remark': item.remark,
                            'star': item.star
                        }
                        detail_dicts.append(detail_dict)
        else:
            # 回退到原有逻辑：使用汇总数据为每个MSKU创建记录
            # 将数据类型转换为中文显示
            data_type_display = {
                1: 'ASIN维度',
                2: 'MSKU维度'
            }.get(self.data_type, f'类型{self.data_type}')
            
            # 基础数据字典（包含所有MSKU详细信息字段）
            base_dict = {
                'hash_id': self.hash_id,
                'asin': self.asin,
                'sid': self.sid,
                'data_type': data_type_display,
                'node_type': self.node_type,
                # 库存信息
                'fba_available': self.fba_available,
                'quantity_fba_valid': self.quantity_fba_valid,
                'fba_shipping': self.fba_shipping,
                'fba_shipping_plan': self.fba_shipping_plan,
                'local_available': self.local_available,
                'oversea_available': self.oversea_available,
                'oversea_shipping': self.oversea_shipping,
                'purchase_plan': self.purchase_plan,
                'reserved_fc_transfers': self.reserved_fc_transfers,
                'reserved_fc_processing': self.reserved_fc_processing,
                # 销量统计（完整）
                'sales_avg_3': self.sales_avg_3,
                'sales_avg_7': self.sales_avg_7,
                'sales_avg_14': self.sales_avg_14,
                'sales_avg_30': self.sales_avg_30,
                'sales_avg_60': self.sales_avg_60,
                'sales_avg_90': self.sales_avg_90,
                'sales_total_3': self.sales_total_3,
                'sales_total_7': self.sales_total_7,
                'sales_total_14': self.sales_total_14,
                'sales_total_30': self.sales_total_30,
                'sales_total_60': self.sales_total_60,
                'sales_total_90': self.sales_total_90,
                # 建议信息（完整）
                'out_stock_flag': self.out_stock_flag,
                'out_stock_date': self.out_stock_date,
                'suggested_purchase': self.suggested_purchase,
                'quantity_sug_replenishment': self.quantity_sug_replenishment,
                'quantity_sug_send': self.quantity_sug_send,
                'suggested_local_to_fba': self.suggested_local_to_fba,
                'quantity_sug_local_to_oversea': self.quantity_sug_local_to_oversea,
                'suggested_oversea_to_fba': self.suggested_oversea_to_fba,
                'quantity_sug_oversea_to_fba': self.quantity_sug_oversea_to_fba,
                # 建议日期
                'sug_date_purchase': self.sug_date_purchase,
                'sug_date_send_local': self.sug_date_send_local,
                'sug_date_send_oversea': self.sug_date_send_oversea,
                # 其他信息
                'available_sale_days': self.available_sale_days,
                'listing_opentime': self.listing_opentime,
                'sync_time': self.sync_time,
                'remark': self.remark,
                'star': self.star
            }
            
            # 如果有MSKU和FNSKU列表，按对应关系展开
            if self.msku_list and self.fnsku_list:
                # 确保两个列表长度一致，取较短的长度
                min_length = min(len(self.msku_list), len(self.fnsku_list))
                for i in range(min_length):
                    detail_dict = base_dict.copy()
                    detail_dict['msku'] = self.msku_list[i]
                    detail_dict['fnsku'] = self.fnsku_list[i]
                    detail_dicts.append(detail_dict)
            elif self.msku_list:
                # 只有MSKU列表
                for msku in self.msku_list:
                    detail_dict = base_dict.copy()
                    detail_dict['msku'] = msku
                    detail_dict['fnsku'] = ''
                    detail_dicts.append(detail_dict)
            elif self.fnsku_list:
                # 只有FNSKU列表
                for fnsku in self.fnsku_list:
                    detail_dict = base_dict.copy()
                    detail_dict['msku'] = ''
                    detail_dict['fnsku'] = fnsku
                    detail_dicts.append(detail_dict)
            else:
                # 没有MSKU和FNSKU列表，返回基础数据
                detail_dict = base_dict.copy()
                detail_dict['msku'] = ''
                detail_dict['fnsku'] = ''
                detail_dicts.append(detail_dict)
        
        return detail_dicts

class RestockAnalyzer:
    """补货分析器"""
    
    def __init__(self, api_client: APIClient = None):
        """
        初始化补货分析器
        
        Args:
            api_client: API客户端实例
        """
        self.api_client = api_client or APIClient()
        self.sellers_cache = None
        self.last_sellers_update = None
    
    def get_sellers(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取店铺列表（带缓存）
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            List[Dict[str, Any]]: 店铺列表
        """
        # 检查缓存是否有效（1小时内）
        if (not force_refresh and 
            self.sellers_cache and 
            self.last_sellers_update and 
            (datetime.now() - self.last_sellers_update).seconds < 3600):
            return self.sellers_cache
        
        try:
            self.sellers_cache = self.api_client.get_seller_lists()
            self.last_sellers_update = datetime.now()
            api_logger.logger.info(f"获取到{len(self.sellers_cache)}个店铺")
            return self.sellers_cache
        except Exception as e:
            api_logger.log_error(e, "获取店铺列表失败")
            if self.sellers_cache:
                api_logger.logger.warning("使用缓存的店铺数据")
                return self.sellers_cache
            raise
    
    def get_restock_data(self, 
                        seller_ids: List[str] = None,
                        data_type: int = 1,
                        asin_list: List[str] = None,
                        msku_list: List[str] = None,
                        mode: int = 0,
                        max_pages: int = None,
                        max_workers: int = 3) -> List[RestockItem]:
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
            
        Returns:
            List[RestockItem]: 补货项目列表
        """
        # 如果没有指定店铺ID，获取所有店铺
        if not seller_ids:
            sellers = self.get_sellers()
            seller_ids = [str(seller['sid']) for seller in sellers]
        
        # 构建查询参数
        params = {
            'sid_list': seller_ids,
            'data_type': data_type,
            'mode': mode,
            'offset': 0,
            'length': APIConfig.MAX_PAGE_SIZE
        }
        
        if asin_list:
            params['asin_list'] = asin_list
        
        if msku_list:
            params['msku_list'] = msku_list
        
        try:
            # 获取原始数据（使用并发模式提高速度）
            # 限制并发线程数在合理范围内
            max_workers = max(1, min(max_workers, 5))
            raw_data = self.api_client.get_all_restock_data_concurrent(params, max_pages, max_workers)
        except Exception as e:
            print(f"并发获取失败，回退到串行模式: {e}")
            raw_data = self.api_client.get_all_restock_data(params, max_pages)
        
        # 转换为RestockItem对象
        restock_items = []
        for item_data in raw_data:
            try:
                restock_item = RestockItem.from_api_data(item_data)
                restock_items.append(restock_item)
            except Exception as e:
                api_logger.log_error(e, f"解析补货数据失败: {item_data.get('basic_info', {}).get('hash_id', 'unknown')}")
                continue
        
        api_logger.logger.info(f"成功解析{len(restock_items)}条补货数据")
        return restock_items
    
    def analyze_urgent_restock(self, restock_items: List[RestockItem], 
                              days_threshold: int = 7) -> List[RestockItem]:
        """
        分析紧急补货需求
        
        Args:
            restock_items: 补货项目列表
            days_threshold: 天数阈值
            
        Returns:
            List[RestockItem]: 紧急补货项目列表
        """
        urgent_items = []
        
        for item in restock_items:
            # 检查是否会断货
            if item.out_stock_flag == 1:
                urgent_items.append(item)
            # 检查可售天数是否小于阈值
            elif item.available_sale_days is not None and 0 < item.available_sale_days <= days_threshold:
                urgent_items.append(item)
        
        # 按可售天数排序（最紧急的在前面）
        urgent_items.sort(key=lambda x: (x.available_sale_days or 0, x.out_stock_date or ''))
        
        api_logger.logger.info(f"发现{len(urgent_items)}个紧急补货项目")
        return urgent_items
    
    def analyze_high_sales_items(self, restock_items: List[RestockItem], 
                               sales_threshold: float = 10.0) -> List[RestockItem]:
        """
        分析高销量商品
        
        Args:
            restock_items: 补货项目列表
            sales_threshold: 销量阈值（日均）
            
        Returns:
            List[RestockItem]: 高销量商品列表
        """
        high_sales_items = []
        
        for item in restock_items:
            if item.sales_avg_30 >= sales_threshold:
                high_sales_items.append(item)
        
        # 按30天日均销量降序排序
        high_sales_items.sort(key=lambda x: x.sales_avg_30, reverse=True)
        
        api_logger.logger.info(f"发现{len(high_sales_items)}个高销量商品")
        return high_sales_items
    
    def generate_summary_report(self, restock_items: List[RestockItem]) -> Dict[str, Any]:
        """
        生成汇总报告
        
        Args:
            restock_items: 补货项目列表
            
        Returns:
            Dict[str, Any]: 汇总报告
        """
        if not restock_items:
            return {
                'total_items': 0,
                'urgent_items': 0,
                'out_of_stock_items': 0,
                'high_sales_items': 0,
                'total_suggested_purchase': 0,
                'avg_available_days': 0,
                'report_time': datetime.now().isoformat()
            }
        
        # 基础统计
        total_items = len(restock_items)
        urgent_items = len([item for item in restock_items if item.out_stock_flag == 1 or (item.available_sale_days is not None and 0 < item.available_sale_days <= 7)])
        out_of_stock_items = len([item for item in restock_items if item.out_stock_flag == 1])
        high_sales_items = len([item for item in restock_items if item.sales_avg_30 >= 10.0])
        
        # 建议采购总量
        total_suggested_purchase = sum(item.suggested_purchase for item in restock_items)
        
        # 平均可售天数
        valid_days = [item.available_sale_days for item in restock_items if item.available_sale_days is not None and item.available_sale_days > 0]
        avg_available_days = sum(valid_days) / len(valid_days) if valid_days else 0
        
        # 按店铺统计
        seller_stats = {}
        for item in restock_items:
            sid = item.sid
            if sid not in seller_stats:
                seller_stats[sid] = {
                    'total_items': 0,
                    'urgent_items': 0,
                    'suggested_purchase': 0
                }
            
            seller_stats[sid]['total_items'] += 1
            seller_stats[sid]['suggested_purchase'] += item.suggested_purchase
            
            if item.out_stock_flag == 1 or (item.available_sale_days is not None and 0 < item.available_sale_days <= 7):
                seller_stats[sid]['urgent_items'] += 1
        
        report = {
            'total_items': total_items,
            'urgent_items': urgent_items,
            'out_of_stock_items': out_of_stock_items,
            'high_sales_items': high_sales_items,
            'total_suggested_purchase': total_suggested_purchase,
            'avg_available_days': round(avg_available_days, 2),
            'seller_stats': seller_stats,
            'report_time': datetime.now().isoformat()
        }
        
        api_logger.logger.info(f"生成汇总报告: 总计{total_items}项，紧急{urgent_items}项，断货{out_of_stock_items}项")
        return report
    
    def export_to_excel(self, restock_items: List[RestockItem], 
                       filename: str = None) -> str:
        """
        导出数据到Excel文件
        
        Args:
            restock_items: 补货项目列表
            filename: 文件名
            
        Returns:
            str: 导出的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"restock_data_{timestamp}.xlsx"
        
        # 确保输出目录存在
        import os
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            # 转换为DataFrame
            data_list = [item.to_dict() for item in restock_items]
            df = pd.DataFrame(data_list)
            
            # 重新排列列顺序
            column_order = [
                'asin', 'sid', 'data_type', 'msku_fnsku',
                'out_stock_flag', 'out_stock_date', 'available_sale_days',
                'fba_available', 'fba_shipping', 'local_available', 'oversea_available',
                'sales_avg_7', 'sales_avg_30', 'sales_total_7', 'sales_total_30',
                'suggested_purchase', 'suggested_local_to_fba', 'suggested_oversea_to_fba',
                'listing_opentime', 'sync_time', 'star', 'remark'
            ]
            
            # 只保留存在的列
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
            
            # 添加中文列名
            column_mapping = {
                'asin': 'ASIN',
                'sid': '店铺ID',
                'data_type': '数据类型',
                'msku_fnsku': 'MSKU/FNSKU',
                'out_stock_flag': '断货标记',
                'out_stock_date': '断货日期',
                'available_sale_days': '可售天数',
                'fba_available': 'FBA可售',
                'fba_shipping': 'FBA在途',
                'local_available': '本地仓可用',
                'oversea_available': '海外仓可用',
                'sales_avg_7': '7天日均销量',
                'sales_avg_30': '30天日均销量',
                'sales_total_7': '7天总销量',
                'sales_total_30': '30天总销量',
                'suggested_purchase': '建议采购量',
                'suggested_local_to_fba': '建议本地发FBA',
                'suggested_oversea_to_fba': '建议海外仓发FBA',
                'listing_opentime': 'Listing创建时间',
                'sync_time': '数据更新时间',
                'star': '关注状态',
                'remark': '备注'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            
            # 导出到Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='补货数据', index=False)
                
                # 获取工作表
                worksheet = writer.sheets['补货数据']
                
                # 设置单元格格式
                from openpyxl.styles import Alignment
                
                # 找到MSKU/FNSKU列的索引
                msku_fnsku_col = None
                for idx, col_name in enumerate(df.columns, 1):
                    if col_name == 'MSKU/FNSKU':
                        msku_fnsku_col = idx
                        break
                
                # 设置MSKU/FNSKU列的格式
                if msku_fnsku_col:
                    for row in range(2, len(df) + 2):  # 从第2行开始（跳过标题行）
                        cell = worksheet.cell(row=row, column=msku_fnsku_col)
                        cell.alignment = Alignment(wrap_text=True, vertical='top')
                
                # 调整列宽
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # 特别设置MSKU/FNSKU列的宽度
                if msku_fnsku_col:
                    col_letter = worksheet.cell(row=1, column=msku_fnsku_col).column_letter
                    worksheet.column_dimensions[col_letter].width = 25
            
            api_logger.logger.info(f"数据已导出到: {filepath}")
            return filepath
            
        except Exception as e:
            api_logger.log_error(e, "导出Excel失败")
            raise
    
    def save_to_json(self, restock_items: List[RestockItem], 
                    filename: str = None) -> str:
        """
        保存数据到JSON文件
        
        Args:
            restock_items: 补货项目列表
            filename: 文件名
            
        Returns:
            str: 保存的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"restock_data_{timestamp}.json"
        
        # 确保输出目录存在
        import os
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            data_list = [item.to_dict() for item in restock_items]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)
            
            api_logger.logger.info(f"数据已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            api_logger.log_error(e, "保存JSON失败")
            raise
    
    def export_to_excel_both(self, restock_items: List[RestockItem],
                           filename: str = None) -> str:
        """
        导出数据到Excel文件，包含两个工作表：
        1. 标准格式（MSKU/FNSKU合并显示）
        2. 明细拆分格式（MSKU和FNSKU分别显示，每个组合单独成行）
        
        Args:
            restock_items: 补货项目列表
            filename: 文件名
            
        Returns:
            str: 导出的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"restock_data_both_{timestamp}.xlsx"
        
        # 确保输出目录存在
        import os
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            # 创建Excel写入器
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 1. 标准格式工作表
                # 转换为DataFrame
                data_list = [item.to_dict() for item in restock_items]
                df_standard = pd.DataFrame(data_list)
                
                # 重新排列列顺序
                column_order_standard = [
                    'asin', 'sid', 'data_type', 'msku_fnsku',
                    'out_stock_flag', 'out_stock_date', 'available_sale_days',
                    'fba_available', 'fba_shipping', 'local_available', 'oversea_available',
                    'sales_avg_7', 'sales_avg_30', 'sales_total_7', 'sales_total_30',
                    'suggested_purchase', 'suggested_local_to_fba', 'suggested_oversea_to_fba',
                    'listing_opentime', 'sync_time', 'star', 'remark'
                ]
                
                # 只保留存在的列
                available_columns_standard = [col for col in column_order_standard if col in df_standard.columns]
                df_standard = df_standard[available_columns_standard]
                
                # 添加中文列名
                column_mapping_standard = {
                    'asin': 'ASIN',
                    'sid': '店铺ID',
                    'data_type': '数据类型',
                    'msku_fnsku': 'MSKU/FNSKU',
                    'out_stock_flag': '断货标记',
                    'out_stock_date': '断货日期',
                    'available_sale_days': '可售天数',
                    'fba_available': 'FBA可售',
                    'fba_shipping': 'FBA在途',
                    'local_available': '本地仓可用',
                    'oversea_available': '海外仓可用',
                    'sales_avg_7': '7天日均销量',
                    'sales_avg_30': '30天日均销量',
                    'sales_total_7': '7天总销量',
                    'sales_total_30': '30天总销量',
                    'suggested_purchase': '建议采购量',
                    'suggested_local_to_fba': '建议本地发FBA',
                    'suggested_oversea_to_fba': '建议海外仓发FBA',
                    'listing_opentime': 'Listing创建时间',
                    'sync_time': '数据更新时间',
                    'star': '关注状态',
                    'remark': '备注'
                }
                
                df_standard.rename(columns=column_mapping_standard, inplace=True)
                
                # 导出到Excel的第一个工作表
                df_standard.to_excel(writer, sheet_name='标准格式', index=False)
                
                # 获取工作表
                worksheet_standard = writer.sheets['标准格式']
                
                # 设置单元格格式
                from openpyxl.styles import Alignment
                
                # 找到MSKU/FNSKU列的索引
                msku_fnsku_col = None
                for idx, col_name in enumerate(df_standard.columns, 1):
                    if col_name == 'MSKU/FNSKU':
                        msku_fnsku_col = idx
                        break
                
                # 设置MSKU/FNSKU列的格式
                if msku_fnsku_col:
                    for row in range(2, len(df_standard) + 2):  # 从第2行开始（跳过标题行）
                        cell = worksheet_standard.cell(row=row, column=msku_fnsku_col)
                        cell.alignment = Alignment(wrap_text=True, vertical='top')
                
                # 调整列宽
                for column in worksheet_standard.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet_standard.column_dimensions[column_letter].width = adjusted_width
                
                # 特别设置MSKU/FNSKU列的宽度
                if msku_fnsku_col:
                    col_letter = worksheet_standard.cell(row=1, column=msku_fnsku_col).column_letter
                    worksheet_standard.column_dimensions[col_letter].width = 25
                
                # 2. 明细拆分格式工作表
                # 将所有数据转换为明细字典列表
                all_detail_data = []
                for item in restock_items:
                    detail_dicts = item.to_detail_dicts()
                    all_detail_data.extend(detail_dicts)
                
                # 创建DataFrame
                df_detail = pd.DataFrame(all_detail_data)
                
                # 重新排列列顺序，包含所有MSKU详细信息字段
                column_order_detail = [
                    # 基础信息
                    'asin', 'msku', 'fnsku', 'data_type', 'node_type',
                    # 库存信息
                    'fba_available', 'quantity_fba_valid', 'local_available', 'oversea_available',
                    'fba_shipping', 'oversea_shipping', 'fba_shipping_plan', 'purchase_plan',
                    'reserved_fc_transfers', 'reserved_fc_processing',
                    # 销量统计（完整）
                    'sales_avg_3', 'sales_avg_7', 'sales_avg_14', 'sales_avg_30', 'sales_avg_60', 'sales_avg_90',
                    'sales_total_3', 'sales_total_7', 'sales_total_14', 'sales_total_30', 'sales_total_60', 'sales_total_90',
                    # 建议信息（完整）
                    'suggested_purchase', 'quantity_sug_replenishment', 'quantity_sug_send',
                    'suggested_local_to_fba', 'quantity_sug_local_to_oversea', 
                    'suggested_oversea_to_fba', 'quantity_sug_oversea_to_fba',
                    # 建议日期
                    'sug_date_purchase', 'sug_date_send_local', 'sug_date_send_oversea',
                    # 其他信息
                    'available_sale_days', 'out_stock_flag', 'out_stock_date',
                    'listing_opentime', 'sync_time', 'remark', 'star'
                ]
                
                # 只保留存在的列
                existing_columns = [col for col in column_order_detail if col in df_detail.columns]
                df_detail = df_detail[existing_columns]
                
                # 重命名列为中文（包含所有MSKU详细信息字段）
                column_mapping_detail = {
                    # 基础信息
                    'asin': 'ASIN',
                    'msku': 'MSKU',
                    'fnsku': 'FNSKU',
                    'data_type': '数据类型',
                    'node_type': '节点类型',
                    # 库存信息
                    'fba_available': 'FBA可用库存',
                    'quantity_fba_valid': 'FBA有效库存',
                    'local_available': '本地可用库存',
                    'oversea_available': '海外可用库存',
                    'fba_shipping': 'FBA在途库存',
                    'oversea_shipping': '海外在途库存',
                    'fba_shipping_plan': 'FBA发货计划',
                    'purchase_plan': '采购计划',
                    'reserved_fc_transfers': '调仓中库存',
                    'reserved_fc_processing': '待调仓库存',
                    # 销量统计（完整）
                    'sales_avg_3': '3天平均销量',
                    'sales_avg_7': '7天平均销量',
                    'sales_avg_14': '14天平均销量',
                    'sales_avg_30': '30天平均销量',
                    'sales_avg_60': '60天平均销量',
                    'sales_avg_90': '90天平均销量',
                    'sales_total_3': '3天总销量',
                    'sales_total_7': '7天总销量',
                    'sales_total_14': '14天总销量',
                    'sales_total_30': '30天总销量',
                    'sales_total_60': '60天总销量',
                    'sales_total_90': '90天总销量',
                    # 建议信息（完整）
                    'suggested_purchase': '建议采购量',
                    'quantity_sug_replenishment': '建议补货量',
                    'quantity_sug_send': '建议发货量',
                    'suggested_local_to_fba': '建议本地转FBA',
                    'quantity_sug_local_to_oversea': '建议本地转海外仓',
                    'suggested_oversea_to_fba': '建议海外转FBA',
                    'quantity_sug_oversea_to_fba': '建议海外仓转FBA',
                    # 建议日期
                    'sug_date_purchase': '建议采购日期',
                    'sug_date_send_local': '建议本地发货日期',
                    'sug_date_send_oversea': '建议海外发货日期',
                    # 其他信息
                    'available_sale_days': '可售天数',
                    'out_stock_flag': '缺货标志',
                    'out_stock_date': '缺货日期',
                    'listing_opentime': '上架时间',
                    'sync_time': '同步时间',
                    'remark': '备注',
                    'star': '星级'
                }
                
                df_detail = df_detail.rename(columns=column_mapping_detail)
                
                # 导出到Excel的第二个工作表
                df_detail.to_excel(writer, sheet_name='明细拆分格式', index=False)
                
                # 获取工作表
                worksheet_detail = writer.sheets['明细拆分格式']
                
                # 设置列宽
                for column in worksheet_detail.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 30)
                    worksheet_detail.column_dimensions[column_letter].width = adjusted_width
            
            api_logger.logger.info(f"数据已导出到: {filepath} (包含标准格式和明细拆分格式)")
            return filepath
            
        except Exception as e:
            api_logger.log_error(e, "导出Excel失败")
            raise
    
    def export_to_excel_detail(self, restock_items: List[RestockItem], 
                              filename: str = None) -> str:
        """
        导出数据到Excel文件（按明细拆分）
        每个MSKU/FNSKU组合单独成行
        
        Args:
            restock_items: 补货项目列表
            filename: 文件名
            
        Returns:
            str: 保存的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"restock_data_detail_{timestamp}.xlsx"
        
        # 确保输出目录存在
        import os
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            # 将所有数据转换为明细字典列表
            all_detail_data = []
            for item in restock_items:
                detail_dicts = item.to_detail_dicts()
                all_detail_data.extend(detail_dicts)
            
            # 创建DataFrame
            df = pd.DataFrame(all_detail_data)
            
            # 重新排列列顺序，包含所有MSKU详细信息字段
            column_order = [
                # 基础信息
                'asin', 'msku', 'fnsku', 'data_type', 'node_type',
                # 库存信息
                'fba_available', 'quantity_fba_valid', 'local_available', 'oversea_available',
                'fba_shipping', 'oversea_shipping', 'fba_shipping_plan', 'purchase_plan',
                'reserved_fc_transfers', 'reserved_fc_processing',
                # 销量统计（完整）
                'sales_avg_3', 'sales_avg_7', 'sales_avg_14', 'sales_avg_30', 'sales_avg_60', 'sales_avg_90',
                'sales_total_3', 'sales_total_7', 'sales_total_14', 'sales_total_30', 'sales_total_60', 'sales_total_90',
                # 建议信息（完整）
                'suggested_purchase', 'quantity_sug_replenishment', 'quantity_sug_send',
                'suggested_local_to_fba', 'quantity_sug_local_to_oversea', 
                'suggested_oversea_to_fba', 'quantity_sug_oversea_to_fba',
                # 建议日期
                'sug_date_purchase', 'sug_date_send_local', 'sug_date_send_oversea',
                # 其他信息
                'available_sale_days', 'out_stock_flag', 'out_stock_date',
                'listing_opentime', 'sync_time', 'remark', 'star'
            ]
            
            # 只保留存在的列
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            # 重命名列为中文（包含所有MSKU详细信息字段）
            column_mapping = {
                # 基础信息
                'asin': 'ASIN',
                'msku': 'MSKU',
                'fnsku': 'FNSKU',
                'data_type': '数据类型',
                'node_type': '节点类型',
                # 库存信息
                'fba_available': 'FBA可用库存',
                'quantity_fba_valid': 'FBA有效库存',
                'local_available': '本地可用库存',
                'oversea_available': '海外可用库存',
                'fba_shipping': 'FBA在途库存',
                'oversea_shipping': '海外在途库存',
                'fba_shipping_plan': 'FBA发货计划',
                'purchase_plan': '采购计划',
                'reserved_fc_transfers': '调仓中库存',
                'reserved_fc_processing': '待调仓库存',
                # 销量统计（完整）
                'sales_avg_3': '3天平均销量',
                'sales_avg_7': '7天平均销量',
                'sales_avg_14': '14天平均销量',
                'sales_avg_30': '30天平均销量',
                'sales_avg_60': '60天平均销量',
                'sales_avg_90': '90天平均销量',
                'sales_total_3': '3天总销量',
                'sales_total_7': '7天总销量',
                'sales_total_14': '14天总销量',
                'sales_total_30': '30天总销量',
                'sales_total_60': '60天总销量',
                'sales_total_90': '90天总销量',
                # 建议信息（完整）
                'suggested_purchase': '建议采购量',
                'quantity_sug_replenishment': '建议补货量',
                'quantity_sug_send': '建议发货量',
                'suggested_local_to_fba': '建议本地转FBA',
                'quantity_sug_local_to_oversea': '建议本地转海外仓',
                'suggested_oversea_to_fba': '建议海外转FBA',
                'quantity_sug_oversea_to_fba': '建议海外仓转FBA',
                # 建议日期
                'sug_date_purchase': '建议采购日期',
                'sug_date_send_local': '建议本地发货日期',
                'sug_date_send_oversea': '建议海外发货日期',
                # 其他信息
                'available_sale_days': '可售天数',
                'out_stock_flag': '缺货标志',
                'out_stock_date': '缺货日期',
                'listing_opentime': '上架时间',
                'sync_time': '同步时间',
                'remark': '备注',
                'star': '星级'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 导出到Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='补货数据明细', index=False)
                
                # 获取工作表
                worksheet = writer.sheets['补货数据明细']
                
                # 设置列宽
                column_widths = {
                    'A': 15,  # ASIN
                    'B': 20,  # MSKU
                    'C': 20,  # FNSKU
                    'D': 12,  # 数据类型
                    'E': 12,  # 节点类型
                    'F': 15,  # FBA可用库存
                    'G': 15,  # 本地可用库存
                    'H': 15,  # 海外可用库存
                    'I': 15,  # FBA在途库存
                    'J': 15,  # 海外在途库存
                    'K': 15,  # FBA发货计划
                    'L': 12,  # 采购计划
                    'M': 12,  # 7天平均销量
                    'N': 12,  # 30天平均销量
                    'O': 12,  # 7天总销量
                    'P': 12,  # 30天总销量
                    'Q': 12,  # 建议采购量
                    'R': 15,  # 建议本地转FBA
                    'S': 15,  # 建议海外转FBA
                    'T': 12,  # 可售天数
                    'U': 10,  # 缺货标志
                    'V': 15,  # 缺货日期
                    'W': 18,  # 上架时间
                    'X': 18,  # 同步时间
                    'Y': 15,  # 备注
                    'Z': 8    # 星级
                }
                
                for col, width in column_widths.items():
                    worksheet.column_dimensions[col].width = width
            
            api_logger.logger.info(f"明细数据已导出到: {filepath}")
            return filepath
            
        except Exception as e:
            api_logger.log_error(e, "导出明细Excel失败")
            raise
    
    def get_msku_detail_info(self, sid: str, msku: str, mode: str = "1") -> dict:
        """
        获取单个MSKU的详细信息
        
        Args:
            sid: 店铺ID
            msku: MSKU编码
            mode: 补货建议模式，默认为"1"
            
        Returns:
            dict: MSKU详细信息
        """
        try:
            api_logger.logger.info(f"获取MSKU详细信息: sid={sid}, msku={msku}, mode={mode}")
            
            # 调用API获取MSKU详细信息
            response = self.api_client.get_msku_detail_info(sid, msku, mode)
            
            if response.get('code') == 0 and response.get('data'):
                api_logger.logger.info(f"成功获取MSKU详细信息: {msku}")
                return response['data']
            else:
                error_msg = response.get('message', '未知错误')
                api_logger.logger.warning(f"获取MSKU详细信息失败: {error_msg}")
                return {}
                
        except Exception as e:
            api_logger.log_error(e, f"获取MSKU详细信息异常: sid={sid}, msku={msku}")
            return {}
    
    def get_msku_details_batch(self, msku_list: List[dict], max_workers: int = 5) -> List[dict]:
        """
        批量获取MSKU详细信息
        
        Args:
            msku_list: MSKU列表，每个元素包含 {'sid': str, 'msku': str, 'mode': str}
            max_workers: 最大并发数
            
        Returns:
            List[dict]: MSKU详细信息列表
        """
        api_logger.logger.info(f"开始批量获取{len(msku_list)}个MSKU的详细信息")
        
        results = []
        
        def fetch_single_msku(msku_info):
            try:
                sid = msku_info['sid']
                msku = msku_info['msku']
                mode = msku_info.get('mode', '1')
                
                detail_info = self.get_msku_detail_info(sid, msku, mode)
                if detail_info:
                    detail_info['sid'] = sid
                    detail_info['msku'] = msku
                    detail_info['mode'] = mode
                    return detail_info
                return None
            except Exception as e:
                api_logger.log_error(e, f"获取单个MSKU详细信息失败: {msku_info}")
                return None
        
        # 使用线程池并发获取
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_msku = {executor.submit(fetch_single_msku, msku_info): msku_info 
                             for msku_info in msku_list}
            
            for future in as_completed(future_to_msku):
                msku_info = future_to_msku[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    api_logger.log_error(e, f"处理MSKU详细信息结果失败: {msku_info}")
        
        api_logger.logger.info(f"批量获取MSKU详细信息完成，成功获取{len(results)}个")
        return results
    
    def enhance_restock_items_with_details(self, restock_items: List[RestockItem]) -> List[RestockItem]:
        """
        使用MSKU详细信息增强补货项目数据
        
        Args:
            restock_items: 原始补货项目列表
            
        Returns:
            List[RestockItem]: 增强后的补货项目列表
        """
        api_logger.logger.info(f"开始增强{len(restock_items)}个补货项目的详细信息")
        
        # 提取需要获取详细信息的MSKU列表
        msku_requests = []
        for item in restock_items:
            if item.msku_list:
                for msku in item.msku_list:
                    msku_requests.append({
                        'sid': item.sid,
                        'msku': msku,
                        'mode': '1'  # 默认模式
                    })
        
        if not msku_requests:
            api_logger.logger.info("没有找到需要获取详细信息的MSKU")
            return restock_items
        
        # 批量获取MSKU详细信息
        msku_details = self.get_msku_details_batch(msku_requests)
        
        # 创建MSKU详细信息映射
        detail_map = {}
        for detail in msku_details:
            key = f"{detail['sid']}_{detail['msku']}"
            detail_map[key] = detail
        
        # 增强补货项目数据
        enhanced_items = []
        for item in restock_items:
            enhanced_item = item
            
            # 如果有MSKU列表，尝试获取详细信息并增强数据
            if item.msku_list:
                # 获取主要MSKU的详细信息（通常使用第一个MSKU）
                primary_msku = item.msku_list[0] if item.msku_list else None
                if primary_msku:
                    key = f"{item.sid}_{primary_msku}"
                    if key in detail_map:
                        detail_data = detail_map[key]
                        
                        # 映射详细销量统计
                        enhanced_item.sales_avg_3 = detail_data.get('sales_avg_3', 0.0)
                        enhanced_item.sales_avg_14 = detail_data.get('sales_avg_14', 0.0)
                        enhanced_item.sales_avg_60 = detail_data.get('sales_avg_60', 0.0)
                        enhanced_item.sales_avg_90 = detail_data.get('sales_avg_90', 0.0)
                        enhanced_item.sales_total_3 = detail_data.get('sales_total_3', 0)
                        enhanced_item.sales_total_14 = detail_data.get('sales_total_14', 0)
                        enhanced_item.sales_total_60 = detail_data.get('sales_total_60', 0)
                        enhanced_item.sales_total_90 = detail_data.get('sales_total_90', 0)
                        
                        # 映射详细建议信息
                        enhanced_item.quantity_sug_replenishment = detail_data.get('quantity_sug_replenishment', 0)
                        enhanced_item.quantity_sug_send = detail_data.get('quantity_sug_send', 0)
                        enhanced_item.quantity_sug_local_to_oversea = detail_data.get('quantity_sug_local_to_oversea', 0)
                        enhanced_item.quantity_sug_oversea_to_fba = detail_data.get('quantity_sug_oversea_to_fba', 0)
                        
                        # 映射建议日期
                        enhanced_item.sug_date_send_local = detail_data.get('sug_date_send_local', '')
                        enhanced_item.sug_date_send_oversea = detail_data.get('sug_date_send_oversea', '')
                        enhanced_item.sug_date_purchase = detail_data.get('sug_date_purchase', '')
                        
                        # 映射详细库存信息
                        enhanced_item.quantity_fba_valid = detail_data.get('quantity_fba_valid', 0)
                        
                        # 处理MSKU库存列表
                        msku_list_data = detail_data.get('msku_list', [])
                        if msku_list_data:
                            # 汇总所有MSKU的库存信息
                            total_reserved_fc_transfers = 0
                            total_reserved_fc_processing = 0
                            for msku_info in msku_list_data:
                                total_reserved_fc_transfers += msku_info.get('reserved_fc_transfers', 0)
                                total_reserved_fc_processing += msku_info.get('reserved_fc_processing', 0)
                            
                            enhanced_item.reserved_fc_transfers = total_reserved_fc_transfers
                            enhanced_item.reserved_fc_processing = total_reserved_fc_processing
                        
                        # 映射运输方式建议列表
                        enhanced_item.suggest_sm_list = detail_data.get('suggest_sm_list', [])
                        
                        # 保存完整的MSKU详细信息原始数据
                        enhanced_item.msku_detail_data = detail_data
                        
                        api_logger.logger.debug(f"成功增强MSKU {primary_msku} 的详细信息")
            
            enhanced_items.append(enhanced_item)
        
        api_logger.logger.info(f"补货项目详细信息增强完成")
        return enhanced_items
