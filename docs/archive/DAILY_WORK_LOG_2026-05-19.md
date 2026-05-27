# 合同预审看板 — 今日修复与功能迭代记录

> 日期：2026-05-19
> 撰写目的：沉淀修复经验、梳理改动链路，便于后续接手人快速了解全貌

---

## 〇、工作阶段总览

今天的工作分为两个大阶段，涉及两段对话：

| 阶段 | 对话 | 核心内容 | 状态 |
|------|------|----------|------|
| A | 第一段对话 | 项目启动 + 钉钉身份分裂修复 + 小红点遮挡 | ✅ |
| B | 第二段对话 | 四大缺陷修复 → 钉钉通讯录 → 审批闭环 → AI助理改造 | ✅ |

---

## 一、阶段 A：项目启动 + 钉钉身份分裂 + 小红点修复

### A1. 项目启动与环境恢复

- 阅读 project 目录下所有 md 文档，理解项目全貌（合同预审看板系统）
- 通过 docker-compose 启动全部服务（backend / frontend / postgres / redis / minio）
- 确认 ngrok 隧道可达（`underfed-isolating-prolonged.ngrok-free.dev`）

### A2. 钉钉双路径用户身份分裂修复

**问题**：发起合同预审选谢明宇为审批人后，他登录后「待我处理」为空，小红点不显示。

**根因**：同一个真实人在 `users` 表里存了**两条记录**，因为两条代码路径写入 `dingtalk_user_id` 字段的值类型不同：

| 路径 | 文件 | 写入内容 | 记录标记 |
|------|------|----------|----------|
| 通讯录选人 | `dingtalk_contact_service.py` | 钉钉 staff userid（如 `0948275635308251`） | UUID-B |
| OAuth 登录 | `dingtalk_auth_service.py` | 钉钉 unionId（如 `VtNc2a14aPIiE`） | UUID-A |

- 发起人选谢明宇 → `reviews.reviewer_id = UUID-B`
- 谢明宇登录 → JWT `user_id = UUID-A`
- 查「待我处理」：`WHERE reviewer_id = UUID-A AND status = 'pending'` → 永远为空

**修复**：

1. **登录匹配逻辑**（`dingtalk_auth_service.py · sync_user_info`）：改为优先按 `dingtalk_union_id == unionId` 匹配，找到后只更新基础字段不覆盖 `dingtalk_user_id`
2. **合并脚本**（`scripts/merge_duplicate_users.py`）：按 `dingtalk_union_id` 分组，迁移外键 + array_replace + 删重复 + 清缓存，支持 `--dry-run`
3. **手工处理孤立用户**：`dingtalk_union_id` 完全不同的陈敏记录，手工迁 review 并删除

**经验**：
- OAuth 登录和通讯录选人必须共用同一个用户唯一标识（推荐 unionId）
- 第三方登录 upsert 应先按全局唯一 ID 匹配，不要用可变的 userid
- 合并脚本必须支持 `--dry-run`，先预览再执行

### A3. 小红点被「抄送我」按钮遮挡

**根因**：Badge `offset={[10, 0]}` 把红点推到按钮外面，被兄弟元素遮住。

**修复**：`offset={[-2, 6]}`（红点贴在右上角内部）+ `.ant-badge-count` 加 `z-index: 2`

---

## 二、阶段 B 前段：四大缺陷修复

### B1. 「发起合同预审」按钮位置调整

按钮从列表顶部挪到底部，调整 `ContractList.tsx` 中 `contract-list-header` 的 JSX 位置。

### B2. 合同列表不显示发起时间

**根因**：后端返回 `created_at`（snake_case），前端 `Contract.createdAt`（camelCase），axios 没做自动转换。

**修复**：在 `useContracts.ts` queryFn 里做局部字段映射。

### B3. 合同详情 + 附件不显示

同 B2 的字段映射问题，附件字段全部蛇形，前端解构 undefined → "暂无附件"。在 `useContractDetail` hook 里做完整映射。

### B4. 评论提交后不显示

**根因**：CommentInput 不传 `reviewId`/`parentCommentId`，后端存为游离顶层评论，但 `review_service.get_reviews()` 没查游离评论。

**修复**：后端新增 `top_level_comments` 字段 + `_build_comment_tree` 递归组装；前端 Timeline 渲染 `topLevelComments` 列表。

---

## 三、评论/附件/布局迭代

### C1. 附件默认展开

`ContractDetail.tsx` 把状态语义反转为 `collapsedGroups`，进入页面立即可见所有附件。

### C2. 评论时间 8 小时偏差

**根因**：后端 `datetime.utcnow().isoformat()` 无时区后缀，浏览器按本地时区解析。

**修复**：`time.ts` 新增 `normalizeIsoString`，补 `Z` 强制 UTC 解析。

### C3. 回复扁平化 + 小红书风格

- `ReplyList.tsx`：`flattenReplies` 展平回复树，二级以上显示 `回复 @某某`，>2 条子回复折叠
- `ReviewCard.tsx` + `TopLevelCommentCard.tsx`：头像+内容+时间一行布局

### C4. 发起合同预审强制上传附件

`ContractForm.tsx`：附件加 required + 硬校验 + 创建后循环上传 + 三态提示。

---

## 四、钉钉通讯录接入

### D1. 下载按钮不可见

**根因**：`index.html` 没有 fontawesome CDN，`<i class="fas fa-download">` 渲染为空。

**修复**：换成 antd `DownloadOutlined` / `FileTextOutlined`。

### D2. 评审人/抄送人改钉钉通讯录

- 后端新增 `dingtalk_contact_service.py`：取企业 token + BFS 拉成员 + upsert 本地 users 表
- 后端新增 `dingtalk.py`：暴露 `GET /api/dingtalk/users`
- 前端 ContractForm 请求地址换为 `/api/dingtalk/users`

### D3. 钉钉组织树选人弹窗（UserPicker）

- 后端扩展 `fetch_contacts`，暴露 `GET /api/dingtalk/contacts`（含部门树+成员+dept_ids）
- 前端新建 `UserPicker.tsx`：左部门树 / 右成员复选 / 顶部搜索 / 底部已选 tag
- ContractForm 评审人/抄送人 Select 换成 UserPicker 触发器

**踩坑**：钉钉 `listsub` 接口权限开通后返回 dict 数组（非文档说的 int 数组），需防御性类型判断。

---

## 五、审批功能完整闭环

| # | 模块 | 问题 / 需求 | 涉及文件 | 状态 |
|---|------|-------------|----------|------|
| 1 | 合同列表 | "同意"按钮占位过大、弹窗内容不符原型 | ContractCard.tsx/css、QuickApprovalDialog.tsx | ✅ |
| 2 | 合同列表 | "同意"按钮与姓名/时间同行、右对齐 | ContractCard.tsx/css | ✅ |
| 3 | 合同列表 | 列表"同意"弹窗显示"暂无可审批项" | QuickApprovalDialog.tsx（改用 DETAIL 接口） | ✅ |
| 4 | 后端 | 审批接口 UUID ≠ str 比较永远成立 → 400 | review_service.py | ✅ |
| 5 | 合同详情 | 内容过多，加折叠/展开功能 | ContractDetail.tsx/css | ✅ |
| 6 | 合同详情 | 折叠范围调整：收起后仅留标题，默认展开 | ContractDetail.tsx | ✅ |
| 7 | 附件下载 | `<a href>` 不带 Authorization → 401 | useAttachments.ts、ContractDetail.tsx | ✅ |
| 8 | 附件下载 | Content-Disposition 中文文件名 → 500 | routes/files.py | ✅ |
| 9 | AI 助理 | 标题改为"AI 合同预审助理"、加"需要"快捷按钮 | AIAdvisor.tsx/css | ✅ |
| 10 | AI 助理 | 后端新增评审进度+意见汇总结构化分支 | ai_service.py | ✅ |
| 11 | AI 助理 | Message.tsx formatRelativeTime(Date) → 渲染崩溃 | AIAdvisor/Message.tsx | ✅ |

---

## 六、逐项详解

### 1. 合同列表"同意"按钮 UI 规范化

**问题**：原始按钮为大号蓝边胶囊，占满整行，与 htys4.html 原型风格（透明背景文字链接式）严重不符。

**修复**：

- `ContractCard.css` — 按钮改为 `background:none; border:none; font-size:12px; padding:3px 10px; border-radius:16px; color:#1890ff`
- `ContractCard.tsx` — 添加 `<CheckOutlined />` 图标前缀

**经验**：UI 还原应优先参考原型文件（htys4.html）的 CSS 变量与数值，而非凭感觉调整。

---

### 2. 卡片 meta 三栏布局（姓名 — 时间 — 同意）

**需求**：将同意、姓名、时间放在同一行，同意右对齐，时间居中。

**修复**：

```css
.contract-card-meta { display: flex; align-items: center; }
.contract-card-initiator { flex-shrink: 0; max-width: 120px; }
.contract-card-date { flex: 1; text-align: center; }
.contract-card-approve-btn { flex-shrink: 0; margin-left: auto; }
```

**经验**：三栏等分用 `flex:1` 居中 + `margin-left:auto` 右对齐是最稳定的方案，避免 float/grid 引入额外复杂度。

---

### 3. 列表"同意"弹窗"暂无可审批项"

**根因**：`QuickApprovalDialog` 调用 `/api/contracts/{id}/reviews` 接口，该接口过滤掉了所有 `opinion` 为空的 review（即 pending 全部丢失）；且返回字段为 snake_case `reviewer_id`，前端期望 camelCase `reviewerId`。

**修复**：改用 `/api/contracts/{id}`（DETAIL 接口），从 `reviewers` 数组过滤 `status !== 'approved' && userId === currentUser.id`，绕过 reviews 接口的双重缺陷。

**经验**：
- 后端接口设计时务必确认：**pending 状态的记录不应被过滤**，否则前端永远拿不到待审批数据
- 前后端字段命名一致性（snake_case vs camelCase）是高频陷阱，接口文档应明确标注

---

### 4. 审批接口 UUID ≠ str 比较失败 → 400

**根因**：`review_service.py` 第 237 行：

```python
if review.reviewer_id != reviewer_id:  # UUID 对象 != str 永远为 True
    raise ValueError("您没有权限审批此评审项")
```

SQLAlchemy `Mapped[uuid.UUID]` 字段直接与字符串 `!=` 比较结果永远为 True。

**修复**：`str(review.reviewer_id) != str(reviewer_id)`

**经验**：**所有 UUID 字段与外部传入 ID 的比较必须显式转 str**。这是 SQLAlchemy + PostgreSQL + UUID 列型的经典陷阱，应作为编码规范写入团队文档。

---

### 5 & 6. 合同详情页折叠/展开功能

**需求**：信息过载时用户看不到下方评论，需要折叠/展开。最终方案：
- **默认展开**，显示全部内容
- **收起后仅保留合同标题**（描述、附件、评审人、我的待审全部隐藏）
- toggle 条文案："展开详情" / "收起详情"（无括号附加说明）

**实现**：

```tsx
const [expanded, setExpanded] = useState(true);

// header 始终显示
<div className="contract-detail-header">
  <h2>{contract.name}</h2>
  {expanded && contract.description && <p>...</p>}
</div>

// toggle 条
<div className="contract-detail-toggle" onClick={() => setExpanded(v => !v)}>
  {expanded ? '收起详情' : '展开详情'}
</div>

// 折叠区
{expanded && (
  <>
    {/* 附件 + 评审人 + 我的待审 */}
  </>
)}
```

**经验**：
- 折叠边界应由用户确认，不要自行假设"哪些该折哪些不该"
- toggle 条建议用虚线 + 图标，视觉上与正文区隔明显

---

### 7. 附件下载 401（Authorization 丢失）

**根因**：下载按钮用 `<a href={url} target="_blank">` 原生导航，浏览器**不会走 axios 拦截器**，不会自动带 `Authorization: Bearer xxx`，后端中间件直接抛 401。

**修复**：

- `useAttachments.ts` 新增 `downloadAttachment(id, fileName)` 函数，走 `axios.get(url, { responseType: 'blob' })` 拿到 Blob 后用 `URL.createObjectURL + <a download>` 触发本地保存
- `ContractDetail.tsx` 下载按钮改为 `onClick + e.preventDefault()` 拦截原生跳转

**经验**：**任何需要鉴权的文件下载都不能用原生 `<a href>` 跳转**，必须走 axios + blob 方案。这是前后端分离架构的通用陷阱。

---

### 8. Content-Disposition 中文文件名 → 500

**根因**：

```python
f'attachment; filename="{attachment.file_name}"'
```

HTTP/1.1 规范要求 header 值必须是 latin-1 兼容编码，中文字符无法编码 → `UnicodeEncodeError` → 500。

**修复**：新增 `_build_content_disposition(file_name)` 按 RFC 5987 输出双层格式：

```
Content-Disposition: attachment; filename="download"; filename*=UTF-8''%E5%90%88%E5%90%8C.pdf
```

- `filename=` — ASCII fallback（老旧客户端兜底）
- `filename*=UTF-8''<urlencode>` — 现代浏览器识别并显示原始中文文件名

**经验**：HTTP header 中任何可能出现非 ASCII 字符的位置（文件名、自定义 metadata）都必须按 RFC 5987 编码，否则中文场景必崩。

---

### 9 & 10. AI 合同预审助理改造

**需求**：
1. 标题从"AI 合同顾问"改为"AI 合同预审助理"
2. 默认显示"需要我帮你总结一下大家的评论和当前评审进度吗？[需要]"
3. 点"需要"后输出：评审进度（谁已通过/谁待审批）+ 意见汇总（每人什么意见/问题/结论）

**前端改动**：

- `AIAdvisor.tsx` — 标题改、welcome 区改、新增 `handleQuickSummary()` 拼详细 prompt
- `AIAdvisor.css` — 新增 `.welcome-quick-action` 蓝色下划线链接样式

**后端改动**：

`ai_service.py` 新增 `_summarize_progress_and_opinions()` 方法：
- 拉取全部 Review + Comment，按 step 排序
- 按 author 分组 Comment，将评审意见 + 评论合并输出
- 结构化格式：`📋 进度` → `✅ 已通过` → `⏳ 待审批` → `💬 意见汇总` → `📌 一句话总结`

**经验**：
- 后端 AI 问答如果用关键词分支，必须覆盖所有前端 prompt 的关键词，否则走默认分支返回无意义内容
- 结构化文本输出比大模型自由生成更可控、更稳定，适合这种确定性业务场景

---

### 11. AI 助理 Message 组件渲染崩溃

**根因**：`Message.tsx` 第 45 行：

```tsx
formatRelativeTime(new Date(message.timestamp))  // ❌ 传入 Date 对象
```

而 `formatRelativeTime(dateString: string)` 期望 ISO 字符串。Date 对象经 `normalizeIsoString` 处理后产生非法字符串 → `new Date(...)` = Invalid Date → fallback 返回 Date 对象本身 → React 抛 "Objects are not valid as a React child" → ErrorBoundary 兜底显示"组件加载失败"。

**修复**：`formatRelativeTime(message.timestamp)`（`message.timestamp` 本就是 ISO 字符串，无需再 `new Date()`）

**经验**：
- **TypeScript 函数签名与实际调用必须匹配**。`formatRelativeTime(s: string)` 被传入 Date 对象是类型安全的假象（tsx 不做运行时检查）
- ErrorBoundary 的兜底文案（"组件加载失败"）容易误导为网络问题，实际可能是渲染异常。调试时应先看浏览器 Console，而非盲目查后端日志

---

## 七、关键经验沉淀

### 3.1 高频陷阱速查表

| 陷阱 | 表现 | 修复 | 适用场景 |
|------|------|------|----------|
| UUID ≠ str | 权限校验永远失败 | `str(a) != str(b)` | SQLAlchemy UUID 列 vs 路径参数/请求体 |
| 原生 `<a>` 不带 Token | 401 / 乱码 JSON | axios + blob + createObjectURL | 所有需鉴权的文件下载 |
| Content-Disposition 中文 | 500 latin-1 编码错误 | RFC 5987 `filename*=UTF-8''` | HTTP header 含非 ASCII |
| snake_case vs camelCase | 前端解构 undefined | 统一转换层或改用 DETAIL 接口 | 前后端字段映射 |
| Date 对象当 React child | 白屏 / 组件加载失败 | 确保 JSX 中只渲染 string/number | formatRelativeTime 等 |
| pending 记录被接口过滤 | 前端拿不到待审批数据 | 不过滤 opinion 为空的记录 | 列表查询接口 |
| 钉钉双路径身份分裂 | 待我处理为空 / 小红点不显示 | 登录按 unionId 匹配 + 合并脚本 | OAuth 登录 vs 通讯录 upsert |
| 钉钉 listsub 返回类型 | 运行时 TypeError | 防御性 isinstance 判断 | 第三方 API 文档与实际不符 |

### 3.2 调试方法论

1. **后端 500 → 先看 docker logs**（不要猜），关注 `ExceptionGroup` / `Traceback` 行
2. **前端"组件加载失败" → 先看浏览器 Console**，区分网络错误 vs 渲染异常
3. **乱码 JSON → 检查 Content-Type / 编码**，常见于原生导航直接渲染后端错误响应
4. **接口 200 但前端异常 → 检查数据契约**（字段名/类型/嵌套层级）

### 3.3 代码规范建议

1. 所有 UUID 字段与外部 ID 的比较，统一 `str()` 后再比较
2. 文件下载一律走 axios + blob，禁止 `<a href>` 直接跳转需鉴权的 URL
3. HTTP header 中出现用户输入的文本，一律走 RFC 5987 或 URL-encode
4. 前端调用工具函数时，严格匹配函数签名的参数类型，不要"包装后再传"
5. 后端查询接口不应过滤 pending 状态的记录（除非业务明确要求）

---

## 八、文件变更清单

### 前端

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/components/ContractList/ContractCard.tsx` | 修改 | 添加 CheckOutlined 图标、按钮挪进 meta 行 |
| `src/components/ContractList/ContractCard.css` | 修改 | 按钮改文字链接式、meta 改 flex 三栏 |
| `src/components/ContractList/QuickApprovalButton.tsx` | 修改 | 默认意见"同意并确认" |
| `src/components/QuickApprovalDialog/QuickApprovalDialog.tsx` | 修改 | 改用 DETAIL 接口、标题/宽度/默认值精简 |
| `src/components/ContractDetail/ContractDetail.tsx` | 修改 | 折叠/展开 state + toggle + 下载改 axios blob |
| `src/components/ContractDetail/ContractDetail.css` | 修改 | 新增 .contract-detail-toggle 样式 |
| `src/components/AIAdvisor/AIAdvisor.tsx` | 修改 | 标题改名、welcome 区改、新增 handleQuickSummary |
| `src/components/AIAdvisor/AIAdvisor.css` | 修改 | 新增 .welcome-quick-action 样式 |
| `src/components/AIAdvisor/Message.tsx` | 修改 | formatRelativeTime 去掉 new Date() 包裹 |
| `src/hooks/useAttachments.ts` | 修改 | 新增 downloadAttachment 函数 |
| `src/hooks/useContracts.ts` | 修改 | 局部字段映射（snake_case → camelCase） |
| `src/components/ContractList/ContractList.tsx` | 修改 | 按钮位置调整 + handleApprove 接通 |
| `src/components/ContractList/FilterBar.tsx` | 修改 | Badge offset + z-index 修复 |
| `src/components/ContractList/FilterBar.css` | 修改 | .ant-badge-count z-index |
| `src/components/ContractForm/ContractForm.tsx` | 修改 | 强制附件 + UserPicker 触发器 + 钉钉接口 |
| `src/components/Timeline/ReplyList.tsx` | 修改 | 扁平化 + 小红书风格 + 折叠规则 |
| `src/components/Timeline/ReplyList.css` | 修改 | 去缩进 + 单行布局 |
| `src/components/Timeline/ReviewCard.tsx` | 修改 | 头像+内容+时间同行 |
| `src/components/Timeline/TopLevelCommentCard.tsx` | 新建 | 顶层游离评论独立卡片 |
| `src/components/Timeline/Timeline.tsx` | 修改 | 渲染 topLevelComments |
| `src/components/UserPicker/UserPicker.tsx` | 新建 | 钉钉组织树选人弹窗 |
| `src/utils/time.ts` | 修改 | 新增 normalizeIsoString 修时区偏差 |

### 后端

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `app/services/review_service.py` | 修改 | UUID 比较 str() 修复；新增 _build_comment_tree 递归评论树组装；新增 top_level_comments 查询 |
| `app/services/ai_service.py` | 修改 | 新增评审进度+意见汇总结构化分支 |
| `app/services/dingtalk_auth_service.py` | 修改 | sync_user_info 改为优先按 unionId 匹配 |
| `app/services/dingtalk_contact_service.py` | 新建 | 钉钉通讯录拉取 + upsert + 部门树 |
| `app/services/contract_service.py` | 修改 | 列表接口新增 hasPendingReview 字段 |
| `app/routes/files.py` | 修改 | 新增 _build_content_disposition (RFC 5987) |
| `app/routes/dingtalk.py` | 新建 | 暴露 GET /api/dingtalk/users 和 /contacts |
| `app/routes/contracts.py` | 修改 | reviewers_data 透出 userId 字段 |
| `app/main.py` | 修改 | 注册 dingtalk 路由 |
| `scripts/merge_duplicate_users.py` | 新建 | 钉钉双路径用户合并脚本 |

---

## 九、架构参考

```
┌─────────────────────────────────────────────────────┐
│                    前端 (React 18)                    │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ContractCard│  │ContractDetail│  │   AIAdvisor      │  │
│  │ 同意按钮   │  │ 折叠/下载   │  │ 预审助理 + 汇总   │  │
│  └─────┬─────┘  └─────┬─────┘  └────────┬──────────┘  │
│        │              │                  │             │
│  QuickApprovalDialog  │          useAIAdvisor          │
│        │         downloadAttachment()    │             │
│        │              │                  │             │
│  ──────┴──────────────┴──────────────────┴──────────  │
│              axios (Authorization Bearer)             │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────┐
│                  后端 (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │reviews.py │  │ files.py │  │   ai_service.py   │  │
│  │ 审批接口   │  │ RFC 5987 │  │ 进度+意见汇总     │  │
│  └─────┬─────┘  └─────┬─────┘  └────────┬──────────┘  │
│        │              │                  │             │
│  review_service   MinIO stream     _summarize_progress │
│  UUID str()修复   Content-Disposition  结构化输出      │
└─────────────────────────────────────────────────────┘
```

---

## 十、阶段 C：小红点遮挡修复 + Docker 构建缓存踩坑

> 时间：阶段 A 钉钉身份分裂修复完成、用户重新登录验证后追加

### C1. 现象

陈敏重登后「待我处理」按钮上小红点 `2` 已经出来了，但红点**被右侧的「抄送我」按钮压住了**，只能看到一小块。

### C2. 根因

[`FilterBar.tsx`](file:///Users/cm/Documents/kiro/project/frontend/src/components/ContractList/FilterBar.tsx) 把 Badge 的 `offset` 设成 `[10, 0]`：

```tsx
<Badge count={pendingCount} offset={[10, 0]}>
  <Button>待我处理</Button>
</Badge>
```

- `offset=[10, 0]` 表示**红点在按钮右上角的基础上再向右偏移 10px**，直接溢出到了按钮外面
- Antd Badge 的 `count` 元素是 `position: absolute`，默认 `z-index: auto`
- DOM 流中「抄送我」按钮在「待我处理」之后渲染，按 stacking context 规则**后渲染的兄弟节点会盖住前一个节点的绝对定位子元素**

两个因素叠加 → 红点被遮。

### C3. 修复

两处一起改，一个治位置、一个兜底层级：

**[FilterBar.tsx](file:///Users/cm/Documents/kiro/project/frontend/src/components/ContractList/FilterBar.tsx#L33)**：

```diff
- <Badge count={pendingCount} offset={[10, 0]}>
+ <Badge count={pendingCount} offset={[-2, 6]}>
```

红点贴在按钮右上角**内部偏一点**，不再溢出到兄弟元素的覆盖区域。

**[FilterBar.css](file:///Users/cm/Documents/kiro/project/frontend/src/components/ContractList/FilterBar.css)**：

```css
.filter-bar .ant-badge-count {
  background-color: #ff4d4f;
  box-shadow: 0 0 0 1px #fff;
  z-index: 2;  /* 防止后续按钮遮挡红点 */
}
```

### C4. 部署踩坑：Docker 构建缓存命中

用户使用的是 **生产部署版本**（`docker-compose.yml`），前端服务定义：

```yaml
frontend:
  build: { context: ./frontend, dockerfile: Dockerfile }
  # 没有 ./frontend:/app 卷挂载
```

Dockerfile 是多阶段构建：builder 跑 `npm run build` 产出 `dist/`，再 COPY 到 nginx 镜像。**没有源码挂载**，所以 `docker restart` 完全无效，必须 `build + up -d`。

第一次用 `docker compose build frontend`，输出全是 `CACHED`：

```
#9 [builder 6/6] RUN npm run build       CACHED
#10 [builder 5/6] COPY . .                CACHED
```

BuildKit 在判断 `COPY . .` 这一步是否命中缓存时，**虽然源文件改了，但因为某些状态原因仍命中了上一次的缓存层**（具体可能与 .dockerignore、文件 mtime、BuildKit 内部哈希有关），导致新代码根本没进镜像。

**解决**：强制 `--no-cache` 重建：

```bash
docker compose build --no-cache frontend
docker compose up -d frontend
```

第二次构建产物哈希变了（`index-D-3dqdB1.js` / `index-8r5s2QIV.css`），容器 Recreate 后新代码生效。

### C5. 经验沉淀

| 类别 | 要点 |
|------|------|
| **Antd Badge 定位** | Badge `offset` 的语义是「在默认右上角基础上的额外偏移」，正值会往外推，**容器有兄弟元素时正向 offset 几乎必踩遮挡坑**。常用值：`[-2, 6]`（贴角内嵌）、`[0, 0]`（紧贴角）、`[4, -4]`（明显外凸，仅在容器孤立时使用） |
| **Antd Badge 兜底** | `.ant-badge-count` 加 `z-index: 2` 是廉价兜底，避免后续布局调整再次踩坑 |
| **Docker 部署模式判断** | 改前端代码后要重启容器时，**必先看 docker-compose 是哪种模式**：① 有 `./frontend:/app` 卷挂载（dev 模式）→ Vite HMR 自动生效；② Dockerfile 多阶段构建（prod 模式）→ 必须 rebuild |
| **Docker 构建缓存** | `docker compose build` 不一定能识别源码改动，**只要怀疑代码没生效就直接 `--no-cache`**，比反复 debug 「为什么我的改动没上去」高效得多 |
| **强制刷新浏览器** | rebuild 后浏览器仍可能拿旧的 hash 化静态资源，告知用户用 `Cmd+Shift+R` / 「清空缓存并硬性重新加载」，避免「已经部署了但还是老样子」的二次困惑 |

### C6. 文件变更追加清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `frontend/src/components/ContractList/FilterBar.tsx` | 修改 | Badge `offset` 从 `[10, 0]` 改为 `[-2, 6]`，红点收回按钮内部 |
| `frontend/src/components/ContractList/FilterBar.css` | 修改 | `.ant-badge-count` 增加 `z-index: 2` 兜底防遮挡 |

### C7. 部署命令记录（供下次参考）

```bash
# 仅改前端代码 + prod 模式部署
cd /Users/cm/Documents/kiro/project
docker compose build --no-cache frontend
docker compose up -d frontend

# 验证
docker ps --filter name=contract_review_frontend --format '{{.Names}}\t{{.Status}}'
```

---

## 十一、今日工作收尾

经过阶段 A → B → C 的串联修复，「待我处理」从「**根本看不到**」到「**看得到但红点被遮**」再到「**红点干净停在右上角**」，整条链路（OAuth 登录 → 用户身份合并 → 列表查询 → 红点显示）已闭环。

后续如果再出现类似「分配了任务但看不到」的问题，按以下顺序排查即可：

1. **DB 层**：`SELECT id, dingtalk_user_id, dingtalk_union_id, name FROM users WHERE name = '某某'` 看是否仍有重复
2. **JWT 层**：浏览器 Console 解 token 看 `user_id` 与 DB 匹配的是哪一条
3. **缓存层**：`docker exec contract_review_redis redis-cli FLUSHDB`
4. **前端层**：F12 看 `/api/contracts/pending-count` 响应数字、再看 Badge 是否被遮
