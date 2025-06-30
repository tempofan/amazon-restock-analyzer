@echo off
chcp 65001 >nul
title 亚马逊补货工具 - 云代理模式

echo 🌐 启动亚马逊补货工具（云代理模式）
echo ==========================================

:: 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先运行部署脚本
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔧 激活Python虚拟环境...
call .venv\Scripts\activate.bat

:: 检查代理配置
echo 🔍 检查代理配置...
python -c "
from config.proxy_config import ProxyConfig
is_valid, msg = ProxyConfig.validate_config()
print(f'代理配置: {msg}')
if ProxyConfig.is_proxy_enabled():
    print(f'代理地址: {ProxyConfig.get_proxy_base_url()}')
    print(f'健康检查: {ProxyConfig.get_health_check_url()}')
else:
    print('代理模式未启用')
exit(0 if is_valid else 1)
"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 代理配置有误，请检查 config/server.env 文件
    echo.
    echo 📋 需要配置以下环境变量：
    echo    ENABLE_PROXY=True
    echo    PROXY_HOST=你的云服务器IP
    echo    PROXY_PORT=8080
    echo    PROXY_PROTOCOL=http
    echo.
    pause
    exit /b 1
)

:: 运行代理测试
echo.
echo 🧪 测试代理连接...
python utils/proxy_tester.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 代理连接测试失败！
    echo.
    echo 📝 请检查：
    echo    1. 云代理服务器是否正常运行
    echo    2. 网络连接是否正常
    echo    3. 防火墙端口是否开放
    echo    4. 代理配置是否正确
    echo.
    choice /c YN /m "是否继续启动项目"
    if !errorlevel! equ 2 (
        pause
        exit /b 1
    )
)

echo.
echo ✅ 代理测试通过！
echo.

:: 显示启动选项
echo 🚀 选择启动模式：
echo.
echo 1. 交互式模式（推荐）
echo 2. 飞书机器人模式
echo 3. 测试API连接
echo 4. 查看店铺列表
echo 5. 获取补货数据
echo 6. 查看代理状态
echo 0. 退出
echo.

set /p choice=请选择启动模式 [1-6]: 

if "%choice%"=="1" (
    echo 🎯 启动交互式模式...
    python main.py --interactive
) else if "%choice%"=="2" (
    echo 🤖 启动飞书机器人模式...
    python main.py --feishu
) else if "%choice%"=="3" (
    echo 🔗 测试API连接...
    python main.py --test
) else if "%choice%"=="4" (
    echo 🏪 获取店铺列表...
    python main.py --sellers
) else if "%choice%"=="5" (
    echo 📦 获取补货数据...
    python main.py --restock
) else if "%choice%"=="6" (
    echo 📊 查看代理状态...
    python -c "
from utils.proxy_tester import ProxyTester
import json
tester = ProxyTester()
results = tester.run_full_test()
"
) else if "%choice%"=="0" (
    echo 👋 退出程序
    exit /b 0
) else (
    echo ❌ 无效选择，启动交互式模式...
    python main.py --interactive
)

echo.
echo ✅ 程序执行完成
pause 
 