# -*- coding: utf-8 -*-
"""
🔍 根本原因分析和解决方案
分析网络连接问题的根本原因并提供永久性解决方案
"""

import os
import sys
import socket
import requests
import subprocess
import platform
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RootCauseAnalyzer:
    """
    🧬 根本原因分析器
    深入分析网络连接问题的根本原因
    """
    
    def __init__(self):
        """初始化分析器"""
        self.target_host = "openapi.lingxing.com"
        self.target_ip = "106.55.220.245"
        self.target_port = 443
        self.analysis_results = {}
        self.root_causes = []
        self.solutions = []
    
    def analyze_network_layer(self) -> Dict:
        """
        分析网络层问题
        
        Returns:
            Dict: 网络层分析结果
        """
        print("🌐 分析网络层连接...")
        results = {}
        
        # 1. DNS解析测试
        try:
            resolved_ip = socket.gethostbyname(self.target_host)
            results['dns_resolution'] = {
                'status': 'success',
                'resolved_ip': resolved_ip,
                'matches_expected': resolved_ip == self.target_ip
            }
            print(f"   ✅ DNS解析正常: {self.target_host} -> {resolved_ip}")
        except Exception as e:
            results['dns_resolution'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"   ❌ DNS解析失败: {e}")
            self.root_causes.append("DNS解析问题")
        
        # 2. ICMP连通性测试
        try:
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '4', self.target_ip]
            else:
                cmd = ['ping', '-c', '4', self.target_ip]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            ping_success = result.returncode == 0
            
            results['icmp_connectivity'] = {
                'status': 'success' if ping_success else 'failed',
                'output': result.stdout if ping_success else result.stderr
            }
            
            if ping_success:
                print(f"   ✅ ICMP连通性正常")
            else:
                print(f"   ❌ ICMP连通性失败")
                self.root_causes.append("ICMP被阻止")
                
        except Exception as e:
            results['icmp_connectivity'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ⚠️ ICMP测试异常: {e}")
        
        # 3. TCP端口连通性测试
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.target_ip, self.target_port))
            sock.close()
            
            tcp_success = result == 0
            results['tcp_connectivity'] = {
                'status': 'success' if tcp_success else 'failed',
                'error_code': result if not tcp_success else None
            }
            
            if tcp_success:
                print(f"   ✅ TCP端口{self.target_port}连通正常")
            else:
                print(f"   ❌ TCP端口{self.target_port}连接失败 (错误码: {result})")
                self.root_causes.append(f"TCP端口{self.target_port}被阻止")
                
        except Exception as e:
            results['tcp_connectivity'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ TCP连接测试异常: {e}")
        
        return results
    
    def analyze_ssl_tls_layer(self) -> Dict:
        """
        分析SSL/TLS层问题
        
        Returns:
            Dict: SSL/TLS层分析结果
        """
        print("\n🔒 分析SSL/TLS层...")
        results = {}
        
        try:
            import ssl
            
            # 创建SSL上下文
            context = ssl.create_default_context()
            
            # 尝试SSL握手
            with socket.create_connection((self.target_ip, self.target_port), timeout=30) as sock:
                with context.wrap_socket(sock, server_hostname=self.target_host) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    results['ssl_handshake'] = {
                        'status': 'success',
                        'certificate': {
                            'subject': dict(x[0] for x in cert['subject']),
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'version': cert['version'],
                            'expires': cert['notAfter']
                        },
                        'cipher': cipher
                    }
                    
                    print(f"   ✅ SSL/TLS握手成功")
                    print(f"   📄 证书主体: {cert['subject']}")
                    print(f"   🔐 加密套件: {cipher}")
                    
        except ssl.SSLError as e:
            results['ssl_handshake'] = {
                'status': 'ssl_error',
                'error': str(e)
            }
            print(f"   ❌ SSL/TLS握手失败: {e}")
            self.root_causes.append("SSL/TLS握手问题")
            
        except socket.timeout:
            results['ssl_handshake'] = {
                'status': 'timeout',
                'error': 'SSL握手超时'
            }
            print(f"   ❌ SSL/TLS握手超时")
            self.root_causes.append("SSL/TLS连接超时")
            
        except Exception as e:
            results['ssl_handshake'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ SSL/TLS测试异常: {e}")
        
        return results
    
    def analyze_http_layer(self) -> Dict:
        """
        分析HTTP层问题
        
        Returns:
            Dict: HTTP层分析结果
        """
        print("\n🌍 分析HTTP层...")
        results = {}
        
        # 测试不同的HTTP客户端配置
        test_configs = [
            {
                'name': '默认配置',
                'config': {'timeout': 30, 'verify': True}
            },
            {
                'name': '禁用SSL验证',
                'config': {'timeout': 30, 'verify': False}
            },
            {
                'name': '自定义User-Agent',
                'config': {
                    'timeout': 30, 
                    'verify': True,
                    'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                }
            },
            {
                'name': '使用HTTP/1.1',
                'config': {
                    'timeout': 30, 
                    'verify': True,
                    'headers': {'Connection': 'close'}
                }
            }
        ]
        
        for test_config in test_configs:
            print(f"   🧪 测试 {test_config['name']}...")
            
            try:
                url = f"https://{self.target_host}"
                response = requests.get(url, **test_config['config'])
                
                results[test_config['name']] = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'response_time': response.elapsed.total_seconds()
                }
                
                print(f"      ✅ 成功: HTTP {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                return results  # 如果有一个成功，就返回
                
            except requests.exceptions.Timeout:
                results[test_config['name']] = {
                    'status': 'timeout',
                    'error': 'HTTP请求超时'
                }
                print(f"      ❌ 超时")
                
            except requests.exceptions.SSLError as e:
                results[test_config['name']] = {
                    'status': 'ssl_error',
                    'error': str(e)
                }
                print(f"      ❌ SSL错误: {e}")
                
            except requests.exceptions.ConnectionError as e:
                results[test_config['name']] = {
                    'status': 'connection_error',
                    'error': str(e)
                }
                print(f"      ❌ 连接错误: {e}")
                
            except Exception as e:
                results[test_config['name']] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"      ❌ 其他错误: {e}")
        
        # 如果所有HTTP测试都失败了
        if not any(r.get('status') == 'success' for r in results.values()):
            self.root_causes.append("HTTP层连接被阻止")
        
        return results
    
    def analyze_firewall_proxy(self) -> Dict:
        """
        分析防火墙和代理设置
        
        Returns:
            Dict: 防火墙和代理分析结果
        """
        print("\n🛡️ 分析防火墙和代理设置...")
        results = {}
        
        # 检查系统代理设置
        try:
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            results['system_proxy'] = {
                'http_proxy': http_proxy,
                'https_proxy': https_proxy,
                'has_proxy': bool(http_proxy or https_proxy)
            }
            
            if http_proxy or https_proxy:
                print(f"   🌐 检测到系统代理:")
                if http_proxy:
                    print(f"      HTTP: {http_proxy}")
                if https_proxy:
                    print(f"      HTTPS: {https_proxy}")
                self.root_causes.append("系统代理可能干扰连接")
            else:
                print(f"   ℹ️ 未检测到系统代理")
                
        except Exception as e:
            results['system_proxy'] = {'error': str(e)}
            print(f"   ⚠️ 代理检查异常: {e}")
        
        # 检查Windows防火墙（如果是Windows系统）
        if platform.system().lower() == 'windows':
            try:
                # 检查防火墙状态
                cmd = ['netsh', 'advfirewall', 'show', 'allprofiles', 'state']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                results['windows_firewall'] = {
                    'status': 'checked',
                    'output': result.stdout if result.returncode == 0 else result.stderr
                }
                
                if result.returncode == 0:
                    if '开启' in result.stdout or 'ON' in result.stdout.upper():
                        print(f"   🛡️ Windows防火墙已启用")
                        self.root_causes.append("Windows防火墙可能阻止连接")
                    else:
                        print(f"   ℹ️ Windows防火墙已关闭")
                else:
                    print(f"   ⚠️ 无法检查防火墙状态")
                    
            except Exception as e:
                results['windows_firewall'] = {'error': str(e)}
                print(f"   ⚠️ 防火墙检查异常: {e}")
        
        return results
    
    def generate_solutions(self) -> List[Dict]:
        """
        根据根本原因生成解决方案
        
        Returns:
            List[Dict]: 解决方案列表
        """
        print("\n🔧 生成解决方案...")
        solutions = []
        
        # 根据不同的根本原因提供解决方案
        if "TCP端口443被阻止" in self.root_causes:
            solutions.append({
                'priority': 1,
                'title': '配置企业防火墙例外',
                'description': 'TCP端口443被企业防火墙阻止',
                'steps': [
                    '联系网络管理员',
                    f'请求将 {self.target_host} (IP: {self.target_ip}) 添加到防火墙白名单',
                    '或者请求开放对端口443的HTTPS访问',
                    '如果是企业环境，可能需要提交IT工单'
                ],
                'type': 'infrastructure'
            })
        
        if "SSL/TLS握手问题" in self.root_causes or "SSL/TLS连接超时" in self.root_causes:
            solutions.append({
                'priority': 2,
                'title': '配置SSL/TLS策略',
                'description': 'SSL/TLS连接被安全策略阻止',
                'steps': [
                    '检查企业SSL/TLS策略设置',
                    '请求网络管理员调整SSL检查设置',
                    '如果使用了SSL代理，需要配置证书信任',
                    '考虑在受信任的网络环境中运行程序'
                ],
                'type': 'security'
            })
        
        if "HTTP层连接被阻止" in self.root_causes:
            solutions.append({
                'priority': 3,
                'title': '配置应用层代理',
                'description': 'HTTP层被应用防火墙阻止',
                'steps': [
                    '配置企业HTTP代理服务器',
                    '在代理服务器中添加领星API白名单',
                    '配置程序使用企业代理',
                    '或者部署云代理服务器方案'
                ],
                'type': 'proxy'
            })
        
        if "系统代理可能干扰连接" in self.root_causes:
            solutions.append({
                'priority': 4,
                'title': '优化代理配置',
                'description': '系统代理配置冲突',
                'steps': [
                    '检查系统代理设置是否正确',
                    '确保代理服务器支持HTTPS',
                    '在代理服务器中配置领星API例外',
                    '或者临时禁用系统代理进行测试'
                ],
                'type': 'configuration'
            })
        
        if "Windows防火墙可能阻止连接" in self.root_causes:
            solutions.append({
                'priority': 5,
                'title': 'Windows防火墙配置',
                'description': 'Windows防火墙阻止出站连接',
                'steps': [
                    '打开Windows防火墙高级设置',
                    '添加出站规则允许Python.exe访问网络',
                    f'或者添加特定规则允许访问 {self.target_host}:443',
                    '确保规则应用于所有网络配置文件'
                ],
                'type': 'local_firewall'
            })
        
        # 如果没有明确的根本原因，提供通用解决方案
        if not self.root_causes:
            solutions.extend([
                {
                    'priority': 1,
                    'title': '部署云代理服务器（推荐）',
                    'description': '通过云服务器代理访问领星API',
                    'steps': [
                        '购买一台有公网IP的云服务器（腾讯云、阿里云等）',
                        '在云服务器上部署代理服务',
                        '在领星ERP后台将云服务器IP添加到白名单',
                        '配置本地程序使用云代理'
                    ],
                    'type': 'cloud_proxy'
                },
                {
                    'priority': 2,
                    'title': '更换网络环境',
                    'description': '使用不受限制的网络环境',
                    'steps': [
                        '尝试使用手机热点运行程序',
                        '在家庭网络环境中测试',
                        '如果在企业网络，申请网络例外',
                        '考虑使用专业VPN服务'
                    ],
                    'type': 'network_change'
                },
                {
                    'priority': 3,
                    'title': '企业IT支持',
                    'description': '寻求企业IT部门支持',
                    'steps': [
                        '联系企业IT支持部门',
                        '说明业务需求和技术要求',
                        '请求配置网络例外或专用连接',
                        '提供领星API的技术文档'
                    ],
                    'type': 'it_support'
                }
            ])
        
        return solutions
    
    def generate_implementation_guide(self, solutions: List[Dict]) -> str:
        """
        生成实施指南
        
        Args:
            solutions: 解决方案列表
            
        Returns:
            str: 实施指南文本
        """
        guide = f"""
# 🔧 根本问题解决方案实施指南

## 📊 问题分析总结

**目标服务器**: {self.target_host} ({self.target_ip})
**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 🔍 检测到的根本原因:
"""
        
        if self.root_causes:
            for i, cause in enumerate(self.root_causes, 1):
                guide += f"{i}. {cause}\n"
        else:
            guide += "未检测到明确的根本原因，可能是复合性网络限制问题。\n"
        
        guide += "\n## 🎯 推荐解决方案\n\n"
        
        for solution in sorted(solutions, key=lambda x: x['priority']):
            guide += f"### {solution['priority']}. {solution['title']} ({solution['type']})\n\n"
            guide += f"**问题描述**: {solution['description']}\n\n"
            guide += "**实施步骤**:\n"
            
            for step in solution['steps']:
                guide += f"- {step}\n"
            
            guide += "\n---\n\n"
        
        guide += """
## 🚀 立即可行的方案

### 方案A: 云代理服务器（最佳方案）
这是最可靠的解决方案，已经为你准备好了完整的部署脚本：

1. **购买云服务器**（推荐配置）:
   - CPU: 1核2G 或更高
   - 带宽: 5Mbps 或更高  
   - 系统: Ubuntu 20.04 LTS
   - 提供商: 腾讯云、阿里云、华为云等

2. **部署代理服务**:
   ```bash
   # 上传部署脚本到云服务器
   scp deploy/deploy_cloud_proxy.sh user@your-server:/opt/
   
   # 在云服务器上运行
   chmod +x /opt/deploy_cloud_proxy.sh
   sudo /opt/deploy_cloud_proxy.sh
   ```

3. **配置白名单**:
   - 登录领星ERP后台
   - 将云服务器IP添加到API白名单

4. **本地配置**:
   ```env
   # 修改 config/server.env
   ENABLE_PROXY=True
   PROXY_HOST=你的云服务器IP
   PROXY_PORT=8080
   ```

### 方案B: 网络环境变更
如果无法使用云代理，尝试：
1. 使用手机热点测试程序是否正常
2. 在家庭网络环境中运行
3. 联系网络管理员申请例外

### 方案C: 企业IT支持
如果在企业环境中：
1. 提交IT工单说明业务需求
2. 提供领星API的技术要求文档
3. 申请网络例外或专用连接

## 📞 技术支持

如果需要进一步的技术支持，请提供：
1. 网络环境描述（家庭/企业/其他）
2. 是否有企业代理或防火墙
3. 具体的错误信息和日志
4. 诊断结果文件

## ⚡ 快速验证

实施解决方案后，使用以下命令验证：
```bash
# 测试连接
python main.py --test

# 运行完整诊断
python test/network_diagnostic.py

# 测试API功能
python main.py --interactive
```
"""
        
        return guide
    
    def run_full_analysis(self) -> Dict:
        """
        运行完整的根本原因分析
        
        Returns:
            Dict: 完整分析结果
        """
        print("🔍 开始根本原因分析...")
        print("=" * 70)
        
        # 重置分析结果
        self.root_causes = []
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'target_host': self.target_host,
            'target_ip': self.target_ip,
            'analysis': {}
        }
        
        # 逐层分析
        self.analysis_results['analysis']['network_layer'] = self.analyze_network_layer()
        self.analysis_results['analysis']['ssl_tls_layer'] = self.analyze_ssl_tls_layer()
        self.analysis_results['analysis']['http_layer'] = self.analyze_http_layer()
        self.analysis_results['analysis']['firewall_proxy'] = self.analyze_firewall_proxy()
        
        # 生成解决方案
        solutions = self.generate_solutions()
        self.analysis_results['solutions'] = solutions
        
        # 生成实施指南
        implementation_guide = self.generate_implementation_guide(solutions)
        
        print("\n" + "=" * 70)
        print("📋 根本原因分析完成")
        print("-" * 40)
        
        if self.root_causes:
            print("🔍 发现的根本原因:")
            for i, cause in enumerate(self.root_causes, 1):
                print(f"   {i}. {cause}")
        else:
            print("ℹ️ 未检测到明确的单一根本原因")
            print("   可能是多层网络限制的组合问题")
        
        print(f"\n💡 生成了 {len(solutions)} 个解决方案")
        print("📄 详细实施指南已生成")
        
        return {
            'analysis_results': self.analysis_results,
            'implementation_guide': implementation_guide
        }

def main():
    """主函数"""
    print("🔍 领星API连接问题根本原因分析")
    print("深入分析网络连接问题并提供根本性解决方案")
    print()
    
    analyzer = RootCauseAnalyzer()
    results = analyzer.run_full_analysis()
    
    # 保存分析结果
    import json
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存JSON结果
    json_file = f"test/root_cause_analysis_{timestamp}.json"
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results['analysis_results'], f, ensure_ascii=False, indent=2)
        print(f"\n📄 分析结果已保存: {json_file}")
    except Exception as e:
        print(f"⚠️ 保存分析结果失败: {e}")
    
    # 保存实施指南
    guide_file = f"test/implementation_guide_{timestamp}.md"
    try:
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(results['implementation_guide'])
        print(f"📋 实施指南已保存: {guide_file}")
    except Exception as e:
        print(f"⚠️ 保存实施指南失败: {e}")
    
    print("\n🎯 下一步行动:")
    print("1. 查看详细的实施指南文件")
    print("2. 选择最适合你环境的解决方案")
    print("3. 按照指南逐步实施")
    print("4. 实施完成后重新测试连接")

if __name__ == "__main__":
    main()