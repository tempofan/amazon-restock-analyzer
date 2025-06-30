@echo off
chcp 65001 >nul
echo 🧹 项目清理工具
echo ===============================
echo.

echo 📂 当前目录: %CD%
echo.

echo 🐍 运行清理脚本...
python scripts\cleanup_project.py

echo.
echo ✅ 清理完成！
echo.
pause 