#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查环境变量加载情况"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🔍 检查环境变量加载情况")
print("="*50)

print("📁 当前工作目录:", os.getcwd())
print("📄 配置文件路径:", os.path.abspath('config/server.env'))
print("📄 配置文件存在:", os.path.exists('config/server.env'))
print()

print("⏳ 加载前的环境变量:")
print(f"  PROXY_HOST: {os.getenv('PROXY_HOST', '未设置')}")
print(f"  ENABLE_PROXY: {os.getenv('ENABLE_PROXY', '未设置')}")
print()

# 加载环境变量
result = load_dotenv('config/server.env')
print(f"📦 环境变量加载结果: {result}")
print()

print("✅ 加载后的环境变量:")
print(f"  PROXY_HOST: {os.getenv('PROXY_HOST', '未设置')}")
print(f"  ENABLE_PROXY: {os.getenv('ENABLE_PROXY', '未设置')}")
print(f"  PROXY_PORT: {os.getenv('PROXY_PORT', '未设置')}")
print(f"  PROXY_PROTOCOL: {os.getenv('PROXY_PROTOCOL', '未设置')}")
print()

# 测试ProxyConfig
try:
    from config.proxy_config import ProxyConfig
    print("🌐 ProxyConfig状态:")
    print(f"  ENABLE_PROXY: {ProxyConfig.ENABLE_PROXY}")
    print(f"  PROXY_HOST: '{ProxyConfig.PROXY_HOST}'")
    print(f"  PROXY_PORT: {ProxyConfig.PROXY_PORT}")
    print(f"  is_proxy_enabled(): {ProxyConfig.is_proxy_enabled()}")
    
    if ProxyConfig.is_proxy_enabled():
        print(f"  代理URL: {ProxyConfig.get_proxy_base_url()}")
        print(f"  健康检查URL: {ProxyConfig.get_health_check_url()}")
    
    valid, msg = ProxyConfig.validate_config()
    print(f"  配置有效性: {valid} - {msg}")
    
except Exception as e:
    print(f"❌ ProxyConfig错误: {e}") 