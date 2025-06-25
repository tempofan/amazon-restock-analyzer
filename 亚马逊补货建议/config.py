#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
包含应用的所有配置信息
"""

import os
from datetime import timedelta

class Config:
    """
    应用配置类
    """
    
    # Flask基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'amazon-replenishment-secret-key-2024'
    
    # 调试模式
    DEBUG = False
    
    # 数据库配置（如果需要）
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///amazon_replenishment.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 领星ERP API配置
    LINGXING_API_CONFIG = {
        'base_url': 'https://openapi.lingxing.com',
        'api_key': 'YESofbbaoY',  # API访问密钥
        'timeout': 30,  # 请求超时时间（秒）
        'retry_times': 3,  # 重试次数
        'retry_delay': 1,  # 重试延迟（秒）
    }
    
    # API接口路径配置
    LINGXING_API_ENDPOINTS = {
        # 补货建议相关接口
        'replenishment_list': '/api/replenishment/list',  # 查询补货列表
        'replenishment_rules_asin': '/api/replenishment/rules/asin',  # 查询规则-ASIN
        'replenishment_rules_msku': '/api/replenishment/rules/msku',  # 查询规则-MSKU
        'replenishment_suggestions_asin': '/api/replenishment/suggestions/asin',  # 查询建议信息-ASIN
        'replenishment_suggestions_msku': '/api/replenishment/suggestions/msku',  # 查询建议信息-MSKU
        
        # 店铺相关接口
        'shop_list': '/api/shop/list',  # 店铺列表
        
        # 产品相关接口
        'product_list': '/api/product/list',  # 产品列表
        'product_detail': '/api/product/detail',  # 产品详情
        
        # 库存相关接口
        'inventory_list': '/api/inventory/list',  # 库存列表
        'inventory_detail': '/api/inventory/detail',  # 库存详情
    }
    
    # 数据处理配置
    DATA_PROCESSING_CONFIG = {
        'default_page_size': 20,  # 默认分页大小
        'max_page_size': 100,  # 最大分页大小
        'cache_timeout': 300,  # 缓存超时时间（秒）
        'export_formats': ['xlsx', 'csv', 'json'],  # 支持的导出格式
    }
    
    # 前端配置
    FRONTEND_CONFIG = {
        'app_name': '亚马逊补货建议系统',
        'app_version': '1.0.0',
        'company_name': '智能补货助手',
        'theme': 'default',
        'language': 'zh-CN',
    }
    
    # 安全配置
    SECURITY_CONFIG = {
        'csrf_enabled': True,
        'session_protection': 'strong',
        'login_required': False,  # 是否需要登录
        'rate_limit': {
            'enabled': True,
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
        }
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'type': 'simple',  # 缓存类型：simple, redis, memcached
        'default_timeout': 300,  # 默认缓存时间（秒）
        'key_prefix': 'amazon_replenishment_',
    }
    
    # 邮件配置（如果需要通知功能）
    MAIL_CONFIG = {
        'enabled': False,
        'server': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True,
        'username': '',
        'password': '',
        'default_sender': '',
    }
    
    # 定时任务配置
    SCHEDULER_CONFIG = {
        'enabled': False,  # 是否启用定时任务
        'timezone': 'Asia/Shanghai',
        'jobs': {
            'sync_replenishment_data': {
                'enabled': True,
                'interval': 3600,  # 每小时同步一次（秒）
                'description': '同步补货建议数据',
            },
            'cleanup_logs': {
                'enabled': True,
                'cron': '0 2 * * *',  # 每天凌晨2点清理日志
                'description': '清理过期日志文件',
            }
        }
    }
    
    # 导出配置
    EXPORT_CONFIG = {
        'max_records': 10000,  # 最大导出记录数
        'temp_dir': 'temp',  # 临时文件目录
        'cleanup_after_hours': 24,  # 临时文件清理时间（小时）
    }
    
    # 监控配置
    MONITORING_CONFIG = {
        'enabled': True,
        'metrics': {
            'api_calls': True,
            'response_time': True,
            'error_rate': True,
            'memory_usage': True,
        },
        'alerts': {
            'error_rate_threshold': 0.05,  # 错误率阈值 5%
            'response_time_threshold': 5000,  # 响应时间阈值 5秒
        }
    }

class DevelopmentConfig(Config):
    """
    开发环境配置
    """
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    LINGXING_API_CONFIG = Config.LINGXING_API_CONFIG.copy()
    LINGXING_API_CONFIG['timeout'] = 60  # 开发环境增加超时时间

class ProductionConfig(Config):
    """
    生产环境配置
    """
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SECURITY_CONFIG = Config.SECURITY_CONFIG.copy()
    SECURITY_CONFIG['csrf_enabled'] = True
    SECURITY_CONFIG['session_protection'] = 'strong'

class TestingConfig(Config):
    """
    测试环境配置
    """
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': Config
}

def get_config(config_name=None):
    """
    获取配置对象
    
    Args:
        config_name (str): 配置名称
        
    Returns:
        Config: 配置对象
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, Config)
