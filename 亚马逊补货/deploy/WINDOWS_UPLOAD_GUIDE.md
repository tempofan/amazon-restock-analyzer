# 🪟 Windows用户云代理更新指南

## 🎯 快速操作步骤

### 方法1: 使用PowerShell脚本（推荐）

```powershell
# 在项目根目录执行
.\deploy\upload_to_cloud.ps1

# 如果用户名不是ubuntu，可以指定:
.\deploy\upload_to_cloud.ps1 -User "你的用户名"
```

### 方法2: 使用WinSCP等图形化工具

1. **下载安装WinSCP** (免费): https://winscp.net/
2. **连接云服务器**:
   - 主机名: `175.178.183.96`
   - 用户名: `ubuntu` (或你的实际用户名)
   - 端口: `22`
3. **上传文件**:
   - 上传 `deploy\cloud_proxy_server.py` 到 `~/`
   - 上传 `deploy\quick_deploy_cloud_proxy.sh` 到 `~/`

### 方法3: 使用WSL（Windows子系统）

```bash
# 打开WSL
wsl

# 进入项目目录
cd /mnt/d/华为家庭存储/Pythonproject/亚马逊补货

# 上传文件
scp deploy/cloud_proxy_server.py ubuntu@175.178.183.96:~/
scp deploy/quick_deploy_cloud_proxy.sh ubuntu@175.178.183.96:~/
```

## 🔄 云服务器操作

### SSH连接到云服务器

```bash
# 使用PowerShell、WSL或SSH客户端
ssh ubuntu@175.178.183.96
```

### 更新代理服务器

```bash
# 停止旧服务
sudo pkill -f cloud_proxy_server.py

# 备份旧版本（如果存在）
if [ -f cloud_proxy_server.py ]; then
    cp cloud_proxy_server.py cloud_proxy_server.py.backup.$(date +%Y%m%d_%H%M%S)
fi

# 启动新版本
nohup python3 cloud_proxy_server.py --host 0.0.0.0 --port 8080 > proxy.log 2>&1 &

# 等待启动
sleep 3

# 检查状态
ps aux | grep cloud_proxy_server
curl http://localhost:8080/health
```

## 🧪 验证更新成功

在Windows PowerShell中运行:

```powershell
python test\test_cloud_proxy_feishu.py
```

期待看到：
- ✅ 云代理健康检查通过
- ✅ 本地服务器直接测试通过  
- ✅ 云代理飞书webhook转发通过
- ✅ 飞书命令转发通过

## 🎉 测试飞书机器人

更新完成后，在飞书群聊中：

1. 确保机器人已添加到群聊
2. 发送: `@补货助手 帮助`
3. 机器人应该立即回复

## ⚠️ 常见问题

### 1. 没有scp命令
- **解决方案**: 使用WinSCP、FileZilla或开启WSL

### 2. SSH连接被拒绝
- **检查**: 用户名是否正确（ubuntu/root/其他）
- **检查**: SSH密钥或密码是否正确

### 3. 权限问题
- **解决方案**: 使用 `sudo` 执行命令
- **或者**: 切换到有权限的用户

### 4. 端口被占用
```bash
# 检查端口占用
sudo netstat -tlnp | grep :8080

# 强制停止占用进程
sudo fuser -k 8080/tcp
```

## 💡 提示

- 确保云服务器防火墙开放8080端口
- 如果是阿里云/腾讯云等，检查安全组设置
- 建议设置SSH密钥认证，避免密码输入 