import { test, expect, Page } from '@playwright/test';

/**
 * 合同合规检查 E2E 测试
 *
 * 测试覆盖:
 * - 管理员旅程: 创建规则集合 + 添加规则 + 切换 active
 * - 销售旅程: 上传 PDF + 提交 + 查看结果
 * - Property 17: 复制不污染剪贴板格式 (Validates: Requirements 5.4)
 * - 失败兜底: 空文本层 PDF → 错误提示 + 重新检查按钮
 * - 角色门禁: 销售访问管理页 → 403 → 前端展示无权限
 *
 * 注意: 部分测试使用 page.route() mock API 响应以便在无真实后端时运行。
 * 需要真实后端的测试已标记为 test.skip。
 */

// ─────────────────────────────────────────────
// 共享 mock 数据
// ─────────────────────────────────────────────

const MOCK_RULE_SET = {
  id: 'rs-001',
  name: '标准合同规范 v1',
  description: '适用于所有销售合同的基础合规规范',
  is_active: true,
  rule_count: 5,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
};

const MOCK_RULES = [
  {
    id: 'rule-001',
    rule_set_id: 'rs-001',
    rule_type: 'number',
    title: '合同编号格式',
    requirement: '合同编号必须以 HT- 开头，后跟 8 位数字',
    severity: 'must',
    order: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rule-002',
    rule_set_id: 'rs-001',
    rule_type: 'name',
    title: '合同名称长度',
    requirement: '合同名称不得少于 10 个字符',
    severity: 'must',
    order: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rule-003',
    rule_set_id: 'rs-001',
    rule_type: 'description',
    title: '合同描述完整性',
    requirement: '合同描述必须包含合同金额、付款方式、交付时间',
    severity: 'should',
    order: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rule-004',
    rule_set_id: 'rs-001',
    rule_type: 'file',
    title: '签字盖章页',
    requirement: '合同文件必须包含签字盖章页',
    severity: 'must',
    order: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'rule-005',
    rule_set_id: 'rs-001',
    rule_type: 'file',
    title: '违禁条款',
    requirement: '合同文件不得包含违禁条款',
    severity: 'must',
    order: 2,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const MOCK_CHECK_RESULT_COMPLETED = {
  id: 'check-001',
  status: 'completed',
  requested_by: { id: 'user-sales-001', name: '张三', avatar: null },
  rule_set_id: 'rs-001',
  rule_set_name: '标准合同规范 v1',
  file_name: 'contract.pdf',
  file_size: 102400,
  file_mime_type: 'application/pdf',
  extracted_text: '本合同由甲方与乙方签订，合同金额为人民币十万元整...',
  text_truncated: false,
  number_draft: 'HT-20240101',
  name_draft: '软件开发服务合同',
  description_draft: '本合同约定软件开发服务的相关条款',
  violations: [
    {
      rule_id: 'rule-001',
      rule_title: '合同编号格式',
      rule_type: 'number',
      location: 'number',
      excerpt: 'HT-20240101',
      description: '合同编号格式不符合规范，应为 HT- 后跟 8 位纯数字',
      suggestion: '请将合同编号修改为 HT-20240101 格式',
      severity: 'must',
    },
  ],
  suggested_name: '软件开发服务合同（2024年度）',
  suggested_description: '本合同约定甲乙双方软件开发服务的相关条款，合同金额为人民币十万元整，付款方式为分期付款，交付时间为2024年12月31日。',
  compliance_score: 88,
  requested_at: '2024-01-01T10:00:00Z',
  completed_at: '2024-01-01T10:00:30Z',
  error_message: null,
};

const MOCK_CHECK_RESULT_FAILED_EMPTY_TEXT = {
  id: 'check-002',
  status: 'failed',
  requested_by: { id: 'user-sales-001', name: '张三', avatar: null },
  rule_set_id: 'rs-001',
  rule_set_name: '标准合同规范 v1',
  file_name: 'image-only.pdf',
  file_size: 51200,
  file_mime_type: 'application/pdf',
  extracted_text: '',
  text_truncated: false,
  number_draft: null,
  name_draft: null,
  description_draft: null,
  violations: [],
  suggested_name: null,
  suggested_description: null,
  compliance_score: null,
  requested_at: '2024-01-01T11:00:00Z',
  completed_at: null,
  error_message: 'empty_extracted_text',
};

// ─────────────────────────────────────────────
// 辅助函数: 设置 mock 登录态
// ─────────────────────────────────────────────

async function mockLoginState(page: Page, role: '法务' | '销售' | '运营') {
  const userId = role === '销售' ? 'user-sales-001' : 'user-legal-001';
  const token = `mock-jwt-token-${role}`;

  await page.addInitScript(
    ({ token, userId, userName, userRole }) => {
      // 模拟 Zustand 持久化的 user-storage
      const userStorage = {
        state: {
          token,
          user: {
            id: userId,
            name: userName,
            role: userRole,
            avatar: null,
          },
        },
        version: 0,
      };
      localStorage.setItem('user-storage', JSON.stringify(userStorage));
    },
    { token, userId, userName: role === '销售' ? '张三' : '李四', userRole: role }
  );
}

// ─────────────────────────────────────────────
// 1. 管理员旅程 (test.skip — 需要真实后端)
// ─────────────────────────────────────────────

test.describe('管理员旅程', () => {
  test.skip(
    true,
    '需要真实运行的后端服务。如需运行，请确保后端已启动并配置好测试数据库。'
  );

  test('法务用户: 创建规则集合 → 添加 5 条规则覆盖 4 种 rule_type → 切换 active', async ({
    page,
  }) => {
    await mockLoginState(page, '法务');
    await page.goto('/compliance/admin/rule-sets');
    await page.waitForLoadState('networkidle');

    // 1. 创建规则集合
    const createBtn = page.locator('button:has-text("新建规则集合"), button:has-text("创建")');
    await expect(createBtn).toBeVisible({ timeout: 10000 });
    await createBtn.click();

    const modal = page.locator('.ant-modal');
    await expect(modal).toBeVisible();

    await page.locator('input[placeholder*="规则集合名称"], input[id*="name"]').fill('E2E测试规范集合');
    await page.locator('textarea[placeholder*="描述"]').fill('E2E 测试用规范集合');

    await page.locator('button:has-text("确定"), button:has-text("提交"), button[type="submit"]').click();
    await expect(modal).not.toBeVisible({ timeout: 5000 });

    // 2. 进入规则集合详情
    await page.locator('text=E2E测试规范集合').click();
    await page.waitForLoadState('networkidle');

    // 3. 添加 5 条规则，覆盖 4 种 rule_type
    const ruleTypes: Array<{ type: string; title: string }> = [
      { type: 'number', title: '编号格式规则' },
      { type: 'name', title: '名称长度规则' },
      { type: 'description', title: '描述完整性规则' },
      { type: 'file', title: '签字盖章规则' },
      { type: 'file', title: '违禁条款规则' },
    ];

    for (const rule of ruleTypes) {
      const addRuleBtn = page.locator('button:has-text("添加规则"), button:has-text("新增规则")');
      await addRuleBtn.click();

      const drawer = page.locator('.ant-drawer');
      await expect(drawer).toBeVisible();

      // 选择 rule_type
      await page.locator('.ant-select').first().click();
      await page.locator(`.ant-select-item[title="${rule.type}"], .ant-select-item:has-text("${rule.type}")`).click();

      // 填写 title
      await page.locator('input[placeholder*="规则名称"], input[id*="title"]').fill(rule.title);

      // 填写 requirement
      await page
        .locator('textarea[placeholder*="规则描述"], textarea[id*="requirement"]')
        .fill(`${rule.title}的具体要求描述，长度超过10个字符`);

      await page.locator('button:has-text("保存"), button:has-text("确定"), button[type="submit"]').click();
      await expect(drawer).not.toBeVisible({ timeout: 5000 });
    }

    // 4. 验证 5 条规则已添加
    const ruleRows = page.locator('table tbody tr, [data-testid="rule-item"]');
    await expect(ruleRows).toHaveCount(5, { timeout: 10000 });

    // 5. 切换 active 状态
    const activeToggle = page.locator('button[role="switch"], .ant-switch').first();
    if (await activeToggle.isVisible()) {
      await activeToggle.click();
      await page.waitForTimeout(500);
      // 验证切换成功（active 状态改变）
      await expect(page.locator('text=当前生效, text=已生效, .ant-tag:has-text("生效")')).toBeVisible({
        timeout: 5000,
      });
    }
  });
});

// ─────────────────────────────────────────────
// 2. 销售旅程 (test.skip — 需要真实后端)
// ─────────────────────────────────────────────

test.describe('销售旅程', () => {
  test.skip(
    true,
    '需要真实运行的后端服务。如需运行，请确保后端已启动并配置好测试数据库。'
  );

  test('销售用户: 上传 PDF + 三 draft → 提交 → 跳转 detail → 看到 violations + 评分 + 复制按钮', async ({
    page,
  }) => {
    await mockLoginState(page, '销售');
    await page.goto('/compliance/check/new');
    await page.waitForLoadState('networkidle');

    // 1. 上传 PDF 文件
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached({ timeout: 10000 });

    // 创建一个最小的合法 PDF buffer（仅用于测试，不含真实文本层）
    await fileInput.setInputFiles({
      name: 'test-contract.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000009 00000 n\ntrailer\n<< /Size 2 /Root 1 0 R >>\nstartxref\n58\n%%EOF'),
    });

    // 2. 填写三个 draft 字段
    await page.locator('input[placeholder*="合同编号"], input[id*="number_draft"]').fill('HT-20240101');
    await page.locator('input[placeholder*="合同名称"], input[id*="name_draft"]').fill('软件开发服务合同');
    await page
      .locator('textarea[placeholder*="合同描述"], textarea[id*="description_draft"]')
      .fill('本合同约定软件开发服务的相关条款，合同金额为人民币十万元整');

    // 3. 提交
    const submitBtn = page.locator('button:has-text("提交"), button:has-text("开始检查"), button[type="submit"]');
    await submitBtn.click();

    // 4. 等待跳转到 detail 页
    await page.waitForURL(/\/compliance\/check\/[a-f0-9-]+/, { timeout: 30000 });

    // 5. 等待检查完成（轮询 pending → completed）
    await expect(page.locator('text=AI 检查中, text=检查中')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=合规评分, text=violations, text=不符合项')).toBeVisible({
      timeout: 90000,
    });

    // 6. 验证 violations 列表
    const violationList = page.locator('[data-testid="violation-list"], .violation-list, text=不符合项');
    await expect(violationList).toBeVisible();

    // 7. 验证合规评分
    await expect(page.locator('text=/合规评分.*\\d+\\/100/')).toBeVisible();

    // 8. 验证复制按钮存在
    const copyButtons = page.locator('button:has-text("复制")');
    await expect(copyButtons.first()).toBeVisible();
  });
});

// ─────────────────────────────────────────────
// 3. Property 17: 复制不污染剪贴板格式
//    Validates: Requirements 5.4
//    使用 page.route() mock，无需真实后端
// ─────────────────────────────────────────────

test.describe('Property 17: 复制不污染剪贴板格式', () => {
  /**
   * **Validates: Requirements 5.4**
   *
   * 断言「复制到剪贴板」按钮写入的内容为纯文本，
   * 与 suggested_name / suggested_description 字段值完全一致，
   * 不含 HTML 标签、Markdown 标记或其他格式污染。
   */
  test('复制 suggested_name 到剪贴板 — 内容为纯文本且与展示值一致', async ({
    page,
    context,
  }) => {
    // 授予剪贴板写权限
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Mock GET /api/compliance/checks/check-001
    await page.route('**/api/compliance/checks/check-001', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_CHECK_RESULT_COMPLETED),
      });
    });

    // Mock 其他可能的 API 请求（auth、rule-sets 等）
    await page.route('**/api/compliance/rule-sets**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [MOCK_RULE_SET], total: 1, page: 1, page_size: 20 }),
      });
    });

    await mockLoginState(page, '销售');
    await page.goto('/compliance/check/check-001');
    await page.waitForLoadState('networkidle');

    // 等待 suggested_name 区块渲染
    const suggestedNameText = MOCK_CHECK_RESULT_COMPLETED.suggested_name;
    await expect(page.locator(`text=${suggestedNameText}`)).toBeVisible({ timeout: 10000 });

    // 点击「建议合同名称」旁的复制按钮
    // 定位策略: 找到包含 suggested_name 文本的 Card，点击其中的复制按钮
    const nameCard = page.locator('.ant-card').filter({ hasText: '建议合同名称' });
    const copyNameBtn = nameCard.locator('button:has-text("复制")');
    await expect(copyNameBtn).toBeVisible({ timeout: 5000 });
    await copyNameBtn.click();

    // 通过 navigator.clipboard.readText() 读取剪贴板内容
    const clipboardContent = await page.evaluate(() => navigator.clipboard.readText());

    // 断言 1: 剪贴板内容与 suggested_name 完全一致
    expect(clipboardContent).toBe(suggestedNameText);

    // 断言 2: 剪贴板内容不含 HTML 标签（纯文本）
    expect(clipboardContent).not.toMatch(/<[^>]+>/);

    // 断言 3: 剪贴板内容不含 Markdown 标记（如 **bold**、# heading）
    expect(clipboardContent).not.toMatch(/\*\*|#{1,6}\s|`{1,3}/);

    // 断言 4: 剪贴板内容非空
    expect(clipboardContent.trim().length).toBeGreaterThan(0);
  });

  test('复制 suggested_description 到剪贴板 — 内容为纯文本且与展示值一致', async ({
    page,
    context,
  }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    await page.route('**/api/compliance/checks/check-001', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_CHECK_RESULT_COMPLETED),
      });
    });

    await page.route('**/api/compliance/rule-sets**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [MOCK_RULE_SET], total: 1, page: 1, page_size: 20 }),
      });
    });

    await mockLoginState(page, '销售');
    await page.goto('/compliance/check/check-001');
    await page.waitForLoadState('networkidle');

    const suggestedDescText = MOCK_CHECK_RESULT_COMPLETED.suggested_description;
    await expect(page.locator(`text=${suggestedDescText.slice(0, 20)}`)).toBeVisible({
      timeout: 10000,
    });

    // 点击「建议合同描述」旁的复制按钮
    const descCard = page.locator('.ant-card').filter({ hasText: '建议合同描述' });
    const copyDescBtn = descCard.locator('button:has-text("复制")');
    await expect(copyDescBtn).toBeVisible({ timeout: 5000 });
    await copyDescBtn.click();

    const clipboardContent = await page.evaluate(() => navigator.clipboard.readText());

    // 断言 1: 剪贴板内容与 suggested_description 完全一致
    expect(clipboardContent).toBe(suggestedDescText);

    // 断言 2: 剪贴板内容不含 HTML 标签
    expect(clipboardContent).not.toMatch(/<[^>]+>/);

    // 断言 3: 剪贴板内容不含 Markdown 标记
    expect(clipboardContent).not.toMatch(/\*\*|#{1,6}\s|`{1,3}/);

    // 断言 4: 剪贴板内容非空
    expect(clipboardContent.trim().length).toBeGreaterThan(0);
  });
});

// ─────────────────────────────────────────────
// 4. 失败兜底: 空文本层 PDF
//    使用 page.route() mock，无需真实后端
// ─────────────────────────────────────────────

test.describe('失败兜底: 空文本层 PDF', () => {
  test('上传文本层为空的 PDF → 看到「合同文件未抽取到可读文本」+ 「重新检查」按钮', async ({
    page,
  }) => {
    // Mock GET /api/compliance/checks/check-002 返回 failed + empty_extracted_text
    await page.route('**/api/compliance/checks/check-002', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_CHECK_RESULT_FAILED_EMPTY_TEXT),
      });
    });

    await page.route('**/api/compliance/rule-sets**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [MOCK_RULE_SET], total: 1, page: 1, page_size: 20 }),
      });
    });

    await mockLoginState(page, '销售');
    await page.goto('/compliance/check/check-002');
    await page.waitForLoadState('networkidle');

    // 断言 1: 展示「合同文件未抽取到可读文本」错误提示
    // 对应 ErrorMessageMap 中 empty_extracted_text 的映射文案
    await expect(
      page.locator('text=合同文件未抽取到可读文本')
    ).toBeVisible({ timeout: 10000 });

    // 断言 2: 展示「重新检查」按钮
    const recheckBtn = page.locator('button:has-text("重新检查")');
    await expect(recheckBtn).toBeVisible({ timeout: 5000 });
  });

  test('点击「重新检查」按钮 → 触发 recheck API 调用', async ({ page }) => {
    let recheckCalled = false;

    await page.route('**/api/compliance/checks/check-002', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_CHECK_RESULT_FAILED_EMPTY_TEXT),
      });
    });

    // Mock recheck 接口
    await page.route('**/api/compliance/checks/check-002/recheck', (route) => {
      recheckCalled = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...MOCK_CHECK_RESULT_FAILED_EMPTY_TEXT,
          id: 'check-002',
          status: 'pending',
        }),
      });
    });

    await page.route('**/api/compliance/rule-sets**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [MOCK_RULE_SET], total: 1, page: 1, page_size: 20 }),
      });
    });

    await mockLoginState(page, '销售');
    await page.goto('/compliance/check/check-002');
    await page.waitForLoadState('networkidle');

    // 等待错误提示渲染
    await expect(page.locator('text=合同文件未抽取到可读文本')).toBeVisible({ timeout: 10000 });

    // 点击「重新检查」
    const recheckBtn = page.locator('button:has-text("重新检查")');
    await recheckBtn.click();

    // 等待 recheck API 被调用
    await page.waitForTimeout(1000);
    expect(recheckCalled).toBe(true);
  });
});

// ─────────────────────────────────────────────
// 5. 角色门禁: 销售访问管理页 → 403 → 前端展示无权限
//    使用 page.route() mock，无需真实后端
// ─────────────────────────────────────────────

test.describe('角色门禁', () => {
  test('销售直接访问 /compliance/admin/rule-sets → 后端 403 → 前端展示无权限', async ({
    page,
  }) => {
    // Mock 规则集合列表接口返回 403
    await page.route('**/api/compliance/rule-sets**', (route) => {
      route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error_code: 'compliance_forbidden',
            message: '权限不足，仅法务或运营角色可访问规则管理',
          },
        }),
      });
    });

    await mockLoginState(page, '销售');
    await page.goto('/compliance/admin/rule-sets');
    await page.waitForLoadState('networkidle');

    // 断言: 前端展示无权限提示
    // 可能的展示形式: 403 页面、「无权限」文案、「权限不足」文案、Ant Design Result 组件
    const forbiddenIndicators = [
      page.locator('text=无权限'),
      page.locator('text=权限不足'),
      page.locator('text=403'),
      page.locator('text=没有访问权限'),
      page.locator('[data-testid="forbidden-page"]'),
      page.locator('.ant-result-403'),
      page.locator('.ant-result-title:has-text("403")'),
    ];

    // 至少有一个无权限指示器可见
    let foundForbidden = false;
    for (const indicator of forbiddenIndicators) {
      if (await indicator.isVisible({ timeout: 5000 }).catch(() => false)) {
        foundForbidden = true;
        break;
      }
    }

    // 如果前端做了路由级别的角色守卫（在请求前就拦截），也算通过
    // 检查是否被重定向到 /compliance 或其他页面
    const currentUrl = page.url();
    const wasRedirected = !currentUrl.includes('/compliance/admin/rule-sets');

    expect(foundForbidden || wasRedirected).toBe(true);
  });

  test('法务用户访问 /compliance/admin/rule-sets → 正常渲染规则管理页', async ({ page }) => {
    // Mock 规则集合列表接口返回 200
    await page.route('**/api/compliance/rule-sets**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [MOCK_RULE_SET],
          total: 1,
          page: 1,
          page_size: 20,
        }),
      });
    });

    await mockLoginState(page, '法务');
    await page.goto('/compliance/admin/rule-sets');
    await page.waitForLoadState('networkidle');

    // 断言: 规则管理页正常渲染（能看到规则集合名称或管理相关 UI）
    await expect(
      page.locator('text=标准合同规范 v1, text=规则集合, text=规则管理, h1, h2').first()
    ).toBeVisible({ timeout: 10000 });
  });
});
