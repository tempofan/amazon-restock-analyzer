# -*- coding: utf-8 -*-
"""
🔍 网络连接诊断工具
用于诊断和解决网络连接问题
"""

import os
import sys
import time
import socket
import requests
import subprocess
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.proxy_config import ProxyConfig
from config.config import APIConfig

class NetworkDiagnostic:
    """
    🩺 网络诊断类
    检测各种网络连接问题并提供解决方案
    """
    
    def __init__(self):
        """初始化网络诊断工具"""
        self.results = {}
        self.recommendations = []
    
    def check_dns_resolution(self, hostname: str = "openapi.lingxing.com") -> Tuple[bool, Dict[str, Any]]:
        """
        检查DNS解析是否正常
        
        Args:
            hostname: 要检查的主机名
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 结果详情)
        """
        print(f"🔍 检查DNS解析: {hostname}")
        
        try:
            start_time = time.time()
            ip_address = socket.gethostbyname(hostname)
            response_time = time.time() - start_time
            
            result = {
                "hostname": hostname,
                "ip_address": ip_address,
                "response_time": round(response_time * 1000, 2),  # 毫秒
                "status": "success"
            }
            
            print(f"   ✅ DNS解析成功: {hostname} -> {ip_address} ({result['response_time']}ms)")
            return True, result
            
        except socket.gaierror as e:
            result = {
                "hostname": hostname,
                "error": str(e),
                "status": "failed"
            }
            
            print(f"   ❌ DNS解析失败: {e}")
            self.recommendations.append("📝 建议: 检查网络连接或更换DNS服务器（如：8.8.8.8，114.114.114.114）")
            return False, result
    
    def check_port_connectivity(self, hostname: str = "openapi.lingxing.com", port: int = 443) -> Tuple[bool, Dict[str, Any]]:
        """
        检查端口连通性
        
        Args:
            hostname: 主机名
            port: 端口号
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 结果详情)
        """
        print(f"🔌 检查端口连通性: {hostname}:{port}")
        
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result_code = sock.connect_ex((hostname, port))
            sock.close()
            response_time = time.time() - start_time
            
            if result_code == 0:
                result = {
                    "hostname": hostname,
                    "port": port,
                    "response_time": round(response_time * 1000, 2),
                    "status": "connected"
                }
                print(f"   ✅ 端口连通: {hostname}:{port} ({result['response_time']}ms)")
                return True, result
            else:
                result = {
                    "hostname": hostname,
                    "port": port,
                    "error_code": result_code,
                    "status": "failed"
                }
                print(f"   ❌ 端口连接失败: {hostname}:{port} (错误码: {result_code})")
                self.recommendations.append("📝 建议: 检查防火墙设置或网络代理配置")
                return False, result
                
        except Exception as e:
            result = {
                "hostname": hostname,
                "port": port,
                "error": str(e),
                "status": "error"
            }
            print(f"   ❌ 连接测试异常: {e}")
            return False, result
    
    def check_http_connectivity(self, url: str = "https://openapi.lingxing.com", timeout: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """
        检查HTTP连接
        
        Args:
            url: 要测试的URL
            timeout: 超时时间（秒）
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 结果详情)
        """
        print(f"🌐 检查HTTP连接: {url}")
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout, verify=True)
            response_time = time.time() - start_time
            
            result = {
                "url": url,
                "status_code": response.status_code,
                "response_time": round(response_time * 1000, 2),
                "headers": dict(response.headers),
                "status": "success" if response.status_code < 400 else "http_error"
            }
            
            if response.status_code < 400:
                print(f"   ✅ HTTP连接成功: {response.status_code} ({result['response_time']}ms)")
                return True, result
            else:
                print(f"   ⚠️ HTTP响应异常: {response.status_code} ({result['response_time']}ms)")
                return False, result
                
        except requests.exceptions.Timeout:
            result = {
                "url": url,
                "error": "连接超时",
                "timeout": timeout,
                "status": "timeout"
            }
            print(f"   ❌ HTTP连接超时: {timeout}秒")
            self.recommendations.append("📝 建议: 增加超时时间或检查网络速度")
            return False, result
            
        except requests.exceptions.ConnectionError as e:
            result = {
                "url": url,
                "error": str(e),
                "status": "connection_error"
            }
            print(f"   ❌ HTTP连接错误: {e}")
            self.recommendations.append("📝 建议: 检查网络连接或使用代理服务器")
            return False, result
            
        except Exception as e:
            result = {
                "url": url,
                "error": str(e),
                "status": "error"
            }
            print(f"   ❌ HTTP请求异常: {e}")
            return False, result
    
    def check_proxy_server(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查代理服务器状态
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 结果详情)
        """
        print("🌐 检查代理服务器状态")
        
        if not ProxyConfig.is_proxy_enabled():
            result = {
                "enabled": False,
                "message": "代理模式未启用",
                "status": "disabled"
            }
            print("   ℹ️ 代理模式未启用")
            return True, result
        
        # 检查代理配置
        is_valid, config_msg = ProxyConfig.validate_config()
        if not is_valid:
            result = {
                "enabled": True,
                "config_valid": False,
                "error": config_msg,
                "status": "config_error"
            }
            print(f"   ❌ 代理配置错误: {config_msg}")
            self.recommendations.append("📝 建议: 检查config/server.env中的代理配置")
            return False, result
        
        # 测试代理服务器连通性
        proxy_host = ProxyConfig.PROXY_HOST
        proxy_port = ProxyConfig.PROXY_PORT
        
        print(f"   🔍 测试代理服务器: {proxy_host}:{proxy_port}")
        port_ok, port_result = self.check_port_connectivity(proxy_host, proxy_port)
        
        if not port_ok:
            result = {
                "enabled": True,
                "config_valid": True,
                "proxy_host": proxy_host,
                "proxy_port": proxy_port,
                "port_check": port_result,
                "status": "unreachable"
            }
            print(f"   ❌ 无法连接到代理服务器")
            self.recommendations.append("📝 建议: 检查代理服务器是否运行正常")
            return False, result
        
        # 测试代理服务器健康检查
        health_url = ProxyConfig.get_health_check_url()
        if health_url:
            print(f"   🏥 测试代理健康检查: {health_url}")
            health_ok, health_result = self.check_http_connectivity(health_url, timeout=10)
            
            result = {
                "enabled": True,
                "config_valid": True,
                "proxy_host": proxy_host,
                "proxy_port": proxy_port,
                "port_check": port_result,
                "health_check": health_result,
                "status": "healthy" if health_ok else "unhealthy"
            }
            
            if health_ok:
                print("   ✅ 代理服务器运行正常")
                return True, result
            else:
                print("   ❌ 代理服务器健康检查失败")
                self.recommendations.append("📝 建议: 重启代理服务器或检查代理服务器日志")
                return False, result
        else:
            result = {
                "enabled": True,
                "config_valid": True,
                "proxy_host": proxy_host,
                "proxy_port": proxy_port,
                "port_check": port_result,
                "status": "accessible"
            }
            print("   ✅ 代理服务器可访问")
            return True, result
    
    def check_api_token(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查API Token状态
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 结果详情)
        """
        print("🔑 检查API Token状态")
        
        try:
            from auth.token_manager import TokenManager
            
            token_manager = TokenManager()
            token_info = token_manager.get_token_info()
            
            if not token_info:
                result = {
                    "has_token": False,
                    "message": "没有保存的Token",
                    "status": "no_token"
                }
                print("   ℹ️ 没有保存的Token，需要重新获取")
                return True, result
            
            result = {
                "has_token": True,
                "token_info": token_info,
                "is_expired": token_info.get("is_expired", True),
                "expires_at": token_info.get("expires_at_readable", "未知"),
                "status": "valid" if not token_info.get("is_expired", True) else "expired"
            }
            
            if token_info.get("is_expired", True):
                print(f"   ⚠️ Token已过期: {token_info.get('expires_at_readable', '未知')}")
                self.recommendations.append("📝 建议: Token已过期，程序将自动刷新")
            else:
                print(f"   ✅ Token有效: 过期时间 {token_info.get('expires_at_readable', '未知')}")
            
            return True, result
            
        except Exception as e:
            result = {
                "has_token": False,
                "error": str(e),
                "status": "error"
            }
            print(f"   ❌ Token检查异常: {e}")
            return False, result
    
    def check_network_speed(self) -> Dict[str, Any]:
        """
        检查网络速度（简单测试）
        
        Returns:
            Dict: 网络速度测试结果
        """
        print("⚡ 检查网络速度")
        
        test_urls = [
            "https://www.baidu.com",
            "https://www.qq.com", 
            "https://api.github.com"
        ]
        
        results = []
        
        for url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code < 400:
                    results.append({
                        "url": url,
                        "response_time": round(response_time * 1000, 2),
                        "status": "success"
                    })
                    print(f"   ✅ {url}: {round(response_time * 1000, 2)}ms")
                else:
                    results.append({
                        "url": url,
                        "status_code": response.status_code,
                        "status": "error"
                    })
                    print(f"   ❌ {url}: HTTP {response.status_code}")
                    
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "status": "failed"
                })
                print(f"   ❌ {url}: {str(e)}")
        
        # 计算平均响应时间
        successful_tests = [r for r in results if r.get("status") == "success"]
        if successful_tests:
            avg_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
            print(f"   📊 平均响应时间: {round(avg_time, 2)}ms")
            
            if avg_time > 3000:  # 超过3秒
                self.recommendations.append("📝 建议: 网络速度较慢，建议检查网络连接")
        
        return {
            "tests": results,
            "successful_count": len(successful_tests),
            "total_count": len(test_urls),
            "average_response_time": round(avg_time, 2) if successful_tests else None
        }
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """
        运行完整的网络诊断
        
        Returns:
            Dict: 完整诊断结果
        """
        print("🔍 开始网络连接诊断...")
        print("=" * 60)
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # 1. DNS解析测试
        dns_ok, dns_result = self.check_dns_resolution()
        self.results["tests"]["dns_resolution"] = dns_result
        
        print()
        
        # 2. 端口连通性测试
        port_ok, port_result = self.check_port_connectivity()
        self.results["tests"]["port_connectivity"] = port_result
        
        print()
        
        # 3. HTTP连接测试
        http_ok, http_result = self.check_http_connectivity()
        self.results["tests"]["http_connectivity"] = http_result
        
        print()
        
        # 4. 代理服务器检查
        proxy_ok, proxy_result = self.check_proxy_server()
        self.results["tests"]["proxy_server"] = proxy_result
        
        print()
        
        # 5. API Token检查
        token_ok, token_result = self.check_api_token()
        self.results["tests"]["api_token"] = token_result
        
        print()
        
        # 6. 网络速度测试
        speed_result = self.check_network_speed()
        self.results["tests"]["network_speed"] = speed_result
        
        print()
        print("=" * 60)
        
        # 生成诊断报告
        self.generate_diagnostic_report()
        
        return self.results
    
    def generate_diagnostic_report(self):
        """生成诊断报告和建议"""
        print("📋 诊断报告")
        print("-" * 40)
        
        # 统计测试结果
        tests = self.results["tests"]
        critical_issues = []
        warnings = []
        
        # DNS解析
        if tests["dns_resolution"]["status"] != "success":
            critical_issues.append("DNS解析失败")
        
        # 端口连通性
        if tests["port_connectivity"]["status"] != "connected":
            critical_issues.append("端口连接失败")
        
        # HTTP连接
        if tests["http_connectivity"]["status"] == "timeout":
            critical_issues.append("HTTP连接超时")
        elif tests["http_connectivity"]["status"] in ["connection_error", "error"]:
            critical_issues.append("HTTP连接错误")
        elif tests["http_connectivity"]["status"] == "http_error":
            warnings.append(f"HTTP响应错误: {tests['http_connectivity'].get('status_code')}")
        
        # 代理服务器
        proxy_status = tests["proxy_server"]["status"]
        if proxy_status in ["config_error", "unreachable", "unhealthy"]:
            if proxy_status == "config_error":
                critical_issues.append("代理配置错误")
            elif proxy_status == "unreachable":
                critical_issues.append("代理服务器不可达")
            elif proxy_status == "unhealthy":
                warnings.append("代理服务器健康检查失败")
        
        # Token状态
        if tests["api_token"]["status"] == "expired":
            warnings.append("API Token已过期")
        elif tests["api_token"]["status"] == "error":
            warnings.append("Token检查异常")
        
        # 输出问题汇总
        if critical_issues:
            print("🚨 严重问题:")
            for issue in critical_issues:
                print(f"   ❌ {issue}")
        
        if warnings:
            print("⚠️ 警告:")
            for warning in warnings:
                print(f"   ⚠️ {warning}")
        
        if not critical_issues and not warnings:
            print("✅ 所有检查均通过！")
        
        print()
        
        # 输出建议
        if self.recommendations:
            print("💡 解决建议:")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("✅ 网络连接正常，无需特别处理")
        
        print()
        
        # 根据问题提供具体解决方案
        if critical_issues or warnings:
            print("🔧 可能的解决方案:")
            
            if "DNS解析失败" in critical_issues:
                print("   🌐 DNS问题:")
                print("      - 更换DNS服务器（8.8.8.8, 114.114.114.114）")
                print("      - 检查网络连接")
                print("      - 使用手机热点测试")
            
            if any("连接" in issue for issue in critical_issues):
                print("   🔌 连接问题:")
                print("      - 检查防火墙设置")
                print("      - 尝试关闭VPN或代理")
                print("      - 使用移动网络测试")
                print("      - 联系网络管理员")
            
            if any("超时" in issue for issue in critical_issues):
                print("   ⏰ 超时问题:")
                print("      - 增加超时时间配置")
                print("      - 检查网络速度")
                print("      - 尝试不同时间段访问")
            
            if "代理" in " ".join(critical_issues + warnings):
                print("   🌐 代理问题:")
                print("      - 检查代理服务器是否运行")
                print("      - 验证代理服务器IP和端口")
                print("      - 临时禁用代理模式测试")
                print("      - 查看代理服务器日志")
        
        print("\n" + "=" * 60)

def main():
    """主函数"""
    print("🔍 网络连接诊断工具")
    print("用于诊断领星API连接问题")
    print()
    
    diagnostic = NetworkDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    # 保存诊断结果
    import json
    output_file = f"test/diagnostic_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        os.makedirs("test", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"📄 诊断结果已保存到: {output_file}")
    except Exception as e:
        print(f"⚠️ 保存诊断结果失败: {e}")

if __name__ == "__main__":
    main()