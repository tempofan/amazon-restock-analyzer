#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领星API文档获取器 - 最终版本
用于自动获取和解析领星FBA补货建议API文档

功能特点：
1. 自动获取API配置信息
2. 正确的文档认证流程
3. 下载完整的Markdown格式API文档
4. 分析和提取关键信息

作者：Augment Agent
版本：1.0 (最终版本)
日期：2025-01-22
"""

import sys
import os
import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse

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
            print(f"📄 配置内容预览: {config_content[:100]}...")
            
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
            
            print("❌ 未在配置中找到API URL")
                
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
        
        print(f"📋 认证响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 认证结果: {result}")
            
            if result.get('data', {}).get('can_access'):
                token = result['data']['can_access']
                print(f"✅ 认证成功，获得访问令牌")
                return token
            else:
                print(f"❌ 认证失败: {result.get('msg', '未知错误')}")
        else:
            print(f"❌ 认证请求失败: {response.status_code}")
            if response.text:
                print(f"   错误信息: {response.text}")
                
    except Exception as e:
        print(f"💥 认证时出错: {e}")
    
    return None

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
    
    # 查找补货相关关键词
    replenishment_keywords = [
        'quantity_sug_purchase', 'quantity_sug_local_to_fba', 'quantity_sug_oversea_to_fba',
        'quantity_sug_local_to_oversea', 'quantity_sug_replenishment', 'quantity_sug_send',
        'fba', 'msku', 'asin', 'suggestion', 'inventory', 'stock'
    ]
    
    found_keywords = []
    content_lower = content.lower()
    for keyword in replenishment_keywords:
        if keyword.lower() in content_lower:
            found_keywords.append(keyword)
    
    if found_keywords:
        print(f"   ✅ 包含补货相关字段: {', '.join(found_keywords[:5])}{'...' if len(found_keywords) > 5 else ''}")
    else:
        print(f"   ❌ 未找到补货相关字段")

def fetch_lingxing_api_docs(doc_key="YESofbbaoY"):
    """
    获取领星API文档的主函数
    
    Args:
        doc_key (str): 文档访问密钥
        
    Returns:
        dict: 包含文档内容的字典
    """
    print("🚀 领星API文档获取器")
    print("=" * 60)
    print(f"🔑 使用访问密钥: {doc_key}")
    
    # 1. 获取全局配置
    api_url = get_global_config()
    print(f"🌐 API基础URL: {api_url}")
    
    # 2. 进行认证
    token = authenticate_with_doc_key(api_url, doc_key)
    
    if not token:
        print("❌ 认证失败，无法继续")
        return {}
    
    # 3. 获取API文档
    doc_paths = [
        "FBASug/InfoMSKU",      # 查询建议信息-MSKU
        "FBASug/SourceListMSKU", # 查询报表型数据明细-MSKU
    ]
    
    documents = {}
    
    for doc_path in doc_paths:
        content = get_markdown_content(api_url, token, doc_path)
        if content:
            # 保存文档
            timestamp = int(time.time())
            filename = f"lingxing_api_{doc_path.replace('/', '_')}_{timestamp}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"💾 文档已保存: {filename}")
            
            # 分析内容
            analyze_document_content(content, doc_path)
            
            # 存储到结果中
            documents[doc_path] = {
                'content': content,
                'filename': filename,
                'timestamp': timestamp
            }
            
            print()  # 添加空行分隔
    
    print(f"🎉 成功获取 {len(documents)} 个API文档!")
    return documents

def main():
    """
    主函数
    """
    try:
        # 获取API文档
        docs = fetch_lingxing_api_docs()
        
        if docs:
            print("\n📚 获取的文档列表:")
            for doc_path, info in docs.items():
                print(f"   📄 {doc_path}: {info['filename']}")
            
            print("\n💡 使用提示:")
            print("   1. 查看生成的.md文件获取完整API文档")
            print("   2. 文档包含完整的请求参数和响应示例")
            print("   3. 可以直接用于API集成开发")
        else:
            print("\n❌ 未能获取任何文档")
            
    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n💥 程序执行出错: {e}")

if __name__ == '__main__':
    main()
