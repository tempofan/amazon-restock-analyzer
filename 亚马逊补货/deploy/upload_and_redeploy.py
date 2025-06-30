#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 上传并重新部署云服务器
从Windows本地上传新代码到云服务器并执行重新部署
"""

import os
import sys
import time
import subprocess
import tempfile
from datetime import datetime

class CloudServerRedeployer:
    """云服务器重新部署器"""
    
    def __init__(self):
        """初始化部署器"""
        self.server_ip = "175.178.183.96"
        self.server_user = "ubuntu"
        self.server_port = 22
        
        # 本地文件路径
        self.local_files = {
            'server_code': 'deploy/cloud_server_redeploy.py',
            'deploy_script': 'deploy/redeploy_cloud_server.sh'
        }
        
        # 远程路径
        self.remote_temp_dir = "/tmp/feishu_redeploy"
        
        print("🚀 云服务器重新部署器初始化完成")
        print(f"🎯 目标服务器: {self.server_ip}")
    
    def check_prerequisites(self):
        """检查前置条件"""
        print("\n🔍 检查前置条件...")

        # 检查本地文件 - 使用绝对路径
        base_dir = r"D:\华为家庭存储\Pythonproject\亚马逊补货"
        missing_files = []
        for name, path in self.local_files.items():
            full_path = os.path.join(base_dir, path)
            if not os.path.exists(full_path):
                missing_files.append(f"{name}: {full_path}")

        if missing_files:
            print("❌ 缺少必要文件:")
            for file in missing_files:
                print(f"   • {file}")
            return False
        
        # 检查SSH连接工具
        try:
            subprocess.run(['ssh', '-V'], capture_output=True, check=True)
            print("✅ SSH工具可用")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ SSH工具不可用，请安装OpenSSH或Git Bash")
            return False
        
        try:
            subprocess.run(['scp', '-h'], capture_output=True)
            print("✅ SCP工具可用")
        except FileNotFoundError:
            print("❌ SCP工具不可用")
            return False
        
        print("✅ 前置条件检查通过")
        return True
    
    def test_server_connection(self):
        """测试服务器连接"""
        print("\n🔌 测试服务器连接...")
        
        try:
            # 测试SSH连接
            cmd = [
                'ssh', 
                '-o', 'ConnectTimeout=10',
                '-o', 'BatchMode=yes',
                f'{self.server_user}@{self.server_ip}',
                'echo "Connection test successful"'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✅ SSH连接测试成功")
                return True
            else:
                print(f"❌ SSH连接失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ SSH连接超时")
            return False
        except Exception as e:
            print(f"❌ SSH连接异常: {str(e)}")
            return False
    
    def backup_current_server(self):
        """备份当前服务器状态"""
        print("\n💾 备份当前服务器状态...")
        
        try:
            backup_commands = [
                'sudo mkdir -p /opt/backup',
                f'sudo cp -r /opt/lingxing-proxy /opt/backup/backup_{int(time.time())} 2>/dev/null || true',
                'sudo systemctl status lingxing-proxy > /tmp/service_status.txt 2>&1 || true'
            ]
            
            for cmd in backup_commands:
                ssh_cmd = [
                    'ssh',
                    f'{self.server_user}@{self.server_ip}',
                    cmd
                ]
                
                result = subprocess.run(ssh_cmd, capture_output=True, text=True)
                if result.returncode != 0 and 'true' not in cmd:
                    print(f"⚠️ 备份命令警告: {cmd}")
            
            print("✅ 服务器状态备份完成")
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {str(e)}")
            return False
    
    def upload_files(self):
        """上传文件到服务器"""
        print("\n📤 上传文件到服务器...")

        try:
            # 创建远程临时目录
            ssh_cmd = [
                'ssh',
                f'{self.server_user}@{self.server_ip}',
                f'mkdir -p {self.remote_temp_dir}'
            ]
            subprocess.run(ssh_cmd, check=True)

            # 上传文件 - 使用绝对路径
            base_dir = r"D:\华为家庭存储\Pythonproject\亚马逊补货"
            for name, local_path in self.local_files.items():
                print(f"📁 上传 {name}...")

                full_local_path = os.path.join(base_dir, local_path)
                remote_path = f"{self.remote_temp_dir}/{os.path.basename(local_path)}"

                scp_cmd = [
                    'scp',
                    '-o', 'ConnectTimeout=30',
                    full_local_path,
                    f'{self.server_user}@{self.server_ip}:{remote_path}'
                ]
                
                result = subprocess.run(scp_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {name} 上传成功")
                else:
                    print(f"❌ {name} 上传失败: {result.stderr}")
                    return False
            
            print("✅ 所有文件上传完成")
            return True
            
        except Exception as e:
            print(f"❌ 文件上传异常: {str(e)}")
            return False
    
    def execute_deployment(self):
        """执行部署脚本"""
        print("\n🚀 执行部署脚本...")
        
        try:
            # 设置脚本权限并执行
            commands = [
                f'cd {self.remote_temp_dir}',
                'chmod +x redeploy_cloud_server.sh',
                'sudo ./redeploy_cloud_server.sh'
            ]
            
            ssh_cmd = [
                'ssh',
                '-t',  # 分配伪终端
                f'{self.server_user}@{self.server_ip}',
                ' && '.join(commands)
            ]
            
            print("🔄 正在执行部署脚本，这可能需要几分钟...")
            print("📋 部署过程:")
            
            # 实时显示部署过程
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时输出
            for line in process.stdout:
                print(f"   {line.rstrip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print("✅ 部署脚本执行成功")
                return True
            else:
                print(f"❌ 部署脚本执行失败，返回码: {process.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ 部署执行异常: {str(e)}")
            return False
    
    def verify_deployment(self):
        """验证部署结果"""
        print("\n🔍 验证部署结果...")
        
        try:
            # 等待服务启动
            print("⏳ 等待服务启动...")
            time.sleep(15)
            
            # 检查服务状态
            ssh_cmd = [
                'ssh',
                f'{self.server_user}@{self.server_ip}',
                'sudo systemctl is-active feishu-cloud-server'
            ]
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True)
            if result.returncode == 0 and 'active' in result.stdout:
                print("✅ 新服务运行正常")
            else:
                print("⚠️ 服务状态检查异常")
            
            # 测试HTTP接口
            import requests
            try:
                response = requests.get(f'http://{self.server_ip}:8080/health', timeout=10)
                if response.status_code == 200:
                    print("✅ HTTP接口响应正常")
                    data = response.json()
                    print(f"   服务器版本: {data.get('server', 'Unknown')}")
                else:
                    print(f"⚠️ HTTP接口响应异常: {response.status_code}")
            except Exception as e:
                print(f"⚠️ HTTP接口测试失败: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 验证过程异常: {str(e)}")
            return False
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        print("\n🧹 清理临时文件...")
        
        try:
            ssh_cmd = [
                'ssh',
                f'{self.server_user}@{self.server_ip}',
                f'rm -rf {self.remote_temp_dir}'
            ]
            
            subprocess.run(ssh_cmd, capture_output=True)
            print("✅ 临时文件清理完成")
            
        except Exception as e:
            print(f"⚠️ 清理临时文件失败: {str(e)}")
    
    def show_final_status(self):
        """显示最终状态"""
        print("\n" + "="*60)
        print("🎉 云服务器重新部署完成！")
        print("="*60)
        print()
        print("📋 服务信息:")
        print(f"   • 服务器地址: {self.server_ip}")
        print(f"   • 健康检查: http://{self.server_ip}:8080/health")
        print(f"   • 飞书Webhook: http://{self.server_ip}:8080/feishu/webhook")
        print(f"   • 统计信息: http://{self.server_ip}:8080/stats")
        print()
        print("🔧 管理命令 (在服务器上执行):")
        print("   • 查看状态: sudo systemctl status feishu-cloud-server")
        print("   • 查看日志: sudo journalctl -u feishu-cloud-server -f")
        print("   • 重启服务: sudo systemctl restart feishu-cloud-server")
        print()
        print("⚙️ 下一步操作:")
        print("   1. 在服务器上配置环境变量 (/opt/feishu-cloud-server/.env)")
        print("   2. 重启服务使配置生效")
        print("   3. 在飞书开放平台更新Webhook URL")
        print("   4. 测试飞书机器人功能")
        print()
        print("🎯 飞书开放平台配置:")
        print(f"   Webhook URL: http://{self.server_ip}:8080/feishu/webhook")
        print()
    
    def run(self):
        """执行完整的重新部署流程"""
        print("🚀 开始云服务器重新部署流程")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        steps = [
            ("检查前置条件", self.check_prerequisites),
            ("测试服务器连接", self.test_server_connection),
            ("备份当前服务器", self.backup_current_server),
            ("上传文件", self.upload_files),
            ("执行部署", self.execute_deployment),
            ("验证部署", self.verify_deployment),
            ("清理临时文件", self.cleanup_temp_files)
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            print(f"\n🔄 执行步骤: {step_name}")
            try:
                if step_func():
                    success_count += 1
                    print(f"✅ {step_name} 完成")
                else:
                    print(f"❌ {step_name} 失败")
                    break
            except Exception as e:
                print(f"❌ {step_name} 异常: {str(e)}")
                break
        
        print(f"\n📊 执行结果: {success_count}/{len(steps)} 步骤成功")
        
        if success_count == len(steps):
            self.show_final_status()
            return True
        else:
            print("\n❌ 部署过程中出现问题，请检查错误信息")
            return False

def main():
    """主函数"""
    print("🚀 云服务器重新部署工具")
    print("="*60)
    
    # 检查项目目录 - 使用绝对路径
    base_dir = r"D:\华为家庭存储\Pythonproject\亚马逊补货"
    deploy_dir = os.path.join(base_dir, 'deploy')
    if not os.path.exists(deploy_dir):
        print("❌ 错误: 找不到项目部署目录")
        print(f"   期望目录: {deploy_dir}")
        return False
    
    # 创建部署器并执行
    deployer = CloudServerRedeployer()
    
    try:
        success = deployer.run()
        if success:
            print("\n🎉 重新部署成功完成！")
            return True
        else:
            print("\n❌ 重新部署失败")
            return False
    except KeyboardInterrupt:
        print("\n🛑 用户中断部署过程")
        return False
    except Exception as e:
        print(f"\n❌ 部署过程异常: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
