# 🚀 亚马逊补货工具部署指南

本文档详细介绍如何将亚马逊补货分析工具部署到服务器上。

## 📋 部署前准备

### 系统要求
- **操作系统**: Linux (Ubuntu 18.04+), Windows Server 2016+, macOS 10.14+
- **Python版本**: 3.7+
- **内存**: 最少 512MB，推荐 1GB+
- **存储**: 最少 1GB 可用空间
- **网络**: 需要访问领星ERP API

### 必需的配置信息
- 领星ERP API密钥 (APP_ID 和 APP_SECRET)
- 服务器访问权限
- Git仓库访问权限

## 🔧 部署方式选择

### 方式一：传统部署 (推荐新手)
适合：小型项目、学习环境、简单部署需求

### 方式二：Docker部署 (推荐生产)
适合：生产环境、容器化部署、微服务架构

### 方式三：云服务部署
适合：云原生应用、自动扩缩容需求

---

## 📦 方式一：传统部署

### 1. 服务器环境准备

#### Ubuntu/Debian系统
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装Python和必要工具
sudo apt install python3 python3-pip python3-venv git curl -y

# 安装系统依赖
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y
```

#### CentOS/RHEL系统
```bash
# 更新系统包
sudo yum update -y

# 安装Python和必要工具
sudo yum install python3 python3-pip git curl -y

# 安装开发工具
sudo yum groupinstall "Development Tools" -y
```

### 2. 克隆项目
```bash
# 克隆项目到服务器
git clone https://github.com/yourusername/amazon-restock-tool.git
cd amazon-restock-tool

# 或者从私有仓库克隆
git clone https://your-git-server.com/amazon-restock-tool.git
cd amazon-restock-tool
```

### 3. 自动部署
```bash
# Linux系统
chmod +x deploy/deploy.sh
./deploy/deploy.sh

# Windows系统
deploy\deploy.bat
```

### 4. 手动配置
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或者 .venv\Scripts\activate.bat  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置文件
```

### 5. 配置系统服务 (Linux)
```bash
# 创建systemd服务文件
sudo nano /etc/systemd/system/amazon-restock.service
```

服务文件内容：
```ini
[Unit]
Description=Amazon Restock Analysis Tool
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/amazon-restock-tool
Environment=PATH=/home/ubuntu/amazon-restock-tool/.venv/bin
ExecStart=/home/ubuntu/amazon-restock-tool/.venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable amazon-restock
sudo systemctl start amazon-restock

# 查看服务状态
sudo systemctl status amazon-restock
```

---

## 🐳 方式二：Docker部署

### 1. 安装Docker

#### Ubuntu系统
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 将用户添加到docker组
sudo usermod -aG docker $USER
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

### 3. 构建和运行
```bash
# 进入部署目录
cd deploy

# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. Docker命令参考
```bash
# 查看运行状态
docker-compose ps

# 进入容器
docker-compose exec amazon-restock bash

# 重启服务
docker-compose restart

# 更新服务
git pull
docker-compose build
docker-compose up -d
```

---

## ☁️ 方式三：云服务部署

### AWS部署
1. 创建EC2实例
2. 配置安全组（开放必要端口）
3. 使用方式一或方式二进行部署

### 阿里云部署
1. 创建ECS实例
2. 配置安全组规则
3. 使用方式一或方式二进行部署

### 腾讯云部署
1. 创建CVM实例
2. 配置安全组
3. 使用方式一或方式二进行部署

---

## 🔐 安全配置

### 1. 防火墙配置
```bash
# Ubuntu UFW
sudo ufw allow ssh
sudo ufw allow 8000  # 如果有Web服务
sudo ufw enable

# CentOS firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### 2. SSL证书配置
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取SSL证书
sudo certbot --nginx -d your-domain.com
```

### 3. 环境变量安全
- 不要在代码中硬编码敏感信息
- 使用 `.env` 文件管理配置
- 确保 `.env` 文件不被提交到Git

---

## 📊 监控和维护

### 1. 日志管理
```bash
# 查看应用日志
tail -f logs/lingxing_api.log

# 查看系统服务日志
sudo journalctl -u amazon-restock -f

# Docker日志
cd deploy && docker-compose logs -f amazon-restock
```

### 2. 性能监控
```bash
# 系统资源监控
htop
df -h
free -h

# Docker资源监控
docker stats
```

### 3. 定时任务
```bash
# 编辑crontab
crontab -e

# 每天凌晨2点运行数据分析
0 2 * * * /home/ubuntu/amazon-restock-tool/.venv/bin/python /home/ubuntu/amazon-restock-tool/main.py --auto
```

### 4. 备份策略
```bash
# 数据备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_$DATE.tar.gz data/ output/ logs/
```

---

## 🔧 故障排除

### 常见问题

1. **Python版本不兼容**
   ```bash
   python3 --version  # 检查版本
   ```

2. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --verbose
   ```

3. **API连接失败**
   - 检查网络连接
   - 验证API密钥
   - 查看防火墙设置

4. **权限问题**
   ```bash
   sudo chown -R $USER:$USER /path/to/project
   chmod +x deploy/deploy.sh
   ```

5. **Docker问题**
   ```bash
   docker system prune  # 清理Docker缓存
   cd deploy && docker-compose down && docker-compose up --build
   ```

### 日志分析
```bash
# 查看错误日志
grep -i error logs/lingxing_api.log

# 查看最近的日志
tail -n 100 logs/lingxing_api.log
```

---

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查项目的 GitHub Issues
3. 查看应用日志文件
4. 联系技术支持团队

---

## 📝 更新日志

- v1.0.0: 初始版本，支持基础部署
- v1.1.0: 添加Docker支持
- v1.2.0: 添加云服务部署指南
- v1.3.0: 重构部署文件结构，统一管理

---

**注意**: 请根据实际情况调整配置参数，确保在生产环境中的安全性和稳定性。