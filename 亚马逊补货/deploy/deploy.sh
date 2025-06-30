#!/bin/bash
# 亚马逊补货工具服务器部署脚本

set -e

echo "🚀 开始部署亚马逊补货分析工具..."

# 检查Python版本
echo "📋 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python版本: $PYTHON_VERSION"

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source .venv/bin/activate

# 升级pip
echo "📦 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装项目依赖..."
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p output
mkdir -p data

# 检查配置文件
echo "⚙️ 检查配置文件..."
if [ ! -f "config/server.env" ]; then
    echo "⚠️ 未找到服务器配置文件 config/server.env"
    echo "📝 请编辑 config/server.env 来配置服务器设置"
else
    echo "✅ 服务器配置文件已存在"
fi

# 创建.env软链接
if [ ! -f ".env" ]; then
    echo "🔗 创建.env软链接..."
    ln -sf config/server.env .env
    echo "✅ .env软链接已创建"
fi

# 设置权限
echo "🔐 设置文件权限..."
chmod +x main.py
chmod 755 logs
chmod 755 output
chmod 755 data

# 测试运行
echo "🧪 测试程序运行..."
if python main.py --help &> /dev/null; then
    echo "✅ 程序测试运行成功"
else
    echo "⚠️ 程序测试运行失败，请检查配置"
fi

echo "🎉 部署完成！"
echo ""
echo "📝 下一步操作："
echo "1. 编辑 config/server.env 文件，配置服务器设置"
echo "2. 运行交互模式: python main.py --interactive"
echo "3. 运行服务器模式: python main.py --server"
echo "4. 检查环境: python main.py --check-env"
echo "5. 测试API连接: python main.py --test"
echo ""
echo "🌐 服务器将运行在: http://192.168.0.99:8000"
echo ""
echo "🔧 可选操作："
echo "- 设置为系统服务（systemd）"
echo "- 配置防火墙规则"
echo "- 设置定时任务"
echo ""
echo "📚 更多信息请查看 README.md"