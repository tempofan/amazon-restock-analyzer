@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 亚马逊补货建议系统 - 系统测试
echo ========================================
echo.

echo 📋 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)

echo ✅ Python环境正常
echo.

echo 🔧 检查项目依赖...
python -c "import requests, flask, Crypto" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 缺少依赖包，正在安装...
    pip install flask requests pycryptodome beautifulsoup4 -i https://pypi.tuna.tsinghua.edu.cn/simple/
) else (
    echo ✅ 依赖包检查通过
)

echo.
echo 🚀 开始运行系统测试...
echo ========================================
echo.

python test_enhanced_system.py

echo.
echo ========================================
echo 📊 测试完成！
echo.
echo 💡 提示：
echo - 查看 test_report.json 获取详细测试报告
echo - 如果测试失败，请检查 logs/app.log 日志文件
echo - 确保网络连接正常，API凭据有效
echo.
pause
