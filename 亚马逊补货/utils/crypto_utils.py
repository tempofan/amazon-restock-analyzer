# -*- coding: utf-8 -*-
"""
加密工具模块
包含签名生成、AES加密等功能
"""

import hashlib
import time
import urllib.parse
from typing import Dict, Any
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64

class CryptoUtils:
    """加密工具类"""
    
    @staticmethod
    def generate_timestamp() -> str:
        """生成时间戳（10位）"""
        return str(int(time.time()))
    
    @staticmethod
    def generate_sign(params: Dict[str, Any], app_id: str) -> str:
        """
        生成API签名
        
        Args:
            params: 请求参数字典
            app_id: 应用ID，用作AES加密密钥
            
        Returns:
            str: 生成的签名
        """
        # 1. 过滤空值参数
        filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
        
        # 2. 按键名ASCII排序
        sorted_keys = sorted(filtered_params.keys())
        
        # 3. 拼接参数字符串（数组参数需要转换为字符串）
        param_parts = []
        for key in sorted_keys:
            value = filtered_params[key]
            if isinstance(value, list):
                # 数组参数转换为JSON字符串
                import json
                value_str = json.dumps(value, separators=(',', ':'), ensure_ascii=False)
            else:
                value_str = str(value)
            param_parts.append(f"{key}={value_str}")
        param_string = "&".join(param_parts)
        
        # 4. MD5加密并转大写
        md5_hash = hashlib.md5(param_string.encode('utf-8')).hexdigest().upper()
        
        # 5. AES加密
        aes_encrypted = CryptoUtils._aes_encrypt(md5_hash, app_id)
        
        return aes_encrypted
    
    @staticmethod
    def _aes_encrypt(data: str, key: str) -> str:
        """
        AES加密（ECB模式，PKCS5PADDING填充）
        
        Args:
            data: 待加密数据
            key: 加密密钥
            
        Returns:
            str: Base64编码的加密结果
        """
        # 确保密钥长度为16字节（AES-128）
        key_bytes = key.encode('utf-8')
        if len(key_bytes) < 16:
            key_bytes = key_bytes.ljust(16, b'\0')
        elif len(key_bytes) > 16:
            key_bytes = key_bytes[:16]
        
        # 创建AES加密器
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        
        # 填充数据
        padded_data = pad(data.encode('utf-8'), AES.block_size)
        
        # 加密
        encrypted = cipher.encrypt(padded_data)
        
        # Base64编码
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def url_encode(text: str) -> str:
        """
        URL编码
        
        Args:
            text: 待编码文本
            
        Returns:
            str: 编码后的文本
        """
        return urllib.parse.quote(text, safe='')
    
    @staticmethod
    def build_query_params(params: Dict[str, Any]) -> str:
        """
        构建查询参数字符串
        
        Args:
            params: 参数字典
            
        Returns:
            str: 查询参数字符串
        """
        param_list = []
        for key, value in params.items():
            if value is not None and value != "":
                encoded_value = urllib.parse.quote(str(value), safe='')
                param_list.append(f"{key}={encoded_value}")
        
        return "&".join(param_list)

class RequestBuilder:
    """请求构建器"""
    
    def __init__(self, app_id: str, access_token: str):
        """
        初始化请求构建器
        
        Args:
            app_id: 应用ID
            access_token: 访问令牌
        """
        self.app_id = app_id
        self.access_token = access_token
    
    def build_common_params(self, business_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        构建公共请求参数
        
        Args:
            business_params: 业务参数
            
        Returns:
            Dict[str, Any]: 包含公共参数的完整参数字典
        """
        timestamp = CryptoUtils.generate_timestamp()
        
        # 公共参数
        common_params = {
            "access_token": self.access_token,
            "app_key": self.app_id,
            "timestamp": timestamp
        }
        
        # 合并业务参数
        if business_params:
            all_params = {**common_params, **business_params}
        else:
            all_params = common_params
        
        # 生成签名
        sign = CryptoUtils.generate_sign(all_params, self.app_id)
        all_params["sign"] = sign
        
        return all_params
    
    def build_get_url(self, base_url: str, endpoint: str, business_params: Dict[str, Any] = None) -> str:
        """
        构建GET请求URL
        
        Args:
            base_url: 基础URL
            endpoint: 接口端点
            business_params: 业务参数
            
        Returns:
            str: 完整的请求URL
        """
        all_params = self.build_common_params(business_params)
        query_string = CryptoUtils.build_query_params(all_params)
        
        return f"{base_url}{endpoint}?{query_string}"
    
    def build_post_params(self, business_params: Dict[str, Any] = None) -> tuple:
        """
        构建POST请求参数
        
        Args:
            business_params: 业务参数
            
        Returns:
            tuple: (查询参数字典, 请求体参数字典)
        """
        timestamp = CryptoUtils.generate_timestamp()
        
        # 公共参数（放在URL中）
        common_params = {
            "access_token": self.access_token,
            "app_key": self.app_id,
            "timestamp": timestamp
        }
        
        # 如果有业务参数，需要参与签名计算
        if business_params:
            sign_params = {**common_params, **business_params}
        else:
            sign_params = common_params
        
        # 生成签名
        sign = CryptoUtils.generate_sign(sign_params, self.app_id)
        common_params["sign"] = sign
        
        return common_params, business_params or {}