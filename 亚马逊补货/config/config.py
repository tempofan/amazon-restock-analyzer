# -*- coding: utf-8 -*-
"""
领星ERP API配置文件
包含API基础配置信息和常量定义
"""

import os
from typing import Dict, Any

# API基础配置
class APIConfig:
    """API配置类"""
    
    # 基础URL
    BASE_URL = "https://openapi.lingxing.com"
    
    # 认证相关URL
    AUTH_URLS = {
        "get_token": "/api/auth-server/oauth/access-token",
        "refresh_token": "/api/auth-server/oauth/refresh"
    }
    
    # 业务接口URL
    BUSINESS_URLS = {
        "seller_lists": "/erp/sc/data/seller/lists",
        "listing_data": "/erp/sc/data/mws/listing",
        "restock_summary": "/erp/sc/routing/restocking/analysis/getSummaryList",
        "msku_detail_info": "/erp/sc/routing/fbaSug/msku/getInfo"
    }
    
    # 应用凭证
    APP_ID = "ak_kRqgsBxncVls3"
    APP_SECRET = "baT6edtY8AwlU9yIAlFqNQ=="
    
    # 请求配置
    REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
    MAX_RETRIES = 3  # 最大重试次数
    RETRY_DELAY = 1  # 重试延迟（秒）
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 50
    
    # Token配置
    TOKEN_REFRESH_THRESHOLD = 300  # Token刷新阈值（秒）
    
    # 错误码映射
    ERROR_CODES = {
        "2001001": "appId不存在，检查值有效性",
        "2001002": "appSecret不正确，检查值有效性",
        "2001003": "token不存在或者已经过期，可刷新token重试",
        "2001004": "请求的api未授权，联系领星相关工作人员确认",
        "2001005": "access_token不正确，检查值有效性",
        "2001006": "接口签名不正确，校验生成签名正确性",
        "2001007": "签名已经过期，可重新发起请求",
        "2001008": "refresh_token过期，请重新获取",
        "2001009": "refresh_token值无效，检查值有效性或重新获取",
        "3001001": "access_token、sign、timestamp、app_key为必传参数",
        "3001002": "ip未加入白名单，确认发起ip地址后在ERP内自行增加",
        "3001008": "接口请求太频繁触发限流，适当下调接口请求频率"
    }
    
    @classmethod
    def get_error_message(cls, error_code: str) -> str:
        """获取错误码对应的错误信息"""
        return cls.ERROR_CODES.get(error_code, f"未知错误码: {error_code}")

# 日志配置
class LogConfig:
    """日志配置类"""
    
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "logs/lingxing_api.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5

# 数据库配置（如果需要）
class DatabaseConfig:
    """数据库配置类"""
    
    # SQLite配置（默认）
    SQLITE_DB_PATH = "data/lingxing_data.db"
    
    # 表名配置
    TABLES = {
        "tokens": "api_tokens",
        "sellers": "seller_info",
        "listings": "listing_data",
        "restock_data": "restock_suggestions"
    }