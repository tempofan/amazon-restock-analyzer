#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH检查工具
"""

import paramiko
import sys

def ssh_execute(command):
    """执行SSH命令"""
    try:
        # SSH连接配置
        hostname = "175.178.183.96"
        username = "root"
        key_file = r"D:\华为家庭存储\开发资料\腾讯云\lingxing_correct.ppk"
        
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 加载PuTTY私钥
        try:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
        except:
            # 如果是PuTTY格式，尝试转换
            from paramiko.pkey import PKey
            import subprocess
            
            # 使用puttygen转换（如果可用）
            print("尝试使用密码连接...")
            ssh.connect(hostname=hostname, username=username, password="Lx2024@#$")
        else:
            # 使用私钥连接
            ssh.connect(hostname=hostname, username=username, pkey=private_key)
        
        # 执行命令
        stdin, stdout, stderr = ssh.exec_command(command)
        
        # 获取输出
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        ssh.close()
        
        if error:
            print(f"错误: {error}")
        
        return output
        
    except Exception as e:
        print(f"SSH连接失败: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        result = ssh_execute(command)
        if result:
            print(result)
    else:
        print("用法: python ssh_check.py <命令>") 