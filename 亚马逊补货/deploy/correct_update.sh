#!/bin/bash
# 正确的云代理服务器更新脚本

echo "🔍 云代理服务器正确更新流程"
echo "================================"

# 1. 停止systemd服务
echo "🛑 停止lingxing-proxy服务..."
sudo systemctl stop lingxing-proxy
sleep 2

# 2. 备份旧版本
echo "💾 备份旧版本..."
sudo cp /opt/lingxing-proxy/cloud_proxy_server.py /opt/lingxing-proxy/cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "无旧版本需要备份"

# 3. 复制新版本到正确位置
echo "📁 复制新版本到/opt/lingxing-proxy/..."
sudo cp ~/cloud_proxy_server.py /opt/lingxing-proxy/

# 4. 设置正确权限
echo "🔧 设置文件权限..."
sudo chown root:root /opt/lingxing-proxy/cloud_proxy_server.py
sudo chmod 755 /opt/lingxing-proxy/cloud_proxy_server.py

# 5. 重新启动服务
echo "🚀 重新启动lingxing-proxy服务..."
sudo systemctl start lingxing-proxy
sleep 3

# 6. 检查服务状态
echo "🔍 检查服务状态..."
sudo systemctl status lingxing-proxy --no-pager

# 7. 测试健康检查
echo "🧪 测试健康检查..."
curl -s http://localhost:8080/health

# 8. 测试新功能
echo "🧪 测试飞书功能..."
curl -X POST http://localhost:8080/feishu/webhook \
  -H 'Content-Type: application/json' \
  -d '{"type": "url_verification", "challenge": "test123"}'

echo
echo "🧪 测试统计功能..."
curl -s http://localhost:8080/stats

echo
echo "✅ 更新完成！" 