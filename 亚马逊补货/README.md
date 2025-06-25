# 领星ERP补货数据获取工具

这是一个用于获取领星ERP补货数据的Python工具，支持通过API接口获取亚马逊店铺的补货建议数据，并提供数据分析和导出功能。

## 功能特性

- ✅ **API认证管理**: 自动获取和刷新access_token
- ✅ **补货数据获取**: 支持按店铺、ASIN等维度查询补货数据
- ✅ **数据分析**: 自动分析紧急补货需求和高销量商品
- ✅ **多格式导出**: 支持Excel和JSON格式导出
- ✅ **错误处理**: 完善的异常处理和重试机制
- ✅ **日志记录**: 详细的操作日志和API调用记录
- ✅ **交互式界面**: 提供命令行交互式操作

## 项目结构

```
亚马逊补货/
├── api/                    # API接口模块
│   └── client.py          # API客户端
├── auth/                   # 认证模块
│   └── token_manager.py   # Token管理器
├── business/              # 业务逻辑模块
│   └── restock_analyzer.py # 补货分析器
├── config/                # 配置模块
│   └── config.py         # 配置文件
├── deploy/                # 部署配置目录
│   ├── README.md         # 部署说明文档
│   ├── DEPLOYMENT.md     # 详细部署指南
│   ├── deploy.sh         # Linux/macOS部署脚本
│   ├── deploy.bat        # Windows部署脚本
│   ├── Dockerfile        # Docker镜像构建文件
│   └── docker-compose.yml # Docker编排配置
├── utils/                 # 工具模块
│   ├── crypto_utils.py   # 加密工具
│   └── logger.py         # 日志工具
├── data/                  # 数据目录
│   └── tokens.json       # Token存储文件（自动生成）
├── logs/                  # 日志目录（自动生成）
├── output/                # 输出目录（自动生成）
├── .env.example          # 环境变量配置模板
├── .gitignore           # Git忽略文件配置
├── main.py               # 主程序入口
├── requirements.txt      # 依赖包列表
└── README.md            # 项目说明文档
```

## 安装说明

### 🚀 快速部署（推荐）

#### Windows 用户
```cmd
# 1. 配置API密钥
copy .env.example .env
# 编辑 .env 文件，填入你的API密钥

# 2. 运行自动部署脚本
deploy\deploy.bat
```

#### Linux/macOS 用户
```bash
# 1. 配置API密钥
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥

# 2. 运行自动部署脚本
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

#### Docker 部署
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置

# 2. 启动Docker服务
cd deploy
docker-compose up -d
```

> 📖 **详细部署指南**: 查看 [deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md)

---

### 🔧 手动安装

#### 1. 环境要求

- Python 3.7+
- Windows/Linux/macOS

#### 2. 安装依赖

```bash
# 进入项目目录
cd 亚马逊补货

# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

#### 3. 配置API信息

编辑 `config/config.py` 文件，设置你的API信息：

```python
class APIConfig:
    # API基础配置
    BASE_URL = "https://openapi.lingxing.com"  # 正式环境
    APP_ID = "your_app_id"                     # 你的APP ID
    APP_SECRET = "your_app_secret"             # 你的APP Secret
```

## 使用方法

### 1. 交互式模式（推荐）

```bash
python main.py --interactive
```

或者直接运行：

```bash
python main.py
```

### 2. 命令行模式

#### 测试API连接
```bash
python main.py --test
```

#### 获取店铺信息
```bash
python main.py --sellers
```

#### 获取所有补货数据
```bash
python main.py --restock
```

#### 获取指定店铺的补货数据
```bash
python main.py --restock --sid "店铺ID1,店铺ID2"
```

#### 获取指定ASIN的补货数据
```bash
python main.py --restock --asin "B07ABC123,B08DEF456"
```

#### 高级选项
```bash
# 指定查询维度和模式
python main.py --restock --data-type 1 --mode 0

# 限制最大页数
python main.py --restock --max-pages 5

# 不导出Excel，只导出JSON
python main.py --restock --no-excel --json
```

### 3. 参数说明

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `--test` | 测试API连接 | - |
| `--sellers` | 获取店铺信息 | - |
| `--restock` | 获取补货数据 | - |
| `--sid` | 指定店铺ID | 多个用逗号分隔 |
| `--asin` | 指定ASIN | 多个用逗号分隔 |
| `--data-type` | 查询维度 | 1=ASIN, 2=MSKU |
| `--mode` | 补货建议模式 | 0=普通模式, 1=海外仓中转模式 |
| `--max-pages` | 最大页数限制 | 正整数 |
| `--no-excel` | 不导出Excel文件 | - |
| `--json` | 导出JSON文件 | - |
| `--interactive` | 交互式模式 | - |

## 输出说明

### 1. 控制台输出

程序会在控制台显示：
- API连接状态
- 店铺信息列表
- 补货数据汇总
- 紧急补货商品列表
- 高销量商品列表
- 文件导出路径

### 2. Excel文件

导出的Excel文件包含以下列：
- ASIN
- 店铺ID
- 断货标记
- 断货日期
- 可售天数
- FBA库存信息
- 销量数据
- 补货建议
- 时间信息等

### 3. JSON文件

包含完整的原始数据，便于程序化处理。

### 4. 日志文件

在 `logs/` 目录下生成详细的操作日志：
- `api_YYYYMMDD.log`: API调用日志
- `error_YYYYMMDD.log`: 错误日志

## 配置说明

### API配置 (`config/config.py`)

```python
class APIConfig:
    # API基础信息
    BASE_URL = "https://openapi.lingxing.com"  # API域名
    APP_ID = "your_app_id"                     # 应用ID
    APP_SECRET = "your_app_secret"             # 应用密钥
    
    # 请求配置
    REQUEST_TIMEOUT = 30                       # 请求超时时间（秒）
    MAX_RETRIES = 3                           # 最大重试次数
    RETRY_DELAY = 1                           # 重试延迟（秒）
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 100                   # 默认页大小
    MAX_PAGE_SIZE = 200                       # 最大页大小
    
    # Token配置
    TOKEN_REFRESH_THRESHOLD = 300             # Token刷新阈值（秒）
```

## 常见问题

### 1. API连接失败

**问题**: 提示"API连接测试失败"

**解决方案**:
- 检查网络连接
- 确认APP_ID和APP_SECRET正确
- 确认IP已加入白名单
- 检查API域名是否正确

### 2. Token获取失败

**问题**: 提示"access token缺失或过期"

**解决方案**:
- 检查APP_SECRET是否需要URL编码
- 确认时间戳和签名生成正确
- 检查请求参数格式

### 3. 数据获取为空

**问题**: 获取到的补货数据为空

**解决方案**:
- 确认店铺ID正确
- 检查店铺是否有补货数据
- 尝试调整查询参数

### 4. 导出文件失败

**问题**: Excel或JSON文件导出失败

**解决方案**:
- 确认output目录存在且有写入权限
- 检查磁盘空间是否充足
- 确认文件未被其他程序占用

## 开发说明

### 1. 添加新功能

- API相关功能：修改 `api/client.py`
- 业务逻辑：修改 `business/restock_analyzer.py`
- 工具函数：添加到 `utils/` 目录
- 配置项：修改 `config/config.py`

### 2. 日志记录

使用 `utils/logger.py` 中的 `api_logger` 记录日志：

```python
from utils.logger import api_logger

# 记录信息
api_logger.logger.info("操作成功")

# 记录错误
api_logger.log_error(exception, "操作失败")

# 记录API请求
api_logger.log_request("GET", "/api/test", {"param": "value"})
```

### 3. 异常处理

使用 `api/client.py` 中的 `APIException` 处理API相关异常：

```python
from api.client import APIException

try:
    # API调用
    result = client.some_api_call()
except APIException as e:
    print(f"API调用失败: {e}")
```

## 许可证

本项目仅供学习和内部使用，请遵守领星ERP的API使用条款。

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持基础的补货数据获取功能
- 提供Excel和JSON导出
- 实现交互式命令行界面

## 技术支持

如有问题或建议，请通过以下方式联系：
- 查看日志文件获取详细错误信息
- 检查API文档确认接口使用方法
- 确认网络和权限配置