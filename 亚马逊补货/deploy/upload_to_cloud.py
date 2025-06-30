#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📤 云服务器部署脚本
自动上传和部署云代理服务器
"""

import os
import sys
import subprocess
import paramiko
import time
from datetime import datetime

class CloudDeployer:
    """
    📤 云服务器部署器
    自动化部署云代理服务器
    """
    
    def __init__(self, host='175.178.183.96', username='root', password=None, key_file=None):
        """
        初始化部署器
        
        Args:
            host: 云服务器IP
            username: SSH用户名
            password: SSH密码
            key_file: SSH私钥文件路径
        """
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.port = 22
        
        # SSH客户端
        self.ssh_client = None
        self.sftp_client = None
        
        print(f"📤 云服务器部署器初始化完成")
        print(f"🌐 目标服务器: {self.host}")
        print(f"👤 用户名: {self.username}")
        print()
    
    def connect(self):
        """
        连接到云服务器
        """
        print("🔗 连接到云服务器...")
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接参数
            connect_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
                'timeout': 30
            }
            
            # 使用密码或密钥认证
            if self.key_file and os.path.exists(self.key_file):
                connect_kwargs['key_filename'] = self.key_file
                print(f"🔑 使用SSH密钥认证: {self.key_file}")
            elif self.password:
                connect_kwargs['password'] = self.password
                print("🔐 使用密码认证")
            else:
                print("❌ 未提供认证信息")
                return False
            
            # 建立连接
            self.ssh_client.connect(**connect_kwargs)
            
            # 创建SFTP客户端
            self.sftp_client = self.ssh_client.open_sftp()
            
            print("✅ 成功连接到云服务器")
            return True
            
        except paramiko.AuthenticationException:
            print("❌ SSH认证失败，请检查用户名、密码或密钥")
            return False
        except paramiko.SSHException as e:
            print(f"❌ SSH连接失败: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ 连接异常: {str(e)}")
            return False
    
    def disconnect(self):
        """
        断开连接
        """
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
        print("🔌 已断开与云服务器的连接")
    
    def execute_command(self, command, timeout=30):
        """
        执行远程命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间
            
        Returns:
            tuple: (stdout, stderr, exit_code)
        """
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            
            # 等待命令完成
            exit_code = stdout.channel.recv_exit_status()
            
            # 读取输出
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            
            return stdout_text, stderr_text, exit_code
            
        except Exception as e:
            print(f"❌ 执行命令失败: {str(e)}")
            return "", str(e), -1
    
    def upload_file(self, local_path, remote_path):
        """
        上传文件到云服务器
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            
        Returns:
            bool: 上传是否成功
        """
        try:
            if not os.path.exists(local_path):
                print(f"❌ 本地文件不存在: {local_path}")
                return False
            
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self.execute_command(f"mkdir -p {remote_dir}")
            
            # 上传文件
            print(f"📤 上传文件: {local_path} -> {remote_path}")
            self.sftp_client.put(local_path, remote_path)
            
            # 设置执行权限（如果是Python文件）
            if remote_path.endswith('.py'):
                self.execute_command(f"chmod +x {remote_path}")
            
            print(f"✅ 文件上传成功: {remote_path}")
            return True
            
        except Exception as e:
            print(f"❌ 文件上传失败: {str(e)}")
            return False
    
    def install_dependencies(self):
        """
        安装Python依赖包
        """
        print("📦 安装Python依赖包...")
        
        # 检查Python版本
        stdout, stderr, exit_code = self.execute_command("python3 --version")
        if exit_code == 0:
            print(f"✅ Python版本: {stdout.strip()}")
        else:
            print("❌ Python3未安装")
            return False
        
        # 检查pip
        stdout, stderr, exit_code = self.execute_command("pip3 --version")
        if exit_code != 0:
            print("📦 安装pip...")
            self.execute_command("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py")
            self.execute_command("python3 get-pip.py")
        
        # 安装依赖包
        packages = [
            'flask',
            'flask-cors',
            'flask-socketio',
            'requests'
        ]
        
        for package in packages:
            print(f"📦 安装 {package}...")
            stdout, stderr, exit_code = self.execute_command(
                f"pip3 install {package} -i https://pypi.tuna.tsinghua.edu.cn/simple/",
                timeout=60
            )
            
            if exit_code == 0:
                print(f"✅ {package} 安装成功")
            else:
                print(f"❌ {package} 安装失败: {stderr}")
                return False
        
        print("✅ 所有依赖包安装完成")
        return True
    
    def deploy_proxy_server(self):
        """
        部署云代理服务器
        """
        print("🚀 部署云代理服务器...")
        
        # 本地文件路径
        local_proxy_file = os.path.join(os.path.dirname(__file__), 'unified_cloud_proxy.py')
        
        if not os.path.exists(local_proxy_file):
            print(f"❌ 云代理服务器文件不存在: {local_proxy_file}")
            return False
        
        # 远程文件路径
        remote_proxy_file = '/root/unified_cloud_proxy.py'
        
        # 上传文件
        if not self.upload_file(local_proxy_file, remote_proxy_file):
            return False
        
        # 创建启动脚本
        start_script = '''#!/bin/bash
cd /root
nohup python3 unified_cloud_proxy.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &
echo $! > proxy.pid
echo "云代理服务器已启动，PID: $(cat proxy.pid)"
'''
        
        # 上传启动脚本
        with open('/tmp/start_proxy.sh', 'w') as f:
            f.write(start_script)
        
        if not self.upload_file('/tmp/start_proxy.sh', '/root/start_proxy.sh'):
            return False
        
        # 设置执行权限
        self.execute_command("chmod +x /root/start_proxy.sh")
        
        # 创建停止脚本
        stop_script = '''#!/bin/bash
if [ -f /root/proxy.pid ]; then
    PID=$(cat /root/proxy.pid)
    kill $PID
    rm /root/proxy.pid
    echo "云代理服务器已停止"
else
    echo "云代理服务器未运行"
fi
'''
        
        with open('/tmp/stop_proxy.sh', 'w') as f:
            f.write(stop_script)
        
        if not self.upload_file('/tmp/stop_proxy.sh', '/root/stop_proxy.sh'):
            return False
        
        self.execute_command("chmod +x /root/stop_proxy.sh")
        
        print("✅ 云代理服务器部署完成")
        return True
    
    def start_proxy_server(self):
        """
        启动云代理服务器
        """
        print("🚀 启动云代理服务器...")
        
        # 停止现有服务
        self.execute_command("/root/stop_proxy.sh")
        time.sleep(2)
        
        # 启动新服务
        stdout, stderr, exit_code = self.execute_command("/root/start_proxy.sh")
        
        if exit_code == 0:
            print("✅ 云代理服务器启动成功")
            print(stdout)
            
            # 等待服务启动
            time.sleep(5)
            
            # 检查服务状态
            return self.check_proxy_server()
        else:
            print(f"❌ 云代理服务器启动失败: {stderr}")
            return False
    
    def check_proxy_server(self):
        """
        检查云代理服务器状态
        """
        print("🔍 检查云代理服务器状态...")
        
        try:
            import requests
            response = requests.get(f"http://{self.host}:8080/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 云代理服务器运行正常")
                print(f"  状态: {data.get('status')}")
                print(f"  服务: {data.get('service')}")
                return True
            else:
                print(f"❌ 云代理服务器响应异常: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 检查云代理服务器失败: {str(e)}")
            return False
    
    def deploy(self):
        """
        执行完整部署流程
        """
        print("🚀 开始云服务器部署")
        print("=" * 50)
        
        try:
            # 1. 连接到云服务器
            if not self.connect():
                return False
            
            # 2. 安装依赖包
            if not self.install_dependencies():
                return False
            
            # 3. 部署代理服务器
            if not self.deploy_proxy_server():
                return False
            
            # 4. 启动代理服务器
            if not self.start_proxy_server():
                return False
            
            print("\n🎉 云服务器部署完成！")
            print(f"🌐 服务地址: http://{self.host}:8080")
            print(f"🔍 健康检查: http://{self.host}:8080/health")
            print(f"📊 统计信息: http://{self.host}:8080/stats")
            print(f"🤖 飞书Webhook: http://{self.host}:8080/feishu/webhook")
            
            return True
            
        except Exception as e:
            print(f"❌ 部署过程中发生异常: {str(e)}")
            return False
        finally:
            self.disconnect()

def main():
    """主函数"""
    import argparse
    import getpass
    
    parser = argparse.ArgumentParser(description='📤 云服务器部署脚本')
    parser.add_argument('--host', default='175.178.183.96', help='云服务器IP地址')
    parser.add_argument('--username', default='root', help='SSH用户名')
    parser.add_argument('--password', help='SSH密码')
    parser.add_argument('--key-file', help='SSH私钥文件路径')
    
    args = parser.parse_args()
    
    # 获取密码（如果未提供）
    password = args.password
    if not password and not args.key_file:
        password = getpass.getpass("请输入SSH密码: ")
    
    # 创建部署器
    deployer = CloudDeployer(
        host=args.host,
        username=args.username,
        password=password,
        key_file=args.key_file
    )
    
    # 执行部署
    success = deployer.deploy()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
