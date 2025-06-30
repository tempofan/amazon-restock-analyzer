#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 API策略配置
根据不同的API类型选择合适的访问策略
"""

from typing import Dict, Any, Optional
from .proxy_config import ProxyConfig
from .config import APIConfig

class APIStrategy:
    """
    API访问策略管理器
    """
    
    # API分类策略
    API_STRATEGIES = {
        # 认证相关API - 使用代理（解决IP白名单问题）
        'auth': {
            'use_proxy': True,
            'reason': '通过云代理访问，解决IP白名单问题'
        },

        # 业务API - 使用代理（解决IP白名单问题）
        'business': {
            'use_proxy': True,
            'reason': '通过云代理访问，解决IP白名单问题'
        },

        # 其他API - 使用代理
        'other': {
            'use_proxy': True,
            'reason': '通过云代理访问，使用固定IP'
        }
    }
    
    @classmethod
    def should_use_proxy(cls, api_type: str = 'other') -> bool:
        """
        判断指定类型的API是否应该使用代理
        
        Args:
            api_type: API类型 ('auth', 'business', 'other')
            
        Returns:
            bool: 是否使用代理
        """
        strategy = cls.API_STRATEGIES.get(api_type, cls.API_STRATEGIES['other'])
        return strategy['use_proxy']
    
    @classmethod
    def get_base_url(cls, api_type: str = 'other') -> str:
        """
        获取指定API类型的基础URL
        
        Args:
            api_type: API类型
            
        Returns:
            str: 基础URL
        """
        if cls.should_use_proxy(api_type):
            # 使用代理
            proxy_url = ProxyConfig.get_proxy_base_url()
            if proxy_url:
                return proxy_url
            else:
                # 代理不可用，回退到直连
                return APIConfig.BASE_URL
        else:
            # 直连
            return APIConfig.BASE_URL
    
    @classmethod
    def get_timeout(cls, api_type: str = 'other') -> int:
        """
        获取指定API类型的超时时间
        
        Args:
            api_type: API类型
            
        Returns:
            int: 超时时间（秒）
        """
        if cls.should_use_proxy(api_type):
            # 代理请求需要更长超时时间
            return ProxyConfig.PROXY_TIMEOUT
        else:
            # 直连使用标准超时时间
            return APIConfig.REQUEST_TIMEOUT
    
    @classmethod
    def get_strategy_info(cls) -> Dict[str, Any]:
        """
        获取当前策略信息
        
        Returns:
            Dict: 策略信息
        """
        proxy_enabled = ProxyConfig.ENABLE_PROXY
        proxy_host = ProxyConfig.PROXY_HOST if proxy_enabled else None
        
        return {
            'proxy_enabled': proxy_enabled,
            'proxy_host': proxy_host,
            'strategies': cls.API_STRATEGIES
        }
    
    @classmethod
    def get_reason(cls, api_type: str = 'other') -> str:
        """
        获取使用某种策略的原因
        
        Args:
            api_type: API类型
            
        Returns:
            str: 原因说明
        """
        strategy = cls.API_STRATEGIES.get(api_type, cls.API_STRATEGIES['other'])
        return strategy['reason']

def print_strategy_info():
    """打印当前API策略信息"""
    info = APIStrategy.get_strategy_info()
    print("🎯 API访问策略信息")
    print("=" * 50)
    print(f"代理是否启用: {info['proxy_enabled']}")
    print(f"代理服务器: {info['proxy_host']}")
    print()
    
    for api_type, strategy in info['strategies'].items():
        print(f"📋 {api_type.upper()} API:")
        print(f"   使用代理: {strategy['use_proxy']}")
        print(f"   基础URL: {strategy['base_url']}")
        print(f"   超时时间: {strategy['timeout']}秒")
        print(f"   原因: {strategy['reason']}")
        print()

if __name__ == "__main__":
    print_strategy_info() 