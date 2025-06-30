@echo off
chcp 65001 >nul
echo ============================================
echo 🗑️ 亚马逊补货工具 Windows 服务卸载程序
echo ============================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 需要管理员权限来卸载Windows服务
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo ✅ 管理员权限检查通过
echo.

REM 检查服务是否存在
echo 🔍 检查服务状态...
sc query AmazonRestockService >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 服务不存在或已被卸载
    echo.
    goto CLEANUP
)

echo ✅ 发现已安装的服务
echo.

REM 显示当前服务状态
echo 📋 当前服务状态：
sc query AmazonRestockService
echo.

REM 停止服务
echo 🛑 停止服务...
net stop AmazonRestockService >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 服务已停止
) else (
    echo ⚠️ 服务可能已经停止或停止失败
)
echo.

REM 等待服务完全停止
echo ⏳ 等待服务完全停止...
timeout /t 3 /nobreak >nul
echo.

REM 激活虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo 🔄 激活虚拟环境...
    call .venv\Scripts\activate.bat
)

REM 卸载服务
echo 🗑️ 卸载Windows服务...
python deploy\windows_service.py remove
if %errorlevel% equ 0 (
    echo ✅ 服务卸载成功
) else (
    echo ❌ 服务卸载失败
    echo 尝试使用系统命令强制删除...
    sc delete AmazonRestockService
)
echo.

:CLEANUP
REM 清理防火墙规则（可选）
echo 🔥 清理防火墙规则...
netsh advfirewall firewall show rule name="Amazon Restock Tool" >nul 2>&1
if %errorlevel% equ 0 (
    echo 删除防火墙规则...
    netsh advfirewall firewall delete rule name="Amazon Restock Tool"
    echo ✅ 防火墙规则已删除
) else (
    echo ✅ 防火墙规则不存在或已删除
)
echo.

REM 询问是否清理数据
echo 📁 数据清理选项：
echo.
set /p CLEAN_DATA="是否删除应用数据？(logs, output, data目录) [y/N]: "
if /i "%CLEAN_DATA%"=="y" (
    echo 🧹 清理应用数据...
    if exist "logs" (
        rmdir /s /q "logs" >nul 2>&1
        echo   - 已删除 logs 目录
    )
    if exist "output" (
        rmdir /s /q "output" >nul 2>&1
        echo   - 已删除 output 目录
    )
    if exist "data" (
        rmdir /s /q "data" >nul 2>&1
        echo   - 已删除 data 目录
    )
    echo ✅ 应用数据清理完成
) else (
    echo ✅ 保留应用数据
)
echo.

REM 询问是否删除虚拟环境
set /p CLEAN_VENV="是否删除虚拟环境？(.venv目录) [y/N]: "
if /i "%CLEAN_VENV%"=="y" (
    echo 🧹 删除虚拟环境...
    if exist ".venv" (
        rmdir /s /q ".venv" >nul 2>&1
        echo ✅ 虚拟环境已删除
    )
) else (
    echo ✅ 保留虚拟环境
)
echo.

echo ============================================
echo 🎉 Windows服务卸载完成！
echo ============================================
echo.
echo 📊 卸载总结：
echo   - Windows服务已卸载
echo   - 防火墙规则已清理
if /i "%CLEAN_DATA%"=="y" (
    echo   - 应用数据已清理
) else (
    echo   - 应用数据已保留
)
if /i "%CLEAN_VENV%"=="y" (
    echo   - 虚拟环境已删除
) else (
    echo   - 虚拟环境已保留
)
echo.
echo 💡 提示：
echo   - 配置文件 config\server.env 已保留
echo   - 如需完全卸载，请手动删除整个项目目录
echo.
pause 