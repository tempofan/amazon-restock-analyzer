# 🧪 测试工具目录

本目录包含了项目的各种测试和诊断工具，用于验证系统功能和排查问题。

## 📋 文件分类

### 🔍 环境检查工具
- **`check_env.py`** - 检查环境变量加载情况
- **`check_public_ip.py`** - 检查当前公网IP地址
- **`check_feishu_config.py`** - 检查飞书配置是否正确

### 🌐 网络诊断工具
- **`network_diagnostic.py`** - 完整的网络连接诊断工具
- **`network_environment_test.py`** - 网络环境测试
- **`proxy_connection_diagnostic.py`** - 代理连接诊断工具
- **`root_cause_analysis.py`** - 根本原因分析工具

### 🤖 飞书机器人测试工具
- **`feishu_bot_diagnostic.py`** - 飞书机器人完整诊断工具
- **`diagnose_feishu_config.py`** - 飞书配置诊断
- **`quick_feishu_diagnostic.py`** - 快速飞书诊断
- **`test_feishu_permissions.py`** - 测试飞书权限配置
- **`test_feishu_webhook.py`** - 测试飞书Webhook功能

## 🚀 使用方法

### 环境检查
```bash
# 检查环境变量配置
python test/check_env.py

# 检查飞书配置
python test/check_feishu_config.py

# 检查公网IP
python test/check_public_ip.py
```

### 网络诊断
```bash
# 完整网络诊断
python test/network_diagnostic.py

# 代理连接诊断
python test/proxy_connection_diagnostic.py

# 根本原因分析
python test/root_cause_analysis.py
```

### 飞书功能测试
```bash
# 飞书机器人完整诊断
python test/feishu_bot_diagnostic.py

# 快速飞书诊断
python test/quick_feishu_diagnostic.py

# 测试飞书权限
python test/test_feishu_permissions.py

# 测试Webhook功能
python test/test_feishu_webhook.py
```

## 📊 诊断流程建议

1. **首次部署时**：
   ```bash
   python test/check_env.py
   python test/network_diagnostic.py
   python test/feishu_bot_diagnostic.py
   ```

2. **遇到网络问题时**：
   ```bash
   python test/network_diagnostic.py
   python test/proxy_connection_diagnostic.py
   python test/root_cause_analysis.py
   ```

3. **飞书功能异常时**：
   ```bash
   python test/check_feishu_config.py
   python test/quick_feishu_diagnostic.py
   python test/test_feishu_webhook.py
   ```

## 💡 提示

- 所有诊断工具都会生成详细的日志和报告
- 运行前请确保项目配置文件已正确设置
- 如果遇到权限问题，请检查API密钥和权限配置
- 网络诊断工具可能需要一定时间来完成检测

## 🔧 维护说明

- 定期运行诊断工具确保系统正常
- 新增功能时应添加相应的测试文件
- 测试文件应包含详细的注释和使用说明 