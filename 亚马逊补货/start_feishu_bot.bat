@echo off
chcp 65001 >nul
echo ============================================
echo 🤖 启动亚马逊补货工具飞书机器人
echo ============================================
echo.

REM 检查虚拟环境
if not exist ".venv" (
    echo ❌ 虚拟环境不存在，请先运行 deploy\deploy.bat
    pause
    exit /b 1
)

echo ✅ 虚拟环境检查通过
echo.

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 检查Flask依赖
echo 🔍 检查Flask依赖...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Flask未安装，正在安装...
    pip install Flask>=2.3.0 psutil>=5.9.0 -i https://pypi.tuna.tsinghua.edu.cn/simple/
    if %errorlevel% neq 0 (
        echo ❌ Flask安装失败
        pause
        exit /b 1
    )
    echo ✅ Flask安装成功
)

REM 检查psutil依赖
python -c "import psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ psutil未安装，正在安装...
    pip install psutil>=5.9.0 -i https://pypi.tuna.tsinghua.edu.cn/simple/
    if %errorlevel% neq 0 (
        echo ❌ psutil安装失败
        pause
        exit /b 1
    )
    echo ✅ psutil安装成功
)

echo ✅ 依赖检查完成
echo.

REM 检查配置文件
echo 🔍 检查飞书配置...
if not exist "config\server.env" (
    echo ❌ 配置文件不存在: config\server.env
    echo 请先配置飞书机器人参数
    pause
    exit /b 1
)

REM 检查必要的配置项
findstr /C:"FEISHU_APP_ID" config\server.env >nul
if %errorlevel% neq 0 (
    echo ⚠️ 未找到FEISHU_APP_ID配置
    echo 请在config\server.env中配置飞书应用ID
)

findstr /C:"FEISHU_APP_SECRET" config\server.env >nul
if %errorlevel% neq 0 (
    echo ⚠️ 未找到FEISHU_APP_SECRET配置
    echo 请在config\server.env中配置飞书应用密钥
)

echo ✅ 配置文件检查完成
echo.

REM 检查服务器环境
echo 🔍 检查服务器环境...
python main.py --check-env
echo.

echo ============================================
echo 🚀 启动飞书机器人服务器
echo ============================================
echo.
echo 📍 服务地址: http://192.168.0.99:8000
echo 🔗 Webhook地址: http://192.168.0.99:8000/feishu/webhook
echo 💊 健康检查: http://192.168.0.99:8000/health
echo 📊 状态接口: http://192.168.0.99:8000/api/status
echo.
echo 💡 提示：
echo   - 确保在飞书开放平台配置了正确的Webhook地址
echo   - 机器人将监听端口8000的HTTP请求
echo   - 按Ctrl+C停止服务
echo.

REM 启动飞书机器人服务器
python main.py --feishu

echo.
echo �� 飞书机器人服务已停止
pause 