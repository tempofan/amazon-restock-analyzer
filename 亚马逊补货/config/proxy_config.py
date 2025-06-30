# -*- coding: utf-8 -*-
"""
🌐 代理配置模块
配置云代理服务器相关信息，解决IP白名单问题
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 🔧 确保加载环境变量配置文件
env_file = os.path.join(os.path.dirname(__file__), 'server.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"📄 加载环境配置文件: {env_file}")
else:
    print(f"⚠️ 环境配置文件不存在: {env_file}")

class ProxyConfig:
    """
    🔧 代理配置类
    管理云代理服务器的配置信息
    """
    
    # 是否启用代理模式
    ENABLE_PROXY = os.getenv('ENABLE_PROXY', 'True').lower() == 'true'
    
    # 云代理服务器配置
    PROXY_HOST = os.getenv('PROXY_HOST', '')  # 云服务器IP
    PROXY_PORT = int(os.getenv('PROXY_PORT', '8080'))  # 代理服务端口
    PROXY_PROTOCOL = os.getenv('PROXY_PROTOCOL', 'http')  # 协议类型
    
    # 代理服务器完整地址
    @classmethod
    def get_proxy_base_url(cls) -> Optional[str]:
        """
        获取代理服务器基础URL
        
        Returns:
            str: 代理服务器地址，如果未配置返回None
        """
        if not cls.ENABLE_PROXY or not cls.PROXY_HOST:
            return None
        
        return f"{cls.PROXY_PROTOCOL}://{cls.PROXY_HOST}:{cls.PROXY_PORT}/api/proxy"
    
    # 代理超时配置
    PROXY_TIMEOUT = int(os.getenv('PROXY_TIMEOUT', '60'))  # 代理请求超时时间（秒）
    PROXY_RETRIES = int(os.getenv('PROXY_RETRIES', '3'))   # 代理请求重试次数
    
    # 代理健康检查
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '300'))  # 健康检查间隔（秒）
    
    @classmethod
    def get_health_check_url(cls) -> Optional[str]:
        """
        获取代理服务器健康检查URL
        
        Returns:
            str: 健康检查地址
        """
        if not cls.ENABLE_PROXY or not cls.PROXY_HOST:
            return None
        
        return f"{cls.PROXY_PROTOCOL}://{cls.PROXY_HOST}:{cls.PROXY_PORT}/health"
    
    @classmethod
    def get_stats_url(cls) -> Optional[str]:
        """
        获取代理服务器统计信息URL
        
        Returns:
            str: 统计信息地址
        """
        if not cls.ENABLE_PROXY or not cls.PROXY_HOST:
            return None
        
        return f"{cls.PROXY_PROTOCOL}://{cls.PROXY_HOST}:{cls.PROXY_PORT}/stats"
    
    @classmethod
    def is_proxy_enabled(cls) -> bool:
        """
        检查是否启用了代理模式
        
        Returns:
            bool: 是否启用代理
        """
        return cls.ENABLE_PROXY and bool(cls.PROXY_HOST)
    
    @classmethod
    def validate_config(cls) -> tuple[bool, str]:
        """
        验证代理配置是否完整
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not cls.ENABLE_PROXY:
            return True, "代理模式已禁用"
        
        if not cls.PROXY_HOST:
            return False, "代理服务器地址未配置 (PROXY_HOST)"
        
        if not (1 <= cls.PROXY_PORT <= 65535):
            return False, f"代理服务器端口无效: {cls.PROXY_PORT}"
        
        if cls.PROXY_PROTOCOL not in ['http', 'https']:
            return False, f"代理协议无效: {cls.PROXY_PROTOCOL}"
        
        return True, "代理配置有效"

# 📋 配置示例和说明
PROXY_CONFIG_EXAMPLE = """
# 🌐 代理配置示例
# 将以下配置添加到 config/server.env 文件中

# ============= 云代理配置 =============
# 是否启用代理模式（True/False）
ENABLE_PROXY=True

# 云服务器IP地址（替换为你的云服务器IP）
PROXY_HOST=123.456.789.123

# 代理服务端口（默认8080）
PROXY_PORT=8080

# 代理协议（http或https）
PROXY_PROTOCOL=http

# 代理超时设置（秒）
PROXY_TIMEOUT=60

# 代理重试次数
PROXY_RETRIES=3

# 健康检查间隔（秒）
HEALTH_CHECK_INTERVAL=300
"""

def print_config_example():
    """打印配置示例"""
    print(PROXY_CONFIG_EXAMPLE) 