#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书机器人服务器启动脚本
专门用于启动飞书Webhook服务器
"""

import os
import sys
from flask import Flask, request, jsonify
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu.feishu_bot import FeishuBot
from utils.logger import api_logger

# 飞书机器人专用配置
FEISHU_HOST = '0.0.0.0'
FEISHU_PORT = 5000

# 创建Flask应用
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON

# 初始化飞书机器人
try:
    feishu_bot = FeishuBot()
    print(f"✅ 飞书机器人初始化成功")
except Exception as e:
    print(f"❌ 飞书机器人初始化失败: {e}")
    feishu_bot = None

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'service': 'feishu-webhook',
        'timestamp': datetime.now().isoformat(),
        'server': f"{FEISHU_HOST}:{FEISHU_PORT}",
        'feishu_bot_status': 'ready' if feishu_bot else 'error'
    })

@app.route('/feishu/webhook', methods=['POST'])
def feishu_webhook():
    """飞书机器人webhook回调接口"""
    if not feishu_bot:
        return jsonify({'error': 'Feishu bot not initialized'}), 500
        
    try:
        # 获取请求数据
        request_data = request.get_json()
        
        if not request_data:
            api_logger.log_error("收到空的webhook请求")
            return jsonify({'error': 'Empty request'}), 400
        
        # 记录接收到的请求
        api_logger.log_info(f"收到飞书webhook请求: {request_data}")
        
        # 检查是否为飞书2.0格式 (schema: 2.0)
        schema = request_data.get('schema')
        if schema == '2.0':
            # 飞书2.0格式处理
            header = request_data.get('header', {})
            event_type = header.get('event_type', '')
            
            api_logger.log_info(f"飞书2.0格式消息，事件类型: {event_type}")
            
            if event_type == 'im.message.receive_v1':
                # 处理接收消息事件
                result = feishu_bot.process_message(request_data)
                return jsonify(result)
            else:
                api_logger.log_info(f"收到未处理的2.0事件类型: {event_type}")
                return jsonify({'status': 'ignored', 'event_type': event_type})
        else:
            # 传统格式处理
            event_type = request_data.get('type')
            
            if event_type == 'url_verification':
                # URL验证
                challenge = request_data.get('challenge', '')
                api_logger.log_info(f"飞书URL验证: {challenge}")
                return jsonify({'challenge': challenge})
                
            elif event_type == 'event_callback':
                # 事件回调
                event = request_data.get('event', {})
                event_type = event.get('type')
                
                if event_type == 'message':
                    # 处理消息
                    result = feishu_bot.process_message(request_data)
                    return jsonify(result)
                else:
                    api_logger.log_info(f"收到未处理的事件类型: {event_type}")
                    return jsonify({'status': 'ignored', 'event_type': event_type})
            else:
                api_logger.log_info(f"收到未知的请求类型: {event_type}")
                return jsonify({'status': 'unknown_type', 'type': event_type})
            
    except Exception as e:
        api_logger.log_error(e, "处理飞书webhook请求异常")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """API状态接口"""
    try:
        from api.client import APIClient
        client = APIClient()
        result = client.test_connection()
        
        return jsonify({
            'feishu_bot': {
                'app_id': feishu_bot.app_id[:8] + '***' if feishu_bot and feishu_bot.app_id else 'Not configured',
                'has_token': bool(feishu_bot.access_token) if feishu_bot else False,
                'status': 'ready' if feishu_bot else 'error'
            },
            'api_connection': result,
            'server': {
                'host': FEISHU_HOST,
                'port': FEISHU_PORT,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        api_logger.log_error(e, "获取API状态异常")
        return jsonify({'error': str(e)}), 500

@app.route('/feishu/command', methods=['POST'])
def execute_command():
    """直接执行命令接口（用于测试）"""
    if not feishu_bot:
        return jsonify({'error': 'Feishu bot not initialized'}), 500
        
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({'error': 'command is required'}), 400
        
        # 处理命令
        response = feishu_bot._process_command(command, 'test_user')
        
        return jsonify({
            'status': 'success',
            'command': command,
            'response': response
        })
        
    except Exception as e:
        api_logger.log_error(e, "执行命令异常")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({'error': 'Not found', 'message': 'The requested URL was not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    api_logger.log_error(f"服务器内部错误: {error}")
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """主函数"""
    print("🤖 飞书机器人Webhook服务器")
    print("="*50)
    print(f"🚀 启动飞书Webhook服务器...")
    print(f"📍 服务地址: http://{FEISHU_HOST}:{FEISHU_PORT}")
    print(f"🔗 Webhook地址: http://{FEISHU_HOST}:{FEISHU_PORT}/feishu/webhook")
    print(f"💊 健康检查: http://{FEISHU_HOST}:{FEISHU_PORT}/health")
    print(f"📊 状态接口: http://{FEISHU_HOST}:{FEISHU_PORT}/api/status")
    print()
    
    # 验证飞书配置
    if not feishu_bot:
        print("⚠️ 警告: 飞书机器人初始化失败")
    elif not feishu_bot.app_id or not feishu_bot.app_secret:
        print("⚠️ 警告: 飞书机器人配置不完整")
    else:
        print("✅ 飞书机器人配置正常")
    
    print()
    print("🎯 在飞书开放平台配置事件订阅地址:")
    print(f"   http://你的公网IP:{FEISHU_PORT}/feishu/webhook")
    print()
    
    try:
        # 运行服务器
        app.run(
            host=FEISHU_HOST,
            port=FEISHU_PORT,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        api_logger.log_error(e, "启动webhook服务器失败")
        print(f"❌ 启动服务器失败: {e}")

if __name__ == '__main__':
    main() 