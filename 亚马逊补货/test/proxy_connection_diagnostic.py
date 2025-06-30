# -*- coding: utf-8 -*-
"""
🌐 云代理连接诊断工具
专门诊断云代理服务器连接问题
"""

import os
import sys
import socket
import requests
import subprocess
import platform
import time
from datetime import datetime
from typing import Dict, Any, Tuple, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
def load_env_file():
    """加载环境变量"""
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'server.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

from config.proxy_config import ProxyConfig

class ProxyConnectionDiagnostic:
    """
    🔍 云代理连接诊断器
    """
    
    def __init__(self):
        """初始化诊断器"""
        self.proxy_host = ProxyConfig.PROXY_HOST
        self.proxy_port = ProxyConfig.PROXY_PORT
        self.proxy_protocol = ProxyConfig.PROXY_PROTOCOL
        self.proxy_enabled = ProxyConfig.is_proxy_enabled()
        self.issues_found = []
        self.solutions = []
    
    def check_proxy_config(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查代理配置
        
        Returns:
            Tuple[bool, Dict]: (是否正确, 配置信息)
        """
        print("🔧 检查云代理配置...")
        
        config_info = {
            'enabled': self.proxy_enabled,
            'host': self.proxy_host,
            'port': self.proxy_port,
            'protocol': self.proxy_protocol,
            'base_url': ProxyConfig.get_proxy_base_url(),
            'health_url': ProxyConfig.get_health_check_url()
        }
        
        print(f"   📋 代理配置:")
        print(f"      启用状态: {'✅ 已启用' if self.proxy_enabled else '❌ 未启用'}")
        print(f"      服务器地址: {self.proxy_host}")
        print(f"      端口: {self.proxy_port}")
        print(f"      协议: {self.proxy_protocol}")
        print(f"      完整URL: {config_info['base_url']}")
        
        if not self.proxy_enabled:
            print("   ❌ 代理模式未启用")
            self.issues_found.append("代理模式未启用")
            return False, config_info
        
        if not self.proxy_host:
            print("   ❌ 代理服务器地址未配置")
            self.issues_found.append("代理服务器地址未配置")
            return False, config_info
        
        print("   ✅ 代理配置正确")
        return True, config_info
    
    def check_proxy_server_connectivity(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查云代理服务器连通性
        
        Returns:
            Tuple[bool, Dict]: (是否连通, 连接信息)
        """
        print(f"\n🌐 检查云代理服务器连通性: {self.proxy_host}:{self.proxy_port}")
        
        # 1. DNS解析测试
        try:
            resolved_ip = socket.gethostbyname(self.proxy_host)
            print(f"   ✅ DNS解析成功: {self.proxy_host} -> {resolved_ip}")
            dns_ok = True
        except Exception as e:
            print(f"   ❌ DNS解析失败: {e}")
            self.issues_found.append("云代理服务器DNS解析失败")
            dns_ok = False
        
        # 2. Ping测试
        ping_ok = False
        try:
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '4', self.proxy_host]
            else:
                cmd = ['ping', '-c', '4', self.proxy_host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            ping_ok = result.returncode == 0
            
            if ping_ok:
                print(f"   ✅ Ping测试成功")
            else:
                print(f"   ❌ Ping测试失败")
                self.issues_found.append("云代理服务器Ping不通")
                
        except Exception as e:
            print(f"   ⚠️ Ping测试异常: {e}")
        
        # 3. TCP端口连通性测试
        tcp_ok = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            start_time = time.time()
            result = sock.connect_ex((self.proxy_host, self.proxy_port))
            response_time = time.time() - start_time
            sock.close()
            
            tcp_ok = result == 0
            
            if tcp_ok:
                print(f"   ✅ TCP端口{self.proxy_port}连通正常 ({response_time:.2f}s)")
            else:
                print(f"   ❌ TCP端口{self.proxy_port}连接失败 (错误码: {result})")
                self.issues_found.append(f"云代理服务器端口{self.proxy_port}不可达")
                
        except Exception as e:
            print(f"   ❌ TCP连接测试异常: {e}")
            self.issues_found.append("云代理服务器TCP连接异常")
        
        connectivity_info = {
            'dns_ok': dns_ok,
            'ping_ok': ping_ok,
            'tcp_ok': tcp_ok,
            'resolved_ip': resolved_ip if dns_ok else None
        }
        
        return tcp_ok, connectivity_info
    
    def check_proxy_server_health(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查云代理服务器健康状态
        
        Returns:
            Tuple[bool, Dict]: (是否健康, 健康信息)
        """
        print(f"\n🏥 检查云代理服务器健康状态...")
        
        health_url = ProxyConfig.get_health_check_url()
        if not health_url:
            print("   ⚠️ 健康检查URL未配置")
            return False, {'error': '健康检查URL未配置'}
        
        print(f"   🔍 健康检查URL: {health_url}")
        
        try:
            start_time = time.time()
            response = requests.get(health_url, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    print(f"   ✅ 代理服务器运行正常 ({response_time:.2f}s)")
                    print(f"   📊 服务器状态: {health_data.get('status', '未知')}")
                    
                    if 'uptime' in health_data:
                        print(f"   ⏰ 运行时间: {health_data['uptime']}")
                    
                    return True, {
                        'status': 'healthy',
                        'response_time': response_time,
                        'health_data': health_data
                    }
                except:
                    print(f"   ✅ 代理服务器响应正常，但健康数据格式异常")
                    return True, {
                        'status': 'responding',
                        'response_time': response_time,
                        'raw_response': response.text[:200]
                    }
            else:
                print(f"   ❌ 代理服务器响应异常: HTTP {response.status_code}")
                self.issues_found.append(f"云代理服务器响应异常: {response.status_code}")
                return False, {
                    'status': 'unhealthy',
                    'status_code': response.status_code,
                    'response_time': response_time
                }
                
        except requests.exceptions.Timeout:
            print(f"   ❌ 代理服务器健康检查超时")
            self.issues_found.append("云代理服务器健康检查超时")
            return False, {'status': 'timeout'}
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ 无法连接到代理服务器: {e}")
            self.issues_found.append("无法连接到云代理服务器")
            return False, {'status': 'connection_error', 'error': str(e)}
            
        except Exception as e:
            print(f"   ❌ 健康检查异常: {e}")
            self.issues_found.append("云代理服务器健康检查异常")
            return False, {'status': 'error', 'error': str(e)}
    
    def check_proxy_api_forwarding(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查代理服务器的API转发功能
        
        Returns:
            Tuple[bool, Dict]: (是否正常, 转发信息)
        """
        print(f"\n🔄 检查代理API转发功能...")
        
        proxy_base_url = ProxyConfig.get_proxy_base_url()
        if not proxy_base_url:
            print("   ❌ 代理基础URL未配置")
            return False, {'error': '代理基础URL未配置'}
        
        # 测试简单的API转发
        test_endpoint = f"{proxy_base_url}/api/auth-server/oauth/access-token"
        print(f"   🧪 测试API转发: {test_endpoint}")
        
        try:
            # 发送一个简单的GET请求测试转发
            response = requests.get(test_endpoint, timeout=30)
            
            forwarding_info = {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'headers': dict(response.headers)
            }
            
            # 检查是否有代理服务器的标识头
            if 'X-Proxy-Server' in response.headers:
                print(f"   ✅ API转发正常，代理服务器标识: {response.headers['X-Proxy-Server']}")
                return True, forwarding_info
            elif response.status_code < 500:
                print(f"   ✅ API转发正常 (HTTP {response.status_code})")
                return True, forwarding_info
            else:
                print(f"   ⚠️ API转发异常 (HTTP {response.status_code})")
                self.issues_found.append(f"API转发异常: {response.status_code}")
                return False, forwarding_info
                
        except requests.exceptions.Timeout:
            print(f"   ❌ API转发测试超时")
            self.issues_found.append("API转发测试超时")
            return False, {'status': 'timeout'}
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ API转发连接失败: {e}")
            self.issues_found.append("API转发连接失败")
            return False, {'status': 'connection_error', 'error': str(e)}
            
        except Exception as e:
            print(f"   ❌ API转发测试异常: {e}")
            self.issues_found.append("API转发测试异常")
            return False, {'status': 'error', 'error': str(e)}
    
    def analyze_network_environment(self) -> Dict[str, Any]:
        """
        分析当前网络环境
        
        Returns:
            Dict: 网络环境分析结果
        """
        print(f"\n🌍 分析当前网络环境...")
        
        analysis = {}
        
        # 检查当前公网IP
        try:
            response = requests.get("https://httpbin.org/ip", timeout=10)
            if response.status_code == 200:
                current_ip = response.json().get('origin', '未知')
                print(f"   🌐 当前公网IP: {current_ip}")
                analysis['current_ip'] = current_ip
            else:
                print(f"   ⚠️ 无法获取公网IP")
                analysis['current_ip'] = '未知'
        except Exception as e:
            print(f"   ⚠️ 获取公网IP失败: {e}")
            analysis['current_ip'] = '获取失败'
        
        # 检查网络类型
        try:
            # 通过网络接口判断网络类型
            import psutil
            interfaces = psutil.net_if_addrs()
            wifi_found = any('wi-fi' in name.lower() or 'wlan' in name.lower() for name in interfaces.keys())
            ethernet_found = any('ethernet' in name.lower() or 'eth' in name.lower() for name in interfaces.keys())
            
            if wifi_found:
                print(f"   📶 检测到WiFi连接")
                analysis['connection_type'] = 'WiFi'
            elif ethernet_found:
                print(f"   🔌 检测到有线连接")
                analysis['connection_type'] = '有线'
            else:
                print(f"   ❓ 未识别的连接类型")
                analysis['connection_type'] = '未知'
        except:
            analysis['connection_type'] = '未知'
        
        # 测试网络速度
        test_sites = [
            ("百度", "https://www.baidu.com"),
            ("腾讯", "https://www.qq.com"), 
            ("阿里", "https://www.taobao.com")
        ]
        
        speeds = []
        for name, url in test_sites:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code < 400:
                    speeds.append(response_time)
                    print(f"   ✅ {name}: {response_time:.0f}ms")
                else:
                    print(f"   ❌ {name}: HTTP {response.status_code}")
            except:
                print(f"   ❌ {name}: 连接失败")
        
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            analysis['average_speed'] = avg_speed
            print(f"   📊 平均响应时间: {avg_speed:.0f}ms")
            
            if avg_speed > 3000:
                print(f"   ⚠️ 网络速度较慢")
                self.issues_found.append("当前网络速度较慢")
        else:
            analysis['average_speed'] = None
            print(f"   ❌ 网络连接异常")
            self.issues_found.append("当前网络连接异常")
        
        return analysis
    
    def generate_solutions(self) -> List[Dict[str, Any]]:
        """
        根据发现的问题生成解决方案
        
        Returns:
            List[Dict]: 解决方案列表
        """
        print(f"\n🔧 生成针对性解决方案...")
        
        solutions = []
        
        if "云代理服务器DNS解析失败" in self.issues_found:
            solutions.append({
                'priority': 1,
                'title': '修复DNS解析问题',
                'description': '云代理服务器域名无法解析',
                'steps': [
                    '更换DNS服务器（8.8.8.8, 114.114.114.114）',
                    '检查代理服务器域名是否正确',
                    '尝试直接使用IP地址'
                ]
            })
        
        if any("端口" in issue for issue in self.issues_found):
            solutions.append({
                'priority': 1,
                'title': '解决端口连接问题',
                'description': '当前网络环境阻止了对云代理服务器端口的访问',
                'steps': [
                    '检查企业防火墙是否阻止了8080端口',
                    '尝试使用手机热点测试',
                    '联系网络管理员开放端口访问',
                    '考虑更换云代理服务器端口（如443, 80）'
                ]
            })
        
        if "云代理服务器Ping不通" in self.issues_found:
            solutions.append({
                'priority': 2,
                'title': '网络连通性问题',
                'description': '当前网络无法访问云代理服务器',
                'steps': [
                    '确认云代理服务器是否正常运行',
                    '检查云代理服务器防火墙设置',
                    '尝试更换网络环境（如手机热点）',
                    '联系云服务商检查网络状态'
                ]
            })
        
        if any("超时" in issue for issue in self.issues_found):
            solutions.append({
                'priority': 2,
                'title': '解决连接超时问题',
                'description': '连接云代理服务器超时',
                'steps': [
                    '增加连接超时时间配置',
                    '检查当前网络速度和稳定性',
                    '尝试在网络较好的时间段使用',
                    '考虑更换云代理服务器地区'
                ]
            })
        
        if "当前网络连接异常" in self.issues_found:
            solutions.append({
                'priority': 1,
                'title': '修复网络连接',
                'description': '当前网络环境存在问题',
                'steps': [
                    '检查网络连接设置',
                    '重启路由器和网络适配器',
                    '尝试使用手机热点',
                    '联系网络供应商'
                ]
            })
        
        # 如果没有具体问题，提供通用解决方案
        if not solutions:
            solutions.append({
                'priority': 1,
                'title': '验证云代理服务器状态',
                'description': '检查云代理服务器是否正常运行',
                'steps': [
                    '登录云服务器检查代理服务状态',
                    '重启云代理服务',
                    '检查云服务器防火墙设置',
                    '验证领星ERP白名单配置'
                ]
            })
        
        return solutions
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """
        运行完整的云代理连接诊断
        
        Returns:
            Dict: 完整诊断结果
        """
        print("🔍 云代理连接问题诊断")
        print("=" * 70)
        print(f"目标云代理服务器: {self.proxy_host}:{self.proxy_port}")
        print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 重置问题列表
        self.issues_found = []
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'proxy_config': {},
            'connectivity': {},
            'health_check': {},
            'api_forwarding': {},
            'network_environment': {},
            'issues': [],
            'solutions': []
        }
        
        # 1. 检查代理配置
        config_ok, config_info = self.check_proxy_config()
        results['proxy_config'] = config_info
        
        if not config_ok:
            print("\n❌ 代理配置有问题，无法继续检查")
            results['issues'] = self.issues_found
            return results
        
        # 2. 检查服务器连通性
        connectivity_ok, connectivity_info = self.check_proxy_server_connectivity()
        results['connectivity'] = connectivity_info
        
        # 3. 检查服务器健康状态
        if connectivity_ok:
            health_ok, health_info = self.check_proxy_server_health()
            results['health_check'] = health_info
            
            # 4. 检查API转发功能
            if health_ok:
                forwarding_ok, forwarding_info = self.check_proxy_api_forwarding()
                results['api_forwarding'] = forwarding_info
        
        # 5. 分析网络环境
        network_analysis = self.analyze_network_environment()
        results['network_environment'] = network_analysis
        
        # 6. 生成解决方案
        solutions = self.generate_solutions()
        results['solutions'] = solutions
        results['issues'] = self.issues_found
        
        # 生成诊断报告
        self.generate_diagnostic_report(results)
        
        return results
    
    def generate_diagnostic_report(self, results: Dict[str, Any]):
        """
        生成诊断报告
        
        Args:
            results: 诊断结果
        """
        print("\n" + "=" * 70)
        print("📋 云代理连接诊断报告")
        print("-" * 40)
        
        # 问题汇总
        if self.issues_found:
            print("🚨 发现的问题:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"   {i}. {issue}")
        else:
            print("✅ 未发现明显问题")
        
        print()
        
        # 连接状态汇总
        print("📊 连接状态汇总:")
        connectivity = results.get('connectivity', {})
        print(f"   DNS解析: {'✅' if connectivity.get('dns_ok') else '❌'}")
        print(f"   Ping连通: {'✅' if connectivity.get('ping_ok') else '❌'}")
        print(f"   TCP连接: {'✅' if connectivity.get('tcp_ok') else '❌'}")
        
        health = results.get('health_check', {})
        if health:
            health_status = health.get('status', 'unknown')
            print(f"   服务健康: {'✅' if health_status in ['healthy', 'responding'] else '❌'}")
        
        forwarding = results.get('api_forwarding', {})
        if forwarding and 'status_code' in forwarding:
            print(f"   API转发: {'✅' if forwarding.get('status_code', 500) < 500 else '❌'}")
        
        print()
        
        # 解决方案
        solutions = results.get('solutions', [])
        if solutions:
            print("💡 推荐解决方案:")
            for solution in solutions:
                print(f"\n🔧 {solution['title']}:")
                print(f"   描述: {solution['description']}")
                print("   步骤:")
                for step in solution['steps']:
                    print(f"   - {step}")
        
        print("\n🎯 下一步建议:")
        if not self.issues_found:
            print("   ✅ 云代理连接正常，问题可能在其他地方")
            print("   💡 尝试直接运行: python main.py --test")
        elif "端口" in " ".join(self.issues_found):
            print("   🔧 主要问题是端口访问被阻止")
            print("   📱 建议先用手机热点测试")
            print("   🏢 如在企业网络，联系IT部门开放端口")
        elif "连接" in " ".join(self.issues_found):
            print("   🌐 主要问题是网络连通性")
            print("   🔍 检查云代理服务器是否正常运行")
            print("   📱 尝试更换网络环境测试")
        
        print("\n" + "=" * 70)

def main():
    """主函数"""
    print("🌐 云代理连接诊断工具")
    print("专门诊断云代理服务器连接问题")
    print()
    
    diagnostic = ProxyConnectionDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    # 保存诊断结果
    import json
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"test/proxy_diagnostic_result_{timestamp}.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 诊断结果已保存: {output_file}")
    except Exception as e:
        print(f"⚠️ 保存诊断结果失败: {e}")

if __name__ == "__main__":
    main()