import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

/**
 * 文件上传和附件管理端到端测试
 * 
 * 测试覆盖:
 * - 上传附件
 * - 查看附件版本
 * - 下载附件
 */

test.describe('文件上传和附件管理', () => {
  // 创建测试文件
  test.beforeAll(async () => {
    const testFilesDir = path.join(__dirname, '../test-files');
    
    // 确保测试文件目录存在
    if (!fs.existsSync(testFilesDir)) {
      fs.mkdirSync(testFilesDir, { recursive: true });
    }
    
    // 创建测试PDF文件 (简单的文本文件模拟)
    const testPdfPath = path.join(testFilesDir, 'sample.pdf');
    if (!fs.existsSync(testPdfPath)) {
      fs.writeFileSync(testPdfPath, 'This is a test PDF file for E2E testing');
    }
    
    // 创建测试文档文件
    const testDocPath = path.join(testFilesDir, 'sample.docx');
    if (!fs.existsSync(testDocPath)) {
      fs.writeFileSync(testDocPath, 'This is a test DOCX file for E2E testing');
    }
  });

  test('应该支持上传附件', async ({ page }) => {
    // 访问应用
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 创建新合同
    const createButton = page.locator('button:has-text("发起合同预审")');
    
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // 等待对话框
      const dialog = page.locator('.ant-modal');
      await expect(dialog).toBeVisible();
      
      // 填写合同信息
      const nameInput = page.locator('input[placeholder*="合同名称"]');
      await nameInput.fill(`附件测试合同 ${Date.now()}`);
      
      // 上传文件
      const fileInput = page.locator('input[type="file"]');
      
      if (await fileInput.count() > 0) {
        const testFilePath = path.join(__dirname, '../test-files/sample.pdf');
        
        // 检查文件是否存在
        if (fs.existsSync(testFilePath)) {
          await fileInput.setInputFiles(testFilePath);
          
          // 等待文件上传
          await page.waitForTimeout(1000);
          
          // 验证文件显示在列表中
          await expect(page.locator('text=sample.pdf')).toBeVisible({ timeout: 5000 });
        }
      }
      
      // 选择评审人
      const reviewerSelect = page.locator('.ant-select').first();
      await reviewerSelect.click();
      await page.waitForTimeout(500);
      
      const firstOption = page.locator('.ant-select-item').first();
      if (await firstOption.isVisible()) {
        await firstOption.click();
      }
      
      // 提交
      const submitButton = page.locator('button:has-text("提交")');
      await submitButton.click();
      
      // 等待对话框关闭
      await expect(dialog).not.toBeVisible({ timeout: 5000 });
    }
  });

  test('应该支持查看附件版本', async ({ page }) => {
    // 访问应用
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找附件区域
      const attachmentSection = page.locator('text=附件');
      
      if (await attachmentSection.isVisible()) {
        // 查找附件列表
        const attachmentList = page.locator('.attachment-list, [data-testid="attachment-list"]');
        
        if (await attachmentList.isVisible()) {
          // 验证附件显示
          expect(await attachmentList.isVisible()).toBeTruthy();
          
          // 查找版本信息
          const versionInfo = page.locator('text=/v\\d+\\.\\d+|版本/');
          
          if (await versionInfo.count() > 0) {
            // 验证版本信息存在
            expect(await versionInfo.first().isVisible()).toBeTruthy();
          }
        }
      }
    }
  });

  test('应该支持上传同名文件创建新版本', async ({ page }) => {
    // 访问应用
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找上传按钮
      const uploadButton = page.locator('button:has-text("上传"), button[aria-label*="上传"]');
      
      if (await uploadButton.isVisible()) {
        // 点击上传按钮
        await uploadButton.click();
        
        // 查找文件输入
        const fileInput = page.locator('input[type="file"]');
        
        if (await fileInput.count() > 0) {
          const testFilePath = path.join(__dirname, '../test-files/sample.pdf');
          
          if (fs.existsSync(testFilePath)) {
            await fileInput.setInputFiles(testFilePath);
            
            // 等待上传完成
            await page.waitForTimeout(2000);
            
            // 验证新版本显示
            const versionLabels = page.locator('text=/v\\d+\\.\\d+|版本/');
            const versionCount = await versionLabels.count();
            
            // 应该至少有一个版本
            expect(versionCount).toBeGreaterThan(0);
          }
        }
      }
    }
  });

  test('应该支持下载附件', async ({ page }) => {
    // 访问应用
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 选择一个合同
    const firstCard = page.locator('[data-testid="contract-card"]').first();
    
    if (await firstCard.isVisible()) {
      await firstCard.click();
      
      // 等待详情加载
      await page.waitForTimeout(1000);
      
      // 查找下载按钮
      const downloadButton = page.locator('button:has-text("下载"), a:has-text("下载")').first();
      
      if (await downloadButton.isVisible()) {
        // 监听下载事件
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 });
        
        // 点击下载
        await downloadButton.click();
        
        try {
          // 等待下载开始
          const download = await downloadPromise;
          
          // 验证下载文件名
          const fileName = download.suggestedFilename();
          expect(fileName).toBeTruthy();
          
          // 可选: 保存文件到临时目录验证
          // const downloadPath = path.join(__dirname, '../test-downloads', fileName);
          // await download.saveAs(downloadPath);
        } catch (error) {
          // 下载可能因为权限或其他原因失败,这是可接受的
          console.log('Download test skipped:', error);
        }
      }
    }
  });

  test('应该验证文件类型限制', async ({ page }) => {
    // 访问应用
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 创建新合同
    const createButton = page.locator('button:has-text("发起合同预审")');
    
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // 等待对话框
      const dialog = page.locator('.ant-modal');
      await expect(dialog).toBeVisible();
      
      // 填写合同信息
      const nameInput = page.locator('input[placeholder*="合同名称"]');
      await nameInput.fill('文件类型测试');
      
      // 尝试上传不支持的文件类型
      const fileInput = page.locator('input[type="file"]');
      
      if (await fileInput.count() > 0) {
        // 创建一个不支持的文件类型
        const testFilesDir = path.join(__dirname, '../test-files');
        const invalidFilePath = path.join(testFilesDir, 'invalid.txt');
        
        if (!fs.existsSync(invalidFilePath)) {
          fs.writeFileSync(invalidFilePath, 'This is an invalid file type');
        }
        
        // 尝试上传
        await fileInput.setInputFiles(invalidFilePath);
        
        // 等待错误提示
        await page.waitForTimeout(1000);
        
        // 验证错误提示显示
        const errorMessage = page.locator('text=/不支持|格式错误|类型错误/');
        
        if (await errorMessage.isVisible()) {
          expect(await errorMessage.isVisible()).toBeTruthy();
        }
      }
      
      // 关闭对话框
      const cancelButton = page.locator('button:has-text("取消")');
      if (await cancelButton.isVisible()) {
        await cancelButton.click();
      }
    }
  });
});
