# Token 调试指南

## 问题现象

登录成功后,合同列表显示 500 错误,右下角显示"未登录"。

## 可能的原因

1. **Token 没有被正确保存到 localStorage**
2. **Token 被保存了,但前端没有正确读取**
3. **Token 被正确发送,但后端验证失败**

## 调试步骤

### 1. 检查 localStorage 中的 token

打开浏览器开发者工具 (F12),在 Console 中执行:

```javascript
console.log('Token:', localStorage.getItem('token'));
console.log('User:', localStorage.getItem('user'));
```

**预期结果**:
- Token 应该是一个长字符串 (JWT token)
- User 应该是一个 JSON 字符串,包含用户信息

**如果 token 为 null**:
- 说明回调页面的 JavaScript 没有正确执行
- 需要检查回调页面是否有 JavaScript 错误

### 2. 检查网络请求中的 Authorization 头

在开发者工具的 Network 标签中:
1. 刷新页面
2. 找到 `/api/contracts` 请求
3. 查看 Request Headers
4. 检查是否有 `Authorization: Bearer <token>` 头

**预期结果**:
- 应该看到 `Authorization: Bearer eyJ...` (token 很长)

**如果没有 Authorization 头**:
- 说明前端 axios 没有正确添加 token
- 检查 `frontend/src/utils/axios.ts` 的请求拦截器

### 3. 手动测试 API

在 Console 中执行:

```javascript
// 获取 token
const token = localStorage.getItem('token');

// 测试 API
fetch('http://localhost:8000/api/contracts?filter=all&page=1&limit=10', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(res => res.json())
.then(data => console.log('API Response:', data))
.catch(err => console.error('API Error:', err));
```

**预期结果**:
- 应该返回合同列表数据

**如果返回 401 错误**:
- 说明 token 无效或已过期
- 需要重新登录

### 4. 检查回调页面的 JavaScript

访问回调 URL 时,打开开发者工具的 Console,查看是否有 JavaScript 错误。

## 快速修复

### 方案 1: 清除缓存并重新登录

1. 打开开发者工具 (F12)
2. 在 Console 中执行:
   ```javascript
   localStorage.clear();
   ```
3. 刷新页面
4. 重新登录

### 方案 2: 手动设置 token (临时测试)

如果你有一个有效的 token,可以手动设置:

```javascript
localStorage.setItem('token', 'YOUR_TOKEN_HERE');
localStorage.setItem('user', '{"id":"xxx","name":"测试用户","role":"业务"}');
location.reload();
```

## 当前修复

我已经修复了回调页面的 JavaScript,使用模板字符串来正确处理 JSON:

```javascript
localStorage.setItem('user', `{json.dumps(result['user'])}`);
```

这样可以避免 JSON 字符串中的引号导致 JavaScript 语法错误。

## 下一步

1. 清除浏览器的 localStorage
2. 重新登录
3. 检查 token 是否被正确保存
4. 如果还有问题,按照上面的调试步骤逐一排查
