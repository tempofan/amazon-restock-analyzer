#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取FBA补货建议列表API文档
专门获取GetSummaryList接口文档
"""

import requests
import json
import time

def get_fba_summary_list_api_doc():
    """
    获取FBA补货建议列表API文档
    """
    print("🔍 获取FBA补货建议列表API文档")
    print("=" * 50)
    
    # API文档基础配置
    base_url = "https://apidoc.lingxing.com"
    api_url = f"{base_url}/api/openapi-manage"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/json',
        'Referer': 'https://apidoc.lingxing.com/',
        'Origin': 'https://apidoc.lingxing.com'
    }
    
    try:
        # 1. 认证
        print("1. 进行文档认证...")
        auth_url = f"{api_url}/account/check/doc_access"
        auth_data = {"docAccess": "YESofbbaoY"}
        
        auth_response = requests.put(auth_url, json=auth_data, headers=headers, timeout=10)
        
        if auth_response.status_code == 200:
            auth_result = auth_response.json()
            if auth_result.get('code') == 200:
                print("✅ 认证成功")
            else:
                print(f"❌ 认证失败: {auth_result}")
                return
        else:
            print(f"❌ 认证HTTP错误: {auth_response.status_code}")
            return
        
        # 2. 尝试获取GetSummaryList文档
        print("\n2. 获取GetSummaryList API文档...")
        
        # 可能的文档路径
        possible_paths = [
            "FBASug/GetSummaryList",
            "FBASug/getSummaryList", 
            "FBASug/SummaryList",
            "FBASug/List",
            "FBASug/GetList"
        ]
        
        for path in possible_paths:
            print(f"\n尝试路径: {path}")
            doc_url = f"{base_url}/docs/{path}.md"
            
            try:
                doc_response = requests.get(doc_url, headers=headers, timeout=10)
                
                if doc_response.status_code == 200:
                    content = doc_response.text
                    
                    # 检查是否是有效的API文档
                    if "API Path" in content and "请求参数" in content:
                        print(f"✅ 成功获取文档: {path}")
                        
                        # 保存文档
                        filename = f"api_doc_FBASug_{path.replace('/', '_')}.md"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        print(f"📄 文档已保存: {filename}")
                        
                        # 分析文档内容
                        print("\n📋 文档内容分析:")
                        lines = content.split('\n')
                        for i, line in enumerate(lines[:50]):  # 显示前50行
                            if line.strip():
                                print(f"   {i+1:2d}: {line}")
                        
                        return content
                    else:
                        print(f"   ⚠️ 不是有效的API文档")
                else:
                    print(f"   ❌ HTTP错误: {doc_response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 请求异常: {e}")
        
        # 3. 如果直接路径不行，尝试通过API列表获取
        print("\n3. 尝试通过API列表获取...")
        
        list_url = f"{api_url}/docs/list"
        list_response = requests.get(list_url, headers=headers, timeout=10)
        
        if list_response.status_code == 200:
            list_result = list_response.json()
            print(f"API列表响应: {json.dumps(list_result, ensure_ascii=False, indent=2)[:1000]}...")
            
            # 查找FBA相关的API
            if 'data' in list_result:
                for category in list_result['data']:
                    if 'FBA' in category.get('name', '') or 'fbaSug' in category.get('name', ''):
                        print(f"\n找到FBA相关分类: {category}")
                        
                        if 'children' in category:
                            for api in category['children']:
                                if 'Summary' in api.get('name', '') or 'List' in api.get('name', ''):
                                    print(f"  找到可能的API: {api}")
        
        print("\n❌ 未找到GetSummaryList API文档")
        print("💡 建议检查API文档网站或联系技术支持确认正确的接口名称")
        
    except Exception as e:
        print(f"❌ 获取文档异常: {e}")

if __name__ == "__main__":
    get_fba_summary_list_api_doc()
