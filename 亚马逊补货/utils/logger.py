# -*- coding: utf-8 -*-
"""
日志工具模块
提供统一的日志记录功能
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

class Logger:
    """日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str = "lingxing_api", 
                   log_file: Optional[str] = None,
                   log_level: str = "INFO") -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件路径
            log_level: 日志级别
            
        Returns:
            logging.Logger: 日志记录器实例
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # 避免重复添加处理器
        if not logger.handlers:
            # 创建格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器
            if log_file:
                # 确保日志目录存在
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, log_level.upper()))
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def setup_default_logger(cls) -> logging.Logger:
        """
        设置默认日志记录器
        
        Returns:
            logging.Logger: 默认日志记录器
        """
        log_file = os.path.join("logs", "lingxing_api.log")
        return cls.get_logger("lingxing_api", log_file, "INFO")

class APILogger:
    """API专用日志记录器"""
    
    def __init__(self, logger_name: str = "lingxing_api"):
        """
        初始化API日志记录器
        
        Args:
            logger_name: 日志记录器名称
        """
        self.logger = Logger.get_logger(
            logger_name, 
            os.path.join("logs", f"{logger_name}.log")
        )
    
    def log_request(self, method: str, url: str, params: dict = None, 
                   headers: dict = None, body: dict = None):
        """
        记录API请求日志
        
        Args:
            method: HTTP方法
            url: 请求URL
            params: 请求参数
            headers: 请求头
            body: 请求体
        """
        self.logger.info(f"API请求 - {method} {url}")
        if params:
            # 隐藏敏感信息
            safe_params = self._mask_sensitive_data(params)
            self.logger.debug(f"请求参数: {safe_params}")
        if headers:
            safe_headers = self._mask_sensitive_data(headers)
            self.logger.debug(f"请求头: {safe_headers}")
        if body:
            safe_body = self._mask_sensitive_data(body)
            self.logger.debug(f"请求体: {safe_body}")
    
    def log_response(self, status_code: int, response_data: dict = None, 
                    response_time: float = None):
        """
        记录API响应日志
        
        Args:
            status_code: HTTP状态码
            response_data: 响应数据
            response_time: 响应时间（秒）
        """
        time_info = f" (耗时: {response_time:.2f}s)" if response_time else ""
        self.logger.info(f"API响应 - 状态码: {status_code}{time_info}")
        
        if response_data:
            if isinstance(response_data, dict):
                code = response_data.get('code', 'N/A')
                message = response_data.get('message', response_data.get('msg', 'N/A'))
                self.logger.info(f"响应结果 - 代码: {code}, 消息: {message}")
                
                # 如果有错误，记录详细信息
                if str(code) != '0' and str(code) != '200':
                    self.logger.error(f"API错误响应: {response_data}")
            else:
                self.logger.debug(f"响应数据: {str(response_data)[:500]}...")  # 限制长度
    
    def log_error(self, error: Exception, context: str = ""):
        """
        记录错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        error_msg = f"错误发生: {str(error)}"
        if context:
            error_msg = f"{context} - {error_msg}"
        
        self.logger.error(error_msg, exc_info=True)
    
    def log_token_operation(self, operation: str, success: bool, details: str = ""):
        """
        记录Token操作日志
        
        Args:
            operation: 操作类型（获取/刷新）
            success: 是否成功
            details: 详细信息
        """
        status = "成功" if success else "失败"
        msg = f"Token{operation}{status}"
        if details:
            msg += f" - {details}"
        
        if success:
            self.logger.info(msg)
        else:
            self.logger.error(msg)
    
    def log_business_operation(self, operation: str, params: dict = None, 
                              result_count: int = None):
        """
        记录业务操作日志
        
        Args:
            operation: 操作名称
            params: 操作参数
            result_count: 结果数量
        """
        msg = f"业务操作: {operation}"
        if params:
            safe_params = self._mask_sensitive_data(params)
            msg += f" - 参数: {safe_params}"
        if result_count is not None:
            msg += f" - 结果数量: {result_count}"
        
        self.logger.info(msg)
    
    def log_info(self, message: str):
        """
        记录信息日志（兼容性方法）
        
        Args:
            message: 日志信息
        """
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """
        记录警告日志（兼容性方法）
        
        Args:
            message: 日志信息
        """
        self.logger.warning(message)
    
    def log_debug(self, message: str):
        """
        记录调试日志（兼容性方法）
        
        Args:
            message: 日志信息
        """
        self.logger.debug(message)
    
    def _mask_sensitive_data(self, data: dict) -> dict:
        """
        隐藏敏感数据
        
        Args:
            data: 原始数据字典
            
        Returns:
            dict: 隐藏敏感信息后的数据字典
        """
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = {
            'access_token', 'refresh_token', 'app_secret', 
            'appSecret', 'sign', 'password', 'token'
        }
        
        masked_data = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys or 'token' in key.lower():
                if isinstance(value, str) and len(value) > 8:
                    masked_data[key] = f"{value[:4]}****{value[-4:]}"
                else:
                    masked_data[key] = "****"
            else:
                masked_data[key] = value
        
        return masked_data

# 创建默认日志记录器实例
default_logger = Logger.setup_default_logger()
api_logger = APILogger()