# 功能：合同列表新增"我发起的"筛选

## 需求描述

在左侧合同列表筛选栏新增 **"我发起的"** 选项，点击后只展示由当前登录用户发起的合同预审列表。

## 改动范围

| 层级 | 文件 | 改动说明 |
|------|------|----------|
| 前端类型 | `frontend/src/types/index.ts:18` | `FilterType` 联合类型新增 `'我发起的'` |
| 前端工具 | `frontend/src/utils/filter.ts:55-62` | 新增 `case '我发起的'`，按 `initiatorId` 过滤 |
| 后端服务 | `backend/app/services/contract_service.py:490-492` | `_apply_filter()` 新增筛选逻辑 |
| 后端路由 | `backend/app/routes/contracts.py:112` | API 文档注释更新 |

> **注意**：前端 `FilterBar.tsx` 中"我发起的"按钮之前已存在，本次只补齐了类型定义、前端过滤工具函数和后端查询逻辑。

---

## 各文件改动详情

### 1. `frontend/src/types/index.ts` (第18行)

`FilterType` 类型定义增加 `'我发起的'`：

```typescript
// 修改前
export type FilterType = 'all' | '进行中' | '已完成' | '待我处理' | '抄送我';

// 修改后
export type FilterType = 'all' | '进行中' | '已完成' | '待我处理' | '抄送我' | '我发起的';
```

### 2. `frontend/src/utils/filter.ts` (新增第55-62行)

在 `switch` 语句中 `case '抄送我'` 之后新增：

```typescript
case '我发起的':
  if (!currentUserId) {
    console.warn('filterContracts: currentUserId is required for "我发起的" filter');
    filtered = [];
  } else {
    filtered = contracts.filter((c) => c.initiatorId === currentUserId);
  }
  break;
```

### 3. `backend/app/services/contract_service.py` (新增第490-492行)

在 `_apply_filter()` 方法中 `elif filter_type == "抄送我"` 之后新增：

```python
elif filter_type == "我发起的":
    # 筛选由当前用户发起的合同
    query = query.where(Contract.initiator_id == user_id)
```

数据库 `contracts` 表上已有索引 `ix_contracts_initiator_id`，此查询可直接走索引。

### 4. `backend/app/routes/contracts.py` (第112行)

更新 `get_contract_list` 的 docstring：

```python
# 修改前
filter: 筛选类型 (all/进行中/已完成/待我处理/抄送我)

# 修改后
filter: 筛选类型 (all/进行中/已完成/待我处理/抄送我/我发起的)
```

---

## 筛选逻辑

`"我发起的"` 筛选在后端通过 `Contract.initiator_id == user_id` 过滤，与 `"抄送我"`（通过 `cc_users` 数组包含判断）的区别：

| 筛选条件 | 数据库字段 | 语义 |
|----------|-----------|------|
| 我发起的 | `contracts.initiator_id` | 当前用户是合同发起人 |
| 抄送我 | `contracts.cc_users` | 当前用户在抄送列表中 |
| 待我处理 | `reviews` 子查询 | 当前用户有待处理的评审项 |

---

## API 调用方式

前端通过 HTTP GET 请求，将 `filter` 参数传入：

```
GET /api/contracts?filter=我发起的
```

后端 `contract_service._apply_filter()` 根据 `filter_type` 值拼接 SQL WHERE 条件。

---

## 部署验证

- **日期**：2026-05-20
- **操作**：`docker-compose restart backend` + `docker-compose up -d --build frontend`
- **验证方式**：登录后点击左侧筛选栏"我发起的"按钮，确认只显示当前用户发起的合同
