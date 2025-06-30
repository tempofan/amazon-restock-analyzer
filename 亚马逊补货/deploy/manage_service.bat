@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:MAIN_MENU
cls
echo ============================================
echo 🔧 亚马逊补货工具 Windows 服务管理器
echo ============================================
echo.
echo 请选择操作：
echo.
echo 1. 查看服务状态
echo 2. 启动服务
echo 3. 停止服务  
echo 4. 重启服务
echo 5. 查看服务日志
echo 6. 测试API连接
echo 7. 检查服务器环境
echo 8. 打开服务管理器
echo 9. 打开事件查看器
echo 0. 退出
echo.
set /p CHOICE="请输入选择 (0-9): "

if "%CHOICE%"=="1" goto STATUS
if "%CHOICE%"=="2" goto START
if "%CHOICE%"=="3" goto STOP
if "%CHOICE%"=="4" goto RESTART
if "%CHOICE%"=="5" goto LOGS
if "%CHOICE%"=="6" goto TEST_API
if "%CHOICE%"=="7" goto CHECK_ENV
if "%CHOICE%"=="8" goto OPEN_SERVICES
if "%CHOICE%"=="9" goto OPEN_EVENTS
if "%CHOICE%"=="0" goto EXIT
goto INVALID_CHOICE

:STATUS
echo.
echo 📋 查看服务状态...
echo ============================================
sc query AmazonRestockService 2>nul
if %errorlevel% neq 0 (
    echo ❌ 服务未安装或已被删除
    echo.
    echo 💡 如需安装服务，请运行 install_windows_service.bat
) else (
    echo.
    echo 📊 详细信息：
    sc qc AmazonRestockService 2>nul
)
echo.
pause
goto MAIN_MENU

:START
echo.
echo 🚀 启动服务...
net start AmazonRestockService
if %errorlevel% equ 0 (
    echo ✅ 服务启动成功！
    echo 🌐 服务地址: http://192.168.0.99:8000
) else (
    echo ❌ 服务启动失败
    echo 💡 请检查日志文件或运行诊断
)
echo.
pause
goto MAIN_MENU

:STOP
echo.
echo 🛑 停止服务...
net stop AmazonRestockService
if %errorlevel% equ 0 (
    echo ✅ 服务停止成功！
) else (
    echo ❌ 服务停止失败或服务未运行
)
echo.
pause
goto MAIN_MENU

:RESTART
echo.
echo 🔄 重启服务...
echo 正在停止服务...
net stop AmazonRestockService >nul 2>&1
echo 等待服务完全停止...
timeout /t 3 /nobreak >nul
echo 正在启动服务...
net start AmazonRestockService
if %errorlevel% equ 0 (
    echo ✅ 服务重启成功！
    echo 🌐 服务地址: http://192.168.0.99:8000
) else (
    echo ❌ 服务重启失败
)
echo.
pause
goto MAIN_MENU

:LOGS
echo.
echo 📄 查看服务日志...
echo ============================================
echo.
echo 🔍 最近的应用日志 (logs\lingxing_api.log):
if exist "logs\lingxing_api.log" (
    echo.
    powershell "Get-Content 'logs\lingxing_api.log' -Tail 20"
) else (
    echo ⚠️ 日志文件不存在
)
echo.
echo ============================================
echo.
pause
goto MAIN_MENU

:TEST_API
echo.
echo 🧪 测试API连接...
echo ============================================
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
python main.py --test
echo.
pause
goto MAIN_MENU

:CHECK_ENV
echo.
echo 🔍 检查服务器环境...
echo ============================================
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
python main.py --check-env
echo.
pause
goto MAIN_MENU

:OPEN_SERVICES
echo.
echo 🔧 打开Windows服务管理器...
start services.msc
goto MAIN_MENU

:OPEN_EVENTS
echo.
echo 📊 打开Windows事件查看器...
start eventvwr.msc
goto MAIN_MENU

:INVALID_CHOICE
echo.
echo ❌ 无效选择，请重新输入
timeout /t 2 /nobreak >nul
goto MAIN_MENU

:EXIT
echo.
echo 👋 感谢使用亚马逊补货工具服务管理器！
echo.
exit /b 0 