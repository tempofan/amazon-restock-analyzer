#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 完整解决方案部署脚本
自动部署云代理服务器和配置本地环境
"""

import os
import sys
import subprocess
import time
import requests
import json
from datetime import datetime
import argparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CompleteSolutionDeployer:
    """
    🚀 完整解决方案部署器
    自动化部署和配置整个系统
    """
    
    def __init__(self, cloud_ip='175.178.183.96', local_ip='192.168.0.99'):
        """
        初始化部署器
        
        Args:
            cloud_ip: 云服务器IP
            local_ip: 本地服务器IP
        """
        self.cloud_ip = cloud_ip
        self.local_ip = local_ip
        self.cloud_port = 8080
        self.local_port = 8000
        
        # 服务器地址
        self.cloud_server_url = f"http://{self.cloud_ip}:{self.cloud_port}"
        self.local_server_url = f"http://{self.local_ip}:{self.local_port}"
        
        print(f"🌐 云服务器: {self.cloud_server_url}")
        print(f"🏠 本地服务器: {self.local_server_url}")
        print()
    
    def check_dependencies(self):
        """
        检查依赖包
        """
        print("🔍 检查依赖包...")
        
        required_packages = [
            'flask',
            'flask-cors', 
            'flask-socketio',
            'python-socketio',
            'requests',
            'openpyxl'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"  ❌ {package}")
        
        if missing_packages:
            print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
            print("请运行以下命令安装:")
            print(f"pip install {' '.join(missing_packages)} -i https://pypi.tuna.tsinghua.edu.cn/simple/")
            return False
        
        print("✅ 所有依赖包已安装")
        return True
    
    def update_config(self):
        """
        更新配置文件
        """
        print("📝 更新配置文件...")
        
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'server.env')
        
        # 读取现有配置
        config_lines = []
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_lines = f.readlines()
        
        # 更新配置项
        config_updates = {
            'SERVER_HOST': self.local_ip,
            'SERVER_PORT': str(self.local_port),
            'PROXY_HOST': self.cloud_ip,
            'PROXY_PORT': str(self.cloud_port),
            'ENABLE_PROXY': 'True'
        }
        
        # 应用更新
        updated_lines = []
        updated_keys = set()
        
        for line in config_lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in config_updates:
                    updated_lines.append(f"{key}={config_updates[key]}\n")
                    updated_keys.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # 添加缺失的配置项
        for key, value in config_updates.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}\n")
        
        # 写入配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print(f"✅ 配置文件已更新: {config_file}")
        
        # 显示关键配置
        print("\n📋 关键配置:")
        for key, value in config_updates.items():
            print(f"  {key}={value}")
    
    def deploy_cloud_server(self):
        """
        部署云代理服务器
        """
        print("🌐 部署云代理服务器...")
        
        # 检查云服务器文件
        cloud_server_file = os.path.join(os.path.dirname(__file__), 'unified_cloud_proxy.py')
        
        if not os.path.exists(cloud_server_file):
            print(f"❌ 云代理服务器文件不存在: {cloud_server_file}")
            return False
        
        print(f"📁 云代理服务器文件: {cloud_server_file}")
        print(f"📤 请将此文件上传到云服务器 {self.cloud_ip}")
        print(f"🚀 在云服务器上运行: python3 unified_cloud_proxy.py --host 0.0.0.0 --port {self.cloud_port}")
        print()
        
        return True
    
    def test_cloud_server(self):
        """
        测试云代理服务器
        """
        print("🧪 测试云代理服务器连接...")
        
        try:
            # 测试健康检查接口
            response = requests.get(f"{self.cloud_server_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 云代理服务器连接正常")
                print(f"  状态: {data.get('status')}")
                print(f"  服务: {data.get('service')}")
                print(f"  活跃连接: {data.get('active_connections', 0)}")
                return True
            else:
                print(f"❌ 云代理服务器响应异常: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到云代理服务器: {self.cloud_server_url}")
            print("请确保:")
            print("1. 云服务器已启动统一代理服务")
            print("2. 防火墙已开放8080端口")
            print("3. 网络连接正常")
            return False
        except Exception as e:
            print(f"❌ 测试云代理服务器失败: {str(e)}")
            return False
    
    def start_local_server(self):
        """
        启动本地服务器
        """
        print("🏠 启动本地飞书服务器...")
        
        try:
            # 检查本地服务器文件
            main_file = os.path.join(os.path.dirname(__file__), '..', 'main.py')
            
            if not os.path.exists(main_file):
                print(f"❌ 主程序文件不存在: {main_file}")
                return False
            
            print(f"🚀 启动命令: python {main_file} --feishu")
            print("💡 请在新的终端窗口中运行上述命令")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ 启动本地服务器失败: {str(e)}")
            return False
    
    def start_reverse_client(self):
        """
        启动反向代理客户端
        """
        print("🔌 启动反向代理客户端...")
        
        try:
            client_file = os.path.join(os.path.dirname(__file__), 'local_reverse_client.py')
            
            if not os.path.exists(client_file):
                print(f"❌ 反向代理客户端文件不存在: {client_file}")
                return False
            
            print(f"🚀 启动命令: python {client_file} --cloud-server {self.cloud_server_url} --local-server {self.local_server_url}")
            print("💡 请在新的终端窗口中运行上述命令")
            print()
            
            return True
            
        except Exception as e:
            print(f"❌ 启动反向代理客户端失败: {str(e)}")
            return False
    
    def test_complete_flow(self):
        """
        测试完整数据流
        """
        print("🔄 测试完整数据流...")
        
        # 等待用户确认服务已启动
        input("请确保本地服务器和反向代理客户端已启动，然后按回车继续...")
        
        try:
            # 模拟飞书webhook请求
            test_data = {
                "type": "event_callback",
                "event": {
                    "type": "message",
                    "message": {
                        "msg_type": "text",
                        "content": json.dumps({"text": "测试"}),
                        "chat_id": "test_chat_id"
                    },
                    "sender": {
                        "sender_id": {
                            "open_id": "test_user"
                        }
                    }
                }
            }
            
            # 发送测试请求到云代理服务器
            response = requests.post(
                f"{self.cloud_server_url}/feishu/webhook",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ 完整数据流测试成功")
                print(f"  响应状态: {response.status_code}")
                print(f"  响应内容: {response.text[:200]}...")
                return True
            else:
                print(f"❌ 完整数据流测试失败: {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 完整数据流测试异常: {str(e)}")
            return False
    
    def generate_deployment_guide(self):
        """
        生成部署指南
        """
        print("📋 生成部署指南...")
        
        guide_content = f"""
# 🚀 飞书机器人云代理完整部署指南

## 📊 系统架构
```
飞书 → 云服务器({self.cloud_ip}:8080) → 本地服务器({self.local_ip}:8000) → 领星API
```

## 🔧 部署步骤

### 1. 云服务器部署
```bash
# 上传文件到云服务器
scp unified_cloud_proxy.py root@{self.cloud_ip}:/root/

# 在云服务器上安装依赖
pip3 install flask flask-cors flask-socketio requests

# 启动云代理服务
python3 unified_cloud_proxy.py --host 0.0.0.0 --port 8080
```

### 2. 本地环境配置
```bash
# 启动本地飞书服务器
python main.py --feishu

# 启动反向代理客户端（新终端）
python deploy/local_reverse_client.py --cloud-server {self.cloud_server_url} --local-server {self.local_server_url}
```

### 3. 飞书机器人配置
- 应用ID: cli_a8d49f76d7fbd00b
- Webhook URL: {self.cloud_server_url}/feishu/webhook
- 请求地址: {self.cloud_server_url}/feishu/webhook

### 4. 测试验证
```bash
# 测试云服务器
curl {self.cloud_server_url}/health

# 测试完整流程
curl -X POST {self.cloud_server_url}/feishu/webhook -H "Content-Type: application/json" -d '{{"type":"url_verification","challenge":"test"}}'
```

## 🔍 故障排查

### 常见问题
1. **云服务器连接失败**
   - 检查防火墙设置
   - 确认8080端口开放
   - 验证服务器IP地址

2. **本地服务器无响应**
   - 检查本地服务是否启动
   - 验证端口8000是否被占用
   - 查看日志文件

3. **WebSocket连接失败**
   - 检查反向代理客户端状态
   - 验证网络连接
   - 查看客户端日志

### 日志文件位置
- 云服务器: unified_proxy.log
- 本地客户端: local_reverse_client.log
- 飞书服务: logs/lingxing_api.log

## 📞 技术支持
如遇问题，请检查日志文件并提供详细错误信息。

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        guide_file = os.path.join(os.path.dirname(__file__), 'DEPLOYMENT_GUIDE.md')
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"✅ 部署指南已生成: {guide_file}")
    
    def deploy(self):
        """
        执行完整部署流程
        """
        print("🚀 开始完整解决方案部署")
        print("=" * 50)
        
        # 1. 检查依赖
        if not self.check_dependencies():
            return False
        
        print()
        
        # 2. 更新配置
        self.update_config()
        print()
        
        # 3. 部署云服务器
        self.deploy_cloud_server()
        print()
        
        # 4. 测试云服务器
        if not self.test_cloud_server():
            print("⚠️ 云服务器测试失败，请先部署云服务器")
            print()
        
        # 5. 启动本地服务
        self.start_local_server()
        
        # 6. 启动反向代理客户端
        self.start_reverse_client()
        
        # 7. 生成部署指南
        self.generate_deployment_guide()
        
        print("🎉 部署流程完成！")
        print()
        print("📋 下一步操作:")
        print("1. 在云服务器上启动统一代理服务")
        print("2. 在本地启动飞书服务器")
        print("3. 在本地启动反向代理客户端")
        print("4. 在飞书开放平台配置Webhook URL")
        print("5. 测试飞书机器人功能")
        
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='🚀 完整解决方案部署脚本')
    parser.add_argument('--cloud-ip', default='175.178.183.96', help='云服务器IP地址')
    parser.add_argument('--local-ip', default='192.168.0.99', help='本地服务器IP地址')
    parser.add_argument('--test-only', action='store_true', help='仅执行测试')
    
    args = parser.parse_args()
    
    # 创建部署器
    deployer = CompleteSolutionDeployer(
        cloud_ip=args.cloud_ip,
        local_ip=args.local_ip
    )
    
    if args.test_only:
        # 仅执行测试
        deployer.test_cloud_server()
        deployer.test_complete_flow()
    else:
        # 执行完整部署
        deployer.deploy()

if __name__ == '__main__':
    main()
