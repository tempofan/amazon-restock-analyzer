#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 反向代理解决方案自动化部署脚本
自动部署WebSocket支持的云代理服务器和本地反向代理客户端
"""

import subprocess
import time
import os
import threading
from datetime import datetime

def run_command(command, description="", timeout=60):
    """
    执行系统命令
    
    Args:
        command: 要执行的命令
        description: 命令描述
        timeout: 超时时间
    
    Returns:
        bool: 命令是否执行成功
    """
    print(f"🔧 {description}")
    print(f"   执行命令: {command}")
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # 发送密码
        stdout, stderr = process.communicate(input="woAIni34\n", timeout=timeout)
        
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
            
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"   ⏰ 超时 ({timeout}秒)")
        return False
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return False

def deploy_cloud_server():
    """部署云服务器"""
    print("\n🌐 步骤1: 部署云服务器")
    print("-" * 50)
    
    # 1. 上传WebSocket版本的云代理服务器
    print("📤 上传WebSocket支持的云代理服务器...")
    if not run_command(
        'scp "deploy/cloud_proxy_server_ws.py" ubuntu@175.178.183.96:~/',
        "上传cloud_proxy_server_ws.py"
    ):
        return False
    
    # 2. 在云服务器上执行部署
    print("\n🔄 在云服务器上执行部署...")
    deploy_commands = [
        "# 停止旧服务",
        "sudo systemctl stop lingxing-proxy",
        "sleep 2",
        "# 备份旧版本",
        "sudo cp /opt/lingxing-proxy/cloud_proxy_server.py /opt/lingxing-proxy/cloud_proxy_server.py.backup.ws.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo '无旧版本需要备份'",
        "# 替换为WebSocket版本",
        "sudo cp ~/cloud_proxy_server_ws.py /opt/lingxing-proxy/cloud_proxy_server.py",
        "# 安装WebSocket依赖",
        "cd /opt/lingxing-proxy && sudo ./venv/bin/pip install websockets",
        "# 重启服务",
        "sudo systemctl start lingxing-proxy",
        "sleep 3",
        "# 检查服务状态",
        "sudo systemctl status lingxing-proxy --no-pager",
        "# 测试健康检查",
        "curl -s http://localhost:8080/health"
    ]
    
    ssh_command = f'ssh ubuntu@175.178.183.96 "{"; ".join(deploy_commands)}"'
    
    if not run_command(ssh_command, "在云服务器上执行部署", timeout=120):
        return False
    
    print("✅ 云服务器部署完成")
    return True

def test_cloud_server():
    """测试云服务器"""
    print("\n🧪 步骤2: 测试云服务器")
    print("-" * 50)
    
    print("等待5秒让服务完全启动...")
    time.sleep(5)
    
    # 测试健康检查
    test_result = subprocess.run(
        'curl -s http://175.178.183.96:8080/health',
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if test_result.returncode == 0:
        print("✅ 云服务器健康检查通过")
        print(f"📄 响应: {test_result.stdout}")
        
        # 检查是否包含WebSocket支持
        if 'feishu-webhook-ws' in test_result.stdout and 'ws_port' in test_result.stdout:
            print("✅ WebSocket支持已启用")
            return True
        else:
            print("⚠️ WebSocket支持可能未正确启用")
            return False
    else:
        print("❌ 云服务器健康检查失败")
        return False

def start_reverse_proxy_client():
    """启动反向代理客户端"""
    print("\n🔄 步骤3: 启动反向代理客户端")
    print("-" * 50)
    
    print("🚀 启动反向代理客户端...")
    print("📝 注意: 反向代理客户端将在后台运行")
    print("📋 可以通过日志文件 reverse_proxy.log 查看运行状态")
    
    # 启动反向代理客户端
    try:
        process = subprocess.Popen(
            "python deploy/reverse_proxy_solution.py",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
        
        print(f"✅ 反向代理客户端已启动 (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ 启动反向代理客户端失败: {e}")
        return None

def test_full_system():
    """测试完整系统"""
    print("\n🧪 步骤4: 测试完整系统")
    print("-" * 50)
    
    print("等待10秒让反向代理客户端连接...")
    time.sleep(10)
    
    # 测试飞书webhook转发
    print("🤖 测试飞书webhook转发...")
    test_result = subprocess.run(
        'curl -X POST http://175.178.183.96:8080/feishu/webhook -H "Content-Type: application/json" -d "{\\"type\\": \\"url_verification\\", \\"challenge\\": \\"test123\\"}" --connect-timeout 30',
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if test_result.returncode == 0:
        print("✅ 飞书webhook转发测试通过")
        print(f"📄 响应: {test_result.stdout}")
        return True
    else:
        print("❌ 飞书webhook转发测试失败")
        print(f"错误: {test_result.stderr}")
        return False

def main():
    """主部署流程"""
    print("🚀 反向代理解决方案自动化部署")
    print("=" * 60)
    print(f"📅 部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🎯 部署目标:")
    print("• 解决本地公网IP不固定问题")
    print("• 通过WebSocket实现反向代理")
    print("• 实现飞书机器人稳定运行")
    print()
    
    # 检查依赖
    print("🔍 检查依赖...")
    try:
        import websockets
        print("✅ websockets 库已安装")
    except ImportError:
        print("❌ websockets 库未安装，正在安装...")
        if not run_command("pip install websockets", "安装websockets库"):
            print("❌ 安装依赖失败，请手动安装: pip install websockets")
            return False
    
    # 检查本地飞书服务器
    print("\n🔍 检查本地飞书服务器...")
    local_test = subprocess.run(
        "curl -s http://127.0.0.1:5000/health",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if local_test.returncode != 0:
        print("⚠️ 本地飞书服务器未运行，请先启动:")
        print("   python feishu/start_feishu_server.py")
        print("\n是否继续部署云服务器部分? (y/n)")
        choice = input().lower()
        if choice != 'y':
            return False
    else:
        print("✅ 本地飞书服务器正常运行")
    
    # 执行部署步骤
    steps = [
        ("部署云服务器", deploy_cloud_server),
        ("测试云服务器", test_cloud_server),
    ]
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                print(f"\n❌ {step_name}失败，部署中止")
                return False
        except Exception as e:
            print(f"\n❌ {step_name}异常: {e}")
            return False
    
    # 启动反向代理客户端
    reverse_proxy_process = start_reverse_proxy_client()
    
    if reverse_proxy_process:
        # 测试完整系统
        if test_full_system():
            print("\n🎉 反向代理解决方案部署成功！")
            print("✅ 现在可以在飞书群聊中@机器人测试了")
            print("\n💡 使用说明:")
            print("1. 在飞书群聊中发送: @机器人 帮助")
            print("2. 查看反向代理日志: tail -f reverse_proxy.log")
            print("3. 停止反向代理: 按 Ctrl+C")
            
            # 保持反向代理运行
            try:
                print("\n🔄 反向代理客户端正在运行...")
                print("按 Ctrl+C 停止")
                reverse_proxy_process.wait()
            except KeyboardInterrupt:
                print("\n👋 正在停止反向代理客户端...")
                reverse_proxy_process.terminate()
                reverse_proxy_process.wait()
                print("✅ 反向代理客户端已停止")
        else:
            print("\n⚠️ 系统测试失败，请检查配置")
            if reverse_proxy_process:
                reverse_proxy_process.terminate()
    else:
        print("\n❌ 反向代理客户端启动失败")
    
    print(f"\n⏰ 部署完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 部署已取消")
    except Exception as e:
        print(f"\n❌ 部署异常: {str(e)}") 