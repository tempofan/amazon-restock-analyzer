#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于官方SDK的领星API实现
解决频率限制和认证问题
"""

import sys
import os
import requests
import json
import time
import hashlib
import base64
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

# 添加SDK路径
sdk_path = os.path.join(os.path.dirname(__file__), '..', 'openapi-python3-sdk-20230419', 'openapi-python3-sdk-0419')
sys.path.insert(0, sdk_path)

try:
    from sign import SignBase
    from aes import aes_encrypt, md5_encrypt
except ImportError as e:
    print(f"警告: 无法导入SDK模块: {e}")
    SignBase = None

class LingxingAPISDKBased:
    """
    基于官方SDK的领星API客户端
    """
    
    def __init__(self):
        """
        初始化API客户端
        """
        # API配置
        self.host = "https://openapi.lingxing.com"
        self.app_id = "20230419000000001"
        self.app_secret = "e10adc3949ba59abbe56e057f20f883e"
        
        # 认证相关
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # 频率控制
        self.last_api_call_time = 0
        self.min_call_interval = 2.0  # 最小调用间隔
        self.rate_limit_retry_count = 2
        self.rate_limit_retry_delay = 8
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
    def generate_sign(self, request_params: dict) -> str:
        """
        生成签名（基于SDK的签名算法）
        """
        if not SignBase:
            raise ValueError("SDK签名模块未正确导入")
            
        return SignBase.generate_sign(self.app_id, request_params)
    
    def get_access_token(self) -> bool:
        """
        获取access_token（基于SDK方式）
        """
        try:
            # 检查token是否仍然有效
            if (self.access_token and self.token_expires_at and 
                datetime.now() < self.token_expires_at - timedelta(minutes=5)):
                return True
            
            self.logger.info("获取新的access_token...")
            
            # 使用SDK方式获取token
            path = '/api/auth-server/oauth/access-token'
            req_url = self.host + path
            
            # 使用params而不是data
            req_params = {
                "appId": self.app_id,
                "appSecret": self.app_secret,
            }
            
            headers = {
                'User-Agent': 'LingxingAPI-SDK/2.0',
                'Accept': 'application/json'
            }
            
            response = requests.post(req_url, params=req_params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    data = result.get('data', {})
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
                    expires_in = data.get('expires_in', 7199)
                    
                    # 计算过期时间
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    self.logger.info(f"access_token获取成功，有效期至: {self.token_expires_at}")
                    return True
                else:
                    self.logger.error(f"获取access_token失败: {result.get('message', '未知错误')}")
                    return False
            else:
                self.logger.error(f"HTTP请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"获取access_token异常: {e}")
            return False
    
    def call_api_with_sign(self, route_name: str, method: str = 'POST', 
                          req_params: Optional[dict] = None,
                          req_body: Optional[dict] = None) -> Dict[str, Any]:
        """
        使用签名调用业务API（基于SDK方式）
        """
        # 确保有有效的access_token
        if not self.get_access_token():
            return {
                'success': False,
                'error': '无法获取access_token',
                'code': 'AUTH_FAILED'
            }
        
        # 频率控制
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time
        if time_since_last_call < self.min_call_interval:
            sleep_time = self.min_call_interval - time_since_last_call
            self.logger.debug(f"频率控制：等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
        
        # 重试逻辑
        for attempt in range(self.rate_limit_retry_count + 1):
            if attempt > 0:
                retry_delay = self.rate_limit_retry_delay + (attempt * 2)
                self.logger.warning(f"第 {attempt} 次重试，等待 {retry_delay:.2f} 秒...")
                time.sleep(retry_delay)
            
            try:
                result = self._make_signed_request(route_name, method, req_params, req_body)
                
                # 检查频率限制错误
                if result.get('success') and isinstance(result.get('data'), dict):
                    api_data = result.get('data', {})
                    if str(api_data.get('code')) == '3001008':
                        self.logger.warning(f"遇到频率限制错误 (3001008)，第 {attempt + 1} 次尝试")
                        if attempt < self.rate_limit_retry_count:
                            continue
                        else:
                            return {
                                'success': False,
                                'error': f'API频率限制，重试 {self.rate_limit_retry_count} 次后仍然失败',
                                'code': '3001008',
                                'data': api_data
                            }
                
                # 更新最后调用时间
                self.last_api_call_time = time.time()
                return result
                
            except Exception as e:
                self.logger.error(f"API调用异常 (尝试 {attempt + 1}): {e}")
                if attempt == self.rate_limit_retry_count:
                    return {
                        'success': False,
                        'error': f'API调用异常: {str(e)}',
                        'code': 'REQUEST_FAILED'
                    }
        
        return {
            'success': False,
            'error': '未知错误',
            'code': 'UNKNOWN_ERROR'
        }
    
    def _make_signed_request(self, route_name: str, method: str,
                           req_params: Optional[dict] = None,
                           req_body: Optional[dict] = None) -> Dict[str, Any]:
        """
        执行带签名的API请求
        """
        req_url = self.host + route_name
        
        req_params = req_params or {}
        
        # 准备签名参数（基于SDK逻辑）
        gen_sign_params = req_body.copy() if req_body else {}
        if req_params:
            gen_sign_params.update(req_params)
        
        sign_params = {
            "app_key": self.app_id,
            "access_token": self.access_token,
            "timestamp": str(int(time.time())),
        }
        gen_sign_params.update(sign_params)
        
        # 生成签名
        sign = self.generate_sign(gen_sign_params)
        sign_params["sign"] = sign
        req_params.update(sign_params)
        
        # 设置请求头
        headers = {
            'User-Agent': 'LingxingAPI-SDK/2.0',
            'Accept': 'application/json'
        }
        
        # 对于带有请求体的请求，设置Content-Type
        if req_body:
            headers['Content-Type'] = 'application/json'
        
        self.logger.info(f"调用API: {method} {route_name}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(req_url, params=req_params, headers=headers, timeout=30)
            else:
                response = requests.post(req_url, params=req_params, json=req_body, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'data': result,
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}',
                    'status_code': response.status_code,
                    'response_text': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'请求异常: {str(e)}',
                'exception': str(e)
            }
    
    def get_shop_list(self) -> Dict[str, Any]:
        """
        获取店铺列表
        """
        return self.call_api_with_sign('/erp/sc/routing/shop/list', 'POST')
    
    def get_replenishment_summary(self, data_type: int = 2, offset: int = 0, 
                                length: int = 20, sid_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取补货建议汇总数据
        """
        req_body = {
            "data_type": data_type,
            "offset": offset,
            "length": length
        }
        
        if sid_list:
            req_body["sid_list"] = sid_list
        
        return self.call_api_with_sign('/erp/sc/routing/restocking/analysis/getSummaryList', 'POST', req_body=req_body)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接
        """
        try:
            if self.get_access_token():
                return {
                    'success': True,
                    'message': 'API连接正常',
                    'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None
                }
            else:
                return {
                    'success': False,
                    'message': 'API连接失败：无法获取access_token'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'API连接异常: {str(e)}'
            }
