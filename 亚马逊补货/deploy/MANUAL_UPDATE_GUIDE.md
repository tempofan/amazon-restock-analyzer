# 🚀 云代理服务器手动更新指南

## 📊 当前问题状态

✅ **本地飞书服务器** - 已在 192.168.0.105:5000 正常运行  
❌ **云代理服务器** - 运行的是旧版本 v2.0，缺少飞书转发功能  
🎯 **目标** - 更新云代理服务器到最新版本，支持飞书webhook转发  

## 🔧 手动更新步骤

### 步骤1: 上传新版本文件

打开命令行，执行以下命令（需要输入SSH密码）：

```bash
# 上传云代理服务器文件
scp "deploy/cloud_proxy_server.py" ubuntu@175.178.183.96:~/

# 如果ubuntu用户不行，尝试root用户
# scp "deploy/cloud_proxy_server.py" root@175.178.183.96:~/
```

### 步骤2: SSH连接到云服务器

```bash
# 连接到云服务器
ssh ubuntu@175.178.183.96

# 如果ubuntu用户不行，尝试root用户
# ssh root@175.178.183.96
```

### 步骤3: 在云服务器上执行更新

连接成功后，在云服务器上执行：

```bash
# 1. 停止旧版本服务
pkill -f cloud_proxy_server.py
sleep 2

# 2. 备份旧版本（可选）
cp cloud_proxy_server.py cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "无旧版本需要备份"

# 3. 启动新版本
nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &
sleep 3

# 4. 检查服务状态
ps aux | grep cloud_proxy_server | grep -v grep

# 5. 测试健康检查
curl -s http://localhost:8080/health

# 6. 测试飞书功能
curl -X POST http://localhost:8080/feishu/webhook \
  -H 'Content-Type: application/json' \
  -d '{"type": "url_verification", "challenge": "test123"}'
```

### 步骤4: 退出SSH并验证

```bash
# 退出SSH连接
exit
```

然后在本地运行测试：

```bash
python test/test_cloud_proxy_feishu.py
```

## 🎯 预期结果

更新成功后，应该看到：

1. **健康检查** ✅ - 包含 `"service": "feishu-webhook"`
2. **URL验证转发** ✅ - 正确返回challenge
3. **消息转发** ✅ - 返回 `"status": "success"`
4. **命令转发** ✅ - 状态码200，有响应内容
5. **统计信息** ✅ - 包含 `feishu_requests` 字段

## 🚨 如果遇到问题

### 问题1: SSH连接失败
- 确认云服务器IP地址正确
- 尝试不同的用户名（ubuntu/root）
- 检查SSH密钥配置

### 问题2: 服务启动失败
```bash
# 检查Python3是否安装
python3 --version

# 检查端口是否被占用
netstat -tlnp | grep :8080

# 查看详细错误日志
cat proxy.log
```

### 问题3: 健康检查失败
```bash
# 检查服务进程
ps aux | grep python

# 检查端口监听
netstat -tlnp | grep :8080

# 重启服务
pkill -f cloud_proxy_server.py
nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &
```

## 📱 飞书测试

云代理更新完成后，在飞书群聊中测试：

1. 确保机器人已添加到群聊
2. 发送: `@补货助手 帮助`
3. 机器人应该立即回复命令帮助信息

## 🔍 验证命令

本地验证命令：

```powershell
# 检查健康状态
Invoke-WebRequest -Uri "http://175.178.183.96:8080/health" -Method GET | ConvertFrom-Json

# 测试URL验证
Invoke-WebRequest -Uri "http://175.178.183.96:8080/feishu/webhook" -Method POST -ContentType "application/json" -Body '{"type": "url_verification", "challenge": "test123"}' | ConvertFrom-Json

# 运行完整测试
python test/test_cloud_proxy_feishu.py
```

---

💡 **更新完成后，你的飞书机器人就能通过云代理正常工作了！** 🎉 