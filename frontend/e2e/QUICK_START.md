# E2E 测试快速开始指南

## 快速运行测试

### 1. 一键运行所有测试

```bash
# 在 frontend 目录下
npm run test:e2e
```

### 2. 使用可视化界面运行

```bash
npm run test:e2e:ui
```

这会打开 Playwright 的 UI 界面,你可以:
- 选择要运行的测试
- 查看测试执行过程
- 调试失败的测试
- 查看时间线和网络请求

### 3. 在浏览器中运行 (查看测试过程)

```bash
npm run test:e2e:headed
```

### 4. 调试单个测试

```bash
npm run test:e2e:debug
```

## 运行特定测试

### 运行单个测试文件

```bash
# 只运行合同工作流测试
npx playwright test e2e/contract-workflow.spec.ts

# 只运行实时更新测试
npx playwright test e2e/realtime-updates.spec.ts
```

### 运行单个测试用例

```bash
# 使用 -g 参数匹配测试名称
npx playwright test -g "应该完成创建合同到审批的完整流程"
```

### 在特定浏览器中运行

```bash
# 只在 Chrome 中运行
npx playwright test --project=chromium

# 只在 Firefox 中运行
npx playwright test --project=firefox

# 只在 Safari 中运行
npx playwright test --project=webkit
```

## 查看测试结果

### 查看 HTML 报告

```bash
npm run test:report
```

这会在浏览器中打开详细的测试报告,包括:
- 测试执行时间
- 失败的测试
- 截图和视频
- 错误堆栈

### 查看失败测试的截图

失败的测试会自动保存截图到:
```
test-results/
  ├── contract-workflow-spec-ts-...
  │   ├── test-failed-1.png
  │   └── trace.zip
```

### 查看测试视频

失败的测试会自动录制视频到:
```
test-results/
  ├── contract-workflow-spec-ts-...
  │   └── video.webm
```

## 常见问题

### Q: 测试失败,提示找不到元素

**A:** 可能的原因:
1. 前端服务未启动 - 运行 `npm run dev`
2. 后端服务未启动 - 运行 `docker-compose up -d`
3. 页面加载太慢 - 增加等待时间或检查网络

**解决方法:**
```bash
# 使用 headed 模式查看实际页面
npm run test:e2e:headed

# 使用 debug 模式逐步调试
npm run test:e2e:debug
```

### Q: 测试超时

**A:** 增加超时时间:
```typescript
// 在测试文件中
test('测试名称', async ({ page }) => {
  test.setTimeout(60000); // 60秒
  // ...
});
```

或在 `playwright.config.ts` 中全局设置:
```typescript
export default defineConfig({
  timeout: 60000, // 60秒
  // ...
});
```

### Q: 如何跳过某个测试

**A:** 使用 `test.skip`:
```typescript
test.skip('暂时跳过的测试', async ({ page }) => {
  // ...
});
```

### Q: 如何只运行某个测试

**A:** 使用 `test.only`:
```typescript
test.only('只运行这个测试', async ({ page }) => {
  // ...
});
```

### Q: 如何查看测试执行的详细日志

**A:** 使用 `DEBUG` 环境变量:
```bash
DEBUG=pw:api npm run test:e2e
```

## 最佳实践

### 1. 使用 UI 模式开发测试

在编写新测试时,使用 UI 模式可以:
- 实时查看测试执行
- 快速定位选择器
- 调试失败的步骤

```bash
npm run test:e2e:ui
```

### 2. 使用 Playwright Inspector

调试测试时,使用 Inspector 可以:
- 逐步执行测试
- 查看页面状态
- 尝试不同的选择器

```bash
npm run test:e2e:debug
```

### 3. 使用 Trace Viewer

查看失败测试的详细信息:
```bash
npx playwright show-trace test-results/.../trace.zip
```

### 4. 并行运行测试

加快测试执行速度:
```bash
npx playwright test --workers=4
```

### 5. 只运行失败的测试

```bash
npx playwright test --last-failed
```

## 测试环境

### 开发环境

```bash
# 1. 启动后端服务
docker-compose up -d

# 2. 启动前端服务
npm run dev

# 3. 运行测试
npm run test:e2e
```

### CI 环境

测试会自动:
- 启动开发服务器
- 运行所有测试
- 失败时重试 2 次
- 上传测试报告

## 更多资源

- [Playwright 官方文档](https://playwright.dev/)
- [Playwright 测试最佳实践](https://playwright.dev/docs/best-practices)
- [Playwright API 参考](https://playwright.dev/docs/api/class-playwright)
- [Playwright 选择器指南](https://playwright.dev/docs/selectors)

## 需要帮助?

如果遇到问题:
1. 查看 `e2e/README.md` 获取详细文档
2. 使用 `--debug` 模式调试
3. 查看测试报告和截图
4. 联系团队成员
