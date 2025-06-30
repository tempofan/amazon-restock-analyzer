#!/bin/bash
"""
快速部署修复版云代理服务器
"""

set -e

echo "🚀 开始部署修复版云代理服务器..."

# 云服务器信息
CLOUD_HOST="175.178.183.96"
CLOUD_USER="ubuntu"
CLOUD_PASSWORD="woAIni34"
SERVICE_DIR="/opt/lingxing-proxy"

echo "🔄 停止当前服务..."
sshpass -p "$CLOUD_PASSWORD" ssh "$CLOUD_USER@$CLOUD_HOST" "sudo systemctl stop lingxing-proxy" || true

echo "📁 备份当前服务器文件..."
sshpass -p "$CLOUD_PASSWORD" ssh "$CLOUD_USER@$CLOUD_HOST" "sudo cp $SERVICE_DIR/cloud_proxy_server.py $SERVICE_DIR/cloud_proxy_server.py.backup"

echo "📤 上传修复版服务器..."
sshpass -p "$CLOUD_PASSWORD" scp deploy/cloud_proxy_server_simple.py "$CLOUD_USER@$CLOUD_HOST:/tmp/cloud_proxy_server_fixed.py"

echo "🔧 安装修复版服务器..."
sshpass -p "$CLOUD_PASSWORD" ssh "$CLOUD_USER@$CLOUD_HOST" "
sudo cp /tmp/cloud_proxy_server_fixed.py $SERVICE_DIR/cloud_proxy_server.py
sudo chown root:root $SERVICE_DIR/cloud_proxy_server.py
sudo chmod 755 $SERVICE_DIR/cloud_proxy_server.py
"

echo "📦 安装依赖包..."
sshpass -p "$CLOUD_PASSWORD" ssh "$CLOUD_USER@$CLOUD_HOST" "
cd $SERVICE_DIR
sudo ./venv/bin/pip install websockets
"

echo "🔄 重启服务..."
sshpass -p "$CLOUD_PASSWORD" ssh "$CLOUD_USER@$CLOUD_HOST" "sudo systemctl start lingxing-proxy"

echo "⏳ 等待服务启动..."
sleep 5

echo "🔍 检查服务状态..."
sshpass -p "$CLOUD_PASSWORD" ssh "$CLOUD_USER@$CLOUD_HOST" "sudo systemctl status lingxing-proxy --no-pager -l"

echo "✅ 修复版云代理服务器部署完成！"
echo "🌐 HTTP服务: http://$CLOUD_HOST:8080"
echo "🔌 WebSocket服务: ws://$CLOUD_HOST:8081"
echo "💊 健康检查: http://$CLOUD_HOST:8080/health" 