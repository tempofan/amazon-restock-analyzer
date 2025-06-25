# 📦 部署文件夹说明

本文件夹包含亚马逊补货分析工具的所有部署相关文件，统一管理部署配置和脚本。

## 📁 文件结构

```
deploy/
├── README.md           # 本说明文件
├── DEPLOYMENT.md       # 详细部署指南
├── deploy.sh          # Linux/macOS 部署脚本
├── deploy.bat         # Windows 部署脚本
├── Dockerfile         # Docker 镜像构建文件
└── docker-compose.yml # Docker 编排配置文件
```

## 🚀 快速开始

### Windows 用户
```cmd
# 在项目根目录运行
deploy\deploy.bat
```

### Linux/macOS 用户
```bash
# 在项目根目录运行
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

### Docker 用户
```bash
# 进入部署目录
cd deploy

# 配置环境变量
cp ../.env.example ../.env
# 编辑 .env 文件配置API密钥

# 启动服务
docker-compose up -d
```

## 📋 部署前准备

1. **配置API密钥**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑配置文件，填入真实的API密钥
   # LINGXING_APP_ID=your_app_id
   # LINGXING_APP_SECRET=your_app_secret
   ```

2. **检查系统要求**
   - Python 3.7+
   - Git
   - 网络连接（访问领星ERP API）

## 🔧 部署方式选择

| 部署方式 | 适用场景 | 文件 |
|---------|---------|------|
| **自动脚本** | 快速部署、开发环境 | `deploy.sh` / `deploy.bat` |
| **Docker** | 生产环境、容器化 | `Dockerfile` + `docker-compose.yml` |
| **手动部署** | 自定义配置、学习 | 参考 `DEPLOYMENT.md` |

## 📖 详细文档

- **完整部署指南**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **项目说明**: [../README.md](../README.md)
- **API文档**: [../api_doc/](../api_doc/)

## 🛠️ 常用命令

### 传统部署
```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate.bat  # Windows

# 运行程序
python main.py
```

### Docker 部署
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

## ⚠️ 注意事项

1. **安全性**
   - 不要将 `.env` 文件提交到版本控制
   - 定期更新API密钥
   - 在生产环境中使用HTTPS

2. **性能**
   - 根据数据量调整内存配置
   - 监控API调用频率
   - 定期清理日志文件

3. **维护**
   - 定期备份数据
   - 监控服务运行状态
   - 及时更新依赖包

## 🆘 故障排除

如果遇到部署问题，请按以下顺序检查：

1. 检查Python版本和依赖
2. 验证API密钥配置
3. 查看错误日志
4. 参考 [DEPLOYMENT.md](./DEPLOYMENT.md) 故障排除部分

## 📞 技术支持

- 📧 邮箱: support@example.com
- 🐛 问题反馈: GitHub Issues
- 📚 文档: [DEPLOYMENT.md](./DEPLOYMENT.md)