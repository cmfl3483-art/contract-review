# 缓存失效策略文档
# Cache Invalidation Strategy Documentation

## 概述 Overview

本文档描述了合同预审看板系统的缓存失效策略实现。该策略确保在数据变更时,相关缓存能够及时、准确地失效,保证数据一致性。

This document describes the cache invalidation strategy implementation for the Contract Pre-Review System. This strategy ensures that related caches are invalidated promptly and accurately when data changes, maintaining data consistency.

## 设计原则 Design Principles

### 1. 统一管理 Centralized Management
- 所有缓存失效逻辑集中在 `app/utils/cache_invalidation.py`
- 避免在各个服务中分散的缓存清除代码
- 便于维护和调试

### 2. 精确失效 Precise Invalidation
- 只清除受影响的缓存,避免过度清除
- 使用模式匹配批量清除相关缓存
- 最小化对系统性能的影响

### 3. 容错处理 Error Tolerance
- 缓存失效失败不影响业务逻辑
- 记录详细的错误日志便于排查
- Redis 不可用时系统仍能正常运行

### 4. 性能优化 Performance Optimization
- 批量删除操作减少网络往返
- 异步执行不阻塞主流程
- 支持缓存预热提升用户体验

## 缓存键命名规范 Cache Key Naming Convention

```
contract:list:{user_id}:{filter}:{search}:{page}:{limit}  # 合同列表
contract:detail:{contract_id}                              # 合同详情
contract:pending:{user_id}                                 # 待办数量
reviews:{contract_id}                                      # 评审记录
ai:summary:{contract_id}                                   # AI总结
user:session:{token}                                       # 用户会话
```

## 缓存失效场景 Cache Invalidation Scenarios

### 1. 合同创建 Contract Creation

**触发时机:** 创建新合同时

**失效范围:**
- `contract:list:*` - 所有用户的合同列表缓存
- `contract:pending:{reviewer_id}` - 所有评审人的待办数量缓存

**实现位置:**
- `app/services/contract_service.py::create_contract()`

**代码示例:**
```python
await cache_invalidation.invalidate_contract_created(
    contract_id=contract.id,
    initiator_id=initiator_id,
    reviewer_ids=reviewer_ids
)
```

### 2. 合同更新 Contract Update

**触发时机:** 更新合同状态或信息时

**失效范围:**
- `contract:list:*` - 所有用户的合同列表缓存
- `contract:detail:{contract_id}` - 合同详情缓存
- `contract:pending:{user_id}` - 相关用户的待办数量缓存

**实现位置:**
- `app/services/contract_service.py::update_contract_status()`
- `app/services/contract_service.py::update_contract()`

**代码示例:**
```python
await cache_invalidation.invalidate_contract_updated(
    contract_id=contract_id,
    affected_user_ids=affected_user_ids
)
```

### 3. 评审通过 Review Approval

**触发时机:** 评审人同意评审项时

**失效范围:**
- `contract:list:*` - 所有用户的合同列表缓存(状态可能变化)
- `reviews:{contract_id}` - 评审记录缓存
- `contract:pending:{reviewer_id}` - 评审人的待办数量缓存
- `ai:summary:{contract_id}` - AI总结缓存(需要重新生成)

**实现位置:**
- `app/services/review_service.py::approve_review()`

**代码示例:**
```python
await cache_invalidation.invalidate_review_approved(
    contract_id=str(contract_id),
    reviewer_id=reviewer_id,
    all_reviewer_ids=all_reviewer_ids
)
```

### 4. 评论添加 Comment Addition

**触发时机:** 添加评论或回复时

**失效范围:**
- `reviews:{contract_id}` - 评审记录缓存(包含评论数据)
- `ai:summary:{contract_id}` - AI总结缓存(关键问题的解决方案可能更新)

**实现位置:**
- `app/services/comment_service.py::create_comment()`

**代码示例:**
```python
await cache_invalidation.invalidate_comment_added(contract_id)
```

### 5. 点赞更新 Like Update

**触发时机:** 点赞或取消点赞评审意见/评论时

**失效范围:**
- `reviews:{contract_id}` - 评审记录缓存(包含点赞数据)

**实现位置:**
- `app/services/review_service.py::like_review()`
- `app/services/comment_service.py::like_comment()`

**代码示例:**
```python
await cache_invalidation.invalidate_like_updated(str(contract_id))
```

### 6. 附件上传 Attachment Upload

**触发时机:** 上传新附件时

**失效范围:**
- `contract:detail:{contract_id}` - 合同详情缓存(包含附件列表)

**实现位置:**
- `app/services/file_service.py::upload_file()`

**代码示例:**
```python
await cache_invalidation.invalidate_attachment_uploaded(contract_id)
```

## 高级功能 Advanced Features

### 1. 缓存预热 Cache Warming

**用途:** 在用户登录后或合同创建后预先加载常用数据到缓存

**用户缓存预热:**
```python
await cache_invalidation.warm_up_cache_for_user(user_id, db)
```

预热内容:
- 常用筛选条件的合同列表(全部、进行中、待我处理)
- 用户待办数量

**合同缓存预热:**
```python
await cache_invalidation.warm_up_cache_for_contract(contract_id, db)
```

预热内容:
- 合同详情
- 评审记录
- AI智能总结

### 2. 批量清除 Batch Invalidation

**清除所有用户缓存:**
```python
await cache_invalidation.invalidate_all_user_caches(user_id)
```

使用场景:
- 用户登出
- 用户权限变更

**清除所有缓存:**
```python
await cache_invalidation.clear_all_caches()
```

使用场景:
- 系统维护
- 数据迁移后
- 紧急情况

⚠️ **警告:** 此操作会清除所有缓存,可能导致短期性能下降

### 3. 缓存统计 Cache Statistics

**获取缓存统计信息:**
```python
stats = await cache_invalidation.get_cache_stats()
```

返回示例:
```python
{
    "contract_list": 15,
    "contract_detail": 8,
    "contract_pending": 12,
    "reviews": 10,
    "ai_summary": 5
}
```

## WebSocket 实时通知集成 WebSocket Real-time Notification Integration

缓存失效策略与 WebSocket 实时通知紧密集成:

1. **写操作触发缓存失效**
   - 数据库更新后立即清除服务端缓存
   
2. **WebSocket 推送事件**
   - 通知所有连接的客户端数据已更新
   
3. **客户端刷新缓存**
   - 客户端收到事件后刷新本地缓存
   - 使用 React Query 的 `invalidateQueries` 方法

**流程图:**
```
写操作 → 更新数据库 → 清除服务端缓存 → 发送 WebSocket 事件 → 客户端刷新缓存
```

## 性能考虑 Performance Considerations

### 1. 缓存 TTL 配置

```python
TTL_SHORT = 60        # 1分钟 - 频繁变化的数据(待办数量)
TTL_MEDIUM = 300      # 5分钟 - 中等频率变化的数据(合同列表)
TTL_LONG = 1800       # 30分钟 - 较少变化的数据(AI总结)
TTL_VERY_LONG = 3600  # 1小时 - 很少变化的数据(用户信息)
```

### 2. 批量操作优化

- 使用 `delete_many()` 批量删除多个键
- 使用 `delete_pattern()` 模式匹配删除
- 每次最多删除 1000 个键,避免阻塞 Redis

### 3. 错误处理

- 所有缓存操作都有 try-catch 保护
- 缓存失败不影响业务逻辑
- 记录详细的错误日志

## 监控和调试 Monitoring and Debugging

### 1. 日志记录

所有缓存失效操作都会记录日志:

```python
logger.info(f"Cleared cache for contract creation: {contract_id}")
logger.error(f"Failed to invalidate cache for contract update: {e}")
```

### 2. 缓存统计

定期检查缓存统计信息:

```python
stats = await cache_invalidation.get_cache_stats()
print(f"Contract list caches: {stats['contract_list']}")
```

### 3. 性能监控

监控指标:
- 缓存命中率
- 缓存失效频率
- Redis 连接池使用情况
- 缓存操作耗时

## 最佳实践 Best Practices

### 1. 何时使用缓存失效

✅ **应该使用:**
- 数据更新后立即清除相关缓存
- 使用统一的缓存失效方法
- 批量清除相关缓存

❌ **不应该:**
- 在读操作中清除缓存
- 过度清除不相关的缓存
- 忽略缓存失效错误

### 2. 缓存键设计

✅ **好的设计:**
- 使用清晰的命名空间
- 包含必要的参数
- 支持模式匹配

❌ **不好的设计:**
- 键名过长或过短
- 缺少命名空间
- 难以批量清除

### 3. 错误处理

✅ **正确做法:**
- 捕获所有缓存异常
- 记录详细的错误日志
- 不影响业务逻辑

❌ **错误做法:**
- 让缓存错误中断业务
- 忽略错误不记录日志
- 过度依赖缓存

## 测试 Testing

### 运行缓存失效测试

```bash
cd backend
python test_cache_invalidation.py
```

### 测试覆盖

- ✅ 合同创建缓存失效
- ✅ 评审通过缓存失效
- ✅ 评论添加缓存失效
- ✅ 点赞更新缓存失效
- ✅ 附件上传缓存失效
- ✅ 缓存统计功能
- ✅ 批量清除功能

## 故障排查 Troubleshooting

### 问题1: 缓存未失效

**症状:** 数据更新后前端仍显示旧数据

**排查步骤:**
1. 检查是否调用了缓存失效方法
2. 检查 Redis 连接是否正常
3. 检查缓存键是否正确
4. 查看错误日志

**解决方案:**
- 确保在数据更新后调用缓存失效
- 检查 Redis 服务状态
- 验证缓存键命名

### 问题2: 缓存过度失效

**症状:** 系统性能下降,缓存命中率低

**排查步骤:**
1. 检查缓存失效频率
2. 查看缓存统计信息
3. 分析缓存失效日志

**解决方案:**
- 优化缓存失效范围
- 增加缓存 TTL
- 使用更精确的缓存键

### 问题3: Redis 连接失败

**症状:** 缓存操作报错

**排查步骤:**
1. 检查 Redis 服务状态
2. 验证连接配置
3. 检查网络连接

**解决方案:**
- 启动 Redis 服务
- 检查 `REDIS_URL` 配置
- 检查防火墙设置

## 未来改进 Future Improvements

### 1. 智能缓存预热
- 基于用户行为预测需要预热的数据
- 在低峰期自动预热热点数据

### 2. 缓存版本控制
- 为缓存添加版本号
- 支持灰度发布时的缓存隔离

### 3. 分布式缓存失效
- 支持多实例部署时的缓存同步
- 使用 Redis Pub/Sub 广播失效事件

### 4. 缓存监控面板
- 实时显示缓存统计信息
- 可视化缓存命中率和失效频率
- 支持手动清除缓存

## 参考资料 References

- [Redis 官方文档](https://redis.io/documentation)
- [缓存失效策略最佳实践](https://docs.microsoft.com/en-us/azure/architecture/best-practices/caching)
- [React Query 缓存管理](https://tanstack.com/query/latest/docs/react/guides/caching)

## 更新日志 Changelog

### v1.0.0 (2025-01-XX)
- ✅ 实现统一的缓存失效策略
- ✅ 集成到所有服务层
- ✅ 添加缓存预热功能
- ✅ 添加缓存统计功能
- ✅ 完善错误处理和日志记录
- ✅ 编写测试用例和文档
