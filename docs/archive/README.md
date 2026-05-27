# 历史文档归档

本目录存放项目早期开发过程中产生的状态记录、修复笔记、任务打卡等文档，绝大多数已过时或被新文档覆盖，保留作为历史上下文参考。

## 当前权威信息源

请优先查阅以下文档（按重要程度排序）：

- `.kiro/steering/project-overview.md` — 项目总览 + 关键约定（每次会话自动加载）
- `CLAUDE.md` — 技术栈、命令、踩坑提醒
- `README.md` — 项目入口
- `.kiro/specs/` — 三个功能规范（requirements / design / tasks）

## 本目录内容分类

### 部署与运维（仍有参考价值）
- `DEPLOYMENT_GUIDE.md` — 部署指南
- `DEPLOY_BIND_MOUNT_LESSON.md` — Docker bind mount 踩坑
- `DOCKER_DEPLOYMENT.md` / `DOCKER_SETUP.md` — Docker 配置
- `NGINX_SETUP.md` — Nginx 配置
- `NGROK_SETUP.md` — ngrok 内网穿透
- `经验沉淀_腾讯云部署与域名迁移.md` — 腾讯云部署经验
- `钉钉授权登录实现指南.md` / `钉钉授权登录实现指南_项目版.md` — 钉钉 OAuth 实现

### 用户与测试
- `USER_MANUAL.md` — 用户手册
- `TEST_GUIDE.md` — 测试指南

### 开发记录
- `DAILY_WORK_LOG_2026-05-19.md` — 一次大改的实战记录（很多约定已抽到 steering）
- `FEATURE_我发起的筛选.md` — 单个功能改动的设计

### 状态打卡（多数已过时）
- `BACKEND_COMPLETE.md` / `CURRENT_STATUS.md` / `FINAL_STATUS*.md` / `IMPLEMENTATION_PROGRESS.md`
- `START_HERE.md` / `QUICK_START.md` / `SUCCESS.md`

### 历史 bug 修复记录
- `*_FIXED.md` 系列（API_500、CALLBACK_LOOP、LOGIN、SYSTEM 等）
- `TOKEN_DEBUG.md`

### 任务完成报告
- `TASK_*_COMPLETE.md` 系列
- `TASK_1.3_SUMMARY.md` / `CONTRACT_DETAIL_IMPLEMENTATION.md` 等

如果发现某条历史教训没出现在 steering 里、且仍然有效，请补充到 `.kiro/steering/project-overview.md`。
