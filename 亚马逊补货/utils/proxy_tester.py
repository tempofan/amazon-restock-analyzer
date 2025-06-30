# -*- coding: utf-8 -*-
"""
🧪 代理连接测试工具
用于测试云代理服务器的连接状态和健康检查
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from config.proxy_config import ProxyConfig
from utils.logger import api_logger

class ProxyTester:
    """
    🔍 代理测试器类
    负责测试代理服务器的各种功能
    """
    
    def __init__(self):
        """初始化代理测试器"""
        self.session = requests.Session()
        self.session.timeout = 10
    
    def test_proxy_health(self) -> Tuple[bool, Dict[str, Any]]:
        """
        测试代理服务器健康状态
        
        Returns:
            Tuple[bool, Dict]: (是否健康, 响应数据)
        """
        if not ProxyConfig.is_proxy_enabled():
            return False, {'error': '代理模式未启用'}
        
        health_url = ProxyConfig.get_health_check_url()
        if not health_url:
            return False, {'error': '健康检查URL未配置'}
        
        try:
            api_logger.log_info(f"🔍 测试代理健康状态: {health_url}")
            
            start_time = time.time()
            response = self.session.get(health_url)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                data['response_time'] = response_time
                api_logger.log_info(f"✅ 代理服务器健康检查通过 - {response_time:.2f}s")
                return True, data
            else:
                error_data = {
                    'error': f'健康检查失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'response_time': response_time
                }
                api_logger.log_error(None, f"❌ 代理健康检查失败: {error_data}")
                return False, error_data
                
        except requests.exceptions.Timeout:
            error_data = {'error': '健康检查超时'}
            api_logger.log_error(None, "⏰ 代理健康检查超时")
            return False, error_data
        except requests.exceptions.ConnectionError:
            error_data = {'error': '无法连接到代理服务器'}
            api_logger.log_error(None, "🔌 无法连接到代理服务器")
            return False, error_data
        except Exception as e:
            error_data = {'error': f'健康检查异常: {str(e)}'}
            api_logger.log_error(e, "❌ 代理健康检查异常")
            return False, error_data
    
    def test_proxy_stats(self) -> Tuple[bool, Dict[str, Any]]:
        """
        获取代理服务器统计信息
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 统计数据)
        """
        if not ProxyConfig.is_proxy_enabled():
            return False, {'error': '代理模式未启用'}
        
        stats_url = ProxyConfig.get_stats_url()
        if not stats_url:
            return False, {'error': '统计URL未配置'}
        
        try:
            api_logger.log_info(f"📊 获取代理统计信息: {stats_url}")
            
            response = self.session.get(stats_url)
            
            if response.status_code == 200:
                data = response.json()
                api_logger.log_info("✅ 成功获取代理统计信息")
                return True, data
            else:
                error_data = {
                    'error': f'获取统计信息失败，状态码: {response.status_code}',
                    'status_code': response.status_code
                }
                return False, error_data
                
        except Exception as e:
            error_data = {'error': f'获取统计信息异常: {str(e)}'}
            api_logger.log_error(e, "❌ 获取代理统计信息异常")
            return False, error_data
    
    def test_proxy_connection(self) -> Tuple[bool, Dict[str, Any]]:
        """
        测试代理服务器与领星API的连接
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 连接测试结果)
        """
        if not ProxyConfig.is_proxy_enabled():
            return False, {'error': '代理模式未启用'}
        
        proxy_base = ProxyConfig.get_proxy_base_url()
        if not proxy_base:
            return False, {'error': '代理URL未配置'}
        
        # 构建测试URL（去掉/api/proxy后缀，使用/test端点）
        test_url = proxy_base.replace('/api/proxy', '/test')
        
        try:
            api_logger.log_info(f"🧪 测试代理连接: {test_url}")
            
            start_time = time.time()
            response = self.session.get(test_url)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                data['response_time'] = response_time
                api_logger.log_info(f"✅ 代理连接测试通过 - {response_time:.2f}s")
                return True, data
            else:
                error_data = {
                    'error': f'连接测试失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'response_time': response_time
                }
                return False, error_data
                
        except Exception as e:
            error_data = {'error': f'连接测试异常: {str(e)}'}
            api_logger.log_error(e, "❌ 代理连接测试异常")
            return False, error_data
    
    def run_full_test(self) -> Dict[str, Any]:
        """
        运行完整的代理测试
        
        Returns:
            Dict: 完整测试结果
        """
        print("🧪 开始代理服务器完整测试...")
        
        results = {
            'test_time': datetime.now().isoformat(),
            'proxy_enabled': ProxyConfig.is_proxy_enabled(),
            'proxy_config': {
                'host': ProxyConfig.PROXY_HOST,
                'port': ProxyConfig.PROXY_PORT,
                'protocol': ProxyConfig.PROXY_PROTOCOL,
                'base_url': ProxyConfig.get_proxy_base_url()
            },
            'tests': {}
        }
        
        # 1. 配置验证
        print("1️⃣ 验证代理配置...")
        is_valid, config_msg = ProxyConfig.validate_config()
        results['tests']['config_validation'] = {
            'success': is_valid,
            'message': config_msg
        }
        print(f"   {'✅' if is_valid else '❌'} {config_msg}")
        
        if not is_valid:
            return results
        
        # 2. 健康检查
        print("2️⃣ 代理服务器健康检查...")
        health_success, health_data = self.test_proxy_health()
        results['tests']['health_check'] = {
            'success': health_success,
            'data': health_data
        }
        print(f"   {'✅' if health_success else '❌'} {health_data.get('message', health_data.get('error', '健康检查'))}")
        
        # 3. 统计信息
        print("3️⃣ 获取代理服务器统计...")
        stats_success, stats_data = self.test_proxy_stats()
        results['tests']['stats'] = {
            'success': stats_success,
            'data': stats_data
        }
        if stats_success:
            stats = stats_data.get('stats', {})
            print(f"   ✅ 总请求数: {stats.get('total_requests', 0)}")
            print(f"   ✅ 成功率: {stats_data.get('success_rate', 0):.1f}%")
            print(f"   ✅ 运行时间: {stats_data.get('uptime_hours', 0):.1f}小时")
        else:
            print(f"   ❌ {stats_data.get('error', '获取统计信息失败')}")
        
        # 4. 连接测试
        print("4️⃣ 测试与领星API连接...")
        conn_success, conn_data = self.test_proxy_connection()
        results['tests']['connection_test'] = {
            'success': conn_success,
            'data': conn_data
        }
        print(f"   {'✅' if conn_success else '❌'} {conn_data.get('message', conn_data.get('error', '连接测试'))}")
        
        # 5. 总结
        all_success = all(test['success'] for test in results['tests'].values())
        results['overall_success'] = all_success
        
        print("\n🎯 测试总结:")
        print(f"   {'✅ 代理服务器运行正常！' if all_success else '❌ 代理服务器存在问题'}")
        
        if all_success:
            print("\n📝 后续步骤:")
            print("   1. 确保在领星ERP后台已将代理服务器IP添加到白名单")
            print("   2. 启动本机项目，验证API调用是否正常")
            print("   3. 测试飞书机器人功能")
        
        return results

def main():
    """主函数：运行代理测试"""
    tester = ProxyTester()
    results = tester.run_full_test()
    
    # 输出JSON格式的详细结果
    print("\n📋 详细测试结果:")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main() 