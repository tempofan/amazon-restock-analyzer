#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 简化部署脚本
通过SSH直接修改云服务器文件，部署简单HTTP轮询代理
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleProxyDeployer:
    """简化代理部署器"""
    
    def __init__(self):
        self.server_ip = "175.178.183.96"
        self.server_user = "ubuntu"
        self.server_path = "/opt/lingxing-proxy"
        self.local_files = {
            'cloud_server': 'deploy/cloud_proxy_server_simple.py',
            'reverse_client': 'deploy/simple_reverse_proxy.py'
        }
    
    def run_ssh_command(self, command, input_text=None):
        """
        执行SSH命令
        
        Args:
            command: 要执行的命令
            input_text: 输入文本（用于密码等）
            
        Returns:
            tuple: (success, output, error)
        """
        try:
            cmd = f'ssh {self.server_user}@{self.server_ip} "{command}"'
            logger.info(f"🔧 执行SSH命令: {command}")
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=input_text)
            success = process.returncode == 0
            
            if success:
                logger.info(f"✅ 命令执行成功")
                if stdout.strip():
                    logger.debug(f"输出: {stdout.strip()}")
            else:
                logger.error(f"❌ 命令执行失败: {stderr.strip()}")
            
            return success, stdout, stderr
            
        except Exception as e:
            logger.error(f"❌ SSH命令执行异常: {str(e)}")
            return False, "", str(e)
    
    def create_temp_script(self, content, filename):
        """
        创建临时脚本文件
        
        Args:
            content: 脚本内容
            filename: 文件名
            
        Returns:
            str: 临时文件路径
        """
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✅ 创建临时文件: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ 创建临时文件失败: {str(e)}")
            return None
    
    def deploy_via_script_replacement(self):
        """
        通过脚本替换方式部署
        """
        logger.info("🚀 开始通过脚本替换方式部署")
        
        # 读取本地云服务器文件
        cloud_server_file = self.local_files['cloud_server']
        if not os.path.exists(cloud_server_file):
            logger.error(f"❌ 本地文件不存在: {cloud_server_file}")
            return False
        
        with open(cloud_server_file, 'r', encoding='utf-8') as f:
            cloud_server_content = f.read()
        
        # 创建替换脚本
        replace_script = f'''#!/bin/bash
# 停止服务
sudo systemctl stop lingxing-proxy

# 备份原文件
sudo cp {self.server_path}/cloud_proxy_server.py {self.server_path}/cloud_proxy_server_backup_$(date +%Y%m%d_%H%M%S).py

# 创建新文件
sudo tee {self.server_path}/cloud_proxy_server.py > /dev/null << 'EOF'
{cloud_server_content}
EOF

# 设置权限
sudo chmod +x {self.server_path}/cloud_proxy_server.py
sudo chown ubuntu:ubuntu {self.server_path}/cloud_proxy_server.py

# 重启服务
sudo systemctl start lingxing-proxy
sudo systemctl status lingxing-proxy

echo "部署完成"
'''
        
        # 创建临时脚本文件
        temp_script = self.create_temp_script(replace_script, "deploy_script.sh")
        if not temp_script:
            return False
        
        try:
            # 上传脚本到服务器
            scp_cmd = f"scp {temp_script} {self.server_user}@{self.server_ip}:/tmp/deploy_script.sh"
            logger.info(f"📤 上传部署脚本")
            
            process = subprocess.Popen(scp_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input="woAIni34\n")
            
            if process.returncode != 0:
                logger.error(f"❌ 脚本上传失败: {stderr}")
                return False
            
            logger.info("✅ 脚本上传成功")
            
            # 执行部署脚本
            success, output, error = self.run_ssh_command("bash /tmp/deploy_script.sh", "woAIni34\n")
            
            if success:
                logger.info("✅ 部署脚本执行成功")
                logger.info(f"输出: {output}")
                return True
            else:
                logger.error(f"❌ 部署脚本执行失败: {error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 部署过程异常: {str(e)}")
            return False
        finally:
            # 清理临时文件
            try:
                os.remove(temp_script)
                logger.info("🧹 清理临时文件")
            except:
                pass
    
    def verify_deployment(self):
        """验证部署结果"""
        logger.info("🔍 验证部署结果")
        
        # 检查服务状态
        success, output, error = self.run_ssh_command("sudo systemctl is-active lingxing-proxy")
        if success and "active" in output:
            logger.info("✅ 服务运行正常")
        else:
            logger.warning("⚠️ 服务可能未正常运行")
        
        # 检查端口监听
        success, output, error = self.run_ssh_command("sudo netstat -tlnp | grep :8080")
        if success and "8080" in output:
            logger.info("✅ 端口8080正常监听")
        else:
            logger.warning("⚠️ 端口8080可能未正常监听")
        
        # 测试健康检查接口
        time.sleep(3)  # 等待服务启动
        try:
            import requests
            response = requests.get(f"http://{self.server_ip}:8080/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ 健康检查接口正常")
                data = response.json()
                logger.info(f"服务状态: {data.get('status')}")
                return True
            else:
                logger.warning(f"⚠️ 健康检查接口异常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {str(e)}")
            return False
    
    def show_client_usage(self):
        """显示客户端使用说明"""
        logger.info("📋 客户端使用说明:")
        logger.info("1. 确保本地飞书服务器运行在 192.168.0.105:5000")
        logger.info("2. 运行反向代理客户端:")
        logger.info("   python deploy/simple_reverse_proxy.py")
        logger.info("3. 或者指定参数:")
        logger.info("   python deploy/simple_reverse_proxy.py --cloud-server http://175.178.183.96:8080 --local-server http://192.168.0.105:5000")
        logger.info("4. 查看云服务器统计信息:")
        logger.info("   http://175.178.183.96:8080/stats")
        logger.info("5. 飞书webhook地址:")
        logger.info("   http://175.178.183.96:8080/feishu/webhook")
    
    def deploy(self):
        """执行完整部署"""
        logger.info("🚀 开始简化代理部署")
        
        # 检查本地文件
        for name, filepath in self.local_files.items():
            if not os.path.exists(filepath):
                logger.error(f"❌ 本地文件不存在: {filepath}")
                return False
        
        logger.info("✅ 本地文件检查通过")
        
        # 执行部署
        if not self.deploy_via_script_replacement():
            logger.error("❌ 部署失败")
            return False
        
        # 验证部署
        if not self.verify_deployment():
            logger.warning("⚠️ 部署验证未完全通过，但服务可能正在启动中")
        
        # 显示使用说明
        self.show_client_usage()
        
        logger.info("🎉 部署完成!")
        return True

def main():
    """主函数"""
    deployer = SimpleProxyDeployer()
    
    try:
        success = deployer.deploy()
        if success:
            logger.info("🎉 部署成功完成!")
            sys.exit(0)
        else:
            logger.error("❌ 部署失败!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 部署被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 部署过程异常: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 