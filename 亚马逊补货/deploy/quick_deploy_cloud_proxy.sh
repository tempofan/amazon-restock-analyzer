#!/bin/bash
# 快速部署脚本
echo "🔄 更新云代理服务器..."

# 停止当前服务
pkill -f cloud_proxy_server.py
sleep 2

# 备份当前版本
if [ -f cloud_proxy_server.py ]; then
    cp cloud_proxy_server.py cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份当前版本"
fi

# 启动新版本
nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &
sleep 3

# 检查状态
if ps aux | grep -q "[c]loud_proxy_server.py"; then
    echo "✅ 代理服务器启动成功"
    
    # 测试健康检查
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ 健康检查通过"
    else
        echo "❌ 健康检查失败"
    fi
    
    # 显示统计信息
    curl -s http://localhost:8080/stats
else
    echo "❌ 代理服务器启动失败"
    echo "查看日志: tail -n 20 proxy.log"
fi
