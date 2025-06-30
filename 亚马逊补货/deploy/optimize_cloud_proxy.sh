#!/bin/bash
# 🚀 云代理服务器优化脚本
# 优化云代理服务器的性能、监控和稳定性

set -e

echo "🔧 开始优化云代理服务器..."

PROJECT_DIR="/opt/lingxing-proxy"
cd $PROJECT_DIR

# 1. 创建监控脚本
echo "📊 创建监控脚本..."
cat > monitor_proxy.sh << 'EOF'
#!/bin/bash
# 云代理服务器监控脚本

LOG_FILE="/opt/lingxing-proxy/logs/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 检查服务状态
if systemctl is-active --quiet lingxing-proxy; then
    STATUS="运行中"
    # 检查端口监听
    if netstat -tln | grep -q ":8080 "; then
        PORT_STATUS="正常"
    else
        PORT_STATUS="异常"
        echo "[$DATE] 警告: 端口8080未监听" >> $LOG_FILE
    fi
    
    # 检查内存使用
    MEM_USAGE=$(ps aux | grep "cloud_proxy_server.py" | grep -v grep | awk '{print $4}')
    if (( $(echo "$MEM_USAGE > 50" | bc -l) )); then
        echo "[$DATE] 警告: 内存使用率过高 ${MEM_USAGE}%" >> $LOG_FILE
    fi
    
    echo "[$DATE] 服务状态: $STATUS, 端口: $PORT_STATUS, 内存: ${MEM_USAGE}%" >> $LOG_FILE
else
    STATUS="已停止"
    echo "[$DATE] 错误: 代理服务已停止，尝试重启..." >> $LOG_FILE
    systemctl start lingxing-proxy
fi
EOF

chmod +x monitor_proxy.sh

# 2. 创建性能统计脚本
echo "📈 创建性能统计脚本..."
cat > stats_collector.sh << 'EOF'
#!/bin/bash
# 性能统计收集脚本

STATS_FILE="/opt/lingxing-proxy/logs/daily_stats.log"
DATE=$(date '+%Y-%m-%d')

# 获取代理服务器统计
STATS=$(curl -s http://localhost:8080/stats 2>/dev/null || echo '{"error": "无法获取统计"}')

echo "[$DATE] 性能统计: $STATS" >> $STATS_FILE

# 清理7天前的日志
find /opt/lingxing-proxy/logs -name "*.log" -mtime +7 -delete
EOF

chmod +x stats_collector.sh

# 3. 配置定时任务
echo "⏰ 配置定时监控任务..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/lingxing-proxy/monitor_proxy.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 0 * * * /opt/lingxing-proxy/stats_collector.sh") | crontab -

# 4. 优化系统配置
echo "⚙️ 优化系统配置..."

# 增加文件描述符限制
echo "lingxing soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "lingxing hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化网络参数
cat >> /etc/sysctl.conf << 'EOF'
# 云代理服务器网络优化
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
EOF

sysctl -p

# 5. 创建备份脚本
echo "💾 创建配置备份脚本..."
cat > backup_config.sh << 'EOF'
#!/bin/bash
# 配置备份脚本

BACKUP_DIR="/opt/lingxing-proxy/backups"
DATE=$(date '+%Y%m%d_%H%M%S')

mkdir -p $BACKUP_DIR

# 备份代理服务器文件
tar -czf "$BACKUP_DIR/proxy_backup_$DATE.tar.gz" \
    cloud_proxy_server.py \
    proxy_requirements.txt \
    logs/ \
    --exclude='logs/*.log'

# 保留最近7天的备份
find $BACKUP_DIR -name "proxy_backup_*.tar.gz" -mtime +7 -delete

echo "配置备份完成: proxy_backup_$DATE.tar.gz"
EOF

chmod +x backup_config.sh

# 6. 重启服务应用优化
echo "🔄 重启服务应用优化..."
sudo systemctl daemon-reload
sudo systemctl restart lingxing-proxy

# 等待服务启动
sleep 5

# 7. 验证优化效果
echo "✅ 验证优化效果..."
if systemctl is-active --quiet lingxing-proxy; then
    echo "✅ 代理服务运行正常"
    
    # 测试健康检查
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ 健康检查通过"
    else
        echo "⚠️ 健康检查失败"
    fi
    
    # 显示服务信息
    echo "📊 服务信息:"
    systemctl status lingxing-proxy --no-pager -l
    
    echo ""
    echo "🎉 云代理服务器优化完成！"
    echo "📋 新增功能:"
    echo "  - 自动监控（每5分钟检查一次）"
    echo "  - 性能统计（每日收集）"
    echo "  - 日志轮转（保留7天）"
    echo "  - 配置备份（手动执行 ./backup_config.sh）"
    echo "  - 系统优化（网络参数调优）"
    
else
    echo "❌ 代理服务启动失败"
    echo "🔍 请检查日志: sudo journalctl -u lingxing-proxy -f"
fi 