@echo off
chcp 65001 >nul
echo ============================================
echo 🚀 亚马逊补货工具 Windows 服务安装程序
echo ============================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 需要管理员权限来安装Windows服务
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo ✅ 管理员权限检查通过
echo.

REM 检查Python环境
echo 🔍 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请安装Python 3.7+并添加到系统PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python版本: %PYTHON_VERSION%
echo.

REM 检查Windows服务依赖
echo 🔍 检查Windows服务依赖...
python -c "import win32serviceutil, win32service, win32event, servicemanager" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 缺少Windows服务依赖，正在安装...
    pip install pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple/
    if %errorlevel% neq 0 (
        echo ❌ 安装Windows服务依赖失败
        pause
        exit /b 1
    )
    echo ✅ Windows服务依赖安装成功
) else (
    echo ✅ Windows服务依赖已存在
)
echo.

REM 检查项目依赖
echo 🔍 检查项目依赖...
if not exist ".venv" (
    echo ⚠️ 虚拟环境不存在，请先运行 deploy.bat
    pause
    exit /b 1
)

echo ✅ 虚拟环境存在
echo.

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 安装Windows服务依赖到虚拟环境
echo 📦 安装Windows服务依赖到虚拟环境...
pip install pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple/
echo.

REM 停止可能存在的服务
echo 🛑 检查并停止已存在的服务...
sc query AmazonRestockService >nul 2>&1
if %errorlevel% equ 0 (
    echo 发现已存在的服务，正在停止...
    net stop AmazonRestockService >nul 2>&1
    python deploy\windows_service.py remove >nul 2>&1
    echo ✅ 已停止并卸载旧服务
)
echo.

REM 安装Windows服务
echo 🔧 安装Windows服务...
python deploy\windows_service.py install
if %errorlevel% neq 0 (
    echo ❌ Windows服务安装失败
    pause
    exit /b 1
)
echo.

REM 配置服务启动类型
echo ⚙️ 配置服务启动类型为自动启动...
sc config AmazonRestockService start= auto
echo.

REM 配置服务描述
sc description AmazonRestockService "亚马逊补货分析工具服务 - 运行在192.168.0.99:8000"
echo.

REM 启动服务
echo 🚀 启动Windows服务...
python deploy\windows_service.py start
if %errorlevel% neq 0 (
    echo ❌ 服务启动失败，请检查日志
) else (
    echo ✅ 服务启动成功！
)
echo.

REM 显示服务状态
echo 📋 服务状态信息：
sc query AmazonRestockService
echo.

REM 配置防火墙（可选）
echo 🔥 配置Windows防火墙规则（可选）...
netsh advfirewall firewall show rule name="Amazon Restock Tool" >nul 2>&1
if %errorlevel% neq 0 (
    echo 添加防火墙入站规则...
    netsh advfirewall firewall add rule name="Amazon Restock Tool" dir=in action=allow protocol=TCP localport=8000
    echo ✅ 防火墙规则添加成功
) else (
    echo ✅ 防火墙规则已存在
)
echo.

echo ============================================
echo 🎉 Windows服务安装完成！
echo ============================================
echo.
echo 📊 服务信息：
echo   服务名称: AmazonRestockService
echo   显示名称: Amazon Restock Analysis Service  
echo   服务地址: http://192.168.0.99:8000
echo   启动类型: 自动启动
echo.
echo 🔧 服务管理命令：
echo   启动服务: net start AmazonRestockService
echo   停止服务: net stop AmazonRestockService
echo   重启服务: net stop AmazonRestockService ^&^& net start AmazonRestockService
echo   卸载服务: python deploy\windows_service.py remove
echo.
echo 📝 管理工具：
echo   - 在"服务"管理器中查看 (services.msc)
echo   - 在事件查看器中查看日志
echo   - 检查项目logs目录中的日志文件
echo.
echo 🌐 访问地址: http://192.168.0.99:8000
echo.
echo ⚠️ 注意事项：
echo   1. 确保已正确配置 config\server.env 文件
echo   2. 确保网络端口8000未被其他程序占用
echo   3. 服务将在系统启动时自动启动
echo.
pause 