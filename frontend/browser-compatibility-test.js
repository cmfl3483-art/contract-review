/**
 * 浏览器兼容性自动化测试脚本
 * 
 * 此脚本用于在多个浏览器中自动测试应用的基本功能
 * 
 * 使用方法:
 * 1. 安装 Playwright: npm install -D @playwright/test
 * 2. 安装浏览器: npx playwright install
 * 3. 运行测试: node browser-compatibility-test.js
 * 
 * 注意: 这是一个示例脚本,需要根据实际应用调整测试用例
 */

// 检查是否安装了 Playwright
let playwright;
try {
  playwright = require('@playwright/test');
} catch (error) {
  console.log('⚠️  Playwright 未安装');
  console.log('请运行以下命令安装:');
  console.log('  npm install -D @playwright/test');
  console.log('  npx playwright install');
  process.exit(1);
}

const { chromium, firefox, webkit } = require('playwright');

// 测试配置
const TEST_URL = process.env.TEST_URL || 'http://localhost:3000';
const TIMEOUT = 30000; // 30秒超时

// 浏览器配置
const browsers = [
  { name: 'Chrome', launcher: chromium },
  { name: 'Firefox', launcher: firefox },
  { name: 'Safari (WebKit)', launcher: webkit },
  // Edge 使用 Chromium 内核,可以用 chromium 测试
];

// 测试结果
const results = {
  passed: 0,
  failed: 0,
  skipped: 0,
  details: []
};

/**
 * 基本功能测试
 */
async function runBasicTests(page, browserName) {
  const tests = [];

  // 测试1: 页面加载
  tests.push({
    name: '页面加载',
    test: async () => {
      await page.goto(TEST_URL, { waitUntil: 'networkidle', timeout: TIMEOUT });
      const title = await page.title();
      if (!title) throw new Error('页面标题为空');
    }
  });

  // 测试2: 三栏布局
  tests.push({
    name: '三栏布局显示',
    test: async () => {
      // 等待主要布局元素加载
      await page.waitForSelector('.contract-list', { timeout: TIMEOUT });
      await page.waitForSelector('.contract-detail', { timeout: TIMEOUT });
      await page.waitForSelector('.ai-advisor', { timeout: TIMEOUT });
      
      // 检查布局宽度
      const contractListWidth = await page.$eval('.contract-list', el => el.offsetWidth);
      const aiAdvisorWidth = await page.$eval('.ai-advisor', el => el.offsetWidth);
      
      if (contractListWidth < 250 || contractListWidth > 300) {
        throw new Error(`合同列表宽度异常: ${contractListWidth}px`);
      }
      if (aiAdvisorWidth < 320 || aiAdvisorWidth > 360) {
        throw new Error(`AI顾问宽度异常: ${aiAdvisorWidth}px`);
      }
    }
  });

  // 测试3: 合同列表渲染
  tests.push({
    name: '合同列表渲染',
    test: async () => {
      const contractCards = await page.$$('.contract-card');
      if (contractCards.length === 0) {
        console.log('  ⚠️  警告: 没有合同数据,跳过此测试');
        return 'skip';
      }
    }
  });

  // 测试4: 筛选按钮
  tests.push({
    name: '筛选按钮功能',
    test: async () => {
      const filterButtons = await page.$$('.filter-button');
      if (filterButtons.length < 5) {
        throw new Error(`筛选按钮数量不足: ${filterButtons.length}`);
      }
      
      // 点击"进行中"筛选
      await page.click('.filter-button:has-text("进行中")');
      await page.waitForTimeout(500); // 等待筛选完成
    }
  });

  // 测试5: 搜索功能
  tests.push({
    name: '搜索功能',
    test: async () => {
      const searchInput = await page.$('.search-input');
      if (!searchInput) {
        throw new Error('搜索输入框未找到');
      }
      
      await searchInput.fill('测试');
      await page.waitForTimeout(500); // 等待防抖
    }
  });

  // 测试6: WebSocket连接
  tests.push({
    name: 'WebSocket连接',
    test: async () => {
      // 检查控制台是否有WebSocket连接错误
      const logs = [];
      page.on('console', msg => {
        if (msg.type() === 'error' && msg.text().includes('WebSocket')) {
          logs.push(msg.text());
        }
      });
      
      await page.waitForTimeout(2000); // 等待连接建立
      
      if (logs.length > 0) {
        throw new Error(`WebSocket错误: ${logs.join(', ')}`);
      }
    }
  });

  // 测试7: 响应式布局
  tests.push({
    name: '响应式布局',
    test: async () => {
      // 测试不同视口大小
      const viewports = [
        { width: 1920, height: 1080 },
        { width: 1366, height: 768 },
        { width: 1024, height: 768 },
      ];
      
      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(500);
        
        // 检查布局是否正常
        const isVisible = await page.isVisible('.contract-list');
        if (!isVisible) {
          throw new Error(`视口 ${viewport.width}x${viewport.height} 下布局异常`);
        }
      }
      
      // 恢复默认视口
      await page.setViewportSize({ width: 1920, height: 1080 });
    }
  });

  // 执行所有测试
  for (const test of tests) {
    try {
      const result = await test.test();
      if (result === 'skip') {
        console.log(`  ⊘ ${test.name} - 跳过`);
        results.skipped++;
      } else {
        console.log(`  ✓ ${test.name} - 通过`);
        results.passed++;
      }
      results.details.push({
        browser: browserName,
        test: test.name,
        status: result === 'skip' ? 'skipped' : 'passed'
      });
    } catch (error) {
      console.log(`  ✗ ${test.name} - 失败`);
      console.log(`    错误: ${error.message}`);
      results.failed++;
      results.details.push({
        browser: browserName,
        test: test.name,
        status: 'failed',
        error: error.message
      });
    }
  }
}

/**
 * 在指定浏览器中运行测试
 */
async function testBrowser(browserConfig) {
  const { name, launcher } = browserConfig;
  console.log(`\n🌐 测试浏览器: ${name}`);
  console.log('─'.repeat(50));

  let browser;
  let context;
  let page;

  try {
    // 启动浏览器
    browser = await launcher.launch({
      headless: true, // 设置为 false 可以看到浏览器界面
    });

    // 创建上下文
    context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: `Mozilla/5.0 (compatible; BrowserCompatibilityTest/1.0; ${name})`,
    });

    // 创建页面
    page = await context.newPage();

    // 监听控制台错误
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`  ⚠️  控制台错误: ${msg.text()}`);
      }
    });

    // 监听页面错误
    page.on('pageerror', error => {
      console.log(`  ⚠️  页面错误: ${error.message}`);
    });

    // 运行测试
    await runBasicTests(page, name);

  } catch (error) {
    console.log(`  ✗ 浏览器测试失败: ${error.message}`);
    results.failed++;
    results.details.push({
      browser: name,
      test: '浏览器启动',
      status: 'failed',
      error: error.message
    });
  } finally {
    // 清理资源
    if (page) await page.close();
    if (context) await context.close();
    if (browser) await browser.close();
  }
}

/**
 * 主测试函数
 */
async function main() {
  console.log('🚀 开始浏览器兼容性测试');
  console.log(`📍 测试URL: ${TEST_URL}`);
  console.log('═'.repeat(50));

  // 检查测试服务器是否运行
  try {
    const http = require('http');
    const url = new URL(TEST_URL);
    
    await new Promise((resolve, reject) => {
      const req = http.get({
        hostname: url.hostname,
        port: url.port,
        path: '/',
        timeout: 5000
      }, (res) => {
        if (res.statusCode === 200 || res.statusCode === 304) {
          resolve();
        } else {
          reject(new Error(`服务器返回状态码: ${res.statusCode}`));
        }
      });
      
      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('连接超时'));
      });
    });
  } catch (error) {
    console.log(`\n❌ 无法连接到测试服务器: ${TEST_URL}`);
    console.log(`错误: ${error.message}`);
    console.log('\n请确保应用正在运行:');
    console.log('  cd frontend');
    console.log('  npm run dev');
    process.exit(1);
  }

  // 在所有浏览器中运行测试
  for (const browserConfig of browsers) {
    await testBrowser(browserConfig);
  }

  // 打印测试结果
  console.log('\n' + '═'.repeat(50));
  console.log('📊 测试结果汇总');
  console.log('═'.repeat(50));
  console.log(`✓ 通过: ${results.passed}`);
  console.log(`✗ 失败: ${results.failed}`);
  console.log(`⊘ 跳过: ${results.skipped}`);
  console.log(`📈 总计: ${results.passed + results.failed + results.skipped}`);

  // 按浏览器分组显示结果
  console.log('\n📋 详细结果:');
  const browserGroups = {};
  results.details.forEach(detail => {
    if (!browserGroups[detail.browser]) {
      browserGroups[detail.browser] = [];
    }
    browserGroups[detail.browser].push(detail);
  });

  Object.entries(browserGroups).forEach(([browser, tests]) => {
    console.log(`\n  ${browser}:`);
    tests.forEach(test => {
      const icon = test.status === 'passed' ? '✓' : test.status === 'failed' ? '✗' : '⊘';
      console.log(`    ${icon} ${test.test}`);
      if (test.error) {
        console.log(`      错误: ${test.error}`);
      }
    });
  });

  // 退出码
  const exitCode = results.failed > 0 ? 1 : 0;
  console.log('\n' + '═'.repeat(50));
  if (exitCode === 0) {
    console.log('✅ 所有测试通过!');
  } else {
    console.log('❌ 部分测试失败,请检查上述错误');
  }
  
  process.exit(exitCode);
}

// 运行测试
main().catch(error => {
  console.error('❌ 测试执行失败:', error);
  process.exit(1);
});
