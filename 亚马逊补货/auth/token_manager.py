# -*- coding: utf-8 -*-
"""
Token管理模块
负责access_token的获取、刷新和管理
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from config.config import APIConfig
from utils.logger import api_logger
from utils.crypto_utils import CryptoUtils

class TokenStorage:
    """Token存储管理器"""
    
    def __init__(self, storage_file: str = "data/tokens.json"):
        """
        初始化Token存储管理器
        
        Args:
            storage_file: Token存储文件路径
        """
        self.storage_file = storage_file
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        storage_dir = os.path.dirname(self.storage_file)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
    
    def save_token(self, token_data: Dict[str, Any]):
        """
        保存Token数据
        
        Args:
            token_data: Token数据字典
        """
        try:
            # 添加保存时间戳
            token_data['saved_at'] = time.time()
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
            
            api_logger.logger.info(f"Token已保存到: {self.storage_file}")
        except Exception as e:
            api_logger.log_error(e, "保存Token失败")
            raise
    
    def load_token(self) -> Optional[Dict[str, Any]]:
        """
        加载Token数据
        
        Returns:
            Optional[Dict[str, Any]]: Token数据字典，如果不存在则返回None
        """
        try:
            if not os.path.exists(self.storage_file):
                return None
            
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            api_logger.logger.info(f"Token已从 {self.storage_file} 加载")
            return token_data
        except Exception as e:
            api_logger.log_error(e, "加载Token失败")
            return None
    
    def clear_token(self):
        """清除Token数据"""
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
                api_logger.logger.info("Token数据已清除")
        except Exception as e:
            api_logger.log_error(e, "清除Token失败")

class TokenManager:
    """Token管理器"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        """
        初始化Token管理器
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
        """
        self.app_id = app_id or APIConfig.APP_ID
        self.app_secret = app_secret or APIConfig.APP_SECRET
        self.storage = TokenStorage()
        self._current_token_data = None
        
        # 加载已保存的Token
        self._load_existing_token()
    
    def _load_existing_token(self):
        """加载已存在的Token"""
        self._current_token_data = self.storage.load_token()
        if self._current_token_data:
            api_logger.logger.info("已加载现有Token数据")
    
    def get_valid_token(self) -> str:
        """
        获取有效的access_token
        
        Returns:
            str: 有效的access_token
        """
        # 检查当前Token是否有效
        if self._is_token_valid():
            return self._current_token_data['access_token']
        
        # 尝试刷新Token
        if self._can_refresh_token():
            if self._refresh_token():
                return self._current_token_data['access_token']
        
        # 获取新Token
        if self._get_new_token():
            return self._current_token_data['access_token']
        
        raise Exception("无法获取有效的access_token")
    
    def _is_token_valid(self) -> bool:
        """
        检查当前Token是否有效
        
        Returns:
            bool: Token是否有效
        """
        if not self._current_token_data:
            return False
        
        # 检查必要字段
        if 'access_token' not in self._current_token_data:
            return False
        
        # 检查过期时间
        if 'expires_at' in self._current_token_data:
            expires_at = self._current_token_data['expires_at']
            # 提前5分钟刷新
            if time.time() >= (expires_at - APIConfig.TOKEN_REFRESH_THRESHOLD):
                api_logger.logger.info("Token即将过期，需要刷新")
                return False
        
        return True
    
    def _can_refresh_token(self) -> bool:
        """
        检查是否可以刷新Token
        
        Returns:
            bool: 是否可以刷新
        """
        if not self._current_token_data:
            return False
        
        # 检查是否有refresh_token
        if 'refresh_token' not in self._current_token_data:
            return False
        
        # 检查refresh_token是否过期（2小时有效期）
        if 'refresh_token_expires_at' in self._current_token_data:
            refresh_expires_at = self._current_token_data['refresh_token_expires_at']
            if time.time() >= refresh_expires_at:
                api_logger.logger.info("refresh_token已过期")
                return False
        
        return True
    
    def _get_new_token(self) -> bool:
        """
        获取新的Token
        
        Returns:
            bool: 是否成功获取
        """
        try:
            api_logger.logger.info("开始获取新的access_token")
            
            url = f"{APIConfig.BASE_URL}{APIConfig.AUTH_URLS['get_token']}"
            
            # 准备请求数据
            data = {
                'appId': self.app_id,
                'appSecret': self.app_secret
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            api_logger.log_request('POST', url, body=data)
            
            # 发送请求
            response = requests.post(
                url, 
                data=data, 
                timeout=APIConfig.REQUEST_TIMEOUT
            )
            
            api_logger.log_response(response.status_code, response_time=None)
            
            if response.status_code == 200:
                result = response.json()
                api_logger.log_response(response.status_code, result)
                
                if result.get('code') == '200' or result.get('code') == 200:
                    token_data = result['data']
                    
                    # 计算过期时间
                    expires_in = int(token_data.get('expires_in', 7200))  # 默认2小时
                    expires_at = time.time() + expires_in
                    refresh_token_expires_at = time.time() + 7200  # refresh_token 2小时有效期
                    
                    # 保存Token数据
                    self._current_token_data = {
                        'access_token': token_data['access_token'],
                        'refresh_token': token_data['refresh_token'],
                        'expires_in': expires_in,
                        'expires_at': expires_at,
                        'refresh_token_expires_at': refresh_token_expires_at,
                        'created_at': time.time()
                    }
                    
                    self.storage.save_token(self._current_token_data)
                    api_logger.log_token_operation("获取", True, f"Token有效期: {expires_in}秒")
                    return True
                else:
                    error_msg = result.get('msg', '未知错误')
                    api_logger.log_token_operation("获取", False, error_msg)
                    return False
            else:
                api_logger.log_token_operation("获取", False, f"HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            api_logger.log_error(e, "获取新Token失败")
            return False
    
    def _refresh_token(self) -> bool:
        """
        刷新Token
        
        Returns:
            bool: 是否成功刷新
        """
        try:
            api_logger.logger.info("开始刷新access_token")
            
            url = f"{APIConfig.BASE_URL}{APIConfig.AUTH_URLS['refresh_token']}"
            
            # 准备请求数据
            data = {
                'appId': self.app_id,
                'refreshToken': self._current_token_data['refresh_token']
            }
            
            headers = {
                'Content-Type': 'multipart/form-data'
            }
            
            api_logger.log_request('POST', url, body=data)
            
            # 发送请求
            response = requests.post(
                url, 
                data=data, 
                timeout=APIConfig.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                api_logger.log_response(response.status_code, result)
                
                if result.get('code') == '200' or result.get('code') == 200:
                    token_data = result['data']
                    
                    # 计算过期时间
                    expires_in = int(token_data.get('expires_in', 7200))
                    expires_at = time.time() + expires_in
                    refresh_token_expires_at = time.time() + 7200  # 新的refresh_token 2小时有效期
                    
                    # 更新Token数据
                    self._current_token_data.update({
                        'access_token': token_data['access_token'],
                        'refresh_token': token_data['refresh_token'],
                        'expires_in': expires_in,
                        'expires_at': expires_at,
                        'refresh_token_expires_at': refresh_token_expires_at,
                        'refreshed_at': time.time()
                    })
                    
                    self.storage.save_token(self._current_token_data)
                    api_logger.log_token_operation("刷新", True, f"新Token有效期: {expires_in}秒")
                    return True
                else:
                    error_msg = result.get('msg', '未知错误')
                    api_logger.log_token_operation("刷新", False, error_msg)
                    return False
            else:
                api_logger.log_token_operation("刷新", False, f"HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            api_logger.log_error(e, "刷新Token失败")
            return False
    
    def force_refresh(self) -> bool:
        """
        强制刷新Token
        
        Returns:
            bool: 是否成功刷新
        """
        api_logger.logger.info("强制刷新Token")
        return self._get_new_token()
    
    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前Token信息
        
        Returns:
            Optional[Dict[str, Any]]: Token信息
        """
        if not self._current_token_data:
            return None
        
        info = self._current_token_data.copy()
        # 隐藏敏感信息
        if 'access_token' in info:
            token = info['access_token']
            info['access_token'] = f"{token[:8]}****{token[-8:]}" if len(token) > 16 else "****"
        if 'refresh_token' in info:
            token = info['refresh_token']
            info['refresh_token'] = f"{token[:8]}****{token[-8:]}" if len(token) > 16 else "****"
        
        # 添加可读的时间信息
        if 'expires_at' in info:
            expires_at = datetime.fromtimestamp(info['expires_at'])
            info['expires_at_readable'] = expires_at.strftime('%Y-%m-%d %H:%M:%S')
            info['is_expired'] = time.time() >= info['expires_at']
        
        return info
    
    def clear_token(self):
        """清除Token数据"""
        self._current_token_data = None
        self.storage.clear_token()
        api_logger.logger.info("Token数据已清除")