#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理器 - 真实API数据版本
处理领星ERP API返回的真实数据结构
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

class RealDataProcessor:
    """
    真实API数据处理器
    专门处理领星ERP API返回的数据结构
    """
    
    def __init__(self):
        """
        初始化数据处理器
        """
        self.logger = logging.getLogger(__name__)
    
    def process_replenishment_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理补货建议数据
        
        Args:
            raw_data (dict): API返回的原始数据
            
        Returns:
            dict: 处理后的数据
        """
        try:
            self.logger.info("开始处理真实补货建议数据")
            
            # 检查数据格式
            if not isinstance(raw_data, dict):
                raise ValueError("原始数据格式错误，应为字典类型")
            
            # 提取API响应数据
            api_data = raw_data.get('data', {})
            if isinstance(api_data, dict):
                # 如果data是字典，提取其中的数据列表
                data_list = api_data.get('data', [])
                total_count = api_data.get('total', 0)
            else:
                # 如果data直接是列表
                data_list = api_data if isinstance(api_data, list) else []
                total_count = len(data_list)
            
            # 处理每条记录
            processed_items = []
            for item in data_list:
                processed_item = self._process_single_item(item)
                if processed_item:
                    processed_items.append(processed_item)
            
            # 计算汇总信息
            summary = self._calculate_summary(processed_items)
            
            result = {
                'items': processed_items,
                'summary': summary,
                'total_count': total_count,
                'processed_count': len(processed_items),
                'processed_at': datetime.now().isoformat(),
                'success': True
            }
            
            self.logger.info(f"数据处理完成，共处理 {len(processed_items)} 条记录")
            return result
            
        except Exception as e:
            self.logger.error(f"数据处理失败: {e}")
            return {
                'items': [],
                'summary': {},
                'total_count': 0,
                'processed_count': 0,
                'error': str(e),
                'success': False
            }
    
    def _process_single_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理单条补货建议记录
        
        Args:
            item (dict): 原始记录
            
        Returns:
            dict: 处理后的记录，如果处理失败返回None
        """
        try:
            # 提取各个部分的数据
            basic_info = item.get('basic_info', {})
            amazon_quantity = item.get('amazon_quantity_info', {})
            scm_quantity = item.get('scm_quantity_info', {})
            sales_info = item.get('sales_info', {})
            suggest_info = item.get('suggest_info', {})
            ext_info = item.get('ext_info', {})
            
            # 提取MSKU和FNSKU信息
            msku_fnsku_list = basic_info.get('msku_fnsku_list', [])
            first_msku_info = msku_fnsku_list[0] if msku_fnsku_list else {}
            
            # 基础信息
            processed = {
                # 标识信息
                'hash_id': basic_info.get('hash_id', ''),
                'asin': basic_info.get('asin', ''),
                'msku': first_msku_info.get('msku', ''),
                'fnsku': first_msku_info.get('fnsku', ''),
                'shop_id': str(basic_info.get('sid', '')),
                'data_type': basic_info.get('data_type', 1),
                'node_type': basic_info.get('node_type', 1),
                
                # 亚马逊库存
                'amazon_valid': self._safe_int(amazon_quantity.get('amazon_quantity_valid', 0)),
                'amazon_shipping': self._safe_int(amazon_quantity.get('amazon_quantity_shipping', 0)),
                'fba_fulfillable': self._safe_int(amazon_quantity.get('afn_fulfillable_quantity', 0)),
                'reserved_transfers': self._safe_int(amazon_quantity.get('reserved_fc_transfers', 0)),
                'reserved_processing': self._safe_int(amazon_quantity.get('reserved_fc_processing', 0)),
                'inbound_receiving': self._safe_int(amazon_quantity.get('afn_inbound_receiving_quantity', 0)),
                
                # 供应链库存
                'local_valid': self._safe_int(scm_quantity.get('sc_quantity_local_valid', 0)),
                'oversea_valid': self._safe_int(scm_quantity.get('sc_quantity_oversea_valid', 0)),
                'oversea_shipping': self._safe_int(scm_quantity.get('sc_quantity_oversea_shipping', 0)),
                'purchase_shipping': self._safe_int(scm_quantity.get('sc_quantity_purchase_shipping', 0)),
                'local_shipping': self._safe_int(scm_quantity.get('sc_quantity_local_shipping', 0)),
                
                # 销售数据
                'sales_avg_3': self._safe_float(sales_info.get('sales_avg_3', 0)),
                'sales_avg_7': self._safe_float(sales_info.get('sales_avg_7', 0)),
                'sales_avg_14': self._safe_float(sales_info.get('sales_avg_14', 0)),
                'sales_avg_30': self._safe_float(sales_info.get('sales_avg_30', 0)),
                'sales_avg_60': self._safe_float(sales_info.get('sales_avg_60', 0)),
                'sales_avg_90': self._safe_float(sales_info.get('sales_avg_90', 0)),
                'sales_total_30': self._safe_int(sales_info.get('sales_total_30', 0)),
                'sales_total_60': self._safe_int(sales_info.get('sales_total_60', 0)),
                'sales_total_90': self._safe_int(sales_info.get('sales_total_90', 0)),
                
                # 补货建议
                'out_stock_flag': suggest_info.get('out_stock_flag', 0),
                'out_stock_date': suggest_info.get('out_stock_date', ''),
                'estimated_sale_quantity': self._safe_int(suggest_info.get('estimated_sale_quantity', 0)),
                'estimated_sale_avg': self._safe_float(suggest_info.get('estimated_sale_avg_quantity', 0)),
                'available_sale_days': self._safe_int(suggest_info.get('available_sale_days', 0)),
                'fba_available_days': self._safe_int(suggest_info.get('fba_available_sale_days', 0)),
                'quantity_sug_purchase': self._safe_int(suggest_info.get('quantity_sug_purchase', 0)),
                'quantity_sug_local_to_fba': self._safe_int(suggest_info.get('quantity_sug_local_to_fba', 0)),
                'quantity_sug_oversea_to_fba': self._safe_int(suggest_info.get('quantity_sug_oversea_to_fba', 0)),
                'sug_date_purchase': suggest_info.get('sug_date_purchase', ''),
                'sug_date_send_local': suggest_info.get('sug_date_send_local', ''),
                
                # 扩展信息
                'restock_status': ext_info.get('restock_status', 0),
                'remark': ext_info.get('remark', ''),
                'star': ext_info.get('star', 0),
                'need_flag': ext_info.get('need_flag'),
                
                # 时间信息
                'sync_time': basic_info.get('sync_time', ''),
                'listing_opentime': basic_info.get('listing_opentime_list', []),
            }
            
            # 计算衍生字段
            processed.update(self._calculate_derived_fields(processed))
            
            return processed
            
        except Exception as e:
            self.logger.warning(f"处理单条记录失败: {e}")
            return None
    
    def _calculate_derived_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算衍生字段
        """
        derived = {}
        
        # 计算总库存
        total_amazon = item.get('amazon_valid', 0) + item.get('amazon_shipping', 0)
        total_local = item.get('local_valid', 0) + item.get('local_shipping', 0)
        total_oversea = item.get('oversea_valid', 0) + item.get('oversea_shipping', 0)
        
        derived['total_amazon_stock'] = total_amazon
        derived['total_local_stock'] = total_local
        derived['total_oversea_stock'] = total_oversea
        derived['total_stock'] = total_amazon + total_local + total_oversea
        
        # 计算可售天数
        daily_sales = max(item.get('sales_avg_30', 0), item.get('sales_avg_7', 0))
        if daily_sales > 0:
            derived['days_of_stock'] = round(item.get('fba_fulfillable', 0) / daily_sales, 1)
        else:
            derived['days_of_stock'] = 999
        
        # 计算紧急程度分数
        days_of_stock = derived['days_of_stock']
        if days_of_stock <= 7:
            derived['urgency_score'] = 100
        elif days_of_stock <= 14:
            derived['urgency_score'] = 80
        elif days_of_stock <= 30:
            derived['urgency_score'] = 60
        elif days_of_stock <= 60:
            derived['urgency_score'] = 40
        else:
            derived['urgency_score'] = 20
        
        # 确定库存状态
        if item.get('out_stock_flag', 0) == 1:
            derived['stock_status'] = 'out_of_stock'
        elif days_of_stock <= 7:
            derived['stock_status'] = 'critical'
        elif days_of_stock <= 14:
            derived['stock_status'] = 'low'
        elif days_of_stock <= 30:
            derived['stock_status'] = 'warning'
        else:
            derived['stock_status'] = 'normal'
        
        # 确定紧急程度
        if derived['urgency_score'] >= 80:
            derived['urgency_level'] = 'urgent'
        elif derived['urgency_score'] >= 60:
            derived['urgency_level'] = 'high'
        elif derived['urgency_score'] >= 40:
            derived['urgency_level'] = 'medium'
        else:
            derived['urgency_level'] = 'low'
        
        # 生成建议
        if item.get('quantity_sug_purchase', 0) > 0:
            derived['recommendation'] = f"建议采购 {item.get('quantity_sug_purchase', 0)} 件"
        elif item.get('quantity_sug_local_to_fba', 0) > 0:
            derived['recommendation'] = f"建议从本地仓发货 {item.get('quantity_sug_local_to_fba', 0)} 件到FBA"
        elif item.get('quantity_sug_oversea_to_fba', 0) > 0:
            derived['recommendation'] = f"建议从海外仓发货 {item.get('quantity_sug_oversea_to_fba', 0)} 件到FBA"
        else:
            derived['recommendation'] = "暂无补货建议"
        
        # 产品名称（如果没有则生成）
        if not item.get('product_name'):
            derived['product_name'] = f"ASIN-{item.get('asin', 'Unknown')}"
        
        # 店铺名称（如果没有则生成）
        if not item.get('shop_name'):
            derived['shop_name'] = f"店铺-{item.get('shop_id', 'Unknown')}"
        
        return derived
    
    def _calculate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算汇总信息
        """
        if not items:
            return {
                'total_products': 0,
                'urgent_replenishment': 0,
                'high_priority_items': 0,
                'out_of_stock_items': 0,
                'critical_items': 0,
                'low_stock_items': 0
            }
        
        # 统计各种状态的商品数量
        urgent_count = len([item for item in items if item.get('urgency_level') == 'urgent'])
        high_priority_count = len([item for item in items if item.get('urgency_level') in ['urgent', 'high']])
        out_of_stock_count = len([item for item in items if item.get('stock_status') == 'out_of_stock'])
        critical_count = len([item for item in items if item.get('stock_status') == 'critical'])
        low_stock_count = len([item for item in items if item.get('stock_status') in ['critical', 'low']])
        
        return {
            'total_products': len(items),
            'urgent_replenishment': urgent_count,
            'high_priority_items': high_priority_count,
            'out_of_stock_items': out_of_stock_count,
            'critical_items': critical_count,
            'low_stock_items': low_stock_count,
            'normal_items': len(items) - high_priority_count
        }
    
    def _safe_int(self, value: Any) -> int:
        """安全转换为整数"""
        try:
            return int(float(value)) if value is not None else 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value: Any) -> float:
        """安全转换为浮点数"""
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
