# 需求文档 - 合同预审看板系统

## 简介

合同预审看板系统是一个协作平台,用于管理合同的预审流程。系统支持合同的创建、评审、讨论和审批,并提供AI辅助功能帮助用户快速了解合同状态和关键问题。用户角色包括销售、法务、财务、业务、运营、人事等部门人员。

## 术语表

- **System**: 合同预审看板系统
- **Contract**: 合同,包含名称、描述、附件、评审人、抄送人等信息
- **Review**: 评审意见,由评审人对合同提出的审核意见
- **Reviewer**: 评审人,被指定对合同进行审核的用户
- **CC_User**: 抄送人,需要知晓合同进展但不需要审核的用户
- **Attachment**: 附件,上传到合同的文件
- **Version**: 附件版本,同一附件文件的不同版本
- **Comment**: 评论,用户对评审意见的回复或讨论
- **Timeline**: 时间线,按时间顺序展示所有评审意见和评论的区域
- **AI_Summary**: AI智能总结,自动生成的审批进度和关键问题摘要
- **AI_Advisor**: AI合同顾问,提供法务意见、风险项等咨询的聊天机器人
- **Status**: 合同状态,包括"进行中"和"已完成"
- **Approval_Status**: 审批状态,包括"✅"(已通过)、"评审中"、"待处理"
- **Current_User**: 当前登录用户

## 需求

### 需求 1: 合同列表管理

**用户故事:** 作为用户,我想查看和筛选合同列表,以便快速找到需要处理的合同。

#### 验收标准

1. THE System SHALL 在左侧边栏显示所有合同列表
2. WHEN 用户点击筛选按钮, THE System SHALL 根据选择的筛选条件(全部/进行中/已完成/待我处理/抄送我)过滤合同列表
3. WHEN 用户在搜索框输入关键词, THE System SHALL 实时过滤显示包含该关键词的合同(按合同名称或发起人匹配)
4. THE System SHALL 为每个合同卡片显示合同名称、发起人、日期和状态标签
5. WHEN 用户选择"待我处理"筛选条件, THE System SHALL 仅显示包含当前用户待处理评审项的合同
6. WHEN 用户选择"抄送我"筛选条件, THE System SHALL 仅显示抄送给当前用户的合同
7. THE System SHALL 在"待我处理"筛选按钮上显示待处理数量徽章
8. WHEN 用户点击合同卡片, THE System SHALL 将该合同设置为当前选中合同并高亮显示

### 需求 2: 合同详情展示

**用户故事:** 作为用户,我想查看合同的详细信息,以便了解合同内容和审核状态。

#### 验收标准

1. WHEN 用户选中一个合同, THE System SHALL 在中间区域显示合同标题、描述和附件信息
2. THE System SHALL 显示合同的所有评审人列表
3. THE System SHALL 区分显示已审核评审人和待审核评审人
4. THE System SHALL 显示需审核人总数统计
5. WHEN 合同没有附件, THE System SHALL 显示"暂无附件"提示
6. WHEN 合同有附件, THE System SHALL 按文件名分组显示所有附件及其版本

### 需求 3: 附件版本管理

**用户故事:** 作为用户,我想上传和管理合同附件的多个版本,以便跟踪文件的修改历史。

#### 验收标准

1. THE System SHALL 支持上传PDF、DOC、DOCX、PPTX、XLSX格式的附件文件
2. THE System SHALL 限制单个附件文件大小不超过20MB
3. WHEN 用户上传同名文件, THE System SHALL 自动创建该文件的新版本
4. THE System SHALL 按文件名分组显示附件,每组显示版本数量
5. THE System SHALL 为每个附件版本显示版本号、上传时间和上传人
6. THE System SHALL 按时间倒序排列同一文件的多个版本
7. THE System SHALL 为最新版本标记"最新"标签
8. THE System SHALL 按最新上传时间倒序排列不同文件组

### 需求 4: 评审时间线

**用户故事:** 作为用户,我想查看所有评审意见和讨论,以便了解合同的审核进展和问题。

#### 验收标准

1. THE System SHALL 在时间线区域按时间倒序显示所有评审意见
2. THE System SHALL 仅显示包含有效意见或回复的评审记录
3. THE System SHALL 过滤掉"待评审"、"待评审,请反馈"等占位文本的空评审记录
4. WHEN 评审意见没有文本但有回复, THE System SHALL 显示"参与了讨论"作为默认文本
5. THE System SHALL 为每条评审意见显示评审人头像、意见内容和时间
6. THE System SHALL 支持用户对评审意见点赞
7. THE System SHALL 显示每条评审意见的点赞数量
8. WHEN 时间在1小时内, THE System SHALL 显示相对时间(如"刚刚"、"5分钟前")
9. WHEN 时间超过30天, THE System SHALL 显示具体日期

### 需求 5: 评论和回复功能

**用户故事:** 作为用户,我想对评审意见进行评论和回复,以便与其他评审人讨论合同问题。

#### 验收标准

1. THE System SHALL 支持用户在底部输入框添加新评论
2. WHEN 用户按回车键或点击发送按钮, THE System SHALL 提交评论并显示在时间线顶部
3. THE System SHALL 支持用户回复任何评审意见
4. THE System SHALL 支持用户回复其他用户的回复(嵌套回复)
5. THE System SHALL 为每条回复显示回复人头像、回复内容和时间
6. THE System SHALL 支持用户对回复点赞
7. WHEN 评审意见的回复数量超过2条, THE System SHALL 默认折叠显示前2条回复
8. WHEN 回复被折叠, THE System SHALL 显示"共N条回复"按钮供用户展开
9. WHEN 用户点击展开按钮, THE System SHALL 显示所有回复并将按钮文本改为"收起"

### 需求 6: AI智能总结

**用户故事:** 作为用户,我想查看AI生成的合同审批总结,以便快速了解审批进度和关键问题。

#### 验收标准

1. WHEN 合同有评审意见, THE System SHALL 在时间线顶部显示AI智能总结区域
2. THE System SHALL 在AI总结中显示审批进度状态(已全部通过/审批进行中)
3. THE System SHALL 在AI总结中显示已完成审批的人数和总人数
4. THE System SHALL 在AI总结中显示评审意见总数
5. THE System SHALL 提取并显示最多3个关键问题(包含"建议"、"需要"、"问题"、"风险"、"隐患"等关键词的意见)
6. WHEN 关键问题有回复, THE System SHALL 在问题下方显示最新的解决方案
7. WHEN 所有评审人都已通过, THE System SHALL 将状态标记为"已全部通过"
8. WHEN 存在待审核评审人, THE System SHALL 将状态标记为"审批进行中"

### 需求 7: AI合同顾问

**用户故事:** 作为用户,我想向AI顾问询问合同相关问题,以便快速获取法务意见、风险项等信息。

#### 验收标准

1. THE System SHALL 在右侧显示AI合同顾问聊天界面
2. THE System SHALL 在聊天界面底部显示当前选中的合同名称
3. WHEN 用户输入问题并发送, THE System SHALL 在聊天区域显示用户消息
4. WHEN 用户询问包含"法务"关键词的问题, THE System SHALL 返回所有法务角色的评审意见
5. WHEN 用户询问包含"风险"或"未确认"关键词的问题, THE System SHALL 返回所有状态为"评审中"的评审项
6. WHEN 用户询问包含"待我处理"关键词的问题, THE System SHALL 返回当前用户所有待处理的评审任务
7. WHEN 用户询问其他问题, THE System SHALL 返回合同评审数量和可询问的问题类型提示
8. THE System SHALL 支持用户通过回车键发送问题

### 需求 8: 发起合同预审

**用户故事:** 作为用户,我想创建新的合同预审,以便启动合同审批流程。

#### 验收标准

1. WHEN 用户点击"发起合同预审"按钮, THE System SHALL 显示合同创建对话框
2. THE System SHALL 要求用户输入合同名称(必填)
3. THE System SHALL 允许用户输入合同描述(可选)
4. THE System SHALL 允许用户从预设列表中选择多个评审人
5. THE System SHALL 允许用户从预设列表中选择多个抄送人
6. THE System SHALL 允许用户上传附件文件
7. WHEN 用户未填写合同名称, THE System SHALL 显示错误提示并阻止提交
8. WHEN 用户提交合同, THE System SHALL 创建新合同并设置状态为"进行中"
9. WHEN 用户提交合同, THE System SHALL 为每个选中的评审人创建待处理的评审任务
10. WHEN 用户提交合同, THE System SHALL 将当前用户设置为合同发起人
11. WHEN 用户提交合同, THE System SHALL 清空表单并关闭对话框
12. WHEN 用户提交合同, THE System SHALL 刷新合同列表并更新待处理徽章

### 需求 9: 快速审批

**用户故事:** 作为评审人,我想快速同意待处理的评审项,以便高效完成审批工作。

#### 验收标准

1. WHEN 合同有当前用户的待处理评审项, THE System SHALL 在合同卡片下方显示"同意"按钮
2. WHEN 合同没有当前用户的待处理评审项, THE System SHALL 不显示"同意"按钮
3. WHEN 用户点击"同意"按钮且只有一个待处理项, THE System SHALL 直接显示同意确认对话框
4. WHEN 用户点击"同意"按钮且有多个待处理项, THE System SHALL 显示待处理项选择列表
5. WHEN 用户在选择列表中点击某个待处理项, THE System SHALL 显示该项的同意确认对话框
6. THE System SHALL 在同意确认对话框中预填"同意并通过"文本
7. WHEN 用户确认同意, THE System SHALL 将评审项状态更新为"✅"
8. WHEN 用户确认同意, THE System SHALL 在时间线中添加新的评论记录
9. WHEN 用户确认同意, THE System SHALL 刷新时间线、合同列表和待处理徽章

### 需求 10: 用户界面交互

**用户故事:** 作为用户,我想获得流畅的界面交互体验,以便高效使用系统。

#### 验收标准

1. WHEN 用户将鼠标悬停在合同卡片上, THE System SHALL 改变卡片背景色提供视觉反馈
2. WHEN 用户选中合同, THE System SHALL 为该合同卡片添加左侧蓝色边框和高亮背景
3. WHEN 用户将鼠标悬停在按钮上, THE System SHALL 改变按钮背景色或颜色
4. WHEN 用户将鼠标悬停在头像上, THE System SHALL 显示用户名称的工具提示
5. THE System SHALL 为所有输入框提供占位符文本提示
6. WHEN 输入框获得焦点, THE System SHALL 改变边框颜色提供视觉反馈
7. THE System SHALL 使用图标增强按钮和标签的可识别性
8. THE System SHALL 使用不同颜色区分不同状态(进行中/已完成/已通过/待处理)
9. WHEN 用户点击取消按钮, THE System SHALL 关闭对话框并不保存更改
10. THE System SHALL 在页面底部状态栏显示当前用户名称

### 需求 11: 数据持久化和状态管理

**用户故事:** 作为用户,我想系统能够保存我的操作,以便数据不会丢失。

#### 验收标准

1. WHEN 用户添加评论, THE System SHALL 将评论数据添加到对应合同的评审记录中
2. WHEN 用户点赞, THE System SHALL 更新点赞计数并保存状态
3. WHEN 用户添加回复, THE System SHALL 将回复数据添加到对应评审意见的回复列表中
4. WHEN 用户上传附件, THE System SHALL 将附件信息添加到合同的附件列表中
5. WHEN 用户创建合同, THE System SHALL 生成唯一的合同ID
6. WHEN 用户同意评审, THE System SHALL 更新评审项的审批状态
7. THE System SHALL 为每条新增的评论和回复自动生成时间戳
8. THE System SHALL 为每条新增的评论和回复自动设置创建人为当前用户

### 需求 12: 响应式布局

**用户故事:** 作为用户,我想在不同设备上使用系统,以便随时随地处理合同审批。

#### 验收标准

1. THE System SHALL 使用三栏布局(左侧合同列表、中间详情和时间线、右侧AI顾问)
2. THE System SHALL 设置左侧合同列表宽度为280px
3. THE System SHALL 设置右侧AI顾问宽度为340px
4. THE System SHALL 使中间区域自适应剩余宽度
5. THE System SHALL 为所有可滚动区域启用垂直滚动
6. THE System SHALL 固定顶部标题栏和底部状态栏
7. THE System SHALL 在移动设备上禁用用户缩放(user-scalable=no)
8. THE System SHALL 使用flexbox布局确保内容不溢出视口

