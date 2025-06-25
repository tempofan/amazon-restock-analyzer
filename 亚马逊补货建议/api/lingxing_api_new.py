#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领星ERP API封装模块 - 新版本
基于正确的认证方式和API端点
"""

import requests
import json
import time
import logging
import hashlib
import base64
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from config import Config
from api.mock_data import MockDataGenerator

class LingxingAPINew:
    """
    领星ERP API客户端类 - 新版本
    使用正确的认证方式和签名算法
    """
    
    def __init__(self):
        """
        初始化API客户端
        """
        self.base_url = Config.LINGXING_API_CONFIG['base_url']
        self.app_id = Config.LINGXING_API_CONFIG['app_id']
        self.app_secret = Config.LINGXING_API_CONFIG['app_secret']
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LingxingAPI/2.0',
            'Accept': 'application/json'
        })
        
        # 认证相关
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # API端点配置（使用正确的端点）
        self.endpoints = {
            'auth_token': '/api/auth-server/oauth/access-token',
            'auth_refresh': '/api/auth-server/oauth/refresh',
            'shop_list': '/erp/sc/data/seller/lists',
            'replenishment_list': '/erp/sc/routing/restocking/analysis/getSummaryList',
            'marketplace_list': '/erp/sc/data/marketplace/lists',
        }
        
        # 初始化模拟数据生成器
        self.mock_generator = MockDataGenerator()
        
        self.logger.info("领星API客户端初始化完成")
    
    def generate_sign(self, params: Dict[str, Any]) -> str:
        """
        生成接口签名
        根据文档要求：
        1. 所有参数按ASCII排序
        2. 拼接成key1=value1&key2=value2格式
        3. MD5加密转大写
        4. AES/ECB/PKCS5PADDING加密，密钥为appId
        """
        try:
            # 1. 过滤空值并排序
            filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
            sorted_params = sorted(filtered_params.items())
            
            # 2. 拼接字符串
            param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            self.logger.debug(f"签名字符串: {param_string}")
            
            # 3. MD5加密转大写
            md5_hash = hashlib.md5(param_string.encode('utf-8')).hexdigest().upper()
            self.logger.debug(f"MD5结果: {md5_hash}")
            
            # 4. AES加密
            # 确保密钥长度为16字节
            key = self.app_id.encode('utf-8')
            if len(key) < 16:
                key = key + b'\0' * (16 - len(key))
            elif len(key) > 16:
                key = key[:16]
            
            cipher = AES.new(key, AES.MODE_ECB)
            encrypted = cipher.encrypt(pad(md5_hash.encode('utf-8'), AES.block_size))
            sign = base64.b64encode(encrypted).decode('utf-8')
            self.logger.debug(f"AES加密结果: {sign}")
            return sign
        except Exception as e:
            self.logger.error(f"签名生成失败: {e}")
            return None
    
    def get_access_token(self) -> bool:
        """
        获取access_token
        """
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            self.logger.debug("access_token仍然有效")
            return True
        
        self.logger.info("正在获取access_token...")
        
        url = f"{self.base_url}{self.endpoints['auth_token']}"
        
        # 使用form-data格式
        data = {
            'appId': self.app_id,
            'appSecret': self.app_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = self.session.post(url, data=data, headers=headers, timeout=15)
            self.logger.debug(f"认证响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"认证响应: {result}")
                
                if result.get('code') == '200' or result.get('code') == 200:
                    data = result.get('data', {})
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    expires_in = data.get('expires_in', 7200)
                    
                    # 设置过期时间（提前5分钟刷新）
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                    
                    self.logger.info("获取access_token成功")
                    return True
                else:
                    self.logger.error(f"获取access_token失败: {result.get('msg', 'Unknown error')}")
                    return False
            else:
                self.logger.error(f"认证HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"获取access_token异常: {e}")
            return False
    
    def call_api(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None, 
                 data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        调用业务API
        """
        # 确保有有效的access_token
        if not self.get_access_token():
            return {
                'success': False,
                'error': '无法获取access_token',
                'code': 'AUTH_FAILED'
            }
        
        self.logger.info(f"调用API: {method} {endpoint}")
        
        # 准备公共参数
        timestamp = int(time.time())
        common_params = {
            'access_token': self.access_token,
            'app_key': self.app_id,
            'timestamp': str(timestamp)
        }
        
        # 合并业务参数用于签名
        sign_params = common_params.copy()
        
        if method == 'GET' and params:
            sign_params.update(params)
        elif method == 'POST' and data:
            # POST请求：业务参数也要参与签名
            def flatten_for_sign(obj, prefix=''):
                """将嵌套对象扁平化用于签名"""
                items = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        new_key = f"{prefix}.{k}" if prefix else k
                        if isinstance(v, (dict, list)):
                            items.extend(flatten_for_sign(v, new_key))
                        else:
                            items.append((new_key, str(v)))
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        new_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                        if isinstance(v, (dict, list)):
                            items.extend(flatten_for_sign(v, new_key))
                        else:
                            items.append((new_key, str(v)))
                else:
                    items.append((prefix, str(obj)))
                return items
            
            # 扁平化业务参数
            flattened = flatten_for_sign(data)
            for key, value in flattened:
                sign_params[key] = value
        
        # 生成签名
        sign = self.generate_sign(sign_params)
        if not sign:
            return {
                'success': False,
                'error': '签名生成失败',
                'code': 'SIGN_FAILED'
            }
        
        # 公共参数包含签名
        query_params = {**common_params, 'sign': sign}
        
        # 构建请求
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                # URL编码sign参数
                encoded_params = {}
                for k, v in query_params.items():
                    if k == 'sign':
                        encoded_params[k] = urllib.parse.quote(v, safe='')
                    else:
                        encoded_params[k] = v
                
                if params:
                    encoded_params.update(params)
                
                response = self.session.get(url, params=encoded_params, timeout=15)
            elif method == 'POST':
                # POST请求：公共参数在URL，业务参数在body
                encoded_query_params = {k: urllib.parse.quote(v, safe='') if k == 'sign' else v 
                                      for k, v in query_params.items()}
                
                headers = {'Content-Type': 'application/json'}
                response = self.session.post(url, params=encoded_query_params, 
                                           json=data or {}, headers=headers, timeout=15)
            
            self.logger.debug(f"请求URL: {response.url}")
            self.logger.debug(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"API响应: {json.dumps(result, ensure_ascii=False)[:500]}...")
                
                return {
                    'success': True,
                    'data': result,
                    'status_code': response.status_code
                }
            else:
                self.logger.error(f"API HTTP错误: {response.status_code}")
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            self.logger.error(f"API请求异常: {e}")
            return {
                'success': False,
                'error': f'请求异常: {e}',
                'code': 'REQUEST_FAILED'
            }
    
    def get_shop_list(self) -> Dict[str, Any]:
        """
        获取店铺列表
        """
        result = self.call_api(self.endpoints['shop_list'], method='GET')
        
        if not result.get('success', False):
            self.logger.warning("店铺列表API调用失败，使用模拟数据")
            return {
                'success': True,
                'data': self.mock_generator.generate_shop_list(),
                'message': '使用模拟数据（API暂时不可用）',
                'is_mock': True
            }
        
        return result
