#!/usr/bin/env python3
"""
上传完整版云代理服务器文件
"""

import paramiko
import os
import sys

def upload_complete_proxy():
    """上传完整版云代理服务器文件到云服务器"""
    
    # SSH连接配置
    hostname = '175.178.183.96'
    username = 'ubuntu'
    password = 'Lx1234567890'
    
    # 本地文件路径
    local_file = 'deploy/cloud_proxy_server_with_api.py'
    remote_file = '/tmp/cloud_proxy_server_with_api.py'
    target_file = '/opt/lingxing-proxy/cloud_proxy_server_with_api.py'
    
    print("🚀 上传完整版云代理服务器文件")
    print(f"📂 本地文件: {local_file}")
    print(f"🌐 目标服务器: {hostname}")
    print("=" * 50)
    
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print("🔗 正在连接到云服务器...")
        ssh.connect(hostname, username=username, password=password)
        
        # 创建SFTP客户端
        sftp = ssh.open_sftp()
        
        print("📤 上传文件...")
        sftp.put(local_file, remote_file)
        print(f"✅ 文件已上传到临时目录: {remote_file}")
        
        # 移动文件到目标目录
        print("📁 移动文件到目标目录...")
        stdin, stdout, stderr = ssh.exec_command(f'sudo mv {remote_file} {target_file}')
        stdout.read()
        
        # 设置文件权限
        print("🔧 设置文件权限...")
        stdin, stdout, stderr = ssh.exec_command(f'sudo chmod +x {target_file}')
        stdout.read()
        
        # 设置文件所有者
        stdin, stdout, stderr = ssh.exec_command(f'sudo chown ubuntu:ubuntu {target_file}')
        stdout.read()
        
        print(f"✅ 完整版云代理服务器文件已成功上传到: {target_file}")
        
        # 关闭连接
        sftp.close()
        ssh.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return False

if __name__ == "__main__":
    success = upload_complete_proxy()
    if success:
        print("🎉 上传完成!")
    else:
        print("💥 上传失败!")
        sys.exit(1) 