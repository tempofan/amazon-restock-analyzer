#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署修复版云代理服务器
"""

import os
import sys
import subprocess
import paramiko

def run_ssh_command(command):
    """执行SSH命令"""
    ssh_tool = os.path.join(os.path.dirname(__file__), "auto_ssh_command.py")
    result = subprocess.run([sys.executable, ssh_tool, command], 
                          capture_output=True, text=True, encoding='utf-8')
    print(f"📝 执行命令: {command}")
    if result.stdout:
        print("✅ 输出:", result.stdout)
    if result.stderr:
        print("⚠️ 错误:", result.stderr)
    return result.returncode == 0

def upload_file(local_path, remote_path):
    """上传文件到服务器"""
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 连接服务器
        print(f"🔗 连接服务器上传文件...")
        ssh.connect("175.178.183.96", username="ubuntu", password="woAIni34")
        
        # 创建SFTP客户端
        sftp = ssh.open_sftp()
        
        print(f"📤 上传文件: {local_path} -> {remote_path}")
        sftp.put(local_path, remote_path)
        
        sftp.close()
        ssh.close()
        
        print(f"✅ 文件上传成功")
        return True
        
    except Exception as e:
        print(f"❌ 文件上传失败: {e}")
        return False

def deploy_fixed_server():
    """部署修复版服务器"""
    print("🚀 开始部署修复版云代理服务器...")
    
    # 1. 备份原文件
    print("\n📦 1. 备份原文件...")
    if not run_ssh_command("sudo cp /opt/lingxing-proxy/cloud_proxy_server.py /opt/lingxing-proxy/cloud_proxy_server.py.backup"):
        print("❌ 备份失败")
        return False
    
    # 2. 检查修复版文件
    fixed_server_path = os.path.join(os.path.dirname(__file__), "cloud_proxy_server_fixed.py")
    if not os.path.exists(fixed_server_path):
        print(f"❌ 修复版文件不存在: {fixed_server_path}")
        return False
    
    # 3. 上传修复版文件
    print("\n📤 2. 上传修复版文件...")
    temp_file = "/tmp/cloud_proxy_server_fixed.py"
    if not upload_file(fixed_server_path, temp_file):
        print("❌ 上传文件失败")
        return False
    
    # 4. 复制到目标位置
    print("\n📂 3. 复制到目标位置...")
    if not run_ssh_command(f"sudo cp {temp_file} /opt/lingxing-proxy/cloud_proxy_server.py"):
        print("❌ 复制文件失败")
        return False
    
    # 5. 设置权限
    print("\n🔐 4. 设置文件权限...")
    if not run_ssh_command("sudo chown root:root /opt/lingxing-proxy/cloud_proxy_server.py"):
        print("❌ 设置权限失败")
        return False
    
    # 6. 启动服务
    print("\n🚀 5. 启动服务...")
    if not run_ssh_command("sudo systemctl start lingxing-proxy"):
        print("❌ 启动服务失败")
        return False
    
    # 7. 检查服务状态
    print("\n📊 6. 检查服务状态...")
    run_ssh_command("sudo systemctl status lingxing-proxy")
    
    # 8. 清理临时文件
    print("\n🧹 7. 清理临时文件...")
    run_ssh_command(f"rm -f {temp_file}")
    
    print("\n✅ 修复版云代理服务器部署完成！")
    return True

if __name__ == "__main__":
    success = deploy_fixed_server()
    sys.exit(0 if success else 1) 