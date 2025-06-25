#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查补货建议数据结构
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.lingxing_api_new import LingxingAPINew

def inspect_data_structure():
    """
    检查数据结构
    """
    print("🔍 检查补货建议数据结构")
    print("=" * 50)
    
    # 创建API客户端
    api = LingxingAPINew()
    
    # 获取补货建议列表
    print("1. 获取补货建议列表...")
    result = api.get_replenishment_suggestions(page=1, page_size=3)
    
    print(f"完整响应结构:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    inspect_data_structure()
