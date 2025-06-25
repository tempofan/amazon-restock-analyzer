#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FBA建议API测试脚本
测试"建议本地发FBA量（普通模式）"API接口
"""

import requests
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fba_suggestion_api():
    """
    测试FBA建议API接口
    """
    print("🎯 开始测试FBA建议API接口")
    print("=" * 50)
    
    # API端点
    base_url = "http://127.0.0.1:5000"
    api_url = f"{base_url}/api/fba-suggestion-info"
    
    # 测试数据
    test_cases = [
        {
            "name": "测试MSKU - 普通模式",
            "data": {
                "shop_id": "136",
                "msku": "CNxxxx",
                "mode": 0
            }
        },
        {
            "name": "测试ASIN - 普通模式", 
            "data": {
                "shop_id": "136",
                "asin": "B07XXXXXXX",
                "mode": 0
            }
        },
        {
            "name": "测试MSKU - 海外仓中转模式",
            "data": {
                "shop_id": "136",
                "msku": "CNxxxx",
                "mode": 1
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # 发送POST请求
            response = requests.post(
                api_url,
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"📡 请求URL: {api_url}")
            print(f"📤 请求数据: {json.dumps(test_case['data'], ensure_ascii=False)}")
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📥 响应结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    print("✅ API调用成功!")
                    
                    # 检查关键字段
                    data = result.get('data', {})
                    local_to_fba = data.get('quantity_sug_local_to_fba', 0)
                    print(f"🎯 建议本地发FBA量（普通模式）: {local_to_fba}")
                    
                    if local_to_fba > 0:
                        print(f"🎉 成功获取到建议本地发FBA量: {local_to_fba} 件")
                    else:
                        print("ℹ️ 当前没有本地发FBA建议")
                        
                else:
                    print(f"❌ API返回失败: {result.get('message', '未知错误')}")
                    
            else:
                print(f"❌ HTTP请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 FBA建议API测试完成")

def test_api_availability():
    """
    测试API服务可用性
    """
    print("🔍 检查API服务可用性...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/api/test-connection", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ API服务正常运行")
                return True
            else:
                print(f"⚠️ API服务异常: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ API服务不可用: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FBA建议API测试工具")
    print("测试目标: 验证'建议本地发FBA量（普通模式）'API接口")
    print()
    
    # 检查API服务可用性
    if test_api_availability():
        print()
        # 运行FBA建议API测试
        test_fba_suggestion_api()
    else:
        print("\n❌ API服务不可用，请确保Flask应用正在运行")
        print("启动命令: python app.py")
        sys.exit(1)
