#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用API文档获取器
支持通过URL输入获取任意领星API文档，自动保存到规范目录

功能特点：
1. 交互式URL输入
2. 自动解析文档路径
3. 智能分类保存
4. 支持批量获取
5. 错误处理和重试

作者：Augment Agent
版本：2.0 (通用版本)
日期：2025-06-23
"""

import sys
import os
import requests
import json
import time
import re
import urllib.parse
from datetime import datetime

def get_global_config():
    """
    获取领星API全局配置信息
    
    Returns:
        str: API基础URL
    """
    print("🔍 获取全局配置...")
    
    try:
        # 获取配置文件
        config_url = "https://apidoc.lingxing.com/config/env.js"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://apidoc.lingxing.com/',
        }
        
        response = requests.get(config_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ 成功获取配置文件")
            
            config_content = response.text
            
            # 查找动态API URL配置
            dynamic_match = re.search(r'apiUrl\s*:\s*location\.origin\s*\+\s*["\']([^"\']+)["\']', config_content)
            if dynamic_match:
                api_path = dynamic_match.group(1)
                api_url = f"https://apidoc.lingxing.com{api_path}"
                print(f"🔗 发现API URL: {api_url}")
                return api_url
            
            # 查找静态API URL配置
            static_match = re.search(r'apiUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']', config_content)
            if static_match:
                api_url = static_match.group(1)
                print(f"🔗 发现API URL: {api_url}")
                return api_url
                
        else:
            print(f"❌ 获取配置文件失败: {response.status_code}")
            
    except Exception as e:
        print(f"💥 获取配置时出错: {e}")
    
    # 返回默认的API URL
    return "https://apidoc.lingxing.com/api/openapi-manage"

def authenticate_with_doc_key(api_url, doc_key):
    """
    使用文档密钥进行认证
    
    Args:
        api_url (str): API基础URL
        doc_key (str): 文档访问密钥
        
    Returns:
        str: 访问令牌，失败返回None
    """
    print("🔐 进行文档认证...")
    
    auth_url = f"{api_url}/account/check/doc_access"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'X-HTTP-Method-Override': 'PUT',
        'Referer': 'https://apidoc.lingxing.com/',
        'Origin': 'https://apidoc.lingxing.com',
    }
    
    auth_data = {"docAccess": doc_key}
    
    try:
        response = requests.put(auth_url, 
                               json=auth_data, 
                               headers=headers, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('data', {}).get('can_access'):
                token = result['data']['can_access']
                print(f"✅ 认证成功")
                return token
            else:
                print(f"❌ 认证失败: {result.get('msg', '未知错误')}")
        else:
            print(f"❌ 认证请求失败: {response.status_code}")
                
    except Exception as e:
        print(f"💥 认证时出错: {e}")
    
    return None

def parse_doc_url(url):
    """
    解析文档URL，提取文档路径
    
    Args:
        url (str): 完整的文档URL
        
    Returns:
        tuple: (doc_path, category)
    """
    # 支持的URL格式：
    # https://apidoc.lingxing.com/#/docs/FBASug/InfoMSKU
    # https://apidoc.lingxing.com/#/docs/Guidance/newInstructions
    
    # 提取文档路径
    if '#/docs/' in url:
        doc_path = url.split('#/docs/')[-1]
    elif '/docs/' in url:
        doc_path = url.split('/docs/')[-1]
    else:
        # 假设整个URL就是文档路径
        parsed = urllib.parse.urlparse(url)
        doc_path = parsed.path.strip('/')
    
    # 根据路径确定分类
    if 'FBASug' in doc_path or 'fba' in doc_path.lower():
        category = 'fba_suggestion'
    elif 'Guidance' in doc_path or 'guidance' in doc_path.lower():
        category = 'guidance'
    elif 'Restocking' in doc_path or 'restocking' in doc_path.lower():
        category = 'restocking'
    elif 'Auth' in doc_path or 'auth' in doc_path.lower():
        category = 'auth'
    else:
        category = 'general'
    
    return doc_path, category

def get_markdown_content(api_url, token, doc_path):
    """
    获取Markdown文档内容
    
    Args:
        api_url (str): API基础URL
        token (str): 访问令牌
        doc_path (str): 文档路径
        
    Returns:
        str: 文档内容，失败返回None
    """
    print(f"📄 获取文档内容: {doc_path}")
    
    # 尝试多种可能的文档URL格式
    doc_urls = [
        f"https://apidoc.lingxing.com/docs/{doc_path}.md",
        f"https://apidoc.lingxing.com/{doc_path}.md",
        f"{api_url}/docs/{doc_path}.md",
        f"{api_url}/{doc_path}.md",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/plain, */*',
        'Referer': 'https://apidoc.lingxing.com/',
        'Authorization': f'Bearer {token}',
        'Cookie': f'doc_access_token={token}',
    }
    
    for doc_url in doc_urls:
        print(f"   🔗 尝试: {doc_url}")
        
        try:
            response = requests.get(doc_url, headers=headers, timeout=30)
            print(f"      状态码: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                print(f"      ✅ 成功获取文档 (长度: {len(content)} 字符)")
                
                # 检查是否是有效的Markdown内容
                if content.strip() and not content.startswith('<!DOCTYPE'):
                    return content
                else:
                    print(f"      ⚠️  内容似乎不是Markdown格式")
            
        except Exception as e:
            print(f"      💥 请求失败: {e}")
    
    return None

def save_document(content, doc_path, category, source_url, doc_key):
    """
    保存文档到规范目录
    
    Args:
        content (str): 文档内容
        doc_path (str): 文档路径
        category (str): 文档分类
        source_url (str): 源URL
        doc_key (str): 访问密钥
        
    Returns:
        str: 保存的文件路径
    """
    # 确保目录存在
    docs_dir = os.path.join("亚马逊补货建议", "api_management", "docs", category)
    os.makedirs(docs_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = int(time.time())
    safe_doc_path = doc_path.replace('/', '_').replace('\\', '_')
    filename = f"lingxing_api_{safe_doc_path}_{timestamp}.md"
    filepath = os.path.join(docs_dir, filename)
    
    # 保存文档
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 领星API文档 - {doc_path}\n\n")
        f.write(f"获取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"文档路径: {doc_path}\n")
        f.write(f"源URL: {source_url}\n")
        f.write(f"分类: {category}\n")
        f.write(f"访问密钥: {doc_key}\n\n")
        f.write("---\n\n")
        f.write(content)
    
    print(f"💾 文档已保存: {filepath}")
    return filepath

def analyze_document_content(content, doc_name):
    """
    分析文档内容并提取关键信息
    
    Args:
        content (str): 文档内容
        doc_name (str): 文档名称
    """
    print(f"📋 分析文档内容: {doc_name}")
    print(f"   长度: {len(content)} 字符")
    print(f"   行数: {len(content.split(chr(10)))}")
    
    # 查找API路径
    api_path_match = re.search(r'`([^`]*(?:erp|api)[^`]*)`', content)
    if api_path_match:
        print(f"   🔗 API路径: {api_path_match.group(1)}")
    
    # 查找关键字段
    keywords = [
        'quantity_sug_purchase', 'quantity_sug_local_to_fba', 'quantity_sug_oversea_to_fba',
        'quantity_sug_local_to_oversea', 'fba', 'msku', 'asin', 'suggestion', 'inventory',
        'access_token', 'app_key', 'timestamp', 'sign', 'error', 'code', 'message'
    ]
    
    found_keywords = []
    content_lower = content.lower()
    for keyword in keywords:
        if keyword.lower() in content_lower:
            found_keywords.append(keyword)
    
    if found_keywords:
        print(f"   ✅ 包含关键字段: {', '.join(found_keywords[:5])}{'...' if len(found_keywords) > 5 else ''}")
    else:
        print(f"   ❌ 未找到关键字段")
