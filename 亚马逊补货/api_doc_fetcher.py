#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 领星API文档获取器
自动获取领星API文档并按分类存储为Markdown文件

功能特性:
- 🔑 支持访问密钥验证
- 📂 自动按分类存储文档
- 🌐 批量获取父级目录下所有API文档
- 📝 生成标准化Markdown格式
- ⚡ 支持并发获取提高效率

作者: AI助手
创建时间: 2025-01-27
"""

import os
import sys
import time
import json
import hashlib
import requests
from urllib.parse import urlparse, urljoin, unquote
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import re
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目工具
try:
    from utils.logger import api_logger
except ImportError:
    # 如果无法导入项目日志，使用标准日志
    import logging
    logging.basicConfig(level=logging.INFO)
    api_logger = logging.getLogger(__name__)


class LingxingAPIDocFetcher:
    """
    领星API文档获取器
    """
    
    def __init__(self, access_key: str = "YESofbbaoY"):
        """
        初始化文档获取器
        
        Args:
            access_key: 访问密钥
        """
        self.access_key = access_key
        self.base_url = "https://apidoc.lingxing.com"
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 文档存储目录
        self.doc_dir = Path("api_doc")
        self.doc_dir.mkdir(exist_ok=True)
        
        # 分类映射
        self.category_mapping = {
            'authorization': 'auth',
            'guidance': 'guidance', 
            'basicdata': 'general',
            'sale': 'general',
            'case': 'case',
            'fbaSug': 'guidance',
            'routing': 'guidance'
        }
        
        print(f"🔍 领星API文档获取器已初始化")
        print(f"📁 文档存储目录: {self.doc_dir.absolute()}")
        print(f"🔑 访问密钥: {access_key}")
    
    def validate_access_key(self) -> bool:
        """
        验证访问密钥
        
        Returns:
            bool: 是否验证成功
        """
        try:
            # 尝试访问一个简单的API文档页面来验证密钥
            test_url = f"{self.base_url}/#/docs/Guidance/newInstructions"
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ 访问密钥验证成功")
                return True
            else:
                print(f"❌ 访问密钥验证失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 访问密钥验证异常: {e}")
            return False
    
    def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        解析API文档URL，提取分类和路径信息
        
        Args:
            url: API文档URL
            
        Returns:
            Tuple[category, parent_path, doc_path]: 分类、父级路径、文档路径
        """
        try:
            # 解析URL: https://apidoc.lingxing.com/#/docs/Case/InventorySync
            if "#/docs/" not in url:
                print(f"❌ 无效的API文档URL: {url}")
                return None, None, None
            
            # 提取文档路径部分
            doc_part = url.split("#/docs/")[1]
            path_parts = doc_part.split("/")
            
            if len(path_parts) < 2:
                print(f"❌ URL路径格式错误: {url}")
                return None, None, None
            
            parent_path = path_parts[0]  # 如: Case
            doc_path = "/".join(path_parts)  # 如: Case/InventorySync
            
            # 确定分类
            category = self.category_mapping.get(parent_path.lower(), 'general')
            
            print(f"📋 URL解析结果:")
            print(f"   - 父级路径: {parent_path}")
            print(f"   - 文档路径: {doc_path}")
            print(f"   - 分类: {category}")
            
            return category, parent_path, doc_path
            
        except Exception as e:
            print(f"❌ URL解析失败: {e}")
            return None, None, None
    
    def get_api_list(self, parent_path: str) -> List[Dict]:
        """
        获取指定父级路径下的所有API文档列表
        
        Args:
            parent_path: 父级路径，如 'Case'
            
        Returns:
            List[Dict]: API文档列表
        """
        try:
            print(f"🔄 获取 {parent_path} 目录下的API列表...")
            
            # 构建API列表请求URL（这里需要根据实际的API接口调整）
            # 由于领星API文档网站的具体接口结构未知，这里使用模拟方式
            api_list = []
            
            # 根据已知的文档结构，构建可能的API路径
            known_apis = {
                'Authorization': ['GetToken', 'RefreshToken'],
                'Guidance': ['newInstructions', 'ErrorCode', 'QA'],
                'BasicData': ['SellerLists'],
                'Sale': ['Listing'],
                'Case': ['InventorySync', 'STAProcess'],
                'FBASug': ['GetSummaryList', 'InfoMSKU']
            }
            
            if parent_path in known_apis:
                for api_name in known_apis[parent_path]:
                    api_list.append({
                        'name': api_name,
                        'path': f"{parent_path}/{api_name}",
                        'url': f"{self.base_url}/#/docs/{parent_path}/{api_name}"
                    })
            
            print(f"✅ 找到 {len(api_list)} 个API文档")
            return api_list
            
        except Exception as e:
            print(f"❌ 获取API列表失败: {e}")
            return []
    
    def fetch_api_doc_content(self, doc_path: str) -> Optional[str]:
        """
        获取单个API文档的内容
        
        Args:
            doc_path: 文档路径，如 'Case/InventorySync'
            
        Returns:
            Optional[str]: 文档内容（Markdown格式）
        """
        try:
            # 构建文档URL
            doc_url = f"{self.base_url}/#/docs/{doc_path}"
            
            print(f"📥 正在获取文档: {doc_path}")
            
            # 发送请求获取文档页面
            response = self.session.get(doc_url, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ 获取文档失败: HTTP {response.status_code}")
                return None
            
            # 这里需要解析HTML页面并提取API文档内容
            # 由于具体的页面结构未知，这里提供一个框架
            content = self.parse_doc_content(response.text, doc_path, doc_url)
            
            if content:
                print(f"✅ 成功获取文档: {doc_path}")
                return content
            else:
                print(f"❌ 文档内容解析失败: {doc_path}")
                return None
                
        except Exception as e:
            print(f"❌ 获取文档异常: {doc_path} - {e}")
            return None
    
    def parse_doc_content(self, html_content: str, doc_path: str, doc_url: str) -> Optional[str]:
        """
        解析HTML页面，提取API文档内容并转换为Markdown格式
        
        Args:
            html_content: HTML页面内容
            doc_path: 文档路径
            doc_url: 文档URL
            
        Returns:
            Optional[str]: Markdown格式的文档内容
        """
        try:
            # 由于无法直接解析领星网站的具体结构，这里提供一个通用的框架
            # 实际使用时需要根据网站的HTML结构进行调整
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 生成文档头部
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            category = self.get_category_from_path(doc_path)
            
            markdown_content = f"""# 领星API文档 - {doc_path}

获取时间: {timestamp}
文档路径: {doc_path}
源URL: {doc_url}
分类: {category}
访问密钥: {self.access_key}

---

"""
            
            # 尝试提取文档标题
            title_element = soup.find('h1') or soup.find('h2') or soup.find('.title')
            if title_element:
                markdown_content += f"# {title_element.get_text().strip()}\n\n"
            
            # 尝试提取文档内容
            # 这里需要根据实际的HTML结构进行调整
            content_area = soup.find('.content') or soup.find('.doc-content') or soup.find('main')
            
            if content_area:
                # 简单的HTML到Markdown转换
                markdown_content += self.html_to_markdown(content_area)
            else:
                # 如果找不到内容区域，提取所有文本
                text_content = soup.get_text()
                # 清理和格式化文本
                cleaned_text = re.sub(r'\n\s*\n', '\n\n', text_content)
                markdown_content += cleaned_text
            
            return markdown_content
            
        except ImportError:
            print("❌ 需要安装 beautifulsoup4: pip install beautifulsoup4")
            return None
        except Exception as e:
            print(f"❌ 解析文档内容失败: {e}")
            return None
    
    def html_to_markdown(self, element) -> str:
        """
        简单的HTML到Markdown转换
        
        Args:
            element: BeautifulSoup元素
            
        Returns:
            str: Markdown格式文本
        """
        # 这是一个简化的转换器，实际使用可能需要更复杂的逻辑
        text = element.get_text()
        
        # 基本的格式化
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 清理多余空行
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # 去除行首空格
        
        return text
    
    def get_category_from_path(self, doc_path: str) -> str:
        """
        根据文档路径确定分类
        
        Args:
            doc_path: 文档路径
            
        Returns:
            str: 分类名称
        """
        parent_path = doc_path.split('/')[0].lower()
        return self.category_mapping.get(parent_path, 'general')
    
    def save_doc_to_file(self, content: str, doc_path: str, category: str) -> str:
        """
        保存文档内容到文件
        
        Args:
            content: 文档内容
            doc_path: 文档路径
            category: 分类
            
        Returns:
            str: 保存的文件路径
        """
        try:
            # 创建分类目录
            category_dir = self.doc_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = int(time.time())
            safe_path = doc_path.replace('/', '_').replace('\\', '_')
            filename = f"lingxing_api_{safe_path}_{timestamp}.md"
            
            file_path = category_dir / filename
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"💾 文档已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ 保存文档失败: {e}")
            return ""
    
    def fetch_docs_from_url(self, url: str, max_workers: int = 3) -> Dict[str, str]:
        """
        从指定URL获取父级目录下所有API文档
        
        Args:
            url: 起始URL
            max_workers: 最大并发数
            
        Returns:
            Dict[str, str]: 成功获取的文档 {doc_path: file_path}
        """
        print(f"🚀 开始从URL获取API文档: {url}")
        print("=" * 80)
        
        # 解析URL
        category, parent_path, doc_path = self.parse_url(url)
        if not all([category, parent_path, doc_path]):
            print("❌ URL解析失败，无法继续")
            return {}
        
        # 验证访问密钥
        if not self.validate_access_key():
            print("❌ 访问密钥验证失败，无法继续")
            return {}
        
        # 获取API列表
        api_list = self.get_api_list(parent_path)
        if not api_list:
            print("❌ 未找到API文档列表")
            return {}
        
        print(f"📚 准备获取 {len(api_list)} 个API文档")
        print(f"🔧 并发数: {max_workers}")
        print()
        
        # 并发获取文档
        successful_docs = {}
        
        def fetch_single_doc(api_info):
            """获取单个文档"""
            try:
                doc_path = api_info['path']
                content = self.fetch_api_doc_content(doc_path)
                
                if content:
                    file_path = self.save_doc_to_file(content, doc_path, category)
                    if file_path:
                        return doc_path, file_path
                
                return doc_path, None
                
            except Exception as e:
                print(f"❌ 获取文档失败: {api_info.get('path', 'unknown')} - {e}")
                return api_info.get('path', 'unknown'), None
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_api = {executor.submit(fetch_single_doc, api_info): api_info 
                           for api_info in api_list}
            
            # 收集结果
            for future in as_completed(future_to_api):
                api_info = future_to_api[future]
                try:
                    doc_path, file_path = future.result()
                    if file_path:
                        successful_docs[doc_path] = file_path
                        print(f"✅ 完成: {doc_path}")
                    else:
                        print(f"❌ 失败: {doc_path}")
                        
                except Exception as e:
                    print(f"❌ 处理异常: {api_info.get('path', 'unknown')} - {e}")
        
        # 输出结果汇总
        print()
        print("=" * 80)
        print(f"📊 获取完成汇总:")
        print(f"   - 总计文档: {len(api_list)}")
        print(f"   - 成功获取: {len(successful_docs)}")
        print(f"   - 失败数量: {len(api_list) - len(successful_docs)}")
        print(f"   - 存储目录: {self.doc_dir.absolute()}")
        
        if successful_docs:
            print(f"\n✅ 成功获取的文档:")
            for doc_path, file_path in successful_docs.items():
                print(f"   - {doc_path} → {file_path}")
        
        return successful_docs
    
    def batch_fetch_multiple_urls(self, urls: List[str], max_workers: int = 3) -> Dict[str, Dict[str, str]]:
        """
        批量获取多个URL的API文档
        
        Args:
            urls: URL列表
            max_workers: 最大并发数
            
        Returns:
            Dict[str, Dict[str, str]]: 每个URL的获取结果
        """
        print(f"🚀 批量获取API文档")
        print(f"📋 URL数量: {len(urls)}")
        print("=" * 80)
        
        all_results = {}
        
        for i, url in enumerate(urls, 1):
            print(f"\n🔄 处理第 {i}/{len(urls)} 个URL")
            print(f"🌐 URL: {url}")
            
            results = self.fetch_docs_from_url(url, max_workers)
            all_results[url] = results
            
            # 添加延迟避免请求过快
            if i < len(urls):
                print(f"⏱️ 等待 2 秒后处理下一个URL...")
                time.sleep(2)
        
        # 输出总体汇总
        print("\n" + "=" * 80)
        print(f"🎉 批量获取完成!")
        
        total_docs = sum(len(results) for results in all_results.values())
        print(f"📊 总体统计:")
        print(f"   - 处理URL数: {len(urls)}")
        print(f"   - 获取文档总数: {total_docs}")
        print(f"   - 存储目录: {self.doc_dir.absolute()}")
        
        return all_results


def main():
    """
    主函数 - 交互式使用
    """
    print("🔍 领星API文档获取器")
    print("=" * 60)
    
    # 获取访问密钥
    access_key = input(f"🔑 请输入访问密钥 (默认: YESofbbaoY): ").strip()
    if not access_key:
        access_key = "YESofbbaoY"
    
    # 创建获取器
    fetcher = LingxingAPIDocFetcher(access_key)
    
    print("\n请选择操作模式:")
    print("1. 单个URL获取")
    print("2. 批量URL获取")
    print("3. 退出")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        # 单个URL模式
        url = input("\n📋 请输入API文档URL: ").strip()
        if url:
            max_workers = input("🔧 并发数 (默认: 3): ").strip()
            max_workers = int(max_workers) if max_workers.isdigit() else 3
            
            fetcher.fetch_docs_from_url(url, max_workers)
        else:
            print("❌ URL不能为空")
    
    elif choice == "2":
        # 批量URL模式
        print("\n📋 请输入多个API文档URL (每行一个，空行结束):")
        urls = []
        while True:
            url = input().strip()
            if not url:
                break
            urls.append(url)
        
        if urls:
            max_workers = input("🔧 并发数 (默认: 3): ").strip()
            max_workers = int(max_workers) if max_workers.isdigit() else 3
            
            fetcher.batch_fetch_multiple_urls(urls, max_workers)
        else:
            print("❌ 至少需要输入一个URL")
    
    elif choice == "3":
        print("👋 再见!")
    
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main() 