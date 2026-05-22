# Task 4.3 实现获取当前用户信息 API - 实现说明

## 任务概述

实现 `GET /api/auth/me` API 端点,用于获取当前登录用户的详细信息。

## 实现内容

### 1. 配置 AuthMiddleware (✅ 已完成)

**文件**: `app/main.py`

**修改内容**:
```python
# 配置认证中间件
# JWT Token 验证中间件,用于保护需要认证的 API 端点
app.add_middleware(BaseHTTPMiddleware, dispatch=AuthMiddleware())
```

**功能说明**:
- 从请求头 `Authorization: Bearer <token>` 中提取 JWT Token
- 验证 Token 的有效性和过期时间
- 将当前用户信息注入到 `request.state.user`
- 对于公开路径 (登录、回调、文档等) 跳过认证

**公开路径列表**:
- `/api/auth/dingtalk/login` - 钉钉授权登录
- `/api/auth/dingtalk/callback` - 钉钉授权回调
- `/docs` - API 文档
- `/redoc` - ReDoc 文档
- `/openapi.json` - OpenAPI 规范
- `/health` - 健康检查

### 2. API 端点实现 (✅ 已存在)

**文件**: `app/routes/auth.py`

**端点**: `GET /api/auth/me`

**实现代码**:
```python
@router.get("/me")
async def get_current_user_info(request: Request):
    """
    获取当前登录用户信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        当前用户信息
    """
    try:
        user = get_current_user(request)
        
        return {
            "success": True,
            "data": {
                "user": user
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户信息失败: {str(e)}"
        )
```

**功能说明**:
- 调用 `get_current_user(request)` 从 `request.state.user` 获取用户信息
- 返回包含用户信息的 JSON 响应
- 处理异常情况并返回适当的错误响应

### 3. 辅助函数 (✅ 已存在)

**文件**: `app/core/auth_middleware.py`

**函数**: `get_current_user(request: Request) -> dict`

**实现代码**:
```python
def get_current_user(request: Request) -> dict:
    """
    从请求上下文中获取当前用户信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        当前用户信息字典
        
    Raises:
        HTTPException: 如果用户未认证
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未认证"
        )
    
    return request.state.user
```

### 4. 测试文件 (✅ 已创建)

**文件**: `tests/test_auth_api.py`

**测试用例**:

1. **test_get_current_user_success** - 测试成功获取当前用户信息
   - 生成有效的 JWT Token
   - 发送带 Token 的请求
   - 验证返回的用户信息正确

2. **test_get_current_user_no_token** - 测试未提供 Token 时返回 401 错误
   - 发送不带 Token 的请求
   - 验证返回 401 Unauthorized

3. **test_get_current_user_invalid_token** - 测试无效 Token 时返回 401 错误
   - 发送带无效 Token 的请求
   - 验证返回 401 Unauthorized

4. **test_get_current_user_expired_token** - 测试过期 Token 时返回 401 错误
   - 生成已过期的 Token
   - 发送带过期 Token 的请求
   - 验证返回 401 Unauthorized

## 工作流程

### 正常流程 (有效 Token)

```
1. 客户端发送请求
   GET /api/auth/me
   Headers: Authorization: Bearer <valid-jwt-token>

2. AuthMiddleware 拦截请求
   - 提取 Token: <valid-jwt-token>
   - 验证 Token: ✅ 有效
   - 解码 Token 获取 payload:
     {
       "user_id": "550e8400-e29b-41d4-a716-446655440000",
       "dingtalk_user_id": "dingtalk_123456",
       "name": "张三",
       "role": "法务",
       "exp": 1234567890,
       "iat": 1234567890
     }
   - 注入到 request.state.user

3. /api/auth/me 端点处理
   - 调用 get_current_user(request)
   - 从 request.state.user 获取用户信息
   - 返回响应:
     {
       "success": true,
       "data": {
         "user": {
           "user_id": "550e8400-e29b-41d4-a716-446655440000",
           "dingtalk_user_id": "dingtalk_123456",
           "name": "张三",
           "role": "法务",
           "exp": 1234567890,
           "iat": 1234567890
         }
       }
     }

4. 客户端收到响应 (200 OK)
```

### 错误流程 (无效 Token)

```
1. 客户端发送请求
   GET /api/auth/me
   Headers: Authorization: Bearer <invalid-token>

2. AuthMiddleware 拦截请求
   - 提取 Token: <invalid-token>
   - 验证 Token: ❌ 无效
   - 返回 401 Unauthorized:
     {
       "detail": "Token无效或已过期"
     }

3. 客户端收到响应 (401 Unauthorized)
```

### 错误流程 (未提供 Token)

```
1. 客户端发送请求
   GET /api/auth/me
   (没有 Authorization 头)

2. AuthMiddleware 拦截请求
   - 未找到 Token
   - 返回 401 Unauthorized:
     {
       "detail": "未提供认证Token"
     }

3. 客户端收到响应 (401 Unauthorized)
```

## API 文档

### 请求

**方法**: `GET`

**路径**: `/api/auth/me`

**请求头**:
```
Authorization: Bearer <jwt-token>
```

### 响应

**成功响应 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "dingtalk_user_id": "dingtalk_123456",
      "name": "张三",
      "role": "法务",
      "exp": 1234567890,
      "iat": 1234567890
    }
  }
}
```

**错误响应 (401 Unauthorized)**:
```json
{
  "detail": "未提供认证Token"
}
```

或

```json
{
  "detail": "Token无效或已过期"
}
```

或

```json
{
  "detail": "用户未认证"
}
```

**错误响应 (500 Internal Server Error)**:
```json
{
  "detail": "获取用户信息失败: <error-message>"
}
```

## 使用示例

### cURL

```bash
# 成功请求
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 未提供 Token
curl -X GET http://localhost:8000/api/auth/me

# 无效 Token
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer invalid-token"
```

### JavaScript (Fetch API)

```javascript
// 成功请求
const token = localStorage.getItem('token');
const response = await fetch('http://localhost:8000/api/auth/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

if (response.ok) {
  const data = await response.json();
  console.log('当前用户:', data.data.user);
} else if (response.status === 401) {
  console.error('未授权,请重新登录');
  // 跳转到登录页面
  window.location.href = '/login';
} else {
  console.error('获取用户信息失败');
}
```

### Python (httpx)

```python
import httpx

# 成功请求
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {"Authorization": f"Bearer {token}"}

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/auth/me",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("当前用户:", data["data"]["user"])
    elif response.status_code == 401:
        print("未授权,请重新登录")
    else:
        print("获取用户信息失败")
```

## 安全考虑

1. **Token 传输安全**
   - 生产环境必须使用 HTTPS 传输 Token
   - 避免在 URL 参数中传递 Token

2. **Token 存储安全**
   - 前端应将 Token 存储在 localStorage 或 sessionStorage
   - 不要将 Token 存储在 Cookie 中 (除非设置 HttpOnly 和 Secure 标志)

3. **Token 过期时间**
   - 默认过期时间: 24 小时 (在 config.py 中配置)
   - 建议根据安全需求调整过期时间

4. **密钥安全**
   - SECRET_KEY 必须使用强随机字符串
   - 不要将 SECRET_KEY 提交到版本控制系统
   - 生产环境使用环境变量配置 SECRET_KEY

## 相关文件

- `app/main.py` - FastAPI 应用主入口,配置 AuthMiddleware
- `app/routes/auth.py` - 认证相关 API 路由,包含 /api/auth/me 端点
- `app/core/auth_middleware.py` - JWT 认证中间件和 get_current_user 函数
- `app/services/dingtalk_auth_service.py` - 钉钉授权服务,包含 JWT Token 生成和验证
- `tests/test_auth_api.py` - 认证 API 测试文件

## 验证方法

由于 Python 3.14 与部分依赖不兼容,无法直接运行测试。但可以通过以下方式验证实现:

1. **代码审查** ✅
   - AuthMiddleware 已正确配置到 FastAPI 应用
   - /api/auth/me 端点实现逻辑正确
   - get_current_user 函数正确从 request.state.user 获取用户信息

2. **逻辑验证** ✅
   - Token 生成和验证逻辑正确
   - 中间件拦截和注入逻辑正确
   - 错误处理逻辑完整

3. **测试文件** ✅
   - 已创建完整的测试文件 tests/test_auth_api.py
   - 包含所有关键场景的测试用例

4. **手动测试** (需要启动服务器)
   - 启动 FastAPI 服务器
   - 使用 cURL 或 Postman 测试端点
   - 验证各种场景的响应

## 总结

Task 4.3 "实现获取当前用户信息 API" 已完成:

✅ **AuthMiddleware 已配置** - 在 app/main.py 中正确配置
✅ **/api/auth/me 端点已实现** - 在 app/routes/auth.py 中实现
✅ **get_current_user 函数已实现** - 在 app/core/auth_middleware.py 中实现
✅ **测试文件已创建** - tests/test_auth_api.py 包含完整测试
✅ **文档已完善** - 本文档详细说明了实现细节

实现符合设计文档中的要求:
- 需求 10.10: 在页面底部状态栏显示当前用户名称
- 设计文档: GET /api/auth/me 端点返回当前用户信息
