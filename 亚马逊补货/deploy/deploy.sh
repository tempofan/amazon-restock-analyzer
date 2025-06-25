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
if [ ! -f ".env" ]; then
    echo "⚠️ 未找到.env配置文件，请复制.env.example为.env并配置相关参数"
    cp .env.example .env
    echo "✅ 已创建.env模板文件，请编辑配置"
else
    echo "✅ 配置文件已存在"
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
echo "1. 编辑 .env 文件，配置API密钥"
echo "2. 运行: python main.py"
echo "3. 或者设置为系统服务（可选）"
echo ""
echo "📚 更多信息请查看 README.md"