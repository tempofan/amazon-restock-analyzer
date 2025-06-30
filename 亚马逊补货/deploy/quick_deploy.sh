#!/bin/bash
# 🚀 快速部署飞书Webhook服务到云服务器

echo "🚀 开始快速部署飞书Webhook服务..."

# 安装基础环境
apt-get update && apt-get install -y python3 python3-pip python3-venv

# 创建项目目录
mkdir -p /opt/feishu-webhook
cd /opt/feishu-webhook

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install flask requests python-dotenv

# 创建应用文件
cat > app.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书Webhook服务 - 云服务器版"""

import os
import json
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'service': 'feishu-webhook',
        'timestamp': datetime.now().isoformat(),
        'server': 'cloud-server:8080'
    })

@app.route('/feishu/webhook', methods=['POST', 'GET'])
def feishu_webhook():
    """飞书机器人webhook回调接口"""
    try:
        if request.method == 'GET':
            return jsonify({'message': 'Feishu Webhook Service is running'})
            
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
            
            print(f"[{datetime.now()}] 处理命令: {text} -> {response_text}")
            
            return jsonify({'status': 'success', 'response': response_text})
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
        return f"📊 系统状态：\n✅ 飞书机器人：正常\n✅ 云服务器：运行中\n⏰ 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    elif '帮助' in text or 'help' in text:
        return """🤖 亚马逊补货工具帮助

📋 可用命令：
• 测试 - 测试机器人连接
• 状态 - 查看系统状态  
• 帮助 - 显示此帮助信息

🎯 使用方法：直接发送命令即可
📍 服务器：云服务器 175.178.183.96:8080"""
    
    else:
        return "❓ 未知命令，发送'帮助'查看可用命令"

if __name__ == '__main__':
    print("🤖 飞书Webhook服务 - 云服务器版")
    print("="*50)
    print("🚀 启动飞书Webhook服务...")
    print("📍 服务地址: http://0.0.0.0:8080")
    print("🔗 Webhook地址: http://0.0.0.0:8080/feishu/webhook")
    print("💊 健康检查: http://0.0.0.0:8080/health")
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=False)
EOF

# 创建systemd服务
cat > /etc/systemd/system/feishu-webhook.service << 'EOF'
[Unit]
Description=Feishu Webhook Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/feishu-webhook
Environment=PATH=/opt/feishu-webhook/venv/bin
ExecStart=/opt/feishu-webhook/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 停止可能冲突的服务
systemctl stop lingxing-proxy 2>/dev/null || true

# 启动服务
systemctl daemon-reload
systemctl enable feishu-webhook
systemctl start feishu-webhook

# 配置防火墙
ufw allow 8080
ufw --force enable

# 等待服务启动
sleep 3

# 验证部署
if systemctl is-active --quiet feishu-webhook; then
    echo "✅ 飞书Webhook服务启动成功"
    
    # 测试健康检查
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ 健康检查通过"
    else
        echo "⚠️ 健康检查失败"
    fi
    
    # 显示服务状态
    echo "📊 服务状态:"
    systemctl status feishu-webhook --no-pager -l
    
else
    echo "❌ 服务启动失败"
    echo "🔍 请检查日志: journalctl -u feishu-webhook -f"
fi

echo ""
echo "🎉 飞书Webhook服务部署完成！"
echo "📋 部署信息:"
echo "  - 项目目录: /opt/feishu-webhook"
echo "  - 服务名称: feishu-webhook"
echo "  - 服务端口: 8080"
echo "  - Webhook地址: http://175.178.183.96:8080/feishu/webhook"
echo ""
echo "📱 飞书配置验证:"
echo "  - 在飞书中@机器人发送'测试'验证连接" 