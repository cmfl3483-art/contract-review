# 合同预审看板系统 API 文档

## 概述

合同预审看板系统提供了一套完整的 RESTful API 和 WebSocket 实时通信接口,用于管理合同预审流程。

**基础信息:**
- **Base URL**: `http://localhost:8000` (开发环境)
- **API 版本**: v0.1.0
- **认证方式**: JWT Bearer Token (钉钉 OAuth 登录)
- **响应格式**: JSON
- **字符编码**: UTF-8

**交互式文档:**
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

## 目录

1. [认证 API](#认证-api)
2. [合同管理 API](#合同管理-api)
3. [评审管理 API](#评审管理-api)
4. [文件管理 API](#文件管理-api)
5. [AI 功能 API](#ai-功能-api)
6. [WebSocket 事件](#websocket-事件)
7. [错误码说明](#错误码说明)
8. [数据模型](#数据模型)

---

## 认证 API

### 1.1 获取钉钉授权登录 URL

获取钉钉 OAuth 授权登录的 URL,用户需要访问此 URL 完成钉钉授权。

**请求:**
```http
GET /api/auth/dingtalk/login?state=default
```

**查询参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| state | string | 否 | 状态参数,用于防止 CSRF 攻击,默认为 "default" |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "authUrl": "https://login.dingtalk.com/oauth2/auth?..."
  }
}
```


### 1.2 钉钉授权回调处理

处理钉钉 OAuth 授权回调,获取用户信息并生成 JWT Token。

**请求:**
```http
GET /api/auth/dingtalk/callback?code=xxx&state=default
```

**查询参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 钉钉授权码 |
| state | string | 否 | 状态参数,默认为 "default" |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "user-uuid",
      "name": "张三",
      "role": "法务",
      "email": "zhangsan@example.com",
      "avatar": "https://..."
    }
  }
}
```

**错误响应:**
```json
{
  "success": false,
  "error": "授权回调处理失败: Invalid code"
}
```


### 1.3 获取当前用户信息

获取当前登录用户的详细信息。

**请求:**
```http
GET /api/auth/me
Authorization: Bearer <token>
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "user-uuid",
      "name": "张三",
      "role": "法务",
      "email": "zhangsan@example.com",
      "mobile": "13800138000",
      "avatar": "https://...",
      "department": "法务部"
    }
  }
}
```

**错误响应:**
```json
{
  "detail": "未授权: Token 无效或已过期"
}
```

### 1.4 用户登出

用户登出接口。注意:JWT 是无状态的,实际的登出需要在客户端删除 token。

**请求:**
```http
POST /api/auth/logout
Authorization: Bearer <token>
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "message": "登出成功"
  }
}
```


---

## 合同管理 API

### 2.1 创建合同

创建新的合同预审,并为每个评审人创建待处理的评审任务。

**请求:**
```http
POST /api/contracts
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "name": "采购合同-2025-001",
  "description": "与供应商A的年度采购合同",
  "reviewers": [
    {
      "user_id": "user-uuid-1",
      "role": "法务",
      "step": "法务初审"
    },
    {
      "user_id": "user-uuid-2",
      "role": "财务",
      "step": "财务审核"
    }
  ],
  "cc_users": ["user-uuid-3", "user-uuid-4"]
}
```

**字段说明:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 合同名称,1-200 字符 |
| description | string | 否 | 合同描述,最多 2000 字符 |
| reviewers | array | 是 | 评审人列表,至少 1 个 |
| reviewers[].user_id | string | 是 | 评审人用户 ID |
| reviewers[].role | string | 否 | 评审人角色,默认"业务" |
| reviewers[].step | string | 否 | 评审步骤,默认"评审" |
| cc_users | array | 否 | 抄送人用户 ID 列表 |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "contractId": "contract-uuid"
  }
}
```


**错误响应:**
```json
{
  "success": false,
  "error": "至少需要一个评审人"
}
```

### 2.2 获取合同列表

获取合同列表,支持筛选、搜索和分页。

**请求:**
```http
GET /api/contracts?filter=all&search=采购&page=1&limit=20
Authorization: Bearer <token>
```

**查询参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filter | string | 否 | 筛选类型: `all`(全部) / `进行中` / `已完成` / `待我处理` / `抄送我`,默认 `all` |
| search | string | 否 | 搜索关键词,按合同名称或发起人匹配 |
| page | integer | 否 | 页码,从 1 开始,默认 1 |
| limit | integer | 否 | 每页数量,1-100,默认 20 |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "contracts": [
      {
        "id": "contract-uuid",
        "name": "采购合同-2025-001",
        "description": "与供应商A的年度采购合同",
        "status": "progress",
        "initiator": {
          "id": "user-uuid",
          "name": "张三",
          "avatar": "https://..."
        },
        "created_at": "2025-03-01T10:00:00Z",
        "updated_at": "2025-03-01T15:30:00Z",
        "review_count": 5,
        "pending_review_count": 2
      }
    ],
    "total": 42,
    "page": 1,
    "limit": 20,
    "pendingCount": 3
  }
}
```


**字段说明:**
- `status`: 合同状态,`progress`(进行中) 或 `completed`(已完成)
- `review_count`: 评审记录总数
- `pending_review_count`: 待处理评审数量
- `pendingCount`: 当前用户的待办数量(用于徽章显示)

### 2.3 获取合同详情

获取合同的详细信息,包括基本信息、附件列表和评审人状态。

**请求:**
```http
GET /api/contracts/{contract_id}
Authorization: Bearer <token>
```

**路径参数:**
| 参数 | 类型 | 说明 |
|------|------|------|
| contract_id | string | 合同 ID |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "contract": {
      "id": "contract-uuid",
      "name": "采购合同-2025-001",
      "description": "与供应商A的年度采购合同",
      "status": "progress",
      "initiator": {
        "id": "user-uuid",
        "name": "张三",
        "avatar": "https://..."
      },
      "cc_users": ["user-uuid-3", "user-uuid-4"],
      "created_at": "2025-03-01T10:00:00Z",
      "updated_at": "2025-03-01T15:30:00Z"
    },
    "attachments": [
      {
        "file_name": "采购合同.pdf",
        "version_count": 3,
        "versions": [
          {
            "id": "attachment-uuid",
            "version": "v3.0",
            "file_size": 2048576,
            "mime_type": "application/pdf",
            "uploader": {
              "id": "user-uuid",
              "name": "张三"
            },
            "created_at": "2025-03-01T15:00:00Z"
          }
        ]
      }
    ],
    "reviewers": [
      {
        "user_id": "user-uuid-1",
        "name": "李四",
        "role": "法务",
        "status": "approved",
        "step": "法务初审"
      }
    ]
  }
}
```


### 2.4 添加评论

为合同添加评论,支持三种场景:直接评论合同、回复评审意见、嵌套回复。

**请求:**
```http
POST /api/contracts/{contract_id}/comments
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "content": "这个条款需要修改",
  "review_id": "review-uuid",
  "parent_comment_id": null
}
```

**字段说明:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 评论内容,1-5000 字符 |
| review_id | string | 否 | 评审 ID,回复评审意见时提供 |
| parent_comment_id | string | 否 | 父评论 ID,嵌套回复时提供 |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "comment": {
      "id": "comment-uuid",
      "contract_id": "contract-uuid",
      "review_id": "review-uuid",
      "parent_comment_id": null,
      "author": {
        "id": "user-uuid",
        "name": "张三",
        "avatar": "https://..."
      },
      "content": "这个条款需要修改",
      "likes": 0,
      "liked_by": [],
      "created_at": "2025-03-01T16:00:00Z",
      "updated_at": "2025-03-01T16:00:00Z"
    }
  }
}
```


---

## 评审管理 API

### 3.1 获取评审记录

获取合同的所有评审记录和 AI 智能总结。

**请求:**
```http
GET /api/contracts/{contract_id}/reviews
Authorization: Bearer <token>
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "reviews": [
      {
        "id": "review-uuid",
        "reviewer": {
          "id": "user-uuid",
          "name": "李四",
          "role": "法务",
          "avatar": "https://..."
        },
        "step": "法务初审",
        "opinion": "合同条款基本符合要求,建议修改第3条",
        "status": "approved",
        "likes": 5,
        "liked_by": ["user-uuid-1", "user-uuid-2"],
        "comments": [
          {
            "id": "comment-uuid",
            "content": "已修改",
            "author": {
              "id": "user-uuid",
              "name": "张三",
              "avatar": "https://..."
            },
            "likes": 2,
            "liked_by": ["user-uuid-1"],
            "parent_comment_id": null,
            "created_at": "2025-03-01T16:00:00Z"
          }
        ],
        "created_at": "2025-03-01T14:00:00Z",
        "updated_at": "2025-03-01T14:30:00Z"
      }
    ],
    "aiSummary": {
      "approval_status": "in_progress",
      "completed_count": 3,
      "total_count": 5,
      "review_count": 8,
      "key_issues": [
        {
          "issue": "建议修改第3条付款条款",
          "solution": "已按建议修改"
        }
      ],
      "updated_at": "2025-03-01T15:00:00Z"
    }
  }
}
```


### 3.2 同意评审

评审人同意评审项,更新评审状态为已通过。

**请求:**
```http
POST /api/contracts/{contract_id}/reviews/{review_id}/approve
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "opinion": "同意并通过"
}
```

**字段说明:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| opinion | string | 是 | 评审意见,1-2000 字符 |

**响应示例:**
```json
{
  "success": true,
  "data": {
    "review": {
      "id": "review-uuid",
      "status": "approved",
      "opinion": "同意并通过",
      "updated_at": "2025-03-01T16:30:00Z"
    }
  }
}
```

**错误响应:**
```json
{
  "success": false,
  "error": "您不是该评审项的评审人"
}
```

### 3.3 点赞评审意见

点赞或取消点赞评审意见。

**请求:**
```http
POST /api/reviews/{review_id}/like
Authorization: Bearer <token>
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "likes": 6
  }
}
```


### 3.4 点赞评论

点赞或取消点赞评论。

**请求:**
```http
POST /api/comments/{comment_id}/like
Authorization: Bearer <token>
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "likes": 3
  }
}
```

---

## 文件管理 API

### 4.1 上传附件

上传合同附件,支持自动版本管理。

**请求:**
```http
POST /api/contracts/{contract_id}/attachments
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**表单字段:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 文件,支持 PDF、DOC、DOCX、PPTX、XLSX,最大 20MB |

**支持的文件类型:**
- `application/pdf` - PDF 文档
- `application/msword` - Word 文档 (.doc)
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - Word 文档 (.docx)
- `application/vnd.ms-powerpoint` - PowerPoint (.ppt)
- `application/vnd.openxmlformats-officedocument.presentationml.presentation` - PowerPoint (.pptx)
- `application/vnd.ms-excel` - Excel (.xls)
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` - Excel (.xlsx)

**响应示例:**
```json
{
  "success": true,
  "data": {
    "attachment": {
      "id": "attachment-uuid",
      "file_name": "采购合同.pdf",
      "version": "v1.0",
      "file_size": 2048576,
      "mime_type": "application/pdf",
      "created_at": "2025-03-01T10:30:00Z"
    }
  }
}
```


**错误响应:**
```json
{
  "success": false,
  "error": "文件大小不能超过20MB"
}
```

**版本管理说明:**
- 上传同名文件时,系统自动创建新版本 (v1.0 -> v2.0 -> v3.0)
- 版本号格式: `v{major}.{minor}`,同名文件递增 major 版本号

### 4.2 下载附件

下载附件文件,重定向到 MinIO 预签名 URL。

**请求:**
```http
GET /api/attachments/{attachment_id}/download
Authorization: Bearer <token>
```

**响应:**
- 302 重定向到 MinIO 预签名 URL
- 预签名 URL 有效期: 1 小时

**错误响应:**
```json
{
  "detail": "您没有权限下载此文件"
}
```

### 4.3 以文件流方式下载附件

直接通过后端返回文件流,适用于需要后端代理的场景。

**请求:**
```http
GET /api/attachments/{attachment_id}/stream
Authorization: Bearer <token>
```

**响应:**
- Content-Type: 文件的 MIME 类型
- Content-Disposition: `attachment; filename="文件名"`
- Content-Length: 文件大小


### 4.4 获取附件信息

获取附件的详细信息。

**请求:**
```http
GET /api/attachments/{attachment_id}
Authorization: Bearer <token>
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "attachment": {
      "id": "attachment-uuid",
      "file_name": "采购合同.pdf",
      "version": "v2.0",
      "file_size": 2048576,
      "mime_type": "application/pdf",
      "storage_key": "contract-uuid/采购合同.pdf/v2.0/abc123.pdf",
      "uploader_id": "user-uuid",
      "created_at": "2025-03-01T15:00:00Z"
    }
  }
}
```

---

## AI 功能 API

### 5.1 生成 AI 智能总结

生成或获取合同的 AI 智能总结。

**请求:**
```http
POST /api/ai/summary/{contract_id}?force_regenerate=false
Authorization: Bearer <token>
```

**查询参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force_regenerate | boolean | 否 | 是否强制重新生成(忽略缓存),默认 false |

**智能行为:**
1. 首先检查是否有缓存的总结
2. 如果有缓存且未过期,直接返回缓存的总结
3. 如果没有缓存或强制重新生成,触发异步任务并返回任务 ID

**响应示例 (有缓存):**
```json
{
  "success": true,
  "data": {
    "summary": {
      "approval_status": "in_progress",
      "completed_count": 3,
      "total_count": 5,
      "review_count": 8,
      "key_issues": [
        {
          "issue": "建议修改第3条付款条款",
          "solution": "已按建议修改"
        }
      ],
      "updated_at": "2025-03-01T15:00:00Z"
    },
    "cached": true
  }
}
```


**响应示例 (无缓存,创建异步任务):**
```json
{
  "success": true,
  "data": {
    "task_id": "celery-task-uuid",
    "status": "PENDING",
    "message": "AI总结生成任务已创建",
    "status_url": "/api/ai/summary/task/celery-task-uuid"
  }
}
```

**响应示例 (降级处理,Celery 不可用时同步生成):**
```json
{
  "success": true,
  "data": {
    "summary": {
      "approval_status": "in_progress",
      "completed_count": 3,
      "total_count": 5,
      "review_count": 8,
      "key_issues": [],
      "updated_at": "2025-03-01T15:00:00Z"
    },
    "fallback": true,
    "message": "任务队列不可用,已同步生成总结"
  }
}
```

**字段说明:**
- `approval_status`: 审批状态,`completed`(已全部通过) 或 `in_progress`(审批进行中)
- `completed_count`: 已完成审批的人数
- `total_count`: 总评审人数
- `review_count`: 评审意见总数
- `key_issues`: 关键问题列表(最多 3 个)
- `key_issues[].issue`: 问题描述
- `key_issues[].solution`: 解决方案(如果有回复)

### 5.2 获取已生成的 AI 智能总结

获取已生成的 AI 智能总结,不触发新的生成任务。

**请求:**
```http
GET /api/ai/summary/{contract_id}
Authorization: Bearer <token>
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "approval_status": "completed",
      "completed_count": 5,
      "total_count": 5,
      "review_count": 12,
      "key_issues": [],
      "updated_at": "2025-03-01T17:00:00Z"
    }
  }
}
```


### 5.3 AI 合同顾问问答

向 AI 顾问询问合同相关问题。

**请求:**
```http
POST /api/ai/advisor
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "contract_id": "contract-uuid",
  "question": "法务有什么意见?"
}
```

**字段说明:**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| contract_id | string | 是 | 合同 ID |
| question | string | 是 | 问题,1-500 字符 |

**支持的问题类型:**
1. **法务意见查询**: 包含"法务"关键词,返回所有法务角色的评审意见
2. **风险项查询**: 包含"风险"或"未确认"关键词,返回所有状态为"评审中"的评审项
3. **待办任务查询**: 包含"待我处理"关键词,返回当前用户所有待处理的评审任务
4. **其他问题**: 返回合同评审数量和可询问的问题类型提示

**响应示例 (法务意见查询):**
```json
{
  "success": true,
  "data": {
    "answer": "法务部门的评审意见如下:\n\n1. 李四(法务): 合同条款基本符合要求,建议修改第3条\n2. 王五(法务): 同意并通过"
  }
}
```

**响应示例 (风险项查询):**
```json
{
  "success": true,
  "data": {
    "answer": "当前有 2 个风险项需要关注:\n\n1. 财务审核 - 待处理\n2. 业务审核 - 评审中"
  }
}
```

**响应示例 (待办任务查询):**
```json
{
  "success": true,
  "data": {
    "answer": "您有 3 个待处理的评审任务:\n\n1. 采购合同-2025-001 - 法务初审\n2. 销售合同-2025-002 - 法务复审\n3. 服务合同-2025-003 - 法务审核"
  }
}
```


### 5.4 获取异步任务状态

获取 AI 总结生成任务的状态和结果。

**请求:**
```http
GET /api/ai/summary/task/{task_id}
Authorization: Bearer <token>
```

**响应示例 (任务进行中):**
```json
{
  "success": true,
  "data": {
    "task_id": "celery-task-uuid",
    "status": "STARTED",
    "message": "任务正在执行中"
  }
}
```

**响应示例 (任务成功):**
```json
{
  "success": true,
  "data": {
    "task_id": "celery-task-uuid",
    "status": "SUCCESS",
    "message": "任务执行成功",
    "result": {
      "summary_id": "summary-uuid",
      "contract_id": "contract-uuid"
    }
  }
}
```

**响应示例 (任务失败):**
```json
{
  "success": true,
  "data": {
    "task_id": "celery-task-uuid",
    "status": "FAILURE",
    "message": "任务执行失败",
    "error": "AI service timeout",
    "timeout": true,
    "max_retries_reached": false
  }
}
```

**任务状态说明:**
- `PENDING`: 任务正在等待执行
- `STARTED`: 任务正在执行中
- `RETRY`: 任务执行失败,正在重试
- `SUCCESS`: 任务执行成功
- `FAILURE`: 任务执行失败


---

## WebSocket 事件

系统使用 Socket.IO 实现实时通信,客户端连接到 `/socket.io` 路径。

### 连接认证

客户端连接时需要提供 JWT Token:

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: {
    token: 'your-jwt-token'
  }
});
```

### 事件列表

#### 6.1 contract:updated

合同信息更新事件。

**事件数据:**
```json
{
  "contract_id": "contract-uuid",
  "status": "completed",
  "updated_at": "2025-03-01T18:00:00Z"
}
```

**触发场景:**
- 合同状态变更(进行中 -> 已完成)
- 合同基本信息更新

#### 6.2 review:added

新增评审意见事件。

**事件数据:**
```json
{
  "contract_id": "contract-uuid",
  "review_id": "review-uuid",
  "reviewer": {
    "id": "user-uuid",
    "name": "张三"
  },
  "opinion": "同意并通过",
  "status": "approved"
}
```

**触发场景:**
- 评审人提交评审意见
- 评审人同意评审


#### 6.3 comment:added

新增评论事件。

**事件数据:**
```json
{
  "contract_id": "contract-uuid",
  "comment_id": "comment-uuid",
  "review_id": "review-uuid",
  "author": {
    "id": "user-uuid",
    "name": "李四"
  },
  "content": "已修改"
}
```

**触发场景:**
- 用户添加评论
- 用户回复评审意见

#### 6.4 reply:added

新增回复事件(嵌套回复)。

**事件数据:**
```json
{
  "contract_id": "contract-uuid",
  "comment_id": "comment-uuid",
  "parent_comment_id": "parent-comment-uuid",
  "author": {
    "id": "user-uuid",
    "name": "王五"
  },
  "content": "好的"
}
```

**触发场景:**
- 用户回复其他用户的评论

#### 6.5 like:updated

点赞更新事件。

**事件数据:**
```json
{
  "type": "review",
  "target_id": "review-uuid",
  "likes": 6,
  "user_id": "user-uuid"
}
```

**字段说明:**
- `type`: 点赞类型,`review`(评审意见) 或 `comment`(评论)
- `target_id`: 目标 ID(评审 ID 或评论 ID)
- `likes`: 更新后的点赞数
- `user_id`: 点赞用户 ID

**触发场景:**
- 用户点赞评审意见
- 用户点赞评论


#### 6.6 pending:changed

待办数量变化事件。

**事件数据:**
```json
{
  "user_id": "user-uuid",
  "pending_count": 5
}
```

**触发场景:**
- 用户被指定为评审人(待办数量增加)
- 用户完成评审(待办数量减少)

### 客户端监听示例

```javascript
// 监听合同更新
socket.on('contract:updated', (data) => {
  console.log('合同更新:', data);
  // 刷新合同详情
});

// 监听新评论
socket.on('comment:added', (data) => {
  console.log('新评论:', data);
  // 刷新时间线
});

// 监听待办变化
socket.on('pending:changed', (data) => {
  console.log('待办数量变化:', data);
  // 更新待办徽章
});
```

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 200 | 成功 | 请求成功 |
| 400 | 请求参数错误 | 缺少必填字段、字段格式错误、文件类型不支持 |
| 401 | 未授权 | Token 过期、Token 无效、未登录 |
| 403 | 权限不足 | 非评审人尝试审批、非发起人尝试删除合同 |
| 404 | 资源不存在 | 合同 ID 不存在、附件已删除 |
| 413 | 文件过大 | 上传文件超过 20MB 限制 |
| 500 | 服务器内部错误 | 数据库连接失败、未捕获的异常 |
| 502 | 上游服务错误 | MinIO 不可用、AI 服务超时 |
| 503 | 服务不可用 | 系统维护、数据库连接池耗尽 |


### 错误响应格式

**标准错误响应:**
```json
{
  "success": false,
  "error": "错误描述信息",
  "code": "ERROR_CODE",
  "field": "字段名"
}
```

**FastAPI 默认错误响应:**
```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| VALIDATION_ERROR | 请求参数验证失败 | 400 |
| TOKEN_EXPIRED | Token 已过期 | 401 |
| TOKEN_INVALID | Token 无效 | 401 |
| UNAUTHORIZED | 未授权 | 401 |
| PERMISSION_DENIED | 权限不足 | 403 |
| RESOURCE_NOT_FOUND | 资源不存在 | 404 |
| FILE_TOO_LARGE | 文件过大 | 413 |
| INTERNAL_ERROR | 服务器内部错误 | 500 |
| AI_SERVICE_UNAVAILABLE | AI 服务不可用 | 502 |
| SERVICE_MAINTENANCE | 系统维护中 | 503 |

---

## 数据模型

### User (用户)

```typescript
interface User {
  id: string;              // UUID
  dingtalk_user_id: string; // 钉钉用户ID(唯一)
  dingtalk_union_id?: string; // 钉钉UnionID
  name: string;            // 显示名称
  role: string;            // 角色(销售/法务/财务/业务/运营/人事)
  email?: string;          // 邮箱
  mobile?: string;         // 手机号
  avatar?: string;         // 头像URL
  department?: string;     // 部门
  created_at: string;      // ISO 8601 格式
  updated_at: string;      // ISO 8601 格式
}
```


### Contract (合同)

```typescript
interface Contract {
  id: string;              // UUID
  name: string;            // 合同名称
  description?: string;    // 合同描述
  status: 'progress' | 'completed';  // 状态
  initiator_id: string;    // 发起人ID
  initiator: User;         // 发起人信息
  cc_users: string[];      // 抄送人ID数组
  created_at: string;      // ISO 8601 格式
  updated_at: string;      // ISO 8601 格式
}
```

### Review (评审记录)

```typescript
interface Review {
  id: string;              // UUID
  contract_id: string;     // 合同ID
  reviewer_id: string;     // 评审人ID
  reviewer: User;          // 评审人信息
  role: string;            // 评审人角色
  step: string;            // 评审步骤(如"法务初审")
  opinion?: string;        // 评审意见
  status: 'pending' | 'reviewing' | 'approved';  // 状态
  likes: number;           // 点赞数
  liked_by: string[];      // 点赞用户ID数组
  comments: Comment[];     // 评论列表
  created_at: string;      // ISO 8601 格式
  updated_at: string;      // ISO 8601 格式
}
```

**状态说明:**
- `pending`: 待处理
- `reviewing`: 评审中
- `approved`: 已通过

### Comment (评论)

```typescript
interface Comment {
  id: string;              // UUID
  contract_id: string;     // 合同ID
  review_id?: string;      // 评审ID(可选)
  parent_comment_id?: string; // 父评论ID(用于嵌套回复)
  author_id: string;       // 作者ID
  author: User;            // 作者信息
  content: string;         // 评论内容
  likes: number;           // 点赞数
  liked_by: string[];      // 点赞用户ID数组
  created_at: string;      // ISO 8601 格式
  updated_at: string;      // ISO 8601 格式
}
```


### Attachment (附件)

```typescript
interface Attachment {
  id: string;              // UUID
  contract_id: string;     // 合同ID
  file_name: string;       // 文件名
  version: string;         // 版本号(如"v1.0")
  file_size: number;       // 文件大小(字节)
  mime_type: string;       // MIME类型
  storage_key: string;     // 存储键(MinIO对象键)
  uploader_id: string;     // 上传人ID
  uploader: User;          // 上传人信息
  created_at: string;      // ISO 8601 格式
}
```

### AISummary (AI总结)

```typescript
interface AISummary {
  id: string;              // UUID
  contract_id: string;     // 合同ID
  approval_status: 'completed' | 'in_progress';  // 审批状态
  completed_count: number; // 已完成人数
  total_count: number;     // 总人数
  review_count: number;    // 评审意见总数
  key_issues: KeyIssue[];  // 关键问题数组
  created_at: string;      // ISO 8601 格式
  updated_at: string;      // ISO 8601 格式
}

interface KeyIssue {
  issue: string;           // 问题描述
  solution?: string;       // 解决方案
}
```

**审批状态说明:**
- `completed`: 已全部通过
- `in_progress`: 审批进行中

---

## 使用示例

### 完整的合同创建和审批流程

```javascript
// 1. 钉钉授权登录
const authResponse = await fetch('http://localhost:8000/api/auth/dingtalk/login');
const { authUrl } = await authResponse.json();
// 用户访问 authUrl 完成授权

// 2. 授权回调后获取 token
const callbackResponse = await fetch(
  `http://localhost:8000/api/auth/dingtalk/callback?code=${code}`
);
const { token, user } = await callbackResponse.json();

// 3. 创建合同
const createResponse = await fetch('http://localhost:8000/api/contracts', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: '采购合同-2025-001',
    description: '与供应商A的年度采购合同',
    reviewers: [
      { user_id: 'user-1', role: '法务', step: '法务初审' },
      { user_id: 'user-2', role: '财务', step: '财务审核' }
    ],
    cc_users: ['user-3']
  })
});
const { contractId } = await createResponse.json();

// 4. 上传附件
const formData = new FormData();
formData.append('file', fileBlob, '采购合同.pdf');

const uploadResponse = await fetch(
  `http://localhost:8000/api/contracts/${contractId}/attachments`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  }
);

// 5. 评审人同意评审
const approveResponse = await fetch(
  `http://localhost:8000/api/contracts/${contractId}/reviews/${reviewId}/approve`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      opinion: '同意并通过'
    })
  }
);

// 6. 添加评论
const commentResponse = await fetch(
  `http://localhost:8000/api/contracts/${contractId}/comments`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: '已修改',
      review_id: reviewId
    })
  }
);

// 7. 生成 AI 智能总结
const summaryResponse = await fetch(
  `http://localhost:8000/api/ai/summary/${contractId}`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

// 8. AI 顾问问答
const advisorResponse = await fetch(
  'http://localhost:8000/api/ai/advisor',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      contract_id: contractId,
      question: '法务有什么意见?'
    })
  }
);
```


### WebSocket 实时通信示例

```javascript
import io from 'socket.io-client';

// 连接 Socket.IO
const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: {
    token: token
  }
});

// 监听连接成功
socket.on('connect', () => {
  console.log('WebSocket 连接成功');
});

// 监听合同更新
socket.on('contract:updated', (data) => {
  console.log('合同更新:', data);
  // 刷新合同详情
  refreshContractDetail(data.contract_id);
});

// 监听新评论
socket.on('comment:added', (data) => {
  console.log('新评论:', data);
  // 刷新时间线
  refreshTimeline(data.contract_id);
});

// 监听点赞更新
socket.on('like:updated', (data) => {
  console.log('点赞更新:', data);
  // 更新点赞数
  updateLikeCount(data.type, data.target_id, data.likes);
});

// 监听待办变化
socket.on('pending:changed', (data) => {
  console.log('待办数量变化:', data);
  // 更新待办徽章
  updatePendingBadge(data.pending_count);
});

// 监听连接错误
socket.on('connect_error', (error) => {
  console.error('WebSocket 连接失败:', error);
});

// 监听断开连接
socket.on('disconnect', (reason) => {
  console.log('WebSocket 断开连接:', reason);
  if (reason === 'io server disconnect') {
    // 服务端主动断开,尝试重连
    socket.connect();
  }
});
```

---

## 性能优化建议

### 1. 缓存策略

系统使用 Redis 缓存以下数据:

| 缓存键 | 过期时间 | 说明 |
|--------|----------|------|
| `contract:list:{userId}:{filter}` | 5 分钟 | 用户的合同列表 |
| `contract:detail:{contractId}` | 10 分钟 | 合同详情 |
| `contract:pending:{userId}` | 1 分钟 | 用户待办数量 |
| `reviews:{contractId}` | 5 分钟 | 合同评审记录 |
| `ai:summary:{contractId}` | 30 分钟 | AI 总结 |
| `user:session:{token}` | 24 小时 | 用户会话 |

**客户端缓存建议:**
- 使用 React Query 或 SWR 进行客户端缓存
- 监听 WebSocket 事件,收到更新时刷新缓存
- 合理设置 `staleTime` 和 `cacheTime`


### 2. 分页和限流

**分页参数:**
- 默认每页 20 条记录
- 最大每页 100 条记录
- 建议使用虚拟滚动处理大量数据

**限流建议:**
- 搜索输入使用防抖(300ms)
- 点赞操作使用节流(1000ms)
- 避免频繁调用 AI 接口

### 3. 文件上传优化

**上传建议:**
- 前端校验文件类型和大小
- 使用 `multipart/form-data` 上传
- 显示上传进度条
- 支持断点续传(大文件)

**下载建议:**
- 使用预签名 URL 直接从 MinIO 下载
- 避免通过后端代理下载(除非有特殊需求)
- 实现下载进度显示

### 4. WebSocket 优化

**连接管理:**
- 实现自动重连机制
- 处理连接超时
- 避免重复连接

**事件处理:**
- 使用事件聚合,避免频繁更新 UI
- 实现事件去重
- 合理使用防抖和节流

---

## 安全建议

### 1. 认证和授权

- **Token 管理**: 
  - Token 存储在 `localStorage` 或 `sessionStorage`
  - Token 过期时间: 24 小时
  - 自动刷新 Token 机制
  
- **权限控制**:
  - 评审人才能审批
  - 发起人才能删除合同
  - 合同相关人员才能下载附件

### 2. 数据验证

- **前端验证**: 提供即时反馈,提升用户体验
- **后端验证**: 必须进行,防止恶意请求
- **文件验证**: 检查文件类型、大小、内容

### 3. HTTPS 传输

- 生产环境必须使用 HTTPS
- 保护 Token 和敏感数据
- 防止中间人攻击

### 4. CORS 配置

- 生产环境配置具体的前端域名
- 不要使用 `allow_origins=["*"]`
- 启用 `allow_credentials=True`


---

## 常见问题 (FAQ)

### Q1: 如何处理 Token 过期?

**A:** 当收到 401 错误时,清除本地 Token 并重定向到钉钉授权登录页:

```javascript
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/api/auth/dingtalk/login';
    }
    return Promise.reject(error);
  }
);
```

### Q2: 如何实现文件上传进度显示?

**A:** 使用 Axios 的 `onUploadProgress` 回调:

```javascript
const formData = new FormData();
formData.append('file', file);

axios.post(`/api/contracts/${contractId}/attachments`, formData, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'multipart/form-data'
  },
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`上传进度: ${percentCompleted}%`);
  }
});
```

### Q3: 如何处理 AI 服务不可用?

**A:** 系统实现了降级处理:
1. 首先尝试使用 Celery 异步任务
2. 如果 Celery 不可用,同步生成总结
3. 如果 AI 服务完全不可用,返回友好提示

客户端应该优雅地处理这些情况:

```javascript
const response = await fetch(`/api/ai/summary/${contractId}`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();

if (data.data.summary) {
  // 显示总结
  displaySummary(data.data.summary);
} else if (data.data.task_id) {
  // 轮询任务状态
  pollTaskStatus(data.data.task_id);
} else {
  // 显示友好提示
  showMessage(data.data.message || 'AI服务暂时不可用');
}
```


### Q4: 如何实现实时更新?

**A:** 结合 WebSocket 和 React Query:

```javascript
import { useQueryClient } from 'react-query';
import { useEffect } from 'react';
import { socket } from './socket';

function useRealtimeUpdates() {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    // 监听合同更新
    socket.on('contract:updated', (data) => {
      // 刷新合同列表缓存
      queryClient.invalidateQueries(['contracts']);
      // 刷新合同详情缓存
      queryClient.invalidateQueries(['contract', data.contract_id]);
    });
    
    // 监听新评论
    socket.on('comment:added', (data) => {
      // 刷新评审记录缓存
      queryClient.invalidateQueries(['reviews', data.contract_id]);
    });
    
    // 监听待办变化
    socket.on('pending:changed', (data) => {
      // 刷新合同列表(包含待办数量)
      queryClient.invalidateQueries(['contracts']);
    });
    
    return () => {
      socket.off('contract:updated');
      socket.off('comment:added');
      socket.off('pending:changed');
    };
  }, [queryClient]);
}
```

### Q5: 如何处理并发更新冲突?

**A:** 系统使用乐观锁防止并发更新冲突。当收到冲突错误时,提示用户刷新:

```javascript
try {
  await updateContract(contractId, data);
} catch (error) {
  if (error.response?.status === 409) {
    // 并发冲突
    alert('合同已被其他用户修改,请刷新后重试');
    // 刷新数据
    queryClient.invalidateQueries(['contract', contractId]);
  }
}
```

### Q6: 如何优化大量合同列表的性能?

**A:** 使用虚拟滚动和分页:

```javascript
import { FixedSizeList } from 'react-window';

function ContractList({ contracts }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <ContractCard contract={contracts[index]} />
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={contracts.length}
      itemSize={100}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```


---

## 附录

### A. 环境变量配置

后端需要配置以下环境变量(参考 `.env.example`):

```bash
# 应用配置
PROJECT_NAME="合同预审看板系统"
ENVIRONMENT="development"
SECRET_KEY="your-secret-key-here"

# 数据库配置
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/contract_review"

# Redis 配置
REDIS_URL="redis://localhost:6379/0"

# MinIO 配置
MINIO_ENDPOINT="localhost:9000"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
MINIO_BUCKET="contract-attachments"
MINIO_SECURE=false

# 钉钉配置
DINGTALK_APP_KEY="your-app-key"
DINGTALK_APP_SECRET="your-app-secret"
DINGTALK_REDIRECT_URI="http://localhost:8000/api/auth/dingtalk/callback"

# AI 配置
AI_PROVIDER="deepseek"  # 或 "custom"
AI_API_BASE="https://api.deepseek.com/v1"
AI_API_KEY="your-api-key"
AI_MODEL="deepseek-chat"

# Celery 配置
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/2"

# CORS 配置
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
```

### B. 数据库迁移

使用 Alembic 进行数据库迁移:

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### C. 开发工具

**推荐工具:**
- **Postman**: API 测试
- **Swagger UI**: 交互式 API 文档 (http://localhost:8000/api/docs)
- **Redis Commander**: Redis 可视化管理
- **pgAdmin**: PostgreSQL 可视化管理
- **MinIO Console**: MinIO 可视化管理 (http://localhost:9000)


### D. 测试 API

**使用 curl 测试:**

```bash
# 1. 获取钉钉授权 URL
curl http://localhost:8000/api/auth/dingtalk/login

# 2. 获取当前用户信息
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/auth/me

# 3. 创建合同
curl -X POST http://localhost:8000/api/contracts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试合同",
    "reviewers": [
      {"user_id": "user-1", "role": "法务", "step": "法务初审"}
    ]
  }'

# 4. 获取合同列表
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/contracts?filter=all&page=1&limit=20"

# 5. 上传附件
curl -X POST http://localhost:8000/api/contracts/CONTRACT_ID/attachments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/file.pdf"

# 6. 生成 AI 总结
curl -X POST http://localhost:8000/api/ai/summary/CONTRACT_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**使用 Python requests 测试:**

```python
import requests

BASE_URL = "http://localhost:8000"
token = "YOUR_TOKEN"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 创建合同
response = requests.post(
    f"{BASE_URL}/api/contracts",
    headers=headers,
    json={
        "name": "测试合同",
        "reviewers": [
            {"user_id": "user-1", "role": "法务", "step": "法务初审"}
        ]
    }
)
print(response.json())

# 获取合同列表
response = requests.get(
    f"{BASE_URL}/api/contracts",
    headers=headers,
    params={"filter": "all", "page": 1, "limit": 20}
)
print(response.json())
```

---

## 更新日志

### v0.1.0 (2025-03-01)

**初始版本:**
- ✅ 钉钉 OAuth 授权登录
- ✅ 合同 CRUD 管理
- ✅ 评审和评论功能
- ✅ 文件上传和下载
- ✅ AI 智能总结和顾问
- ✅ WebSocket 实时通信
- ✅ Redis 缓存优化
- ✅ 乐观锁并发控制

---

## 联系方式

如有问题或建议,请联系开发团队:

- **项目地址**: https://github.com/your-org/contract-review
- **问题反馈**: https://github.com/your-org/contract-review/issues
- **邮箱**: dev@example.com

---

**文档最后更新时间**: 2025-03-01
