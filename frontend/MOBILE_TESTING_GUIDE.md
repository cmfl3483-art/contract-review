# 移动端测试指南

## 测试概述

本文档提供合同预审看板系统的移动端测试指南,包括测试方法、测试用例和验收标准。

## 测试环境

### 推荐测试设备

**移动设备:**
- iPhone 12/13/14 (iOS 15+)
- iPhone SE (小屏幕测试)
- Samsung Galaxy S21/S22 (Android 11+)
- Google Pixel 6/7 (Android 12+)

**平板设备:**
- iPad Air/Pro (iPadOS 15+)
- Samsung Galaxy Tab S8

**浏览器:**
- Safari (iOS)
- Chrome (Android/iOS)
- Firefox (Android)
- Samsung Internet (Android)

### 开发者工具测试

如果没有真实设备,可以使用浏览器开发者工具:

**Chrome DevTools:**
1. 打开 Chrome 浏览器
2. 按 F12 打开开发者工具
3. 点击设备工具栏图标 (Ctrl+Shift+M / Cmd+Shift+M)
4. 选择设备型号或自定义尺寸

**常用测试尺寸:**
- iPhone SE: 375 x 667
- iPhone 12/13: 390 x 844
- iPhone 14 Pro Max: 430 x 932
- Samsung Galaxy S20: 360 x 800
- iPad: 768 x 1024
- iPad Pro: 1024 x 1366

## 测试用例

### 1. 视口配置测试 (需求 12.7)

**测试目标:** 验证移动设备上禁用用户缩放

**测试步骤:**
1. 在移动设备上打开应用
2. 尝试使用双指捏合手势缩放页面
3. 尝试双击页面进行缩放

**预期结果:**
- ✅ 页面不应响应缩放手势
- ✅ 双击不应触发缩放
- ✅ 页面保持固定缩放比例

**验证方法:**
```bash
# 检查 index.html 中的 viewport meta 标签
grep "user-scalable=no" frontend/index.html
```

### 2. 响应式布局测试 (需求 12.1-12.6)

**测试目标:** 验证三栏布局在移动设备上正确适配

**测试步骤:**
1. 在移动设备 (宽度 < 768px) 上打开应用
2. 观察布局结构
3. 滚动各个区域
4. 切换到平板设备 (768px - 1024px)
5. 切换到桌面设备 (> 1024px)

**预期结果:**

**移动设备 (< 768px):**
- ✅ 三栏布局改为垂直堆叠
- ✅ 左侧合同列表占据顶部 30% 视口高度
- ✅ 中间详情区域占据中间 40% 视口高度
- ✅ 右侧 AI 顾问占据底部 30% 视口高度
- ✅ 每个区域独立滚动

**平板设备 (768px - 1024px):**
- ✅ 保持三栏水平布局
- ✅ 左侧宽度调整为 240px
- ✅ 右侧宽度调整为 300px
- ✅ 中间区域自适应剩余宽度

**桌面设备 (> 1024px):**
- ✅ 左侧宽度 280px
- ✅ 右侧宽度 340px
- ✅ 中间区域自适应剩余宽度

### 3. 触摸交互测试

**测试目标:** 验证触摸事件正常工作

**测试步骤:**
1. 点击合同卡片
2. 点击筛选按钮
3. 在搜索框输入文字
4. 点击"同意"按钮
5. 点击评审意见的点赞按钮
6. 在评论输入框输入文字
7. 点击附件下载按钮
8. 向 AI 顾问发送问题

**预期结果:**
- ✅ 所有点击事件正常响应
- ✅ 触摸反馈明显 (高亮、颜色变化)
- ✅ 输入框正常弹出键盘
- ✅ 滚动流畅无卡顿
- ✅ 按钮点击区域足够大 (至少 44x44px)

### 4. 合同列表移动端测试

**测试步骤:**
1. 在移动设备上打开合同列表
2. 滚动合同列表
3. 点击筛选按钮切换筛选条件
4. 在搜索框输入关键词
5. 点击合同卡片选择合同
6. 点击"同意"按钮

**预期结果:**
- ✅ 合同卡片宽度自适应屏幕
- ✅ 卡片内容清晰可读
- ✅ 筛选按钮排列合理,不重叠
- ✅ 搜索框宽度自适应
- ✅ 待处理徽章清晰可见
- ✅ 选中状态明显

### 5. 合同详情移动端测试

**测试步骤:**
1. 选择一个合同
2. 查看合同标题和描述
3. 查看评审人列表
4. 查看附件列表
5. 点击附件版本展开/折叠
6. 点击下载按钮

**预期结果:**
- ✅ 标题和描述文字自动换行
- ✅ 评审人列表清晰显示
- ✅ 附件列表布局合理
- ✅ 展开/折叠动画流畅
- ✅ 下载按钮可点击

### 6. 时间线移动端测试

**测试步骤:**
1. 滚动时间线查看评审意见
2. 点击点赞按钮
3. 点击"展开回复"按钮
4. 在评论输入框输入文字
5. 点击发送按钮

**预期结果:**
- ✅ AI 智能总结卡片宽度自适应
- ✅ 评审意见卡片布局合理
- ✅ 头像和文字对齐
- ✅ 点赞按钮响应灵敏
- ✅ 回复列表展开/折叠流畅
- ✅ 评论输入框宽度自适应
- ✅ 键盘弹出时输入框可见

### 7. AI 顾问移动端测试

**测试步骤:**
1. 查看 AI 顾问界面
2. 滚动消息列表
3. 在输入框输入问题
4. 点击发送按钮
5. 查看 AI 回复

**预期结果:**
- ✅ 消息气泡宽度自适应
- ✅ 用户消息和 AI 消息区分明显
- ✅ 输入框宽度自适应
- ✅ 发送按钮可点击
- ✅ 消息自动滚动到底部

### 8. 表单和对话框移动端测试

**测试步骤:**
1. 点击"发起合同预审"按钮
2. 在对话框中填写表单
3. 选择评审人和抄送人
4. 上传附件
5. 提交表单

**预期结果:**
- ✅ 对话框宽度自适应屏幕
- ✅ 表单字段清晰可见
- ✅ 下拉选择器正常工作
- ✅ 文件选择器正常工作
- ✅ 按钮布局合理

### 9. 性能测试

**测试目标:** 验证移动设备上的性能表现

**测试步骤:**
1. 使用 Chrome DevTools Performance 工具
2. 记录页面加载过程
3. 记录滚动操作
4. 记录点击交互

**预期结果:**
- ✅ 首次内容绘制 (FCP) < 2 秒
- ✅ 最大内容绘制 (LCP) < 3 秒
- ✅ 首次输入延迟 (FID) < 100ms
- ✅ 累积布局偏移 (CLS) < 0.1
- ✅ 滚动帧率 > 30 FPS

### 10. 网络条件测试

**测试目标:** 验证弱网环境下的表现

**测试步骤:**
1. 在 Chrome DevTools 中启用网络节流
2. 选择 "Slow 3G" 或 "Fast 3G"
3. 刷新页面
4. 执行各种操作

**预期结果:**
- ✅ 显示加载状态指示器
- ✅ 图片和资源懒加载
- ✅ 操作响应及时
- ✅ 错误提示友好

## 测试工具

### 1. Chrome DevTools 移动端模拟

```bash
# 启动 Chrome 并打开应用
open -a "Google Chrome" http://localhost:5173

# 按 F12 打开开发者工具
# 按 Ctrl+Shift+M (Mac: Cmd+Shift+M) 切换到设备模式
```

### 2. 使用 BrowserStack 或 Sauce Labs

如果需要在真实设备上测试,可以使用云测试平台:

- [BrowserStack](https://www.browserstack.com/)
- [Sauce Labs](https://saucelabs.com/)
- [LambdaTest](https://www.lambdatest.com/)

### 3. 本地网络测试

在移动设备上测试本地开发服务器:

```bash
# 1. 获取本机 IP 地址
# Mac/Linux:
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows:
ipconfig

# 2. 启动开发服务器
cd frontend
npm run dev -- --host

# 3. 在移动设备上访问
# http://<your-ip>:5173
```

## 自动化测试

### Playwright 移动端测试示例

```typescript
// tests/mobile.spec.ts
import { test, expect, devices } from '@playwright/test';

test.use({
  ...devices['iPhone 12'],
});

test('移动端合同列表显示正常', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // 验证布局
  const layout = await page.locator('.three-column-layout');
  await expect(layout).toHaveCSS('flex-direction', 'column');
  
  // 验证合同列表
  const contractList = await page.locator('.left-panel');
  await expect(contractList).toBeVisible();
  
  // 验证触摸交互
  await page.tap('.contract-card:first-child');
  await expect(page.locator('.contract-card:first-child')).toHaveClass(/selected/);
});

test('移动端禁用缩放', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // 验证 viewport meta 标签
  const viewport = await page.locator('meta[name="viewport"]');
  const content = await viewport.getAttribute('content');
  expect(content).toContain('user-scalable=no');
});
```

## 常见问题

### 1. 页面在移动设备上可以缩放

**原因:** viewport meta 标签缺少 `user-scalable=no`

**解决方案:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
```

### 2. 布局在移动设备上显示异常

**原因:** 缺少响应式 CSS 媒体查询

**解决方案:** 检查 `ThreeColumnLayout.css` 中的媒体查询

### 3. 触摸事件不响应

**原因:** 
- 元素被其他元素遮挡
- 点击区域太小
- CSS `pointer-events: none`

**解决方案:**
- 检查 z-index
- 增大点击区域 (至少 44x44px)
- 移除 `pointer-events: none`

### 4. 键盘弹出时输入框被遮挡

**原因:** 固定定位或视口高度问题

**解决方案:**
```css
/* 确保输入框在键盘弹出时可见 */
.comment-input {
  position: relative;
  bottom: 0;
}
```

### 5. 滚动不流畅

**原因:** 
- 滚动容器设置不正确
- 过多的重绘和重排

**解决方案:**
```css
/* 启用硬件加速滚动 */
.scrollable-container {
  -webkit-overflow-scrolling: touch;
  overflow-y: auto;
}
```

## 验收标准

### 必须通过的测试

- ✅ 视口配置正确 (user-scalable=no)
- ✅ 响应式布局在所有设备上正常显示
- ✅ 所有触摸交互正常工作
- ✅ 文字清晰可读,不需要缩放
- ✅ 按钮和链接点击区域足够大
- ✅ 滚动流畅无卡顿
- ✅ 表单和输入框正常工作
- ✅ 键盘弹出时输入框可见

### 推荐通过的测试

- ✅ 性能指标达标 (FCP < 2s, LCP < 3s)
- ✅ 弱网环境下体验良好
- ✅ 支持横屏和竖屏切换
- ✅ 支持暗黑模式 (如果实现)

## 测试报告模板

```markdown
# 移动端测试报告

**测试日期:** 2025-03-XX
**测试人员:** XXX
**测试环境:** iPhone 12, iOS 16.5, Safari

## 测试结果

### 1. 视口配置测试
- 状态: ✅ 通过
- 备注: 页面无法缩放,符合要求

### 2. 响应式布局测试
- 状态: ✅ 通过
- 备注: 三栏布局在移动设备上正确转换为垂直堆叠

### 3. 触摸交互测试
- 状态: ✅ 通过
- 备注: 所有按钮和链接响应正常

### 4. 性能测试
- 状态: ⚠️ 部分通过
- 备注: FCP 2.3s,略高于目标值

## 发现的问题

1. **问题描述:** XXX
   - 严重程度: 高/中/低
   - 复现步骤: XXX
   - 预期结果: XXX
   - 实际结果: XXX

## 建议

1. XXX
2. XXX
```

## 总结

移动端测试是确保应用在各种设备上正常工作的关键步骤。请按照本指南进行全面测试,并记录测试结果。如有问题,请及时反馈给开发团队。
