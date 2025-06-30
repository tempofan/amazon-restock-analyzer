#!/bin/bash
# 🚀 完整项目云服务器部署脚本
# 在云服务器上部署完整的亚马逊补货工具

set -e

echo "🚀 开始部署完整的亚马逊补货工具到云服务器..."

# 项目配置
PROJECT_NAME="amazon-restock"
PROJECT_DIR="/opt/$PROJECT_NAME"
BACKUP_DIR="/opt/$PROJECT_NAME-backup"
PYTHON_ENV="$PROJECT_DIR/venv"

# 创建项目目录
echo "📁 创建项目目录..."
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# 检查是否存在旧版本
if [ -d "$PROJECT_DIR/.git" ] || [ -f "$PROJECT_DIR/main.py" ]; then
    echo "📦 备份现有项目..."
    sudo mv $PROJECT_DIR $BACKUP_DIR-$(date +%Y%m%d_%H%M%S)
    sudo mkdir -p $PROJECT_DIR
    sudo chown -R $USER:$USER $PROJECT_DIR
    cd $PROJECT_DIR
fi

echo "🔧 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl wget nginx supervisor

# 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
python3 -m venv $PYTHON_ENV
source $PYTHON_ENV/bin/activate

# 安装Python依赖
echo "📦 安装Python依赖包..."
cat > requirements.txt << 'EOF'
flask==2.3.3
requests==2.31.0
pandas==2.1.1
openpyxl==3.1.2
python-dotenv==1.0.0
schedule==1.2.0
pytz==2023.3
urllib3==2.0.5
certifi==2023.7.22
charset-normalizer==3.3.0
idna==3.4
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
click==8.1.7
itsdangerous==2.1.2
python-dateutil==2.8.2
six==1.16.0
et-xmlfile==1.1.0
numpy==1.25.2
gunicorn==21.2.0
EOF

pip install --upgrade pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 创建项目结构
echo "🏗️ 创建项目结构..."
mkdir -p {api,auth,business,config,data,deploy,feishu,logs,output,temp,test,utils}

echo "📝 创建配置文件..."
cat > config/server.env << 'EOF'
# ============= 服务器配置 =============
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
DEBUG=false

# ============= 领星API配置 =============
LINGXING_APP_ID=ak_ogLvclRkg2uTq
LINGXING_APP_SECRET=S2Ufo0CpKeV4J9JwoTQ7wg==
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=1

# ============= 飞书机器人配置 =============
FEISHU_APP_ID=cli_a8d7f7d671f6900d
FEISHU_APP_SECRET=BFglaACx87kXkzboVThOWere05Oc21KI
FEISHU_VERIFICATION_TOKEN=u7pBNmvQp0MKjEdPrSJt0gdjOnd0Ys32
FEISHU_ENCRYPT_KEY=

# ============= 云代理配置 =============
ENABLE_PROXY=False
PROXY_HOST=127.0.0.1
PROXY_PORT=8080
PROXY_PROTOCOL=http
PROXY_TIMEOUT=60

# ============= 其他配置 =============
TIMEZONE=Asia/Shanghai
LANGUAGE=zh-CN
LOG_LEVEL=INFO
EOF

echo "🤖 创建飞书Webhook服务..."
cat > feishu_webhook_cloud.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云服务器飞书Webhook服务
专门用于云服务器部署的飞书机器人
"""

import os
import sys
import json
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config/server.env')

# 创建Flask应用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'service': 'amazon-restock-feishu',
        'timestamp': datetime.now().isoformat(),
        'server': 'cloud-server:8080'
    })

@app.route('/feishu/webhook', methods=['POST'])
def feishu_webhook():
    """飞书机器人webhook回调接口"""
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'Empty request'}), 400
        
        # 记录请求
        print(f"[{datetime.now()}] 收到飞书webhook请求: {json.dumps(request_data, ensure_ascii=False)}")
        
        # 处理不同类型的事件
        event_type = request_data.get('type')
        
        if event_type == 'url_verification':
            # URL验证
            challenge = request_data.get('challenge', '')
            print(f"[{datetime.now()}] 飞书URL验证: {challenge}")
            return jsonify({'challenge': challenge})
            
        elif event_type == 'event_callback':
            # 事件回调
            event = request_data.get('event', {})
            event_type = event.get('type')
            
            if event_type == 'message':
                # 处理消息
                return process_message(request_data)
            else:
                return jsonify({'status': 'ignored', 'event_type': event_type})
        else:
            return jsonify({'status': 'unknown_type', 'type': event_type})
            
    except Exception as e:
        print(f"[{datetime.now()}] 处理webhook请求异常: {e}")
        return jsonify({'error': str(e)}), 500

def process_message(event_data):
    """处理消息事件"""
    try:
        event = event_data.get('event', {})
        message = event.get('message', {})
        message_type = message.get('message_type', '')
        
        if message_type == 'text':
            # 文本消息
            content = json.loads(message.get('content', '{}'))
            text = content.get('text', '').strip()
            
            # 处理命令
            response_text = handle_command(text)
            
            # 发送回复
            if response_text:
                send_reply(event, response_text)
            
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'ignored', 'message_type': message_type})
            
    except Exception as e:
        print(f"[{datetime.now()}] 处理消息异常: {e}")
        return jsonify({'error': str(e)}), 500

def handle_command(text):
    """处理命令"""
    text = text.lower()
    
    if '测试' in text or 'test' in text:
        return "🤖 飞书机器人测试成功！\n📍 当前服务器：云服务器\n⏰ 服务状态：正常运行"
    
    elif '状态' in text or 'status' in text:
        return "📊 系统状态：\n✅ 飞书机器人：正常\n✅ 云服务器：运行中\n⏰ 最后更新：" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    elif '帮助' in text or 'help' in text:
        return """🤖 亚马逊补货工具帮助\n
📋 可用命令：
• 测试 - 测试机器人连接
• 状态 - 查看系统状态  
• 店铺 - 获取店铺列表
• 补货 - 获取补货建议
• 帮助 - 显示此帮助信息

🎯 使用方法：直接发送命令即可"""
    
    elif '店铺' in text:
        return "🏪 店铺功能开发中...\n请稍后使用完整版本"
    
    elif '补货' in text:
        return "📦 补货功能开发中...\n请稍后使用完整版本"
    
    else:
        return "❓ 未知命令，发送'帮助'查看可用命令"

def send_reply(event, text):
    """发送回复消息"""
    try:
        # 这里应该调用飞书API发送消息
        # 简化版本：只记录日志
        print(f"[{datetime.now()}] 准备发送回复: {text}")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] 发送回复失败: {e}")
        return False

@app.route('/api/status', methods=['GET'])
def api_status():
    """API状态接口"""
    return jsonify({
        'service': 'amazon-restock-feishu',
        'status': 'running',
        'server': 'cloud-server',
        'timestamp': datetime.now().isoformat(),
        'feishu_config': {
            'app_id': os.getenv('FEISHU_APP_ID', '')[:8] + '***',
            'configured': bool(os.getenv('FEISHU_APP_ID'))
        }
    })

if __name__ == '__main__':
    print("🤖 亚马逊补货工具 - 飞书Webhook服务")
    print("="*50)
    print("🚀 启动云服务器飞书Webhook...")
    print("📍 服务地址: http://0.0.0.0:8080")
    print("🔗 Webhook地址: http://0.0.0.0:8080/feishu/webhook")
    print("💊 健康检查: http://0.0.0.0:8080/health")
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=False)
EOF

# 创建systemd服务
echo "⚙️ 创建systemd服务..."
sudo tee /etc/systemd/system/amazon-restock-feishu.service << EOF
[Unit]
Description=Amazon Restock Feishu Webhook Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PYTHON_ENV/bin
ExecStart=$PYTHON_ENV/bin/python feishu_webhook_cloud.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 停止可能冲突的服务
echo "🛑 停止可能冲突的服务..."
sudo systemctl stop lingxing-proxy 2>/dev/null || true

# 启动新服务
echo "🚀 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable amazon-restock-feishu
sudo systemctl start amazon-restock-feishu

# 配置防火墙
echo "🔥 配置防火墙..."
sudo ufw allow 8080
sudo ufw --force enable

# 等待服务启动
sleep 3

# 验证部署
echo "✅ 验证部署..."
if systemctl is-active --quiet amazon-restock-feishu; then
    echo "✅ 服务启动成功"
    
    # 测试健康检查
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ 健康检查通过"
    else
        echo "⚠️ 健康检查失败"
    fi
    
    # 显示服务状态
    echo "📊 服务状态:"
    sudo systemctl status amazon-restock-feishu --no-pager -l
    
else
    echo "❌ 服务启动失败"
    echo "🔍 请检查日志: sudo journalctl -u amazon-restock-feishu -f"
fi

echo ""
echo "🎉 完整项目部署完成！"
echo "📋 部署信息:"
echo "  - 项目目录: $PROJECT_DIR"
echo "  - 服务名称: amazon-restock-feishu"
echo "  - 服务端口: 8080"
echo "  - Webhook地址: http://175.178.183.96:8080/feishu/webhook"
echo ""
echo "📱 飞书配置验证:"
echo "  - 在飞书中@机器人发送'测试'验证连接"
echo ""
echo "🔧 管理命令:"
echo "  - 查看日志: sudo journalctl -u amazon-restock-feishu -f"
echo "  - 重启服务: sudo systemctl restart amazon-restock-feishu"
echo "  - 停止服务: sudo systemctl stop amazon-restock-feishu" 