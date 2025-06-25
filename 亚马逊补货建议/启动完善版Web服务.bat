@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 亚马逊补货建议系统 - 完善版
echo ========================================
echo.

echo 📋 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境正常

echo.
echo 📦 检查依赖包...
python -c "import requests, flask, pycryptodome" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 缺少必要的依赖包，正在安装...
    echo.
    echo 安装Flask...
    pip install flask -i https://pypi.tuna.tsinghua.edu.cn/simple/
    echo.
    echo 安装Requests...
    pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple/
    echo.
    echo 安装加密库...
    pip install pycryptodome -i https://pypi.tuna.tsinghua.edu.cn/simple/
    echo.
    echo 安装BeautifulSoup4...
    pip install beautifulsoup4 -i https://pypi.tuna.tsinghua.edu.cn/simple/
) else (
    echo ✅ 依赖包已安装
)

echo.
echo 📁 创建必要目录...
if not exist "logs" mkdir logs
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
if not exist "static\images" mkdir static\images
if not exist "temp" mkdir temp
echo ✅ 目录创建完成

echo.
echo 🔧 配置检查...
python -c "from config import Config; print('✅ 配置文件正常')" 2>nul
if errorlevel 1 (
    echo ❌ 配置文件有问题
    pause
    exit /b 1
)

echo.
echo 🌐 启动Web服务...
echo 📍 访问地址: http://localhost:5000
echo 📍 本地网络: http://0.0.0.0:5000
echo.
echo ⚠️ 按 Ctrl+C 停止服务
echo ========================================
echo.

python app.py

echo.
echo 服务已停止
pause
