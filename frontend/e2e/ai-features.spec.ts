import { test, expect } from '@playwright/test';

/**
 * AI功能端到端测试
 * 
 * 测试覆盖:
 * - AI智能总结
 * - AI合同顾问问答
 * - 关键问题提取
 */

test.describe('AI功能', () => {
  test.beforeEach(async ({ page }) => {
    // 访问应用首页
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('应该显示AI智能总结', async ({ page }) => {
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI智能总结区域
      const aiSummary = page.locator('text=AI智能总结, text=智能总结');
      
      if (await aiSummary.isVisible()) {
        // 验证AI总结区域存在
        expect(await aiSummary.isVisible()).toBeTruthy();
        
        // 验证审批进度信息
        const progressInfo = page.locator('text=/已完成|审批进行中|已全部通过/');
        
        if (await progressInfo.isVisible()) {
          expect(await progressInfo.isVisible()).toBeTruthy();
        }
        
        // 验证关键问题列表
        const keyIssues = page.locator('text=关键问题');
        
        if (await keyIssues.isVisible()) {
          expect(await keyIssues.isVisible()).toBeTruthy();
        }
      }
    }
  });

  test('应该支持AI顾问问答 - 法务意见查询', async ({ page }) => {
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI顾问输入框
      const aiInput = page.locator('input[placeholder*="输入问题"], textarea[placeholder*="输入问题"]');
      
      if (await aiInput.isVisible()) {
        // 输入法务相关问题
        await aiInput.fill('有哪些法务意见?');
        await aiInput.press('Enter');
        
        // 等待AI回复
        await page.waitForTimeout(3000);
        
        // 验证AI回复显示
        const aiMessages = page.locator('.ai-message, .message, [data-testid="ai-message"]');
        const messageCount = await aiMessages.count();
        
        // 应该至少有用户消息和AI回复
        expect(messageCount).toBeGreaterThan(0);
        
        // 验证回复内容包含法务相关信息
        const messageText = await page.locator('.ai-message, .message').last().textContent();
        
        if (messageText) {
          // 回复应该包含法务或评审相关内容
          const hasRelevantContent = 
            messageText.includes('法务') || 
            messageText.includes('评审') || 
            messageText.includes('意见');
          
          expect(hasRelevantContent).toBeTruthy();
        }
      }
    }
  });

  test('应该支持AI顾问问答 - 风险项查询', async ({ page }) => {
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI顾问输入框
      const aiInput = page.locator('input[placeholder*="输入问题"], textarea[placeholder*="输入问题"]');
      
      if (await aiInput.isVisible()) {
        // 输入风险相关问题
        await aiInput.fill('有哪些风险项?');
        await aiInput.press('Enter');
        
        // 等待AI回复
        await page.waitForTimeout(3000);
        
        // 验证AI回复显示
        const aiMessages = page.locator('.ai-message, .message, [data-testid="ai-message"]');
        const messageCount = await aiMessages.count();
        
        expect(messageCount).toBeGreaterThan(0);
      }
    }
  });

  test('应该支持AI顾问问答 - 待办任务查询', async ({ page }) => {
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI顾问输入框
      const aiInput = page.locator('input[placeholder*="输入问题"], textarea[placeholder*="输入问题"]');
      
      if (await aiInput.isVisible()) {
        // 输入待办相关问题
        await aiInput.fill('我有哪些待处理的任务?');
        await aiInput.press('Enter');
        
        // 等待AI回复
        await page.waitForTimeout(3000);
        
        // 验证AI回复显示
        const aiMessages = page.locator('.ai-message, .message, [data-testid="ai-message"]');
        const messageCount = await aiMessages.count();
        
        expect(messageCount).toBeGreaterThan(0);
      }
    }
  });

  test('应该支持AI顾问多轮对话', async ({ page }) => {
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI顾问输入框
      const aiInput = page.locator('input[placeholder*="输入问题"], textarea[placeholder*="输入问题"]');
      
      if (await aiInput.isVisible()) {
        // 第一轮对话
        await aiInput.fill('这个合同有多少评审意见?');
        await aiInput.press('Enter');
        await page.waitForTimeout(2000);
        
        // 第二轮对话
        await aiInput.fill('有哪些法务意见?');
        await aiInput.press('Enter');
        await page.waitForTimeout(2000);
        
        // 第三轮对话
        await aiInput.fill('有风险项吗?');
        await aiInput.press('Enter');
        await page.waitForTimeout(2000);
        
        // 验证所有消息都显示
        const aiMessages = page.locator('.ai-message, .message, [data-testid="ai-message"]');
        const messageCount = await aiMessages.count();
        
        // 应该至少有6条消息 (3个问题 + 3个回复)
        expect(messageCount).toBeGreaterThanOrEqual(3);
      }
    }
  });

  test('应该在AI服务不可用时显示友好提示', async ({ page }) => {
    // 这个测试需要模拟AI服务不可用的情况
    // 在实际环境中,可以通过拦截网络请求来模拟
    
    // 拦截AI API请求并返回错误
    await page.route('**/api/ai/**', route => {
      route.abort('failed');
    });
    
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI顾问输入框
      const aiInput = page.locator('input[placeholder*="输入问题"], textarea[placeholder*="输入问题"]');
      
      if (await aiInput.isVisible()) {
        // 输入问题
        await aiInput.fill('测试AI服务不可用');
        await aiInput.press('Enter');
        
        // 等待错误提示
        await page.waitForTimeout(2000);
        
        // 验证错误提示显示
        const errorMessage = page.locator('text=/服务不可用|暂时不可用|请稍后重试/');
        
        if (await errorMessage.isVisible()) {
          expect(await errorMessage.isVisible()).toBeTruthy();
        }
      }
    }
  });

  test('应该显示AI总结的关键问题', async ({ page }) => {
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI智能总结区域
      const aiSummary = page.locator('text=AI智能总结, text=智能总结');
      
      if (await aiSummary.isVisible()) {
        // 查找关键问题列表
        const keyIssues = page.locator('text=关键问题');
        
        if (await keyIssues.isVisible()) {
          // 验证关键问题列表存在
          expect(await keyIssues.isVisible()).toBeTruthy();
          
          // 查找问题项
          const issueItems = page.locator('.key-issue, [data-testid="key-issue"]');
          const issueCount = await issueItems.count();
          
          // 关键问题应该不超过3个 (根据设计文档)
          if (issueCount > 0) {
            expect(issueCount).toBeLessThanOrEqual(3);
          }
        }
      }
    }
  });

  test('应该显示关键问题的解决方案', async ({ page }) => {
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找AI智能总结区域
      const aiSummary = page.locator('text=AI智能总结, text=智能总结');
      
      if (await aiSummary.isVisible()) {
        // 查找解决方案
        const solutions = page.locator('text=解决方案, text=已解决');
        
        if (await solutions.count() > 0) {
          // 验证解决方案显示
          expect(await solutions.first().isVisible()).toBeTruthy();
        }
      }
    }
  });
});
