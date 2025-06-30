#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏗️ 混合架构管理器
统一管理本地项目和云代理服务器的混合架构方案
"""

import sys
import os
import time
import json
import requests
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 确保加载环境变量
load_dotenv('config/server.env')

from config.proxy_config import ProxyConfig
from config.config import APIConfig
from utils.logger import api_logger

class HybridArchitectureManager:
    """
    🏗️ 混合架构管理器
    管理本地项目和云代理服务器的协调工作
    """
    
    def __init__(self):
        """初始化混合架构管理器"""
        self.proxy_config = ProxyConfig
        self.local_project_status = {}
        self.cloud_proxy_status = {}
        
    def check_cloud_proxy_status(self) -> Dict[str, Any]:
        """
        检查云代理服务器状态
        
        Returns:
            Dict[str, Any]: 云代理状态信息
        """
        print("🌐 检查云代理服务器状态...")
        
        if not self.proxy_config.is_proxy_enabled():
            return {
                'status': 'disabled',
                'message': '代理模式未启用'
            }
        
        try:
            # 健康检查
            health_url = self.proxy_config.get_health_check_url()
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # 获取统计信息
                stats_url = self.proxy_config.get_stats_url()
                stats_response = requests.get(stats_url, timeout=10)
                stats_data = stats_response.json() if stats_response.status_code == 200 else {}
                
                return {
                    'status': 'healthy',
                    'message': '云代理服务器运行正常',
                    'health': health_data,
                    'stats': stats_data,
                    'server_ip': self.proxy_config.PROXY_HOST,
                    'port': self.proxy_config.PROXY_PORT
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': f'健康检查失败: HTTP {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'status': 'unreachable',
                'message': '无法连接到云代理服务器'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'检查失败: {str(e)}'
            }
    
    def check_local_project_status(self) -> Dict[str, Any]:
        """
        检查本地项目状态
        
        Returns:
            Dict[str, Any]: 本地项目状态信息
        """
        print("💻 检查本地项目状态...")
        
        status = {
            'proxy_config': 'unknown',
            'api_credentials': 'unknown',
            'dependencies': 'unknown',
            'token_status': 'unknown'
        }
        
        try:
            # 检查代理配置
            is_valid, config_msg = self.proxy_config.validate_config()
            status['proxy_config'] = 'valid' if is_valid else 'invalid'
            status['proxy_config_message'] = config_msg
            
            # 检查API凭据
            if APIConfig.APP_ID and APIConfig.APP_SECRET:
                if APIConfig.APP_ID != "your_app_id":
                    status['api_credentials'] = 'configured'
                else:
                    status['api_credentials'] = 'not_configured'
            else:
                status['api_credentials'] = 'missing'
            
            # 检查依赖包
            try:
                import requests, pandas, openpyxl
                status['dependencies'] = 'installed'
            except ImportError as e:
                status['dependencies'] = f'missing: {str(e)}'
            
            # 检查Token状态
            try:
                from auth.token_manager import TokenManager
                tm = TokenManager()
                token_info = tm.get_token_info()
                if token_info:
                    status['token_status'] = 'valid' if not token_info.get('is_expired', True) else 'expired'
                else:
                    status['token_status'] = 'none'
            except Exception as e:
                status['token_status'] = f'error: {str(e)}'
            
            return {
                'status': 'checked',
                'components': status
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'检查失败: {str(e)}'
            }
    
    def test_end_to_end_connectivity(self) -> Dict[str, Any]:
        """
        测试端到端连接
        
        Returns:
            Dict[str, Any]: 连接测试结果
        """
        print("🔗 测试端到端连接...")
        
        try:
            from api.client import APIClient
            
            # 创建API客户端
            client = APIClient()
            
            # 执行连接测试
            test_result = client.test_connection()
            
            return {
                'status': 'success',
                'message': '端到端连接测试成功',
                'result': test_result
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'连接测试失败: {str(e)}'
            }
    
    def generate_architecture_report(self) -> Dict[str, Any]:
        """
        生成混合架构状态报告
        
        Returns:
            Dict[str, Any]: 架构状态报告
        """
        print("📊 生成混合架构状态报告...")
        
        # 收集各组件状态
        cloud_status = self.check_cloud_proxy_status()
        local_status = self.check_local_project_status()
        connectivity_test = self.test_end_to_end_connectivity()
        
        # 生成报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'architecture_type': 'hybrid',
            'components': {
                'cloud_proxy': cloud_status,
                'local_project': local_status,
                'connectivity': connectivity_test
            },
            'overall_status': self._calculate_overall_status(cloud_status, local_status, connectivity_test),
            'recommendations': self._generate_recommendations(cloud_status, local_status, connectivity_test)
        }
        
        return report
    
    def _calculate_overall_status(self, cloud_status: Dict, local_status: Dict, connectivity_test: Dict) -> str:
        """计算整体状态"""
        if (cloud_status.get('status') == 'healthy' and 
            local_status.get('status') == 'checked' and
            connectivity_test.get('status') == 'success'):
            return 'excellent'
        elif connectivity_test.get('status') == 'success':
            return 'good'
        elif cloud_status.get('status') in ['healthy', 'disabled']:
            return 'needs_attention'
        else:
            return 'critical'
    
    def _generate_recommendations(self, cloud_status: Dict, local_status: Dict, connectivity_test: Dict) -> list:
        """生成优化建议"""
        recommendations = []
        
        # 云代理相关建议
        if cloud_status.get('status') == 'unreachable':
            recommendations.append({
                'priority': 'high',
                'component': 'cloud_proxy',
                'issue': '云代理服务器无法访问',
                'action': '检查云服务器状态和网络连接'
            })
        elif cloud_status.get('status') == 'unhealthy':
            recommendations.append({
                'priority': 'medium',
                'component': 'cloud_proxy',
                'issue': '云代理服务器健康检查失败',
                'action': '检查代理服务器日志和配置'
            })
        
        # 本地项目相关建议
        local_components = local_status.get('components', {})
        if local_components.get('api_credentials') != 'configured':
            recommendations.append({
                'priority': 'high',
                'component': 'local_project',
                'issue': 'API凭据未正确配置',
                'action': '配置正确的APP_ID和APP_SECRET'
            })
        
        if local_components.get('token_status') == 'expired':
            recommendations.append({
                'priority': 'low',
                'component': 'local_project',
                'issue': 'Token已过期',
                'action': 'Token会自动刷新，无需手动处理'
            })
        
        # 连接相关建议
        if connectivity_test.get('status') == 'failed':
            recommendations.append({
                'priority': 'critical',
                'component': 'connectivity',
                'issue': '端到端连接失败',
                'action': '检查网络配置和API白名单设置'
            })
        
        return recommendations
    
    def print_status_report(self, report: Dict[str, Any]):
        """打印状态报告"""
        print("\n" + "="*80)
        print("🏗️ 混合架构状态报告")
        print("="*80)
        
        print(f"📅 报告时间: {report['timestamp']}")
        print(f"🎯 架构类型: {report['architecture_type']}")
        print(f"📊 整体状态: {self._get_status_emoji(report['overall_status'])} {report['overall_status'].upper()}")
        
        print("\n🔍 组件状态详情:")
        print("-"*50)
        
        # 云代理状态
        cloud = report['components']['cloud_proxy']
        print(f"☁️  云代理服务器: {self._get_status_emoji(cloud['status'])} {cloud['status']}")
        print(f"   💬 {cloud['message']}")
        if cloud.get('server_ip'):
            print(f"   🌐 服务器: {cloud['server_ip']}:{cloud['port']}")
        
        # 本地项目状态
        local = report['components']['local_project']
        print(f"💻 本地项目: {self._get_status_emoji(local['status'])} {local['status']}")
        if 'components' in local:
            for component, status in local['components'].items():
                emoji = "✅" if status in ['valid', 'configured', 'installed'] else "❌"
                print(f"   {emoji} {component}: {status}")
        
        # 连接测试状态
        connectivity = report['components']['connectivity']
        print(f"🔗 端到端连接: {self._get_status_emoji(connectivity['status'])} {connectivity['status']}")
        print(f"   💬 {connectivity['message']}")
        
        # 建议
        if report['recommendations']:
            print("\n💡 优化建议:")
            print("-"*30)
            for i, rec in enumerate(report['recommendations'], 1):
                priority_emoji = {"critical": "🚨", "high": "⚠️", "medium": "💡", "low": "ℹ️"}
                emoji = priority_emoji.get(rec['priority'], "📝")
                print(f"{i}. {emoji} [{rec['priority'].upper()}] {rec['component']}")
                print(f"   问题: {rec['issue']}")
                print(f"   建议: {rec['action']}")
        else:
            print("\n✅ 所有组件运行正常，无需特殊处理")
        
        print("\n" + "="*80)
    
    def _get_status_emoji(self, status: str) -> str:
        """获取状态对应的emoji"""
        status_emojis = {
            'excellent': '🟢',
            'good': '🟡', 
            'needs_attention': '🟠',
            'critical': '🔴',
            'healthy': '✅',
            'unhealthy': '⚠️',
            'unreachable': '❌',
            'disabled': '⏸️',
            'success': '✅',
            'failed': '❌',
            'checked': '✅',
            'error': '❌'
        }
        return status_emojis.get(status, '❓')
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """保存报告到文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/hybrid_architecture_report_{timestamp}.json"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 报告已保存: {filename}")

def main():
    """主函数"""
    print("🚀 混合架构管理器启动")
    print("="*60)
    
    manager = HybridArchitectureManager()
    
    # 生成状态报告
    report = manager.generate_architecture_report()
    
    # 显示报告
    manager.print_status_report(report)
    
    # 保存报告
    manager.save_report(report)
    
    # 根据状态提供操作建议
    overall_status = report['overall_status']
    if overall_status == 'excellent':
        print("\n🎉 混合架构运行完美！可以开始正常使用了。")
    elif overall_status == 'good':
        print("\n✅ 混合架构基本正常，建议关注上述优化建议。")
    elif overall_status == 'needs_attention':
        print("\n⚠️ 混合架构需要注意，请优先处理高优先级问题。")
    else:
        print("\n🚨 混合架构存在严重问题，请立即处理关键问题。")

if __name__ == "__main__":
    main() 