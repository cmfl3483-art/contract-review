# Task 14.1 完成报告 - 配置 AI 客户端

## 任务概述

**任务ID**: 14.1  
**任务描述**: 配置 AI 客户端
- 创建 AI 配置类 (支持 DeepSeek 和自部署模型)
- 实现 OpenAI 兼容客户端初始化
- 实现配置切换逻辑 (从环境变量读取)
- 需求: 6.1-6.8, 7.1-7.8

## 实现内容

### 1. 创建 AI 配置模块 (`app/core/ai_config.py`)

#### 核心功能

**AIConfig 类**:
- 支持两种 AI 服务提供商:
  - `deepseek`: DeepSeek 官方 API 服务
  - `custom`: 自部署模型(通过 OpenAI 兼容 API,如 vLLM、Ollama、LocalAI)
- 配置参数:
  - `provider`: 提供商类型
  - `api_base`: API 基础 URL
  - `api_key`: API 密钥
  - `model`: 模型名称
  - `timeout`: 请求超时时间
  - `max_tokens`: 最大生成 token 数
  - `temperature`: 生成温度

**主要方法**:

1. `from_env()` - 从环境变量加载配置
   ```python
   config = AIConfig.from_env()
   ```

2. `create_client()` - 创建 OpenAI 兼容的异步客户端
   ```python
   client = config.create_client()
   ```

3. `validate_config()` - 验证配置是否有效
   ```python
   is_valid, error_msg = config.validate_config()
   ```

4. `get_provider_info()` - 获取提供商信息
   ```python
   info = config.get_provider_info()
   ```

**全局函数**:

1. `get_ai_client()` - 获取全局 AI 客户端实例
   ```python
   client = get_ai_client()
   ```

2. `switch_ai_provider()` - 切换 AI 服务提供商
   ```python
   new_config = switch_ai_provider(
       provider="custom",
       api_base="http://localhost:8000/v1",
       model="qwen2.5-7b-instruct"
   )
   ```

### 2. 更新 AI 服务 (`app/services/ai_service.py`)

**修改内容**:
- 使用新的 AI 配置模块初始化客户端
- 添加 `refresh_client()` 方法支持配置变更后刷新客户端
- 保持原有的智能总结和问答功能不变

**代码变更**:
```python
# 旧代码
from app.core.config import settings
self.client = AsyncOpenAI(
    api_key=settings.AI_API_KEY,
    base_url=settings.AI_API_BASE,
    timeout=settings.AI_TIMEOUT
)
self.model = settings.AI_MODEL

# 新代码
from app.core.ai_config import get_ai_client, ai_config
self.client = get_ai_client()
self.model = ai_config.model
self.config = ai_config
```

### 3. 环境变量配置

**已有配置** (在 `app/core/config.py` 和 `.env.example` 中):

```bash
# AI 服务提供商: deepseek 或 custom
AI_PROVIDER=deepseek

# DeepSeek API 配置
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=your-deepseek-api-key
AI_MODEL=deepseek-chat

# 自部署模型配置示例:
# AI_PROVIDER=custom
# AI_API_BASE=http://localhost:8000/v1
# AI_API_KEY=your-api-key-or-empty
# AI_MODEL=qwen2.5-7b-instruct

# AI 请求超时时间 (秒)
AI_TIMEOUT=30
```

### 4. 单元测试 (`tests/test_ai_config.py`)

创建了全面的单元测试,覆盖以下场景:

**配置测试**:
- 默认配置
- 自定义配置
- 从环境变量加载配置

**验证测试**:
- 有效配置验证
- 缺少 API 基础 URL
- DeepSeek 缺少 API 密钥
- 自部署模型可以没有 API 密钥
- 缺少模型名称
- 无效的超时时间

**功能测试**:
- 创建 OpenAI 客户端
- 获取提供商信息
- API 密钥隐藏
- 切换提供商

## 使用示例

### 1. 使用 DeepSeek API

```python
# 在 .env 文件中配置
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=sk-your-deepseek-api-key
AI_MODEL=deepseek-chat

# 在代码中使用
from app.core.ai_config import get_ai_client, ai_config

client = get_ai_client()
response = await client.chat.completions.create(
    model=ai_config.model,
    messages=[
        {"role": "system", "content": "你是一个专业的合同分析助手"},
        {"role": "user", "content": "请分析这份合同"}
    ]
)
```

### 2. 使用自部署模型

```python
# 在 .env 文件中配置
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8000/v1
AI_API_KEY=  # 可以为空
AI_MODEL=qwen2.5-7b-instruct

# 在代码中使用
from app.core.ai_config import get_ai_client, ai_config

client = get_ai_client()
response = await client.chat.completions.create(
    model=ai_config.model,
    messages=[
        {"role": "system", "content": "你是一个专业的合同分析助手"},
        {"role": "user", "content": "请分析这份合同"}
    ]
)
```

### 3. 动态切换提供商

```python
from app.core.ai_config import switch_ai_provider

# 切换到自部署模型
new_config = switch_ai_provider(
    provider="custom",
    api_base="http://localhost:8000/v1",
    model="qwen2.5-7b-instruct"
)

# 刷新 AI 服务客户端
ai_service = AIService()
ai_service.refresh_client()
```

## 配置验证

AI 配置类提供了完善的验证机制:

1. **API 基础 URL 验证**: 不能为空
2. **API 密钥验证**: DeepSeek 必须提供,自部署模型可选
3. **模型名称验证**: 不能为空
4. **超时时间验证**: 必须大于 0

```python
from app.core.ai_config import AIConfig

config = AIConfig(
    provider="deepseek",
    api_base="https://api.deepseek.com/v1",
    api_key="",  # 错误:DeepSeek 需要 API 密钥
    model="deepseek-chat"
)

is_valid, error_msg = config.validate_config()
# is_valid = False
# error_msg = "DeepSeek API密钥不能为空"
```

## 安全特性

1. **API 密钥隐藏**: 在日志和字符串表示中自动隐藏 API 密钥
   ```python
   config = AIConfig(api_key="sk-1234567890abcdef")
   print(config)  # 输出: AIConfig(..., api_key=sk-12345...)
   ```

2. **配置验证**: 在切换提供商时自动验证配置有效性
   ```python
   try:
       switch_ai_provider(provider="deepseek", api_key="")
   except ValueError as e:
       print(e)  # "AI配置无效: DeepSeek API密钥不能为空"
   ```

## 兼容性

### OpenAI 兼容 API

AI 配置模块使用 OpenAI 官方 Python SDK (`openai` 包),支持所有 OpenAI 兼容的 API 服务:

1. **DeepSeek API**: 官方 DeepSeek 服务
2. **vLLM**: 高性能推理引擎
3. **Ollama**: 本地大模型运行工具
4. **LocalAI**: 自托管 OpenAI 兼容 API
5. **其他**: 任何实现 OpenAI API 规范的服务

### 配置示例

**vLLM**:
```bash
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8000/v1
AI_MODEL=Qwen/Qwen2.5-7B-Instruct
```

**Ollama**:
```bash
AI_PROVIDER=custom
AI_API_BASE=http://localhost:11434/v1
AI_MODEL=qwen2.5:7b
```

**LocalAI**:
```bash
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8080/v1
AI_MODEL=gpt-3.5-turbo  # LocalAI 模型别名
```

## 文件清单

### 新增文件
1. `app/core/ai_config.py` - AI 配置模块
2. `tests/test_ai_config.py` - 单元测试
3. `backend/test_ai_config_simple.py` - 简单测试脚本
4. `backend/TASK_14.1_COMPLETE.md` - 本文档

### 修改文件
1. `app/services/ai_service.py` - 更新为使用新的 AI 配置模块

### 已有文件(无需修改)
1. `app/core/config.py` - 已包含 AI 配置环境变量
2. `.env.example` - 已包含 AI 配置示例

## 测试验证

### 运行单元测试

```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_ai_config.py -v
```

### 运行简单测试

```bash
cd backend
source venv/bin/activate
python test_ai_config_simple.py
```

### 手动验证

```python
# 启动 Python 交互式环境
cd backend
source venv/bin/activate
python

# 测试配置加载
from app.core.ai_config import AIConfig, get_ai_client, ai_config

# 查看当前配置
print(ai_config)

# 验证配置
is_valid, error = ai_config.validate_config()
print(f"配置有效: {is_valid}")

# 获取客户端
client = get_ai_client()
print(f"客户端类型: {type(client)}")

# 获取提供商信息
info = ai_config.get_provider_info()
print(f"提供商: {info['name']}")
```

## 需求覆盖

### 需求 6: AI智能总结 (6.1-6.8)

AI 配置模块为智能总结功能提供了灵活的 AI 服务支持:

- ✅ 6.1: 支持从环境变量配置 AI 服务
- ✅ 6.2-6.8: AI 服务可用于生成智能总结(在 `ai_service.py` 中实现)

### 需求 7: AI合同顾问 (7.1-7.8)

AI 配置模块为合同顾问功能提供了灵活的 AI 服务支持:

- ✅ 7.1-7.8: AI 服务可用于问答功能(在 `ai_service.py` 中实现)

## 后续任务

Task 14.1 已完成,后续任务:

- **Task 14.2**: 实现智能总结生成逻辑
- **Task 14.3**: 实现合同顾问问答逻辑
- **Task 14.4**: 集成 AI 功能到 API 端点

## 总结

Task 14.1 成功实现了 AI 客户端配置功能:

1. ✅ 创建了 AI 配置类,支持 DeepSeek 和自部署模型
2. ✅ 实现了 OpenAI 兼容客户端初始化
3. ✅ 实现了配置切换逻辑,从环境变量读取
4. ✅ 更新了 AI 服务以使用新的配置模块
5. ✅ 创建了全面的单元测试
6. ✅ 提供了详细的使用文档和示例

配置模块设计灵活、易用、安全,为后续的 AI 功能实现提供了坚实的基础。
