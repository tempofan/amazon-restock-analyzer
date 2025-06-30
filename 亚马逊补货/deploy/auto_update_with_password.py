#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 云代理服务器自动更新脚本（带密码）
使用提供的SSH密码自动更新云代理服务器
"""

import subprocess
import time
import os
from datetime import datetime

def run_command_with_password(command, password, description=""):
    """
    使用密码执行SSH命令
    
    Args:
        command: 要执行的命令
        password: SSH密码
        description: 命令描述
    
    Returns:
        bool: 命令是否执行成功
    """
    print(f"🔧 {description}")
    print(f"   执行命令: {command}")
    
    try:
        # 使用sshpass来自动输入密码
        full_command = f'echo "{password}" | {command}'
        
        # 对于Windows，我们需要使用不同的方法
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 发送密码到stdin
        stdout, stderr = process.communicate(input=f"{password}\n")
        
        if process.returncode == 0:
            print(f"   ✅ 成功")
            if stdout.strip():
                print(f"   输出: {stdout.strip()}")
            return True
        else:
            print(f"   ❌ 失败 (退出码: {process.returncode})")
            if stderr.strip():
                print(f"   错误: {stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return False

def main():
    """主更新流程"""
    print("🚀 云代理服务器自动更新（带密码）")
    print("=" * 60)
    print(f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 配置
    server_ip = "175.178.183.96"
    password = "woAIni34"
    local_file = "deploy/cloud_proxy_server.py"
    
    # 尝试不同的用户名
    users = ["ubuntu", "root"]
    
    for user in users:
        print(f"🔑 尝试使用用户: {user}")
        
        # 步骤1: 上传文件
        print("\n📤 步骤1: 上传云代理服务器文件...")
        scp_command = f'scp "{local_file}" {user}@{server_ip}:~/'
        
        if run_command_with_password(scp_command, password, f"上传文件到 {user}@{server_ip}"):
            print(f"✅ 文件上传成功 ({user})")
            
            # 步骤2: 执行更新
            print("\n🔄 步骤2: 在云服务器上执行更新...")
            
            update_script = """
pkill -f cloud_proxy_server.py
sleep 2
cp cloud_proxy_server.py cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo '无旧版本需要备份'
nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &
sleep 3
ps aux | grep cloud_proxy_server | grep -v grep
curl -s http://localhost:8080/health
"""
            
            ssh_command = f'ssh {user}@{server_ip} "{update_script}"'
            
            if run_command_with_password(ssh_command, password, f"在云服务器上执行更新"):
                print(f"✅ 更新执行成功 ({user})")
                
                # 步骤3: 验证更新
                print("\n🧪 步骤3: 验证更新结果...")
                print("等待5秒让服务完全启动...")
                time.sleep(5)
                
                # 运行本地测试
                print("运行云代理测试...")
                test_result = subprocess.run(
                    "python test/test_cloud_proxy_feishu.py",
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if test_result.returncode == 0:
                    print("🎉 云代理服务器更新成功！")
                    print("✅ 可以在飞书群聊中@机器人测试了")
                    print("\n💡 测试方法:")
                    print("1. 确保机器人已添加到飞书群聊")
                    print("2. 在群聊中发送: @机器人 帮助")
                    print("3. 检查机器人是否回复")
                else:
                    print("⚠️ 更新完成但测试失败，请检查配置")
                    print(f"测试输出: {test_result.stdout}")
                    print(f"测试错误: {test_result.stderr}")
                
                return True
            else:
                print(f"❌ 更新执行失败 ({user})")
        else:
            print(f"❌ 文件上传失败 ({user})")
    
    print("❌ 所有用户尝试都失败了")
    return False

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 更新已取消")
    except Exception as e:
        print(f"\n❌ 更新异常: {str(e)}") 