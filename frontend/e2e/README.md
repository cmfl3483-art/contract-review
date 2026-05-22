# 端到端测试 (End-to-End Tests)

本目录包含使用 Playwright 编写的端到端测试,用于验证合同预审看板系统的完整用户流程。

## 测试文件

### 1. contract-workflow.spec.ts
测试合同预审的核心工作流程:
- ✅ 创建合同流程
- ✅ 查看合同详情
- ✅ 添加评论
- ✅ 快速审批
- ✅ 筛选和搜索功能
- ✅ AI顾问问答
- ✅ 点赞功能

### 2. realtime-updates.spec.ts
测试 WebSocket 实时更新功能:
- ✅ 多用户实时评论同步
- ✅ 实时点赞更新
- ✅ 实时审批状态更新
- ✅ 实时待办数量更新

### 3. file-upload.spec.ts
测试文件上传和附件管理:
- ✅ 上传附件
- ✅ 查看附件版本
- ✅ 上传同名文件创建新版本
- ✅ 下载附件
- ✅ 文件类型验证

### 4. ai-features.spec.ts
测试 AI 功能:
- ✅ AI智能总结显示
- ✅ AI顾问问答 (法务意见、风险项、待办任务)
- ✅ 多轮对话
- ✅ 关键问题提取
- ✅ 错误处理

## 运行测试

### 前置条件

1. 确保已安装依赖:
```bash
npm install
```

2. 确保 Playwright 浏览器已安装:
```bash
npx playwright install
```

3. 确保后端服务正在运行:
```bash
# 在项目根目录
docker-compose up -d
```

### 运行所有测试

```bash
npm run test:e2e
```

### 运行特定测试文件

```bash
# 只运行合同工作流测试
npx playwright test e2e/contract-workflow.spec.ts

# 只运行实时更新测试
npx playwright test e2e/realtime-updates.spec.ts

# 只运行文件上传测试
npx playwright test e2e/file-upload.spec.ts

# 只运行AI功能测试
npx playwright test e2e/ai-features.spec.ts
```

### 使用 UI 模式运行

UI 模式提供可视化界面,方便调试:

```bash
npm run test:e2e:ui
```

### 使用 headed 模式运行

在有界面的浏览器中运行测试:

```bash
npm run test:e2e:headed
```

### 调试模式

逐步调试测试:

```bash
npm run test:e2e:debug
```

### 查看测试报告

```bash
npm run test:report
```

## 测试配置

测试配置位于 `playwright.config.ts` 文件中:

- **baseURL**: `http://localhost:5173` (前端开发服务器)
- **浏览器**: Chromium, Firefox, WebKit
- **超时**: 默认 30 秒
- **重试**: CI 环境重试 2 次
- **截图**: 失败时自动截图
- **视频**: 失败时保留视频

## 测试数据

### 测试文件

测试文件位于 `test-files/` 目录:
- `sample.pdf` - 测试 PDF 文件
- `sample.docx` - 测试 Word 文档
- `invalid.txt` - 用于测试文件类型验证

这些文件会在测试运行时自动创建。

### 测试用户

由于系统使用钉钉 OAuth 登录,E2E 测试需要:
1. 配置测试环境的钉钉应用
2. 或使用 mock 登录状态
3. 或在测试环境中设置测试用户的 token

## 注意事项

### 1. 登录状态

当前测试假设用户已登录。在实际环境中,可能需要:
- 在 `beforeEach` 中设置测试用户的 token
- 使用测试环境的登录方式
- Mock 钉钉 OAuth 登录流程

### 2. 数据隔离

测试应该使用独立的测试数据库,避免影响生产数据:
- 使用 Docker Compose 的测试配置
- 在测试前清理数据库
- 使用唯一的测试数据标识 (如时间戳)

### 3. 异步操作

测试中使用了 `waitForTimeout` 来等待异步操作完成。在实际环境中,建议:
- 使用 `waitForSelector` 等待特定元素出现
- 使用 `waitForResponse` 等待 API 响应
- 使用 `waitForLoadState` 等待页面加载完成

### 4. 选择器稳定性

测试使用了多种选择器策略:
- `data-testid` 属性 (推荐)
- 文本内容 (适用于静态文本)
- CSS 类名 (可能因样式变化而失效)

建议在组件中添加 `data-testid` 属性以提高测试稳定性。

## 持续集成

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## 测试覆盖

根据设计文档,E2E 测试应该覆盖以下核心用户流程:

- ✅ 用户登录
- ✅ 创建合同
- ✅ 上传附件
- ✅ 添加评论
- ✅ 快速审批
- ✅ 筛选和搜索
- ✅ AI顾问问答
- ✅ 实时更新

目标: **100% 核心用户流程覆盖**

## 故障排查

### 测试失败

1. 检查服务是否正在运行:
```bash
docker-compose ps
```

2. 检查前端开发服务器:
```bash
curl http://localhost:5173
```

3. 检查后端 API:
```bash
curl http://localhost:8000/api/health
```

### 超时错误

如果测试经常超时:
- 增加 `playwright.config.ts` 中的 `timeout` 配置
- 检查网络连接
- 检查服务器性能

### 选择器错误

如果选择器找不到元素:
- 使用 `--headed` 模式查看实际页面
- 使用 `--debug` 模式逐步调试
- 检查元素是否已渲染
- 检查选择器是否正确

## 参考资料

- [Playwright 官方文档](https://playwright.dev/)
- [Playwright 最佳实践](https://playwright.dev/docs/best-practices)
- [Playwright API 参考](https://playwright.dev/docs/api/class-playwright)
