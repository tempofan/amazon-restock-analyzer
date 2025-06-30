# -*- coding: utf-8 -*-
"""
飞书Webhook服务器
接收和处理飞书机器人的回调请求
"""

import json
import os
import sys
from flask import Flask, request, jsonify
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu.feishu_bot import FeishuBot
from utils.logger import api_logger
from config.config import ServerConfig

# 创建Flask应用
app = Flask(__name__)

# 初始化飞书机器人
feishu_bot = FeishuBot()

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'server': f"{ServerConfig.HOST}:{ServerConfig.PORT}"
    })

@app.route('/feishu/webhook', methods=['POST'])
def feishu_webhook():
    """
    飞书机器人webhook回调接口
    """
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        if not request_data:
            api_logger.log_error("收到空的webhook请求")
            return jsonify({'error': 'Empty request'}), 400
        
        # 记录接收到的请求
        api_logger.log_info(f"收到飞书webhook请求: {json.dumps(request_data, ensure_ascii=False)}")
        
        # 处理不同类型的事件
        event_type = request_data.get('type')
        
        if event_type == 'url_verification':
            # URL验证
            challenge = request_data.get('challenge', '')
            api_logger.log_info(f"飞书URL验证: {challenge}")
            return jsonify({'challenge': challenge})
            
        elif event_type == 'event_callback':
            # 事件回调
            event_data = request_data
            
            # 验证签名（如果配置了）
            headers = request.headers
            timestamp = headers.get('X-Lark-Request-Timestamp', '')
            nonce = headers.get('X-Lark-Request-Nonce', '')
            signature = headers.get('X-Lark-Signature', '')
            body = request.get_data(as_text=True)
            
            # 这里可以添加签名验证逻辑
            # if not feishu_bot.verify_signature(timestamp, nonce, body, signature):
            #     return jsonify({'error': 'Invalid signature'}), 401
            
            # 处理消息事件
            event = event_data.get('event', {})
            inner_event_type = event.get('type')
            
            if inner_event_type == 'message':
                # 处理消息
                result = feishu_bot.process_message(event_data)
                return jsonify(result)
            else:
                api_logger.log_info(f"收到未处理的事件类型: {inner_event_type}")
                return jsonify({'status': 'ignored', 'event_type': inner_event_type})
        else:
            api_logger.log_info(f"收到未知的请求类型: {event_type}")
            return jsonify({'status': 'unknown_type', 'type': event_type})
            
    except Exception as e:
        api_logger.log_error(e, "处理飞书webhook请求异常")
        return jsonify({'error': str(e)}), 500

@app.route('/feishu/test', methods=['POST'])
def test_feishu_message():
    """
    测试飞书消息发送接口
    """
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        message = data.get('message', '这是一条测试消息')
        
        if not chat_id:
            return jsonify({'error': 'chat_id is required'}), 400
        
        # 发送测试消息
        success = feishu_bot.send_text_message(chat_id, message)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Test message sent'})
        else:
            return jsonify({'status': 'failed', 'message': 'Failed to send message'}), 500
            
    except Exception as e:
        api_logger.log_error(e, "发送测试消息异常")
        return jsonify({'error': str(e)}), 500

@app.route('/feishu/command', methods=['POST'])
def execute_command():
    """
    直接执行命令接口（用于测试）
    """
    try:
        data = request.get_json()
        command = data.get('command', '')
        chat_id = data.get('chat_id', '')
        
        if not command:
            return jsonify({'error': 'command is required'}), 400
        
        # 处理命令
        response = feishu_bot._process_command(command, 'test_user')
        
        # 如果提供了chat_id，发送消息
        if chat_id and response:
            feishu_bot.send_text_message(chat_id, response)
        
        return jsonify({
            'status': 'success',
            'command': command,
            'response': response
        })
        
    except Exception as e:
        api_logger.log_error(e, "执行命令异常")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """
    API状态接口
    """
    try:
        from api.client import APIClient
        client = APIClient()
        result = client.test_connection()
        
        return jsonify({
            'feishu_bot': {
                'app_id': feishu_bot.app_id[:8] + '***' if feishu_bot.app_id else 'Not configured',
                'has_token': bool(feishu_bot.access_token),
                'token_expire': datetime.fromtimestamp(feishu_bot.token_expire_time).isoformat() if feishu_bot.token_expire_time else None
            },
            'api_connection': result,
            'server': {
                'host': ServerConfig.HOST,
                'port': ServerConfig.PORT,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        api_logger.log_error(e, "获取API状态异常")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """
    404错误处理
    """
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """
    500错误处理
    """
    api_logger.log_error(f"服务器内部错误: {error}")
    return jsonify({'error': 'Internal server error'}), 500

def create_app():
    """
    创建并配置Flask应用
    """
    # 配置应用
    app.config['DEBUG'] = ServerConfig.DEBUG
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON
    
    return app

def run_server():
    """
    运行webhook服务器
    """
    try:
        print(f"🚀 启动飞书Webhook服务器...")
        print(f"📍 服务地址: http://{ServerConfig.HOST}:{ServerConfig.PORT}")
        print(f"🔗 Webhook地址: http://{ServerConfig.HOST}:{ServerConfig.PORT}/feishu/webhook")
        print(f"💊 健康检查: http://{ServerConfig.HOST}:{ServerConfig.PORT}/health")
        print(f"📊 状态接口: http://{ServerConfig.HOST}:{ServerConfig.PORT}/api/status")
        print()
        
        # 验证飞书配置
        if not feishu_bot.app_id or not feishu_bot.app_secret:
            print("⚠️ 警告: 飞书机器人配置不完整，请在环境变量中配置：")
            print("  - FEISHU_APP_ID")
            print("  - FEISHU_APP_SECRET")
            print("  - FEISHU_VERIFICATION_TOKEN (可选)")
            print("  - FEISHU_ENCRYPT_KEY (可选)")
            print()
        
        # 运行服务器
        app.run(
            host=ServerConfig.HOST,
            port=ServerConfig.PORT,
            debug=ServerConfig.DEBUG,
            threaded=True
        )
        
    except Exception as e:
        api_logger.log_error(e, "启动webhook服务器失败")
        print(f"❌ 启动服务器失败: {e}")

if __name__ == '__main__':
    app = create_app()
    run_server()