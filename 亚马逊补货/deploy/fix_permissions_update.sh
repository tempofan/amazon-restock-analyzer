#!/bin/bash
# 解决权限问题的云代理更新脚本

echo "🔍 检查当前运行的云代理进程..."

# 检查当前进程
ps aux | grep cloud_proxy_server | grep -v grep

echo "🔧 尝试不同方法停止服务..."

# 方法1: 尝试普通用户停止
pkill -f cloud_proxy_server.py 2>/dev/null || echo "普通用户无法停止进程"

# 方法2: 尝试使用sudo停止
sudo pkill -f cloud_proxy_server.py 2>/dev/null || echo "sudo停止失败或无sudo权限"

# 方法3: 尝试停止systemd服务
sudo systemctl stop lingxing-proxy 2>/dev/null || echo "无systemd服务或无权限"

# 方法4: 使用fuser强制停止端口
sudo fuser -k 8080/tcp 2>/dev/null || echo "fuser停止失败或无权限"

# 等待进程完全停止
sleep 2

echo "🔍 检查进程是否已停止..."
ps aux | grep cloud_proxy_server | grep -v grep || echo "进程已停止"

# 备份旧版本
echo "💾 备份旧版本..."
cp cloud_proxy_server.py cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "无旧版本需要备份"

# 启动新版本（使用当前用户权限）
echo "🚀 启动新版本..."
nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &
sleep 3

# 检查服务状态
echo "🔍 检查新服务状态..."
ps aux | grep cloud_proxy_server | grep -v grep

# 测试健康检查
echo "🧪 测试健康检查..."
curl -s http://localhost:8080/health

echo "✅ 更新完成！" 