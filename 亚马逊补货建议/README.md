# 🚀 亚马逊补货建议系统 - 完善版

基于领星ERP API的智能补货建议系统，提供实时的库存分析和补货建议。

## 📋 项目概述

本系统通过集成领星ERP API，实时获取亚马逊店铺的库存、销售和补货数据，为卖家提供智能化的补货建议和数据分析。

### 🎯 主要功能

- **实时数据同步** - 与领星ERP API实时同步店铺和产品数据
- **智能补货建议** - 基于销售趋势和库存状况提供补货建议
- **多维度分析** - 库存状态、紧急程度、销售趋势等多角度分析
- **可视化仪表板** - 直观的图表和数据展示
- **多店铺支持** - 支持管理多个亚马逊店铺
- **导出功能** - 支持数据导出和报告生成

## 🏗️ 系统架构

```
亚马逊补货建议系统/
├── api/                    # API模块
│   ├── lingxing_api_new.py       # 领星API客户端（新版）
│   ├── data_processor_real.py    # 真实数据处理器
│   └── mock_data.py              # 模拟数据生成器
├── templates/              # Web模板
│   ├── index.html               # 主页仪表板
│   ├── replenishment_list.html  # 补货建议列表
│   └── analytics.html           # 数据分析页面
├── static/                 # 静态资源
├── utils/                  # 工具模块
├── config.py              # 配置文件
├── app.py                 # 主应用文件
└── test_enhanced_system.py # 系统测试脚本
```

## 🔧 安装和配置

### 1. 环境要求

- Python 3.8+
- Windows 11 (推荐)

### 2. 依赖安装

```bash
pip install flask requests pycryptodome beautifulsoup4 -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 3. 配置API凭据

在 `config.py` 中配置您的领星ERP API凭据：

```python
LINGXING_API_CONFIG = {
    'base_url': 'https://openapi.lingxing.com',
    'app_id': 'your_app_id',
    'app_secret': 'your_app_secret',
    'timeout': 30,
    'retry_times': 3,
    'retry_delay': 1
}
```

## 🚀 快速启动

### 方法一：使用启动脚本（推荐）

双击运行 `启动完善版Web服务.bat`

### 方法二：命令行启动

```bash
python app.py
```

### 访问系统

- 本地访问：http://localhost:5000
- 网络访问：http://0.0.0.0:5000

## 📊 功能详解

### 1. 仪表板概览

- **关键指标展示** - 紧急补货数量、高优先级商品、总产品数等
- **库存状态分布** - 饼图展示不同库存状态的商品分布
- **紧急程度分析** - 柱状图显示不同紧急程度的商品数量
- **紧急补货清单** - 表格展示最需要补货的商品

### 2. 补货建议列表

- **详细商品信息** - ASIN、MSKU、店铺、库存状态等
- **销售数据分析** - 3/7/14/30/60/90天销售趋势
- **库存信息** - FBA库存、本地库存、海外库存等
- **补货建议** - 具体的补货数量和时间建议

### 3. 数据分析

- **销售趋势分析** - 时间序列图表展示销售趋势
- **库存周转分析** - 库存周转率和可售天数分析
- **补货效果评估** - 补货建议的执行效果分析

## 🔌 API接口

### 认证相关

- `POST /api/auth-server/oauth/access-token` - 获取访问令牌
- `POST /api/auth-server/oauth/refresh` - 刷新令牌

### 数据获取

- `GET /erp/sc/data/seller/lists` - 获取店铺列表
- `POST /erp/sc/routing/restocking/analysis/getSummaryList` - 获取补货建议

### Web API

- `GET /api/replenishment-data` - 获取补货数据
- `GET /api/shop-list` - 获取店铺列表
- `GET /api/test-connection` - 测试API连接

## 🧪 测试

运行系统测试：

```bash
python test_enhanced_system.py
```

测试包括：
- API认证测试
- 连接测试
- 店铺列表获取测试
- 补货建议获取测试
- 数据处理测试

## 📈 数据处理流程

1. **数据获取** - 通过领星API获取原始数据
2. **数据清洗** - 处理空值、格式转换等
3. **字段映射** - 将API字段映射到系统字段
4. **衍生计算** - 计算可售天数、紧急程度等
5. **状态判断** - 确定库存状态和优先级
6. **建议生成** - 生成具体的补货建议

## 🔐 安全特性

- **签名验证** - 使用MD5+AES加密确保API安全
- **Token管理** - 自动管理访问令牌的获取和刷新
- **错误处理** - 完善的异常处理和重试机制
- **日志记录** - 详细的操作日志记录

## 📝 配置说明

### API配置

```python
LINGXING_API_CONFIG = {
    'base_url': 'https://openapi.lingxing.com',  # API基础URL
    'app_id': 'your_app_id',                     # 应用ID
    'app_secret': 'your_app_secret',             # 应用密钥
    'timeout': 30,                               # 请求超时时间
    'retry_times': 3,                            # 重试次数
    'retry_delay': 1                             # 重试延迟
}
```

### 数据处理配置

```python
DATA_PROCESSING_CONFIG = {
    'max_page_size': 100,        # 最大页面大小
    'default_page_size': 20,     # 默认页面大小
    'cache_timeout': 300,        # 缓存超时时间
    'batch_size': 50             # 批处理大小
}
```

## 🚨 故障排除

### 常见问题

1. **认证失败**
   - 检查APP ID和APP Secret是否正确
   - 确认API凭据是否有效

2. **连接超时**
   - 检查网络连接
   - 调整timeout配置

3. **数据为空**
   - 确认店铺是否有数据
   - 检查API权限设置

### 日志查看

系统日志保存在 `logs/app.log` 文件中，可以查看详细的运行信息和错误记录。

## 📞 技术支持

如有问题，请查看：
1. 系统日志文件
2. 测试报告 `test_report.json`
3. API文档分析结果

## 🎉 更新日志

### v2.0.0 (完善版)
- ✅ 集成真实的领星ERP API
- ✅ 实现正确的认证和签名机制
- ✅ 完善数据处理和分析功能
- ✅ 优化Web界面和用户体验
- ✅ 添加完整的测试套件
- ✅ 支持多店铺管理
- ✅ 实时数据同步

### v1.0.0 (初始版)
- 基础框架搭建
- 模拟数据展示
- 基本Web界面

---

🎯 **系统已完善并通过所有测试，可以正常使用！**
