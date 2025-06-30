#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动SSH命令执行工具
使用私钥文件进行认证，避免手动输入密码
"""

import paramiko
import sys
import time
import os

def execute_ssh_command(host, username, private_key_path, command, timeout=30):
    """
    使用私钥执行SSH命令
    
    Args:
        host (str): 服务器地址
        username (str): 用户名  
        private_key_path (str): 私钥文件路径
        command (str): 要执行的命令
        timeout (int): 超时时间（秒）
    
    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    try:
        # 检查私钥文件是否存在
        if not os.path.exists(private_key_path):
            print(f"❌ 私钥文件不存在: {private_key_path}")
            return 1, "", "私钥文件不存在"
        
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"🔗 正在连接到 {host}...")
        print(f"🔑 使用私钥: {private_key_path}")
        
        # 加载私钥（支持PPK格式需要转换）
        try:
            # 尝试加载RSA私钥
            private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        except paramiko.PasswordRequiredException:
            print("❌ 私钥需要密码，请提供密码")
            return 1, "", "私钥需要密码"
        except Exception as e:
            # 如果是PPK文件，需要转换
            if str(e).find("not a valid") != -1 or private_key_path.endswith('.ppk'):
                print("⚠️ 检测到PPK格式私钥，尝试使用密码连接...")
                # PPK文件通常需要转换，这里回退到密码方式
                ssh.connect(host, username=username, password="woAIni34", timeout=timeout)
            else:
                raise e
        else:
            # 使用私钥连接
            ssh.connect(host, username=username, pkey=private_key, timeout=timeout)
        
        print(f"📝 执行命令: {command}")
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        
        # 获取输出
        exit_code = stdout.channel.recv_exit_status()
        stdout_data = stdout.read().decode('utf-8')
        stderr_data = stderr.read().decode('utf-8')
        
        ssh.close()
        
        if stdout_data:
            print("✅ 标准输出:")
            print(stdout_data)
        
        if stderr_data:
            print("⚠️ 错误输出:")
            print(stderr_data)
            
        print(f"🎯 命令执行完成，退出代码: {exit_code}")
        return exit_code, stdout_data, stderr_data
        
    except Exception as e:
        print(f"❌ SSH连接失败: {e}")
        return 1, "", str(e)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("❌ 用法: python auto_ssh_command.py <command>")
        print("📝 示例: python auto_ssh_command.py 'sudo systemctl stop lingxing-proxy'")
        sys.exit(1)
    
    # 服务器配置
    HOST = "175.178.183.96"
    USERNAME = "ubuntu"
    PRIVATE_KEY_PATH = r"D:\华为家庭存储\开发资料\腾讯云\lingxing_correct.ppk"
    
    # 要执行的命令
    command = " ".join(sys.argv[1:])
    
    print(f"🚀 自动SSH命令执行工具")
    print(f"🎯 目标服务器: {HOST}")
    print(f"👤 用户名: {USERNAME}")
    print(f"🔑 私钥文件: {PRIVATE_KEY_PATH}")
    print(f"📝 命令: {command}")
    print("="*50)
    
    # 执行命令
    exit_code, stdout, stderr = execute_ssh_command(HOST, USERNAME, PRIVATE_KEY_PATH, command)
    
    # 返回退出代码
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 