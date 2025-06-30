#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 云代理服务器自动更新脚本
自动上传并部署最新版本的云代理服务器
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def run_command(command, description=""):
    """
    执行系统命令并处理结果
    
    Args:
        command: 要执行的命令
        description: 命令描述
    
    Returns:
        bool: 命令是否执行成功
    """
    print(f"🔧 {description}")
    print(f"   执行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(f"   ✅ 成功")
            if result.stdout.strip():
                print(f"   输出: {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ 失败 (退出码: {result.returncode})")
            if result.stderr.strip():
                print(f"   错误: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return False

def main():
    """主更新流程"""
    print("🚀 云代理服务器自动更新")
    print("=" * 60)
    print(f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 云服务器配置
    server_ip = "175.178.183.96"
    server_user = "ubuntu"  # 可能需要根据实际情况调整
    
    # 文件路径
    local_proxy_file = "deploy/cloud_proxy_server.py"
    local_deploy_script = "deploy/quick_deploy_cloud_proxy.sh"
    
    # 检查本地文件
    if not os.path.exists(local_proxy_file):
        print(f"❌ 本地文件不存在: {local_proxy_file}")
        return False
    
    # 步骤1: 上传云代理服务器文件
    print("📤 步骤1: 上传云代理服务器文件...")
    scp_command = f'scp "{local_proxy_file}" {server_user}@{server_ip}:~/'
    if not run_command(scp_command, "上传云代理服务器文件"):
        print("⚠️ 尝试使用root用户上传...")
        scp_command = f'scp "{local_proxy_file}" root@{server_ip}:~/'
        if not run_command(scp_command, "使用root用户上传"):
            print("❌ 文件上传失败，请检查SSH连接")
            return False
    
    # 步骤2: 上传部署脚本（如果存在）
    if os.path.exists(local_deploy_script):
        print("\n📤 步骤2: 上传部署脚本...")
        scp_command = f'scp "{local_deploy_script}" {server_user}@{server_ip}:~/'
        if not run_command(scp_command, "上传部署脚本"):
            scp_command = f'scp "{local_deploy_script}" root@{server_ip}:~/'
            run_command(scp_command, "使用root用户上传部署脚本")
    
    # 步骤3: 在云服务器上执行更新
    print("\n🔄 步骤3: 在云服务器上执行更新...")
    
    # 构建SSH命令
    update_commands = [
        "# 停止旧版本服务",
        "pkill -f cloud_proxy_server.py",
        "sleep 2",
        "# 备份旧版本",
        "cp cloud_proxy_server.py cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo '无旧版本需要备份'",
        "# 启动新版本",
        "nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &",
        "sleep 3",
        "# 检查服务状态",
        "ps aux | grep cloud_proxy_server | grep -v grep",
        "# 测试健康检查",
        "curl -s http://localhost:8080/health || echo '健康检查失败'"
    ]
    
    ssh_command = f'ssh {server_user}@{server_ip} "{"; ".join(update_commands)}"'
    
    if not run_command(ssh_command, "在云服务器上执行更新"):
        print("⚠️ 尝试使用root用户执行...")
        ssh_command = f'ssh root@{server_ip} "{"; ".join(update_commands)}"'
        if not run_command(ssh_command, "使用root用户执行更新"):
            print("❌ 云服务器更新失败")
            return False
    
    # 步骤4: 验证更新结果
    print("\n🧪 步骤4: 验证更新结果...")
    print("等待5秒让服务完全启动...")
    time.sleep(5)
    
    # 运行本地测试
    test_command = "python test/test_cloud_proxy_feishu.py"
    if run_command(test_command, "运行云代理测试"):
        print("\n🎉 云代理服务器更新成功！")
        print("✅ 可以在飞书群聊中@机器人测试了")
    else:
        print("\n⚠️ 更新完成但测试失败，请检查配置")
    
    print(f"\n⏰ 更新完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 更新已取消")
    except Exception as e:
        print(f"\n❌ 更新异常: {str(e)}") 