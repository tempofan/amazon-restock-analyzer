#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 检查当前公网IP地址
"""

import requests
import json
from datetime import datetime

def check_public_ip():
    """检查当前的公网IP地址"""
    
    # 多个IP查询服务
    services = [
        {
            'name': 'ipify',
            'url': 'https://api.ipify.org?format=json',
            'key': 'ip'
        },
        {
            'name': 'ip-api',
            'url': 'http://ip-api.com/json/',
            'key': 'query'
        },
        {
            'name': 'httpbin',
            'url': 'https://httpbin.org/ip',
            'key': 'origin'
        }
    ]
    
    results = {}
    
    print("🔍 检查当前公网IP地址...")
    print("=" * 50)
    
    for service in services:
        try:
            print(f"📡 查询 {service['name']}...")
            response = requests.get(service['url'], timeout=10)
            if response.status_code == 200:
                data = response.json()
                ip = data.get(service['key'], '未知')
                results[service['name']] = ip
                print(f"✅ {service['name']}: {ip}")
            else:
                print(f"❌ {service['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {service['name']}: {str(e)}")
    
    print("\n" + "=" * 50)
    print("📊 汇总结果:")
    
    # 统计最常见的IP
    ip_counts = {}
    for service, ip in results.items():
        if ip != '未知':
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
    
    if ip_counts:
        most_common_ip = max(ip_counts, key=ip_counts.get)
        print(f"🎯 当前公网IP: {most_common_ip}")
        
        # 检查是否匹配问题中的IP
        target_ip = "113.74.43.40"
        if most_common_ip == target_ip:
            print(f"✅ 确认: {target_ip} 就是你当前的公网IP!")
            print("💡 建议: 将此IP添加到领星ERP的API白名单中")
        else:
            print(f"⚠️  注意: 当前IP ({most_common_ip}) 与错误日志中的IP ({target_ip}) 不匹配")
            print("💡 可能原因:")
            print("   - 网络环境发生了变化")
            print("   - 使用了不同的网络出口")
            print("   - IP地址是动态分配的")
    else:
        print("❌ 无法获取公网IP地址")
    
    print(f"\n🕒 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return results

if __name__ == "__main__":
    check_public_ip() 