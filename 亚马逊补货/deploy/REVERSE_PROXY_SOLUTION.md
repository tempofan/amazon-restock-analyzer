# 🔄 反向代理解决方案

## 📋 方案概述

针对本地公网IP不固定的问题，我们设计了一个**反向代理架构**：

- **传统方式**: 飞书 → 云服务器 → 本地服务器 (❌ 需要固定IP)
- **反向代理**: 本地客户端 ← WebSocket ← 云服务器 ← 飞书 (✅ 无需固定IP)

## 🏗️ 架构图

```
飞书平台
    ↓ HTTP POST
云代理服务器 (175.178.183.96:8080)
    ↓ WebSocket (8081端口)
反向代理客户端 (本地运行)
    ↓ HTTP转发
本地飞书服务器 (127.0.0.1:5000)
    ↓ HTTP代理
领星API (通过云代理)
```

## 🔧 解决方案优势

### ✅ **解决的问题**:
1. **公网IP不固定** - 本地主动连接云服务器
2. **NAT穿透** - 无需端口转发配置
3. **防火墙问题** - 只需要出站连接
4. **实时通信** - WebSocket保持长连接

### 🚀 **技术特性**:
- **自动重连** - 连接断开自动重新连接
- **请求排队** - 支持并发请求处理
- **错误恢复** - 完善的异常处理机制
- **状态监控** - 实时连接状态监控

## 📦 部署步骤

### 步骤1: 安装依赖

```bash
# 安装WebSocket支持
pip install websockets

# 如果已有requirements.txt，添加以下依赖：
echo "websockets>=10.0" >> requirements.txt
pip install -r requirements.txt
```

### 步骤2: 部署云服务器

```bash
# 1. 上传新的WebSocket支持的云代理服务器
scp "deploy/cloud_proxy_server_ws.py" ubuntu@175.178.183.96:~/

# 2. SSH连接到云服务器
ssh ubuntu@175.178.183.96

# 3. 停止旧服务
sudo systemctl stop lingxing-proxy

# 4. 备份并替换
sudo cp cloud_proxy_server_ws.py /opt/lingxing-proxy/cloud_proxy_server.py

# 5. 安装WebSocket依赖
cd /opt/lingxing-proxy
sudo ./venv/bin/pip install websockets

# 6. 重启服务
sudo systemctl start lingxing-proxy

# 7. 检查状态
sudo systemctl status lingxing-proxy
curl http://localhost:8080/health
```

### 步骤3: 启动本地反向代理

```bash
# 在本地项目目录运行
python deploy/reverse_proxy_solution.py
```

## 🧪 测试验证

### 1. 检查云服务器状态
```bash
curl http://175.178.183.96:8080/health
```

应该看到：
```json
{
  "service": "feishu-webhook-ws",
  "ws_port": 8081,
  "active_connections": 1
}
```

### 2. 测试WebSocket连接
```bash
# 检查反向代理客户端日志
# 应该看到 "✅ 成功连接到云服务器"
```

### 3. 测试飞书webhook转发
```bash
curl -X POST http://175.178.183.96:8080/feishu/webhook \
  -H 'Content-Type: application/json' \
  -d '{"type": "url_verification", "challenge": "test123"}'
```

### 4. 飞书群聊测试
在飞书群聊中发送: `@机器人 帮助`

## 🔍 故障排除

### 问题1: WebSocket连接失败
```bash
# 检查云服务器8081端口
netstat -tlnp | grep :8081

# 检查防火墙
sudo ufw status
sudo ufw allow 8081
```

### 问题2: 本地连接异常
```bash
# 检查本地网络连接
telnet 175.178.183.96 8081

# 检查本地飞书服务器
curl http://127.0.0.1:5000/health
```

### 问题3: 请求超时
- 检查本地飞书服务器是否正常运行
- 检查WebSocket连接是否稳定
- 查看云服务器和本地客户端日志

## 📊 监控和管理

### 云服务器监控
```bash
# 健康检查
curl http://175.178.183.96:8080/health

# 统计信息
curl http://175.178.183.96:8080/stats

# 查看日志
sudo journalctl -u lingxing-proxy -f
```

### 本地客户端管理
```bash
# 启动反向代理客户端
python deploy/reverse_proxy_solution.py

# 后台运行
nohup python deploy/reverse_proxy_solution.py > reverse_proxy.log 2>&1 &

# 检查运行状态
ps aux | grep reverse_proxy
```

## 🎯 预期结果

部署成功后，整个流程应该是：

1. **飞书用户** 在群聊中 @机器人
2. **飞书平台** 发送webhook到云服务器
3. **云服务器** 通过WebSocket转发给本地客户端
4. **本地客户端** 转发给本地飞书服务器
5. **本地服务器** 处理请求，调用领星API
6. **响应** 沿原路返回给用户

## 🔄 自动化脚本

创建自动启动脚本：

```bash
# Windows (start_reverse_proxy.bat)
@echo off
echo 🔄 启动反向代理客户端...
python deploy/reverse_proxy_solution.py
pause

# Linux (start_reverse_proxy.sh)
#!/bin/bash
echo "🔄 启动反向代理客户端..."
python3 deploy/reverse_proxy_solution.py
```

## 💡 优化建议

1. **多连接支持** - 可以启动多个反向代理客户端实现负载均衡
2. **健康检查** - 定期检查连接状态，自动重连
3. **日志轮转** - 配置日志文件大小限制和自动清理
4. **性能监控** - 监控请求延迟和成功率

---

💡 **这个方案完全解决了公网IP不固定的问题，让您可以在任何网络环境下使用飞书机器人！** 🎉 