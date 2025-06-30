#!/bin/bash
# 🚀 云代理服务器部署脚本
# 在云服务器上运行此脚本来部署API代理服务

set -e

echo "🌐 开始部署领星API云代理服务器..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本要求3.7+，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 创建项目目录
PROJECT_DIR="/opt/lingxing-proxy"
echo "📁 创建项目目录: $PROJECT_DIR"
sudo mkdir -p $PROJECT_DIR
sudo chown $(whoami):$(whoami) $PROJECT_DIR
cd $PROJECT_DIR

# 创建虚拟环境
echo "🔧 创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖包..."
if [ -f "proxy_requirements.txt" ]; then
    pip install -r proxy_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
else
    echo "📋 从国内镜像安装基础依赖..."
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
        Flask==2.3.3 \
        flask-cors==4.0.0 \
        requests==2.31.0 \
        urllib3==2.0.7 \
        python-dateutil==2.8.2
fi

# 复制代理服务器文件
echo "📋 复制代理服务器文件..."
if [ ! -f "cloud_proxy_server.py" ]; then
    echo "⚠️ 请将 cloud_proxy_server.py 文件上传到当前目录"
    echo "📍 当前目录: $(pwd)"
    exit 1
fi

# 创建systemd服务文件
echo "⚙️ 创建系统服务..."
sudo tee /etc/systemd/system/lingxing-proxy.service > /dev/null <<EOF
[Unit]
Description=LingXing API Proxy Server
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python cloud_proxy_server.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 创建日志目录
echo "📝 创建日志目录..."
mkdir -p logs

# 配置防火墙（如果使用ufw）
if command -v ufw >/dev/null 2>&1; then
    echo "🔥 配置防火墙规则..."
    sudo ufw allow 8080/tcp
    echo "✅ 已开放端口8080"
fi

# 启用并启动服务
echo "🚀 启动代理服务..."
sudo systemctl daemon-reload
sudo systemctl enable lingxing-proxy
sudo systemctl start lingxing-proxy

# 检查服务状态
sleep 3
if sudo systemctl is-active --quiet lingxing-proxy; then
    echo "✅ 代理服务启动成功！"
    
    # 获取服务器IP
    SERVER_IP=$(curl -s http://checkip.amazonaws.com/ || curl -s http://ipinfo.io/ip || echo "未知IP")
    
    echo ""
    echo "🎉 部署完成！"
    echo "🌐 服务器IP: $SERVER_IP"
    echo "🔗 代理服务地址: http://$SERVER_IP:8080"
    echo "🔍 健康检查: http://$SERVER_IP:8080/health"
    echo "📊 统计信息: http://$SERVER_IP:8080/stats"
    echo "🧪 连接测试: http://$SERVER_IP:8080/test"
    echo ""
    echo "📝 接下来的步骤："
    echo "1. 在领星ERP后台将此IP添加到白名单: $SERVER_IP"
    echo "2. 修改本机项目配置文件，将API地址指向: http://$SERVER_IP:8080/api/proxy"
    echo "3. 重启本机项目服务"
    echo ""
    echo "📋 管理命令："
    echo "  查看服务状态: sudo systemctl status lingxing-proxy"
    echo "  查看日志: sudo journalctl -u lingxing-proxy -f"
    echo "  重启服务: sudo systemctl restart lingxing-proxy"
    echo "  停止服务: sudo systemctl stop lingxing-proxy"
    
else
    echo "❌ 代理服务启动失败！"
    echo "📋 查看错误日志:"
    sudo journalctl -u lingxing-proxy --no-pager
    exit 1
fi 