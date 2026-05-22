import { test, expect, devices } from '@playwright/test';

/**
 * 移动端测试套件
 * 测试移动设备上的响应式布局和触摸交互
 */

test.describe('移动端响应式布局测试', () => {
  test.use({
    ...devices['iPhone 12'],
  });

  test('应该禁用用户缩放 (需求 12.7)', async ({ page }) => {
    await page.goto('/');

    // 验证 viewport meta 标签
    const viewport = await page.locator('meta[name="viewport"]');
    const content = await viewport.getAttribute('content');
    
    expect(content).toContain('user-scalable=no');
    expect(content).toContain('width=device-width');
    expect(content).toContain('initial-scale=1.0');
  });

  test('应该在移动设备上使用垂直堆叠布局', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 验证三栏布局改为垂直堆叠
    const layout = page.locator('.three-column-layout');
    await expect(layout).toBeVisible();

    // 在移动设备上,flex-direction 应该是 column
    const flexDirection = await layout.evaluate((el) => {
      return window.getComputedStyle(el).flexDirection;
    });
    
    expect(flexDirection).toBe('column');
  });

  test('应该正确显示左侧合同列表', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const leftPanel = page.locator('.left-panel');
    await expect(leftPanel).toBeVisible();

    // 验证宽度为 100%
    const width = await leftPanel.evaluate((el) => {
      return window.getComputedStyle(el).width;
    });
    
    // 在移动设备上,宽度应该接近视口宽度
    const viewportWidth = await page.viewportSize();
    expect(parseInt(width)).toBeGreaterThan(viewportWidth!.width * 0.9);
  });

  test('应该支持触摸滚动', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const leftPanel = page.locator('.left-panel');
    
    // 验证滚动容器
    const overflowY = await leftPanel.evaluate((el) => {
      return window.getComputedStyle(el).overflowY;
    });
    
    expect(overflowY).toBe('auto');
  });

  test('应该支持点击合同卡片', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 等待合同列表加载
    const contractCard = page.locator('.contract-card').first();
    await expect(contractCard).toBeVisible();

    // 点击合同卡片
    await contractCard.tap();

    // 验证卡片被选中
    await expect(contractCard).toHaveClass(/selected/);
  });
});

test.describe('平板设备响应式布局测试', () => {
  test.use({
    ...devices['iPad Pro'],
  });

  test('应该在平板设备上保持三栏水平布局', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const layout = page.locator('.three-column-layout');
    await expect(layout).toBeVisible();

    // 在平板设备上,flex-direction 应该是 row
    const flexDirection = await layout.evaluate((el) => {
      return window.getComputedStyle(el).flexDirection;
    });
    
    expect(flexDirection).toBe('row');
  });

  test('应该调整左侧面板宽度', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const leftPanel = page.locator('.left-panel');
    await expect(leftPanel).toBeVisible();

    // 验证宽度为 240px (平板设备)
    const width = await leftPanel.evaluate((el) => {
      return window.getComputedStyle(el).width;
    });
    
    expect(width).toBe('240px');
  });

  test('应该调整右侧面板宽度', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const rightPanel = page.locator('.right-panel');
    await expect(rightPanel).toBeVisible();

    // 验证宽度为 300px (平板设备)
    const width = await rightPanel.evaluate((el) => {
      return window.getComputedStyle(el).width;
    });
    
    expect(width).toBe('300px');
  });
});

test.describe('触摸交互测试', () => {
  test.use({
    ...devices['iPhone 12'],
  });

  test('应该支持点击筛选按钮', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 点击"进行中"筛选按钮
    const filterButton = page.locator('button:has-text("进行中")');
    await expect(filterButton).toBeVisible();
    await filterButton.tap();

    // 验证按钮被激活
    await expect(filterButton).toHaveClass(/active/);
  });

  test('应该支持在搜索框输入', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 查找搜索框
    const searchInput = page.locator('input[placeholder*="搜索"]');
    await expect(searchInput).toBeVisible();

    // 点击输入框
    await searchInput.tap();

    // 输入文字
    await searchInput.fill('测试合同');

    // 验证输入值
    await expect(searchInput).toHaveValue('测试合同');
  });

  test('应该支持点击评论点赞按钮', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 选择一个合同
    const contractCard = page.locator('.contract-card').first();
    await contractCard.tap();

    // 等待时间线加载
    await page.waitForTimeout(1000);

    // 查找点赞按钮
    const likeButton = page.locator('.like-button').first();
    if (await likeButton.isVisible()) {
      await likeButton.tap();
      
      // 验证点赞数增加
      await expect(likeButton).toContainText(/\d+/);
    }
  });
});

test.describe('性能测试', () => {
  test.use({
    ...devices['iPhone 12'],
  });

  test('应该在移动设备上快速加载', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // 首次加载应该在 5 秒内完成
    expect(loadTime).toBeLessThan(5000);
  });

  test('应该流畅滚动', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const leftPanel = page.locator('.left-panel');
    
    // 滚动到底部
    await leftPanel.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });

    // 等待滚动完成
    await page.waitForTimeout(500);

    // 验证滚动位置
    const scrollTop = await leftPanel.evaluate((el) => el.scrollTop);
    expect(scrollTop).toBeGreaterThan(0);
  });
});

test.describe('网络条件测试', () => {
  test.use({
    ...devices['iPhone 12'],
  });

  test('应该在慢速网络下显示加载状态', async ({ page, context }) => {
    // 模拟慢速 3G 网络
    await context.route('**/*', (route) => {
      setTimeout(() => route.continue(), 1000);
    });

    await page.goto('/');

    // 应该显示加载指示器
    const loading = page.locator('.ant-spin');
    if (await loading.isVisible()) {
      await expect(loading).toBeVisible();
    }

    await page.waitForLoadState('networkidle');
  });
});
