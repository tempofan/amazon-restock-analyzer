#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亚马逊补货建议Web应用
基于领星ERP API的补货建议系统
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import logging
from datetime import datetime
import json
from config import Config
from api.lingxing_api import LingxingAPI
from api.data_processor import DataProcessor
from utils.logger import setup_logger

# 创建Flask应用实例
app = Flask(__name__)
app.config.from_object(Config)

# 设置日志
logger = setup_logger('amazon_replenishment', 'logs/app.log')

# 初始化API和数据处理器
lingxing_api = LingxingAPI()
data_processor = DataProcessor()

@app.route('/')
def index():
    """
    首页路由
    显示补货建议概览
    """
    try:
        logger.info("访问首页")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"首页加载错误: {str(e)}")
        flash(f'页面加载失败: {str(e)}', 'error')
        return render_template('error.html', error=str(e))

@app.route('/api/test-connection', methods=['GET'])
def test_api_connection():
    """
    测试API连接
    """
    try:
        result = lingxing_api.test_connection()
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'API连接成功',
                'data': result.get('data', {})
            })
        else:
            return jsonify({
                'success': False,
                'message': f'API连接失败: {result.get("error", "未知错误")}'
            })
    except Exception as e:
        logger.error(f"API连接测试失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'连接测试异常: {str(e)}'
        })

@app.route('/replenishment')
def replenishment_list():
    """
    补货建议列表页面
    """
    try:
        logger.info("访问补货建议列表页面")
        return render_template('replenishment_list.html')
    except Exception as e:
        logger.error(f"补货建议列表页面加载错误: {str(e)}")
        flash(f'页面加载失败: {str(e)}', 'error')
        return render_template('error.html', error=str(e))

@app.route('/api/replenishment-data', methods=['GET'])
def get_replenishment_data():
    """
    获取补货建议数据API
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        shop_id = request.args.get('shop_id', '')
        asin = request.args.get('asin', '')
        msku = request.args.get('msku', '')
        
        logger.info(f"获取补货数据 - 页码: {page}, 页大小: {page_size}")
        
        # 调用领星API获取补货建议数据
        api_result = lingxing_api.get_replenishment_suggestions(
            page=page,
            page_size=page_size,
            shop_id=shop_id,
            asin=asin,
            msku=msku
        )
        
        if api_result['success']:
            # 处理数据
            processed_data = data_processor.process_replenishment_data(api_result['data'])
            
            return jsonify({
                'success': True,
                'data': processed_data,
                'message': '数据获取成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'数据获取失败: {api_result.get("error", "未知错误")}'
            })
            
    except Exception as e:
        logger.error(f"获取补货数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'数据获取异常: {str(e)}'
        })

@app.route('/api/replenishment-rules/<rule_type>')
def get_replenishment_rules(rule_type):
    """
    获取补货规则
    rule_type: 'asin' 或 'msku'
    """
    try:
        if rule_type not in ['asin', 'msku']:
            return jsonify({
                'success': False,
                'message': '无效的规则类型'
            })
        
        logger.info(f"获取补货规则 - 类型: {rule_type}")
        
        # 调用API获取规则
        api_result = lingxing_api.get_replenishment_rules(rule_type)
        
        if api_result['success']:
            return jsonify({
                'success': True,
                'data': api_result['data'],
                'message': '规则获取成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'规则获取失败: {api_result.get("error", "未知错误")}'
            })
            
    except Exception as e:
        logger.error(f"获取补货规则失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'规则获取异常: {str(e)}'
        })

@app.route('/analytics')
def analytics():
    """
    数据分析页面
    """
    try:
        logger.info("访问数据分析页面")
        return render_template('analytics.html')
    except Exception as e:
        logger.error(f"数据分析页面加载错误: {str(e)}")
        flash(f'页面加载失败: {str(e)}', 'error')
        return render_template('error.html', error=str(e))

@app.route('/api/analytics-data')
def get_analytics_data():
    """
    获取分析数据API
    """
    try:
        logger.info("获取分析数据")
        
        # 获取补货建议数据进行分析
        api_result = lingxing_api.get_replenishment_suggestions(page=1, page_size=1000)
        
        if api_result['success']:
            # 生成分析报告
            analytics_data = data_processor.generate_analytics(api_result['data'])
            
            return jsonify({
                'success': True,
                'data': analytics_data,
                'message': '分析数据获取成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'分析数据获取失败: {api_result.get("error", "未知错误")}'
            })
            
    except Exception as e:
        logger.error(f"获取分析数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'分析数据获取异常: {str(e)}'
        })

@app.route('/settings')
def settings():
    """
    设置页面
    """
    try:
        logger.info("访问设置页面")
        return render_template('settings.html')
    except Exception as e:
        logger.error(f"设置页面加载错误: {str(e)}")
        flash(f'页面加载失败: {str(e)}', 'error')
        return render_template('error.html', error=str(e))

@app.errorhandler(404)
def not_found_error(error):
    """404错误处理"""
    return render_template('error.html', error='页面未找到'), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"内部服务器错误: {str(error)}")
    return render_template('error.html', error='内部服务器错误'), 500

if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs('logs', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    logger.info("启动亚马逊补货建议Web应用")
    
    # 启动Flask应用
    # host='0.0.0.0' 允许外部访问
    # debug=False 生产环境模式
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
