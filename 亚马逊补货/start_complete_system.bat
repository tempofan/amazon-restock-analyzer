@echo off
chcp 65001 >nul
echo 🚀 启动飞书机器人完整系统
echo ================================

echo.
echo 📋 系统架构:
echo 飞书 → 云服务器(175.178.183.96:8080) → 本地服务器(192.168.0.99:8000) → 领星API
echo.

echo 🔍 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)

echo.
echo 📦 检查依赖包...
python -c "import flask, flask_cors, flask_socketio, socketio, requests, openpyxl" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 缺少依赖包，正在安装...
    pip install flask flask-cors flask-socketio python-socketio requests openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple/
    if %errorlevel% neq 0 (
        echo ❌ 依赖包安装失败
        pause
        exit /b 1
    )
)

echo.
echo 🌐 测试云服务器连接...
python -c "import requests; r=requests.get('http://175.178.183.96:8080/health', timeout=5); print('✅ 云服务器连接正常' if r.status_code==200 else '❌ 云服务器连接失败')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 云服务器连接失败，请确保云代理服务已启动
    echo 💡 在云服务器上运行: python3 deploy/unified_cloud_proxy.py
    echo.
)

echo.
echo 🚀 启动系统组件...
echo.

echo 📝 创建启动脚本...

:: 创建本地服务器启动脚本
echo @echo off > start_local_server.bat
echo chcp 65001 ^>nul >> start_local_server.bat
echo title 飞书本地服务器 >> start_local_server.bat
echo echo 🏠 启动飞书本地服务器... >> start_local_server.bat
echo python main.py --feishu >> start_local_server.bat
echo pause >> start_local_server.bat

:: 创建反向代理客户端启动脚本
echo @echo off > start_reverse_client.bat
echo chcp 65001 ^>nul >> start_reverse_client.bat
echo title 反向代理客户端 >> start_reverse_client.bat
echo echo 🔌 启动反向代理客户端... >> start_reverse_client.bat
echo python deploy/local_reverse_client.py --cloud-server http://175.178.183.96:8080 --local-server http://192.168.0.99:8000 >> start_reverse_client.bat
echo pause >> start_reverse_client.bat

echo ✅ 启动脚本已创建
echo.

echo 🎯 请按以下顺序操作:
echo.
echo 1️⃣ 云服务器部署 (如果还未部署):
echo    - 上传 deploy/unified_cloud_proxy.py 到云服务器
echo    - 在云服务器运行: python3 unified_cloud_proxy.py --host 0.0.0.0 --port 8080
echo.
echo 2️⃣ 启动本地服务器:
echo    - 双击运行 start_local_server.bat
echo    - 或手动运行: python main.py --feishu
echo.
echo 3️⃣ 启动反向代理客户端:
echo    - 双击运行 start_reverse_client.bat
echo    - 或手动运行: python deploy/local_reverse_client.py
echo.
echo 4️⃣ 配置飞书机器人:
echo    - Webhook URL: http://175.178.183.96:8080/feishu/webhook
echo    - 应用ID: cli_a8d49f76d7fbd00b
echo    - 应用密钥: ivQKKw0UsCHC2spYjrssvb0Hx4AdLxE6
echo.
echo 5️⃣ 测试系统:
echo    - 在飞书中向机器人发送消息: "帮助"
echo    - 检查各个组件的日志输出
echo.

echo 📊 监控地址:
echo    - 云服务器状态: http://175.178.183.96:8080/stats
echo    - 云服务器健康: http://175.178.183.96:8080/health
echo    - 本地服务器状态: http://192.168.0.99:8000/api/status
echo.

echo 📁 日志文件位置:
echo    - 云服务器: unified_proxy.log
echo    - 本地客户端: local_reverse_client.log
echo    - 飞书服务: logs/lingxing_api.log
echo.

echo 🔧 故障排查:
echo    - 如果云服务器连接失败，检查防火墙和端口8080
echo    - 如果本地服务无响应，检查端口8000是否被占用
echo    - 如果WebSocket连接失败，检查网络连接和代理设置
echo.

echo 💡 现在可以选择:
echo    A - 自动启动本地服务器
echo    B - 自动启动反向代理客户端
echo    C - 运行完整测试
echo    D - 查看部署指南
echo    Q - 退出
echo.

:menu
set /p choice="请选择操作 (A/B/C/D/Q): "

if /i "%choice%"=="A" (
    echo 🏠 启动本地服务器...
    start "飞书本地服务器" start_local_server.bat
    goto menu
)

if /i "%choice%"=="B" (
    echo 🔌 启动反向代理客户端...
    start "反向代理客户端" start_reverse_client.bat
    goto menu
)

if /i "%choice%"=="C" (
    echo 🧪 运行完整测试...
    python deploy/deploy_complete_solution.py --test-only
    goto menu
)

if /i "%choice%"=="D" (
    echo 📋 查看部署指南...
    if exist deploy\DEPLOYMENT_GUIDE.md (
        notepad deploy\DEPLOYMENT_GUIDE.md
    ) else (
        echo 正在生成部署指南...
        python deploy/deploy_complete_solution.py
        if exist deploy\DEPLOYMENT_GUIDE.md (
            notepad deploy\DEPLOYMENT_GUIDE.md
        )
    )
    goto menu
)

if /i "%choice%"=="Q" (
    echo 👋 再见！
    goto end
)

echo ❌ 无效选择，请重新输入
goto menu

:end
echo.
echo 🎉 感谢使用飞书机器人系统！
echo 如有问题，请查看日志文件或联系技术支持。
echo.
pause
