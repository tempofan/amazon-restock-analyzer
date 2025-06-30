@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 🚀 云服务器重新部署批处理脚本
:: 解决云服务器代码缺陷，重新部署完整的飞书机器人系统

echo.
echo 🚀 云服务器重新部署工具
echo ================================
echo.

:: 检查当前目录
if not exist "deploy" (
    echo ❌ 错误: 请在项目根目录下运行此脚本
    echo    当前目录应包含 deploy/ 文件夹
    echo.
    pause
    exit /b 1
)

:: 检查必要文件
echo 🔍 检查必要文件...
set "missing_files="

if not exist "deploy\cloud_server_redeploy.py" (
    set "missing_files=!missing_files! cloud_server_redeploy.py"
)

if not exist "deploy\redeploy_cloud_server.sh" (
    set "missing_files=!missing_files! redeploy_cloud_server.sh"
)

if not "!missing_files!"=="" (
    echo ❌ 缺少必要文件: !missing_files!
    echo.
    pause
    exit /b 1
)

echo ✅ 必要文件检查通过
echo.

:: 显示部署信息
echo 📋 部署信息:
echo    • 目标服务器: 175.178.183.96
echo    • 服务端口: 8080
echo    • 部署方式: 完全重新部署
echo    • 新架构: 云服务器直接处理飞书请求
echo.

:: 确认部署
echo ⚠️  警告: 此操作将完全替换云服务器上的现有代码
echo.
set /p "confirm=是否继续部署? (y/N): "
if /i not "!confirm!"=="y" (
    echo 🛑 部署已取消
    pause
    exit /b 0
)

echo.
echo 🚀 开始部署过程...
echo ================================
echo.

:: 方法选择
echo 📋 请选择部署方法:
echo    1. 自动化部署 (推荐)
echo    2. 手动上传文件
echo    3. 查看部署指南
echo.
set /p "method=请选择 (1-3): "

if "!method!"=="1" goto auto_deploy
if "!method!"=="2" goto manual_upload
if "!method!"=="3" goto show_guide

echo ❌ 无效选择
pause
exit /b 1

:auto_deploy
echo.
echo 🤖 执行自动化部署...
echo ================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    echo    请安装Python 3.6+
    pause
    exit /b 1
)

:: 检查requests模块
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 📦 安装requests模块...
    pip install requests
    if errorlevel 1 (
        echo ❌ 安装requests失败
        pause
        exit /b 1
    )
)

:: 执行自动化部署脚本
echo 🚀 启动自动化部署脚本...
echo.
python deploy\upload_and_redeploy.py

if errorlevel 1 (
    echo.
    echo ❌ 自动化部署失败
    echo 💡 建议尝试手动部署方法
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ 自动化部署完成
    goto deployment_success
)

:manual_upload
echo.
echo 📤 手动上传文件...
echo ================================
echo.

:: 检查SSH工具
ssh -V >nul 2>&1
if errorlevel 1 (
    echo ❌ SSH工具不可用
    echo    请安装Git Bash或OpenSSH
    echo    或者使用WinSCP等图形化工具手动上传
    echo.
    echo 📋 需要上传的文件:
    echo    • deploy\cloud_server_redeploy.py → /tmp/cloud_server_redeploy.py
    echo    • deploy\redeploy_cloud_server.sh → /tmp/redeploy_cloud_server.sh
    echo.
    echo 📋 上传后在服务器执行:
    echo    cd /tmp
    echo    chmod +x redeploy_cloud_server.sh
    echo    sudo ./redeploy_cloud_server.sh
    echo.
    pause
    exit /b 1
)

echo 📤 上传文件到云服务器...
echo.

:: 上传Python脚本
echo 上传服务器代码...
scp -o ConnectTimeout=30 deploy\cloud_server_redeploy.py ubuntu@175.178.183.96:/tmp/
if errorlevel 1 (
    echo ❌ 上传服务器代码失败
    goto upload_error
)
echo ✅ 服务器代码上传成功

:: 上传部署脚本
echo 上传部署脚本...
scp -o ConnectTimeout=30 deploy\redeploy_cloud_server.sh ubuntu@175.178.183.96:/tmp/
if errorlevel 1 (
    echo ❌ 上传部署脚本失败
    goto upload_error
)
echo ✅ 部署脚本上传成功

echo.
echo 📋 文件上传完成，现在需要在服务器上执行部署脚本
echo.
echo 🔧 请手动执行以下命令:
echo    ssh ubuntu@175.178.183.96
echo    cd /tmp
echo    chmod +x redeploy_cloud_server.sh
echo    sudo ./redeploy_cloud_server.sh
echo.

set /p "continue=是否现在连接到服务器执行部署? (y/N): "
if /i "!continue!"=="y" (
    echo.
    echo 🔗 连接到服务器...
    ssh -t ubuntu@175.178.183.96 "cd /tmp && chmod +x redeploy_cloud_server.sh && sudo ./redeploy_cloud_server.sh"
    
    if errorlevel 1 (
        echo ❌ 远程部署执行失败
        pause
        exit /b 1
    ) else (
        echo ✅ 远程部署执行完成
        goto deployment_success
    )
) else (
    echo 📋 请手动连接服务器执行部署脚本
    pause
    exit /b 0
)

:upload_error
echo.
echo ❌ 文件上传失败
echo 💡 可能的原因:
echo    • 网络连接问题
echo    • SSH密钥未配置
echo    • 服务器不可访问
echo.
echo 🔧 建议解决方案:
echo    1. 检查网络连接
echo    2. 配置SSH密钥认证
echo    3. 使用WinSCP等工具手动上传
echo.
pause
exit /b 1

:show_guide
echo.
echo 📖 部署指南
echo ================================
echo.
echo 📋 完整部署指南请查看:
echo    deploy\CLOUD_REDEPLOY_GUIDE.md
echo.
echo 🎯 快速步骤:
echo    1. 上传文件到云服务器 /tmp/ 目录
echo    2. 在服务器执行: sudo ./redeploy_cloud_server.sh
echo    3. 配置环境变量: /opt/feishu-cloud-server/.env
echo    4. 重启服务: sudo systemctl restart feishu-cloud-server
echo    5. 更新飞书Webhook URL
echo.
echo 🔗 新的Webhook URL:
echo    http://175.178.183.96:8080/feishu/webhook
echo.

if exist "deploy\CLOUD_REDEPLOY_GUIDE.md" (
    set /p "open_guide=是否打开详细指南? (y/N): "
    if /i "!open_guide!"=="y" (
        start notepad "deploy\CLOUD_REDEPLOY_GUIDE.md"
    )
)

pause
exit /b 0

:deployment_success
echo.
echo 🎉 云服务器重新部署完成！
echo ================================
echo.
echo 📋 服务信息:
echo    • 服务器地址: 175.178.183.96:8080
echo    • 健康检查: http://175.178.183.96:8080/health
echo    • 飞书Webhook: http://175.178.183.96:8080/feishu/webhook
echo    • 统计信息: http://175.178.183.96:8080/stats
echo.
echo ⚙️ 下一步操作:
echo    1. 配置飞书应用信息 (在服务器上编辑 .env 文件)
echo    2. 重启服务使配置生效
echo    3. 在飞书开放平台更新Webhook URL
echo    4. 测试飞书机器人功能
echo.
echo 🔗 飞书开放平台配置:
echo    Webhook URL: http://175.178.183.96:8080/feishu/webhook
echo.

:: 询问是否测试服务
set /p "test_service=是否现在测试服务状态? (y/N): "
if /i "!test_service!"=="y" (
    echo.
    echo 🧪 测试服务状态...
    
    :: 使用curl测试（如果可用）
    curl --version >nul 2>&1
    if not errorlevel 1 (
        echo 测试健康检查接口...
        curl -s http://175.178.183.96:8080/health
        echo.
    ) else (
        :: 使用PowerShell测试
        echo 测试健康检查接口...
        powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://175.178.183.96:8080/health' -TimeoutSec 10; Write-Host '✅ 服务响应正常'; Write-Host $response.Content } catch { Write-Host '❌ 服务无响应或异常' }"
    )
)

echo.
echo 🎯 重要提醒:
echo    • 新架构直接在云服务器处理飞书请求
echo    • 不再需要本地服务器转发
echo    • 应该能解决之前的"53个请求失败"问题
echo.
echo 📖 详细配置说明请查看: deploy\CLOUD_REDEPLOY_GUIDE.md
echo.
pause
exit /b 0
