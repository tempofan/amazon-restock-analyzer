# -*- coding: utf-8 -*-
"""
领星ERP API配置文件
包含API基础配置信息和常量定义
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 🔧 加载环境变量配置文件
load_dotenv('config/server.env')

# 服务器配置
class ServerConfig:
    """服务器配置类"""
    
    # 服务器基础配置
    HOST = os.getenv('SERVER_HOST', '127.0.0.1')  # 服务器IP
    PORT = int(os.getenv('SERVER_PORT', '8000'))      # 服务器端口
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # 允许访问的主机
    ALLOWED_HOSTS = [
        '192.168.0.99',
        'localhost',
        '127.0.0.1',
        '0.0.0.0'
    ]
    
    # 跨域配置
    CORS_ALLOWED_ORIGINS = [
        'http://192.168.0.99:8000',
        'http://localhost:8000',
        'http://127.0.0.1:8000'
    ]

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
    
    # 应用凭证 - 直接设置正确的值
    APP_ID = 'ak_ogLvclRkg2uTq'
    APP_SECRET = 'S2Ufo0CpKeV4J9JwoTQ7wg=='
    
    # 请求配置
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))  # 请求超时时间（秒）
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))          # 最大重试次数
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '1'))          # 重试延迟（秒）
    
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
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "logs/lingxing_api.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5

# 数据库配置
class DatabaseConfig:
    """数据库配置类"""
    
    # 数据库类型
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # sqlite, mysql, postgresql
    
    # SQLite配置（默认）
    SQLITE_DB_PATH = "data/lingxing_data.db"
    
    # MySQL配置
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', '192.168.0.99'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'amazon_restock'),
        'charset': 'utf8mb4'
    }
    
    # PostgreSQL配置
    POSTGRESQL_CONFIG = {
        'host': os.getenv('POSTGRES_HOST', '192.168.0.99'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'database': os.getenv('POSTGRES_DATABASE', 'amazon_restock')
    }
    
    # 表名配置
    TABLES = {
        "tokens": "api_tokens",
        "sellers": "seller_info",
        "listings": "listing_data",
        "restock_data": "restock_suggestions"
    }
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接URL"""
        if cls.DB_TYPE == 'mysql':
            config = cls.MYSQL_CONFIG
            return f"mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        elif cls.DB_TYPE == 'postgresql':
            config = cls.POSTGRESQL_CONFIG
            return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        else:
            return f"sqlite:///{cls.SQLITE_DB_PATH}"

# 文件存储配置
class StorageConfig:
    """文件存储配置类"""
    
    # 输出目录
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    
    # 数据目录
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    
    # 日志目录
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # 临时文件目录
    TEMP_DIR = os.getenv('TEMP_DIR', 'temp')
    
    # 文件上传配置
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '100')) * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES = ['.xlsx', '.xls', '.csv', '.json']
    
    @classmethod
    def ensure_directories(cls):
        """确保所有必要目录存在"""
        directories = [cls.OUTPUT_DIR, cls.DATA_DIR, cls.LOG_DIR, cls.TEMP_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

# 安全配置
class SecurityConfig:
    """安全配置类"""
    
    # API密钥
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # 请求频率限制
    RATE_LIMIT = {
        'requests_per_minute': int(os.getenv('RATE_LIMIT_PER_MINUTE', '60')),
        'requests_per_hour': int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))
    }
    
    # IP白名单
    ALLOWED_IPS = os.getenv('ALLOWED_IPS', '').split(',') if os.getenv('ALLOWED_IPS') else []
    
    # 会话配置
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1小时