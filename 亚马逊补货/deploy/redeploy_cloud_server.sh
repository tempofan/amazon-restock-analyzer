#!/bin/bash
# Cloud Server Redeployment Script
# Complete redeployment of cloud server to fix existing code defects

set -e  # 遇到错误立即退出

echo "🚀 开始云服务器重新部署"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 停止现有服务
stop_existing_services() {
    log_step "1️⃣ 停止现有服务..."
    
    # 停止可能存在的服务
    systemctl stop lingxing-proxy 2>/dev/null || true
    systemctl stop feishu-cloud-server 2>/dev/null || true
    
    # 杀死可能占用端口的进程
    pkill -f "python.*cloud_proxy" 2>/dev/null || true
    pkill -f "python.*8080" 2>/dev/null || true
    
    # 等待进程完全停止
    sleep 3
    
    log_info "✅ 现有服务已停止"
}

# 备份现有配置
backup_existing_config() {
    log_step "2️⃣ 备份现有配置..."
    
    BACKUP_DIR="/opt/backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份现有文件
    if [ -d "/opt/lingxing-proxy" ]; then
        cp -r /opt/lingxing-proxy "$BACKUP_DIR/" 2>/dev/null || true
        log_info "✅ 已备份现有配置到: $BACKUP_DIR"
    fi
    
    # 备份环境变量文件
    if [ -f "/etc/environment" ]; then
        cp /etc/environment "$BACKUP_DIR/environment.bak" 2>/dev/null || true
    fi
}

# 安装依赖
install_dependencies() {
    log_step "3️⃣ 安装系统依赖..."
    
    # 更新包管理器
    apt update -qq
    
    # 安装Python和必要工具
    apt install -y python3 python3-pip python3-venv git curl wget
    
    # 安装Python包 (跳过pip升级以避免系统包冲突)
    pip3 install flask flask-cors requests python-dotenv --break-system-packages
    
    log_info "✅ 系统依赖安装完成"
}

# 创建新的部署目录
create_deployment_directory() {
    log_step "4️⃣ 创建部署目录..."
    
    # 创建新的部署目录
    DEPLOY_DIR="/opt/feishu-cloud-server"
    rm -rf "$DEPLOY_DIR" 2>/dev/null || true
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR/logs"
    
    # 设置权限
    chown -R ubuntu:ubuntu "$DEPLOY_DIR" 2>/dev/null || true
    chmod -R 755 "$DEPLOY_DIR"
    
    log_info "✅ 部署目录创建完成: $DEPLOY_DIR"
    echo "$DEPLOY_DIR" > /tmp/deploy_dir
}

# 部署新代码
deploy_new_code() {
    log_step "5️⃣ 部署新代码..."
    
    DEPLOY_DIR=$(cat /tmp/deploy_dir)
    
    # 复制新的服务器代码
    if [ -f "cloud_server_redeploy.py" ]; then
        cp cloud_server_redeploy.py "$DEPLOY_DIR/server.py"
        log_info "✅ 新服务器代码已部署"
    else
        log_error "❌ 找不到新的服务器代码文件"
        exit 1
    fi
    
    # 创建启动脚本
    cat > "$DEPLOY_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /opt/feishu-cloud-server
export PYTHONPATH=/opt/feishu-cloud-server:$PYTHONPATH
python3 server.py
EOF
    
    chmod +x "$DEPLOY_DIR/start.sh"
    
    # 创建环境变量模板
    cat > "$DEPLOY_DIR/.env.template" << 'EOF'
# 飞书应用配置
FEISHU_APP_ID=cli_your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_VERIFICATION_TOKEN=your_verification_token

# 领星API配置（可选）
LINGXING_APP_ID=your_lingxing_app_id
LINGXING_APP_SECRET=your_lingxing_app_secret
EOF
    
    log_info "✅ 新代码部署完成"
}

# 创建systemd服务
create_systemd_service() {
    log_step "6️⃣ 创建系统服务..."
    
    DEPLOY_DIR=$(cat /tmp/deploy_dir)
    
    # 创建systemd服务文件
    cat > /etc/systemd/system/feishu-cloud-server.service << EOF
[Unit]
Description=Feishu Cloud Server v2.0
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$DEPLOY_DIR
Environment=PYTHONPATH=$DEPLOY_DIR
EnvironmentFile=-$DEPLOY_DIR/.env
ExecStart=/usr/bin/python3 $DEPLOY_DIR/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=feishu-cloud-server

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DEPLOY_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    systemctl daemon-reload
    systemctl enable feishu-cloud-server
    
    log_info "✅ 系统服务创建完成"
}

# 配置防火墙
configure_firewall() {
    log_step "7️⃣ 配置防火墙..."
    
    # 检查ufw是否安装
    if command -v ufw >/dev/null 2>&1; then
        # 允许8080端口
        ufw allow 8080/tcp
        log_info "✅ 防火墙规则已更新 (ufw)"
    fi
    
    # 检查iptables
    if command -v iptables >/dev/null 2>&1; then
        # 确保8080端口开放
        iptables -C INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null || \
        iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
        log_info "✅ 防火墙规则已更新 (iptables)"
    fi
}

# 启动新服务
start_new_service() {
    log_step "8️⃣ 启动新服务..."
    
    # 启动服务
    systemctl start feishu-cloud-server
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if systemctl is-active --quiet feishu-cloud-server; then
        log_info "✅ 新服务启动成功"
        
        # 显示服务状态
        systemctl status feishu-cloud-server --no-pager -l
    else
        log_error "❌ 新服务启动失败"
        log_info "查看日志: journalctl -u feishu-cloud-server -f"
        exit 1
    fi
}

# 验证部署
verify_deployment() {
    log_step "9️⃣ 验证部署..."
    
    # 等待服务完全启动
    sleep 10
    
    # 测试健康检查接口
    if curl -s http://localhost:8080/health >/dev/null; then
        log_info "✅ 健康检查接口正常"
    else
        log_warn "⚠️ 健康检查接口无响应"
    fi
    
    # 测试统计接口
    if curl -s http://localhost:8080/stats >/dev/null; then
        log_info "✅ 统计接口正常"
    else
        log_warn "⚠️ 统计接口无响应"
    fi
    
    # 显示服务信息
    echo ""
    log_info "🎉 云服务器重新部署完成！"
    echo ""
    echo "📋 服务信息:"
    echo "  • 服务名称: feishu-cloud-server"
    echo "  • 服务地址: http://$(curl -s ifconfig.me):8080"
    echo "  • 健康检查: http://$(curl -s ifconfig.me):8080/health"
    echo "  • 飞书Webhook: http://$(curl -s ifconfig.me):8080/feishu/webhook"
    echo "  • 统计信息: http://$(curl -s ifconfig.me):8080/stats"
    echo ""
    echo "🔧 管理命令:"
    echo "  • 查看状态: systemctl status feishu-cloud-server"
    echo "  • 查看日志: journalctl -u feishu-cloud-server -f"
    echo "  • 重启服务: systemctl restart feishu-cloud-server"
    echo "  • 停止服务: systemctl stop feishu-cloud-server"
    echo ""
    echo "⚙️ 配置文件:"
    echo "  • 服务代码: $(cat /tmp/deploy_dir)/server.py"
    echo "  • 环境变量: $(cat /tmp/deploy_dir)/.env"
    echo "  • 环境模板: $(cat /tmp/deploy_dir)/.env.template"
    echo ""
}

# 显示配置说明
show_configuration_guide() {
    DEPLOY_DIR=$(cat /tmp/deploy_dir)
    
    echo "📝 配置说明:"
    echo "=================================="
    echo ""
    echo "1️⃣ 配置飞书应用信息:"
    echo "   编辑文件: $DEPLOY_DIR/.env"
    echo "   参考模板: $DEPLOY_DIR/.env.template"
    echo ""
    echo "2️⃣ 必需的环境变量:"
    echo "   FEISHU_APP_ID=cli_your_app_id"
    echo "   FEISHU_APP_SECRET=your_app_secret"
    echo ""
    echo "3️⃣ 配置完成后重启服务:"
    echo "   systemctl restart feishu-cloud-server"
    echo ""
    echo "4️⃣ 在飞书开放平台配置Webhook URL:"
    echo "   http://$(curl -s ifconfig.me):8080/feishu/webhook"
    echo ""
    echo "🎯 下一步操作:"
    echo "   1. 配置环境变量"
    echo "   2. 重启服务"
    echo "   3. 在飞书中测试机器人"
    echo ""
}

# 主函数
main() {
    echo "🚀 云服务器重新部署开始"
    echo "时间: $(date)"
    echo "=================================="
    
    # 检查权限
    check_root
    
    # 执行部署步骤
    stop_existing_services
    backup_existing_config
    install_dependencies
    create_deployment_directory
    deploy_new_code
    create_systemd_service
    configure_firewall
    start_new_service
    verify_deployment
    
    # 显示配置说明
    show_configuration_guide
    
    echo ""
    echo "🎉 云服务器重新部署完成！"
    echo "=================================="
    
    # 清理临时文件
    rm -f /tmp/deploy_dir
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"
