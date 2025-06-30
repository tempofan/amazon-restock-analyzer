# -*- coding: utf-8 -*-
"""
API客户端模块
负责处理HTTP请求和响应
"""

import json
import time
import requests
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from config.config import APIConfig
from config.proxy_config import ProxyConfig
from config.api_strategy import APIStrategy
from auth.token_manager import TokenManager
from utils.logger import api_logger
from utils.crypto_utils import RequestBuilder, CryptoUtils

class APIClient:
    """API客户端"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        """
        初始化API客户端
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
        """
        self.app_id = app_id or APIConfig.APP_ID
        self.app_secret = app_secret or APIConfig.APP_SECRET
        
        # 🌐 根据代理配置决定使用的基础URL
        if ProxyConfig.is_proxy_enabled():
            self.base_url = ProxyConfig.get_proxy_base_url()
            api_logger.logger.info(f"🌐 启用代理模式: {self.base_url}")
        else:
            self.base_url = APIConfig.BASE_URL
            api_logger.logger.info(f"🔗 直连模式: {self.base_url}")
        
        # 初始化Token管理器
        self.token_manager = TokenManager(self.app_id, self.app_secret)
        
        # 初始化HTTP会话
        self.session = self._create_session()
        self._request_lock = threading.Lock()  # 添加请求锁，确保token刷新的线程安全
    
    def _create_session(self) -> requests.Session:
        """
        创建HTTP会话，配置重试策略
        
        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()
        
        # 🔄 根据代理模式配置重试策略
        if ProxyConfig.is_proxy_enabled():
            # 代理模式：使用代理配置的重试次数
            max_retries = ProxyConfig.PROXY_RETRIES
            timeout = ProxyConfig.PROXY_TIMEOUT
        else:
            # 直连模式：使用API配置的重试次数
            max_retries = APIConfig.MAX_RETRIES
            timeout = APIConfig.REQUEST_TIMEOUT
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=APIConfig.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Dict[str, Any] = None,
                     json_data: Dict[str, Any] = None,
                     headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            json_data: JSON数据
            headers: 请求头
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        start_time = time.time()
        
        try:
            # 获取有效Token
            access_token = self.token_manager.get_valid_token()
            
            # 创建请求构建器
            request_builder = RequestBuilder(self.app_id, access_token)
            
            # 🎯 根据API类型决定是否使用代理
            api_type = 'business'  # 大部分API都是业务API
            if '/auth-server/' in endpoint:
                api_type = 'auth'
            
            use_proxy = APIStrategy.should_use_proxy(api_type)
            base_url = APIStrategy.get_base_url(api_type)
            
            # 准备请求参数
            if method.upper() == 'GET':
                if use_proxy:
                    # 🌐 代理模式：构建完整的原始URL然后通过代理转发
                    original_url = request_builder.build_get_url(APIConfig.BASE_URL, endpoint, params)
                    # 提取原始URL中的endpoint和参数部分
                    url_parts = original_url.replace(APIConfig.BASE_URL, "").lstrip('/')
                    url = f"{base_url}/{url_parts}"
                    final_params = None
                    final_json = None
                else:
                    # 🔗 直连模式：原有逻辑
                    url = request_builder.build_get_url(base_url, endpoint, params)
                    final_params = None
                    final_json = None
            else:
                if use_proxy:
                    # 🌐 代理模式：POST请求处理
                    query_params, body_params = request_builder.build_post_params(params)
                    original_query = CryptoUtils.build_query_params(query_params)
                    url = f"{base_url}{endpoint}?{original_query}"
                    final_params = None
                    final_json = body_params if body_params else json_data
                else:
                    # 🔗 直连模式：原有逻辑
                    query_params, body_params = request_builder.build_post_params(params)
                    url = f"{base_url}{endpoint}?" + CryptoUtils.build_query_params(query_params)
                    final_params = None
                    final_json = body_params if body_params else json_data
            
            # 设置默认请求头
            final_headers = {
                'User-Agent': 'LingXing-API-Client/1.0',
                'Accept': 'application/json'
            }
            
            if method.upper() == 'POST' and final_json:
                final_headers['Content-Type'] = 'application/json'
            
            if headers:
                final_headers.update(headers)
            
            # 记录请求日志
            api_logger.log_request(method, url, final_params, final_headers, final_json)
            
            # 🔄 根据API策略选择超时时间
            timeout = APIStrategy.get_timeout(api_type)
            
            # 发送请求
            response = self.session.request(
                method=method,
                url=url,
                params=final_params,
                json=final_json,
                headers=final_headers,
                timeout=timeout
            )
            
            # 计算响应时间
            response_time = time.time() - start_time
            
            # 解析响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {'raw_response': response.text}
            
            # 记录响应日志
            api_logger.log_response(response.status_code, response_data, response_time)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                raise APIException(
                    f"HTTP错误: {response.status_code}",
                    response.status_code,
                    response_data
                )
            
            # 检查业务状态码
            if isinstance(response_data, dict):
                code = response_data.get('code')
                if code is not None and str(code) not in ['0', '200']:
                    error_msg = response_data.get('message', response_data.get('msg', '未知错误'))
                    error_details = response_data.get('error_details', [])
                    
                    # 检查是否是Token相关错误
                    if str(code) in ['2001003', '2001005', '2001008', '2001009']:
                        api_logger.logger.warning(f"Token错误，尝试重新获取: {error_msg}")
                        # 清除当前Token并重试
                        self.token_manager.clear_token()
                        if hasattr(self, '_retry_count'):
                            self._retry_count += 1
                        else:
                            self._retry_count = 1
                        
                        if self._retry_count <= 2:  # 最多重试2次
                            api_logger.logger.info(f"第{self._retry_count}次重试请求")
                            return self._make_request(method, endpoint, params, json_data, headers)
                    
                    # 🚦 检查是否是频率限制错误
                    elif str(code) == '3001008':
                        api_logger.logger.warning(f"触发频率限制，等待后重试: {error_msg}")
                        if hasattr(self, '_rate_limit_retry_count'):
                            self._rate_limit_retry_count += 1
                        else:
                            self._rate_limit_retry_count = 1
                        
                        if self._rate_limit_retry_count <= 5:  # 增加到最多重试5次
                            # 更积极的延迟策略：3^retry_count 秒，最少5秒
                            delay = max(5, 3 ** self._rate_limit_retry_count)
                            api_logger.logger.info(f"频率限制第{self._rate_limit_retry_count}次重试，等待{delay}秒")
                            time.sleep(delay)
                            return self._make_request(method, endpoint, params, json_data, headers)
                    
                    raise APIException(
                        f"API错误: {error_msg}",
                        code,
                        response_data,
                        error_details
                    )
            
            # 重置重试计数
            if hasattr(self, '_retry_count'):
                delattr(self, '_retry_count')
            if hasattr(self, '_rate_limit_retry_count'):
                delattr(self, '_rate_limit_retry_count')
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            api_logger.log_error(e, f"请求异常: {method} {endpoint}")
            raise APIException(f"请求失败: {str(e)}", None, None)
        except Exception as e:
            api_logger.log_error(e, f"未知错误: {method} {endpoint}")
            raise
    
    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送GET请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        return self._make_request('GET', endpoint, params)
    
    def post(self, endpoint: str, data: Dict[str, Any] = None, 
             json_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送POST请求
        
        Args:
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        return self._make_request('POST', endpoint, data, json_data)
    
    def get_seller_lists(self) -> List[Dict[str, Any]]:
        """
        获取店铺列表
        
        Returns:
            List[Dict[str, Any]]: 店铺列表
        """
        api_logger.log_business_operation("获取店铺列表")
        
        response = self.get(APIConfig.BUSINESS_URLS['seller_lists'])
        
        if response.get('code') == 0:
            sellers = response.get('data', [])
            api_logger.log_business_operation("获取店铺列表", result_count=len(sellers))
            return sellers
        else:
            raise APIException("获取店铺列表失败", response.get('code'), response)
    
    def get_restock_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取补货建议列表
        
        Args:
            params: 查询参数
            
        Returns:
            Dict[str, Any]: 补货建议数据
        """
        api_logger.log_business_operation("获取补货建议", params)
        
        response = self.post(APIConfig.BUSINESS_URLS['restock_summary'], data=params)
        
        if response.get('code') == 0:
            total = response.get('total', 0)
            data = response.get('data', [])
            api_logger.log_business_operation("获取补货建议", params, len(data))
            return response
        else:
            raise APIException("获取补货建议失败", response.get('code'), response)
    
    def get_listing_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取Listing数据
        
        Args:
            params: 查询参数
            
        Returns:
            Dict[str, Any]: Listing数据
        """
        api_logger.log_business_operation("获取Listing数据", params)
        
        response = self.post(APIConfig.BUSINESS_URLS['listing_data'], data=params)
        
        if response.get('code') == 0:
            data = response.get('data', [])
            api_logger.log_business_operation("获取Listing数据", params, len(data))
            return response
        else:
            raise APIException("获取Listing数据失败", response.get('code'), response)
    
    def get_msku_detail_info(self, sid: int, msku: str, mode: int = 0) -> Dict[str, Any]:
        """
        获取MSKU详细信息
        
        Args:
            sid: 店铺ID
            msku: MSKU编码
            mode: 补货建议模式（0: 普通模式, 1: 海外仓中转模式）
            
        Returns:
            Dict[str, Any]: MSKU详细信息
        """
        params = {
            'sid': sid,
            'msku': msku,
            'mode': mode
        }
        
        api_logger.log_business_operation("获取MSKU详细信息", params)
        
        response = self.post(APIConfig.BUSINESS_URLS['msku_detail_info'], data=params)
        
        if response.get('code') == 0:
            data = response.get('data', {})
            api_logger.log_business_operation("获取MSKU详细信息", params, 1 if data else 0)
            return response
        else:
            raise APIException("获取MSKU详细信息失败", response.get('code'), response)
    
    def get_all_restock_data(self, base_params: Dict[str, Any], 
                            max_pages: int = None) -> List[Dict[str, Any]]:
        """
        获取所有补货数据（自动分页）
        
        Args:
            base_params: 基础查询参数
            max_pages: 最大页数限制
            
        Returns:
            List[Dict[str, Any]]: 所有补货数据
        """
        all_data = []
        offset = base_params.get('offset', 0)
        length = base_params.get('length', APIConfig.DEFAULT_PAGE_SIZE)
        page_count = 0
        
        api_logger.logger.info(f"开始获取所有补货数据，每页{length}条")
        
        while True:
            if max_pages and page_count >= max_pages:
                api_logger.logger.info(f"达到最大页数限制: {max_pages}")
                break
            
            # 更新分页参数
            current_params = base_params.copy()
            current_params.update({
                'offset': offset,
                'length': length
            })
            
            try:
                response = self.get_restock_summary(current_params)
                data = response.get('data', [])
                total = response.get('total', 0)
                
                if not data:
                    api_logger.logger.info("没有更多数据")
                    break
                
                all_data.extend(data)
                page_count += 1
                
                api_logger.logger.info(
                    f"第{page_count}页: 获取{len(data)}条数据，累计{len(all_data)}条，总计{total}条"
                )
                
                # 检查是否还有更多数据
                if len(all_data) >= total or len(data) < length:
                    api_logger.logger.info("已获取所有数据")
                    break
                
                # 更新偏移量
                offset += length
                
                # 添加延迟避免请求过快
                time.sleep(0.5)
                
            except Exception as e:
                api_logger.log_error(e, f"获取第{page_count + 1}页数据失败")
                break
        
        api_logger.logger.info(f"总共获取{len(all_data)}条补货数据，共{page_count}页")
        return all_data
    
    def get_all_restock_data_concurrent(self, base_params: Dict[str, Any],
                                      max_pages: int = None,
                                      max_workers: int = 3) -> List[Dict[str, Any]]:
        """
        并发获取所有补货数据（提高获取速度）
        
        Args:
            base_params: 基础查询参数
            max_pages: 最大页数限制
            max_workers: 最大并发线程数
            
        Returns:
            List[Dict[str, Any]]: 所有补货数据
        """
        # 首先获取第一页数据，确定总数
        first_params = base_params.copy()
        first_params.update({'offset': 0, 'length': base_params.get('length', APIConfig.DEFAULT_PAGE_SIZE)})
        
        try:
            first_response = self.get_restock_summary(first_params)
            first_data = first_response.get('data', [])
            total = first_response.get('total', 0)
            length = first_params['length']
            
            if not first_data or total <= length:
                api_logger.logger.info(f"数据获取完成，共{len(first_data)}条")
                return first_data
            
            # 计算需要获取的页数
            total_pages = (total + length - 1) // length
            if max_pages:
                total_pages = min(total_pages, max_pages)
            
            api_logger.logger.info(f"开始并发获取数据，总计{total}条，分{total_pages}页，每页{length}条")
            
            all_data = first_data.copy()
            
            # 如果只有一页，直接返回
            if total_pages <= 1:
                return all_data
            
            # 准备并发任务
            def fetch_page(page_num):
                offset = page_num * length
                params = base_params.copy()
                params.update({'offset': offset, 'length': length})
                
                try:
                    with self._request_lock:  # 确保token操作的线程安全
                        response = self.get_restock_summary(params)
                    return page_num, response.get('data', [])
                except Exception as e:
                    api_logger.log_error(e, f"获取第{page_num + 1}页数据失败")
                    return page_num, []
            
            # 使用线程池并发获取剩余页面
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交任务（从第2页开始）
                future_to_page = {executor.submit(fetch_page, page): page 
                                for page in range(1, total_pages)}
                
                # 收集结果
                page_results = {}
                for future in as_completed(future_to_page):
                    page_num, data = future.result()
                    page_results[page_num] = data
                    api_logger.logger.info(f"第{page_num + 1}页: 获取{len(data)}条数据")
                
                # 按页码顺序合并数据
                for page_num in sorted(page_results.keys()):
                    all_data.extend(page_results[page_num])
            
            api_logger.logger.info(f"并发数据获取完成，共{len(all_data)}条")
            return all_data
            
        except Exception as e:
            api_logger.log_error(e, "并发获取数据失败，回退到串行模式")
            return self.get_all_restock_data(base_params, max_pages)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接
        
        Returns:
            Dict[str, Any]: 连接测试结果
        """
        try:
            api_logger.logger.info("测试API连接")
            sellers = self.get_seller_lists()
            api_logger.logger.info(f"连接测试成功，获取到{len(sellers)}个店铺")
            
            # 获取Token信息
            token_info = self.token_manager.get_token_info()
            token_status = "有效" if token_info else "无效"
            
            return {
                'success': True,
                'token_status': token_status,
                'seller_count': len(sellers),
                'message': '连接测试成功'
            }
        except Exception as e:
            api_logger.log_error(e, "API连接测试失败")
            return {
                'success': False,
                'token_status': '无效',
                'seller_count': 0,
                'message': f'连接测试失败: {str(e)}'
            }
    
    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前Token信息
        
        Returns:
            Optional[Dict[str, Any]]: Token信息
        """
        return self.token_manager.get_token_info()
    
    def force_refresh_token(self) -> bool:
        """
        强制刷新Token
        
        Returns:
            bool: 是否成功
        """
        return self.token_manager.force_refresh()

class APIException(Exception):
    """API异常类"""
    
    def __init__(self, message: str, code: Any = None, 
                 response_data: Dict[str, Any] = None,
                 error_details: List = None):
        """
        初始化API异常
        
        Args:
            message: 错误消息
            code: 错误代码
            response_data: 响应数据
            error_details: 错误详情
        """
        super().__init__(message)
        self.code = code
        self.response_data = response_data
        self.error_details = error_details or []
        
        # 获取详细错误信息
        if code:
            detailed_msg = APIConfig.get_error_message(str(code))
            if detailed_msg != f"未知错误码: {code}":
                self.message = f"{message} - {detailed_msg}"
            else:
                self.message = message
        else:
            self.message = message
    
    def __str__(self):
        return f"APIException: {self.message} (code: {self.code})"