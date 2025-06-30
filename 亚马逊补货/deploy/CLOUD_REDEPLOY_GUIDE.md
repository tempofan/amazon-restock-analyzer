# 🚀 云服务器重新部署指南

## 📋 问题背景

从测试结果可以看出：
- ✅ 云服务器收到54个飞书请求
- ❌ 53个请求失败
- ❌ 转发时数据丢失  
- ❌ 直接处理也超时

**根本原因**：云服务器上的代码存在严重缺陷，无法正确处理飞书请求。

## 🎯 解决方案

**完全重新部署云服务器**，使用新的、经过测试的代码替换现有的有缺陷代码。

## 🔧 部署方案特点

### ✅ 新架构优势
1. **直接处理** - 云服务器直接处理飞书请求，不再转发
2. **简化架构** - 减少网络传输环节，提高可靠性
3. **完整功能** - 支持所有飞书机器人命令
4. **健壮设计** - 完善的错误处理和日志记录
5. **易于维护** - 标准化的systemd服务管理

### 🏗️ 新架构流程
```
飞书开放平台 → 云服务器(直接处理) → 领星API
```

## 🚀 快速部署步骤

### 方法1: 自动化部署 (推荐)

在Windows本地执行：

```bash
# 1. 进入项目目录
cd 亚马逊补货

# 2. 执行自动化部署
python deploy/upload_and_redeploy.py
```

### 方法2: 手动部署

#### 步骤1: 上传文件到云服务器

```bash
# 上传新代码
scp deploy/cloud_server_redeploy.py ubuntu@175.178.183.96:/tmp/
scp deploy/redeploy_cloud_server.sh ubuntu@175.178.183.96:/tmp/
```

#### 步骤2: 在云服务器上执行部署

```bash
# 连接到云服务器
ssh ubuntu@175.178.183.96

# 执行部署脚本
cd /tmp
chmod +x redeploy_cloud_server.sh
sudo ./redeploy_cloud_server.sh
```

## ⚙️ 部署后配置

### 1. 配置飞书应用信息

在云服务器上编辑配置文件：

```bash
sudo nano /opt/feishu-cloud-server/.env
```

添加以下内容：

```env
# 飞书应用配置
FEISHU_APP_ID=cli_你的实际app_id
FEISHU_APP_SECRET=你的实际app_secret
FEISHU_VERIFICATION_TOKEN=你的实际verification_token

# 领星API配置（可选）
LINGXING_APP_ID=你的领星app_id
LINGXING_APP_SECRET=你的领星app_secret
```

### 2. 重启服务使配置生效

```bash
sudo systemctl restart feishu-cloud-server
```

### 3. 验证服务状态

```bash
# 检查服务状态
sudo systemctl status feishu-cloud-server

# 查看服务日志
sudo journalctl -u feishu-cloud-server -f

# 测试健康检查
curl http://localhost:8080/health
```

## 🔗 飞书开放平台配置

### 1. 更新Webhook URL

在飞书开放平台中，将事件订阅的请求URL更新为：

```
http://175.178.183.96:8080/feishu/webhook
```

### 2. 验证URL

点击"验证"按钮，确保显示"验证成功"。

### 3. 确认事件订阅

确保以下事件已添加：
- `im.message.receive_v1` - 接收消息
- `im.chat.member.bot.added_v1` - 机器人加入群聊

## 🧪 功能测试

### 1. 基础功能测试

```bash
# 测试健康检查
curl http://175.178.183.96:8080/health

# 测试统计信息
curl http://175.178.183.96:8080/stats

# 测试配置状态
curl http://175.178.183.96:8080/test
```

### 2. 飞书机器人测试

在飞书群聊中发送：

```
@机器人 帮助
@机器人 测试
@机器人 状态
```

## 📊 服务管理

### 常用命令

```bash
# 查看服务状态
sudo systemctl status feishu-cloud-server

# 启动服务
sudo systemctl start feishu-cloud-server

# 停止服务
sudo systemctl stop feishu-cloud-server

# 重启服务
sudo systemctl restart feishu-cloud-server

# 查看实时日志
sudo journalctl -u feishu-cloud-server -f

# 查看最近日志
sudo journalctl -u feishu-cloud-server -n 50
```

### 日志文件位置

- 系统日志: `journalctl -u feishu-cloud-server`
- 应用日志: `/var/log/feishu_cloud_server.log`

## 🔍 故障排除

### 1. 服务无法启动

```bash
# 查看详细错误信息
sudo journalctl -u feishu-cloud-server -n 20

# 检查配置文件
sudo cat /opt/feishu-cloud-server/.env

# 手动测试启动
cd /opt/feishu-cloud-server
sudo -u ubuntu python3 server.py
```

### 2. 飞书消息无响应

```bash
# 查看实时日志
sudo journalctl -u feishu-cloud-server -f

# 检查网络连接
curl -I http://175.178.183.96:8080/health

# 测试Webhook接口
curl -X POST http://175.178.183.96:8080/feishu/webhook \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test"}'
```

### 3. 配置问题

```bash
# 检查环境变量
sudo systemctl show feishu-cloud-server --property=Environment

# 验证配置文件格式
sudo cat /opt/feishu-cloud-server/.env | grep -v '^#' | grep '='
```

## 🎯 预期结果

部署成功后，应该实现：

1. ✅ 云服务器直接处理飞书请求
2. ✅ 飞书机器人正常响应用户消息
3. ✅ 支持所有基础命令（帮助、测试、状态等）
4. ✅ 完善的日志记录和错误处理
5. ✅ 稳定的服务运行

## 📞 技术支持

如果遇到问题：

1. **查看日志**: `sudo journalctl -u feishu-cloud-server -f`
2. **检查配置**: 确保 `.env` 文件配置正确
3. **网络测试**: 确保端口8080可访问
4. **重启服务**: `sudo systemctl restart feishu-cloud-server`

## 🎉 成功标志

当看到以下情况时，说明部署成功：

- ✅ 服务状态显示 `active (running)`
- ✅ 健康检查接口返回正常响应
- ✅ 飞书群聊中@机器人有响应
- ✅ 日志中显示正常处理消息

---

💡 **重要提醒**: 这个新的部署方案完全替换了原有的有缺陷代码，应该能够解决"53个请求失败"的问题。
