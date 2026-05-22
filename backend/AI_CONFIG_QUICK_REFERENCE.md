# AI 配置快速参考

## 快速开始

### 1. 配置 DeepSeek API

编辑 `.env` 文件:

```bash
AI_PROVIDER=deepseek
AI_API_BASE=https://api.deepseek.com/v1
AI_API_KEY=sk-your-deepseek-api-key
AI_MODEL=deepseek-chat
AI_TIMEOUT=30
```

### 2. 配置自部署模型

编辑 `.env` 文件:

```bash
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8000/v1
AI_API_KEY=  # 可选
AI_MODEL=qwen2.5-7b-instruct
AI_TIMEOUT=30
```

## 代码示例

### 基本使用

```python
from app.core.ai_config import get_ai_client, ai_config

# 获取客户端
client = get_ai_client()

# 调用 AI 服务
response = await client.chat.completions.create(
    model=ai_config.model,
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ],
    max_tokens=ai_config.max_tokens,
    temperature=ai_config.temperature
)

print(response.choices[0].message.content)
```

### 切换提供商

```python
from app.core.ai_config import switch_ai_provider

# 切换到自部署模型
new_config = switch_ai_provider(
    provider="custom",
    api_base="http://localhost:8000/v1",
    model="qwen2.5-7b-instruct"
)

# 切换回 DeepSeek
new_config = switch_ai_provider(
    provider="deepseek",
    api_key="sk-your-key"
)
```

### 验证配置

```python
from app.core.ai_config import AIConfig

config = AIConfig(
    provider="deepseek",
    api_base="https://api.deepseek.com/v1",
    api_key="sk-test",
    model="deepseek-chat"
)

is_valid, error_msg = config.validate_config()
if not is_valid:
    print(f"配置错误: {error_msg}")
```

### 获取提供商信息

```python
from app.core.ai_config import ai_config

info = ai_config.get_provider_info()
print(f"提供商: {info['name']}")
print(f"描述: {info['description']}")
print(f"需要 API 密钥: {info['requires_api_key']}")
```

## 常见配置

### vLLM

```bash
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8000/v1
AI_MODEL=Qwen/Qwen2.5-7B-Instruct
```

### Ollama

```bash
AI_PROVIDER=custom
AI_API_BASE=http://localhost:11434/v1
AI_MODEL=qwen2.5:7b
```

### LocalAI

```bash
AI_PROVIDER=custom
AI_API_BASE=http://localhost:8080/v1
AI_MODEL=gpt-3.5-turbo
```

## 配置参数说明

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `AI_PROVIDER` | 提供商类型 (`deepseek` 或 `custom`) | `deepseek` | 是 |
| `AI_API_BASE` | API 基础 URL | `https://api.deepseek.com/v1` | 是 |
| `AI_API_KEY` | API 密钥 | - | DeepSeek 必填 |
| `AI_MODEL` | 模型名称 | `deepseek-chat` | 是 |
| `AI_TIMEOUT` | 超时时间(秒) | `30` | 否 |

## 故障排查

### 问题: "DeepSeek API密钥不能为空"

**解决方案**: 在 `.env` 文件中设置 `AI_API_KEY`

```bash
AI_API_KEY=sk-your-deepseek-api-key
```

### 问题: "API基础URL不能为空"

**解决方案**: 在 `.env` 文件中设置 `AI_API_BASE`

```bash
AI_API_BASE=https://api.deepseek.com/v1
```

### 问题: 连接超时

**解决方案**: 增加超时时间

```bash
AI_TIMEOUT=60
```

### 问题: 自部署模型连接失败

**解决方案**: 
1. 确认模型服务正在运行
2. 检查 `AI_API_BASE` 地址是否正确
3. 确认模型名称 `AI_MODEL` 与服务中的模型匹配

## 安全建议

1. **不要提交 API 密钥到版本控制**
   - 使用 `.env` 文件存储密钥
   - 确保 `.env` 在 `.gitignore` 中

2. **生产环境使用强密钥**
   ```bash
   # 生成随机密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **定期轮换 API 密钥**

4. **使用环境变量而非硬编码**
   ```python
   # ❌ 不要这样做
   api_key = "sk-1234567890"
   
   # ✅ 应该这样做
   from app.core.ai_config import ai_config
   api_key = ai_config.api_key
   ```

## 更多信息

- 完整文档: `TASK_14.1_COMPLETE.md`
- 单元测试: `tests/test_ai_config.py`
- 源代码: `app/core/ai_config.py`
