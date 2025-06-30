#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查飞书机器人配置"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv('config/server.env')

print("🤖 飞书机器人配置检查")
print("="*50)

app_id = os.getenv('FEISHU_APP_ID', '未设置')
app_secret = os.getenv('FEISHU_APP_SECRET', '未设置')
verification_token = os.getenv('FEISHU_VERIFICATION_TOKEN', '未设置')
encrypt_key = os.getenv('FEISHU_ENCRYPT_KEY', '未设置')

print(f"📱 App ID: {app_id}")
print(f"🔑 App Secret: {app_secret[:10]}..." if app_secret != '未设置' else f"🔑 App Secret: {app_secret}")
print(f"🎫 Verification Token: {verification_token}")
print(f"🔐 Encrypt Key: {encrypt_key}")

print("\n✅ 配置状态:")
if app_id.startswith('cli_'):
    print("  ✅ App ID: 已配置")
else:
    print("  ❌ App ID: 需要配置")

if app_secret != 'your_feishu_app_secret' and app_secret != '未设置':
    print("  ✅ App Secret: 已配置")
else:
    print("  ❌ App Secret: 需要配置")

if verification_token != 'your_verification_token' and verification_token != '未设置':
    print("  ✅ Verification Token: 已配置")
else:
    print("  ⚠️ Verification Token: 需要配置")

if encrypt_key != 'your_encrypt_key' and encrypt_key != '未设置':
    print("  ✅ Encrypt Key: 已配置")
else:
    print("  ⚠️ Encrypt Key: 需要配置（可选）")

print("\n💡 接下来的步骤:")
if verification_token == 'your_verification_token':
    print("1. 在飞书开放平台找到 Verification Token")
    print("2. 更新 config/server.env 中的 FEISHU_VERIFICATION_TOKEN")
    print("3. 重新运行此脚本验证")
else:
    print("✅ 基本配置已完成！")
    print("🚀 可以尝试启动飞书机器人服务") 