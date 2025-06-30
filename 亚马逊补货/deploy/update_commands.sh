#!/bin/bash
# 云代理服务器更新脚本

echo "🔄 开始更新云代理服务器..."

# 停止旧版本服务
echo "🛑 停止旧版本服务..."
pkill -f cloud_proxy_server.py
sleep 2

# 备份旧版本
echo "💾 备份旧版本..."
cp cloud_proxy_server.py cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "无旧版本需要备份"

# 启动新版本
echo "🚀 启动新版本..."
nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &
sleep 3

# 检查服务状态
echo "🔍 检查服务状态..."
ps aux | grep cloud_proxy_server | grep -v grep

# 测试健康检查
echo "🧪 测试健康检查..."
curl -s http://localhost:8080/health

echo "✅ 更新完成！" 