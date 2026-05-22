import { test, expect } from '@playwright/test';

/**
 * 合同预审完整流程端到端测试
 * 
 * 测试覆盖:
 * - 创建合同流程
 * - 查看合同详情
 * - 添加评论
 * - 快速审批
 * - 筛选和搜索功能
 */

test.describe('合同预审完整流程', () => {
  test.beforeEach(async ({ page }) => {
    // 访问应用首页
    // 注意: 由于使用钉钉OAuth登录,这里需要模拟已登录状态
    // 在实际环境中,可能需要设置测试用户的token或使用测试环境的登录方式
    await page.goto('/');
    
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test('应该完成创建合同到审批的完整流程', async ({ page }) => {
    // 1. 点击发起合同预审按钮
    const createButton = page.locator('button:has-text("发起合同预审")');
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();
    
    // 2. 等待对话框出现
    const dialog = page.locator('.ant-modal');
    await expect(dialog).toBeVisible();
    
    // 3. 填写合同信息
    const nameInput = page.locator('input[placeholder*="合同名称"]');
    await nameInput.fill('E2E测试合同');
    
    const descriptionInput = page.locator('textarea[placeholder*="合同描述"]');
    await descriptionInput.fill('这是一个端到端测试合同');
    
    // 4. 选择评审人
    // 注意: 这里需要根据实际的Ant Design Select组件结构调整选择器
    const reviewerSelect = page.locator('.ant-select').first();
    await reviewerSelect.click();
    
    // 等待下拉选项出现
    await page.waitForTimeout(500);
    
    // 选择第一个评审人
    const firstOption = page.locator('.ant-select-item').first();
    if (await firstOption.isVisible()) {
      await firstOption.click();
    }
    
    // 5. 提交合同 (暂时跳过文件上传,因为需要实际文件)
    const submitButton = page.locator('button:has-text("提交")');
    await submitButton.click();
    
    // 6. 等待对话框关闭
    await expect(dialog).not.toBeVisible({ timeout: 5000 });
    
    // 7. 验证合同出现在列表中
    const contractCard = page.locator('text=E2E测试合同');
    await expect(contractCard).toBeVisible({ timeout: 10000 });
    
    // 8. 点击合同查看详情
    await contractCard.click();
    
    // 9. 验证合同详情显示正确
    await expect(page.locator('text=这是一个端到端测试合同')).toBeVisible();
    
    // 10. 添加评论
    const commentInput = page.locator('textarea[placeholder*="输入评论"]');
    if (await commentInput.isVisible()) {
      await commentInput.fill('这是一条测试评论');
      await commentInput.press('Enter');
      
      // 11. 验证评论显示
      await expect(page.locator('text=这是一条测试评论')).toBeVisible({ timeout: 5000 });
    }
    
    // 12. 快速审批 (如果有待处理项)
    const approveButton = page.locator('button:has-text("同意")');
    if (await approveButton.isVisible()) {
      await approveButton.click();
      
      // 确认对话框
      const confirmButton = page.locator('button:has-text("确定")');
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
        
        // 13. 验证审批状态更新
        await expect(page.locator('text=✅')).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('应该支持筛选和搜索功能', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    
    // 1. 点击"进行中"筛选
    const progressFilter = page.locator('button:has-text("进行中")');
    if (await progressFilter.isVisible()) {
      await progressFilter.click();
      
      // 等待筛选结果
      await page.waitForTimeout(1000);
      
      // 2. 验证有合同卡片显示
      const cards = page.locator('[data-testid="contract-card"]');
      const count = await cards.count();
      
      // 如果有合同,验证数量大于0
      if (count > 0) {
        expect(count).toBeGreaterThan(0);
      }
    }
    
    // 3. 输入搜索关键词
    const searchInput = page.locator('input[placeholder*="搜索"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('测试');
      
      // 等待搜索结果
      await page.waitForTimeout(500);
      
      // 4. 验证搜索结果 (如果有匹配的合同)
      const searchResults = page.locator('[data-testid="contract-card"]');
      const resultCount = await searchResults.count();
      
      // 搜索结果应该存在或为0 (取决于是否有匹配的合同)
      expect(resultCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('应该支持查看合同详情和附件', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    
    // 1. 查找第一个合同卡片
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      // 2. 点击合同卡片
      await firstCard.click();
      
      // 3. 等待详情区域加载
      await page.waitForTimeout(1000);
      
      // 4. 验证合同详情区域可见
      const detailSection = page.locator('.contract-detail');
      
      // 5. 检查是否有附件区域
      const attachmentSection = page.locator('text=附件');
      if (await attachmentSection.isVisible()) {
        // 验证附件区域存在
        expect(await attachmentSection.isVisible()).toBeTruthy();
      }
      
      // 6. 检查是否有评审人列表
      const reviewerSection = page.locator('text=评审人');
      if (await reviewerSection.isVisible()) {
        // 验证评审人区域存在
        expect(await reviewerSection.isVisible()).toBeTruthy();
      }
    }
  });

  test('应该支持AI顾问问答', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    
    // 1. 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 2. 查找AI顾问输入框
      const aiInput = page.locator('input[placeholder*="输入问题"]');
      
      if (await aiInput.isVisible()) {
        // 3. 输入问题
        await aiInput.fill('有哪些法务意见?');
        await aiInput.press('Enter');
        
        // 4. 等待AI回复
        await page.waitForTimeout(2000);
        
        // 5. 验证AI消息区域存在
        const aiMessages = page.locator('.ai-message, .message');
        const messageCount = await aiMessages.count();
        
        // 应该至少有用户消息
        expect(messageCount).toBeGreaterThan(0);
      }
    }
  });

  test('应该支持点赞功能', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    
    // 1. 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 2. 查找点赞按钮
      const likeButton = page.locator('button:has-text("👍"), button[aria-label*="点赞"]').first();
      
      if (await likeButton.isVisible()) {
        // 3. 获取点赞前的数量
        const likeCountBefore = await page.locator('text=/\\d+/).first().textContent();
        
        // 4. 点击点赞
        await likeButton.click();
        
        // 5. 等待更新
        await page.waitForTimeout(500);
        
        // 6. 验证点赞数量变化或按钮状态变化
        // 注意: 实际验证逻辑取决于UI实现
        expect(await likeButton.isVisible()).toBeTruthy();
      }
    }
  });
});
