-- =============================================================
-- YCHD2026-033 邮件审批链 → 单合同数据导入
-- 72封邮件 = 1个发起 + 71个回复 = 1个合同
-- =============================================================

-- 用户ID速查：
-- 常佳宇:c75af014  周喜春:d09f90a5  孟涛:15f0dc3b  赵迎春:6216d133
-- 畅红霞:e5cf05ea  曾硕:f9c21e4f  王建磊:39caab2c  王娅惠:aebe2c36
-- 吕海青:6dcbeb05  吴起玥:1abd0dda  王宇航:7baf87ae  边莹:05feb500
-- 陈宇:39c2b898  毛福建:895cfce6  陈敏:90a8199b  谢明宇:5a81730a
-- 胡首:a0000001-0000-0000-0000-000000000001
-- 王朋:a0000001-0000-0000-0000-000000000002
-- 孔繁强:a0000001-0000-0000-0000-000000000003
-- 毛凤娇:a0000001-0000-0000-0000-000000000004

-- ============ 1. 合同 ============
INSERT INTO contracts (id, name, description, status, initiator_id, cc_users, version, created_at, updated_at)
VALUES (
  'b0000001-0001-0001-0001-000000000001',
  'YCHD2026-033 九江银行鄱阳湖数据中心灾备完善项目-GPU算力服务器',
  E'商机编号: XS-2026_0122\n\n预计销售金额为6,600,000.00元，采购合同金额为5,250,000.00元，税率13%，毛利率18.71%。\n\n预计销售合同三月份签约，为了锁定低价的货源，申请提前采购合同的盖章和付款流程。\n\n请各位领导特批！',
  'progress',
  'c75af014-ff4e-4720-8199-c779720cccb8',
  ARRAY[
    '90a8199b-df52-460e-a339-019c569a5d6c','5a81730a-0421-40f8-af82-bb25436c4ec5',
    'a0000001-0000-0000-0000-000000000002','a0000001-0000-0000-0000-000000000003',
    'a0000001-0000-0000-0000-000000000004','6dcbeb05-9274-4469-b16c-d32d4553548b',
    '1abd0dda-55cd-4d4f-8e4a-7cb6520e5835','7baf87ae-539c-4801-9e47-75dc4a07732a',
    '05feb500-8e9d-4bd6-8592-db5550234dfa','39c2b898-b143-4f16-801b-9379bebf6d01',
    '895cfce6-059e-4d64-9c5c-5ba54236fe73','aebe2c36-6588-4613-9b35-8fcfe160562a',
    '39caab2c-d43c-4f89-88ed-02c53bcffe89','e5cf05ea-df4f-47fc-9adf-2e0e231f5168'
  ]::varchar[],
  1, '2026-02-04 16:41:12', '2026-05-14 17:29:44'
);

-- ============ 2. 评审记录 ============

-- 胡首 - 副总裁 - approved（多次同意）
INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000001',
  'b0000001-0001-0001-0001-000000000001',
  'a0000001-0000-0000-0000-000000000001', '副总裁', '领导审批',
  '同意！', 'approved', 0, ARRAY[]::varchar[],
  '2026-02-05 16:24:27', '2026-04-27 18:25:11');

-- 周喜春 - 项目管理 - approved（多次确认）
INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000002',
  'b0000001-0001-0001-0001-000000000001',
  'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', '项目管理', '业务确认',
  E'确认，已与客户沟通目标成交价，为锁定硬件采购价，提前采购阿里GPU设备。\n\n减少了耗材采购。采购合同与招标要求不符，经销售沟通，目前采购阿里的整机+拿到的浪潮原厂邮件附件与招标要求已符合。',
  'approved', 0, ARRAY[]::varchar[],
  '2026-02-05 09:03:36', '2026-04-27 18:01:15');

-- 赵迎春 - 内核部/法务 - pending（仍有多项问题未解决）
INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000003',
  'b0000001-0001-0001-0001-000000000001',
  '6216d133-4017-41e4-8f27-b714cd72ab25', '内核部', '法务审核',
  E'1.采购阿里、浪潮合同，均未涉及安装部署责任，销售合同提及了"集成改造"、"安装部署"、另有附件"软件工作说明书"等服务内容；问题：损益显示该合同为纯代理合同，不涉及内部人员成本，请复核；\n2.销售合同保修条款的具体要求，采购合同未明确，内容对应性无法评估；\n3.销售合同违约扣罚比例高，且采购合同未同步；采购合同设有责任限制、保管责任、进出口管制等多项条款，销售合同未同步；\n4.销售合同14.5款约定的增值服务，未见采购合同中的对应内容；\n5.销售合同标的物为"浪潮英政服务器3台"，与采购2合同标的物无法书面对应；\n6.销售合同约定永久保密，采购合同未对应；\n\n综上，上下游合同有多项核心条款及大量其他条款无法对应，请各位领导复审批示。\n\n---\n灵码合同：采购阿里合同第2页，合同约定有甲方及最终用户安装部署，与邮件描述不符；上下游合同条款及标的物描述存在出入。请各位领导复审评估。',
  'pending', 1, ARRAY[]::varchar[],
  '2026-02-06 09:01:05', '2026-04-27 15:06:24');

-- 孟涛 - 内核部 - pending（质疑基础错误）
INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000004',
  'b0000001-0001-0001-0001-000000000001',
  '15f0dc3b-1473-4523-b698-4419ea5f45ef', '内核部', '内核审核',
  E'鉴于此合同倒置问题跟付款模式已经经过特批。但是预审的上下游对应现在无法全面评估。此次仅为了采购行为本身做了责任分解跟落实。等上下游合同都到齐之后再做正式审定。在此之前请做好风险防控跟责任落实。\n\n情况特殊。请bd跟交付切实落实风险控制。其他无异议。\n\n---\n合同基础性错误为啥就都无视了？这些不修改是不行的。',
  'pending', 0, ARRAY[]::varchar[],
  '2026-02-13 12:32:42', '2026-04-21 11:23:26');

-- 畅红霞 - 财务 - approved
INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000005',
  'b0000001-0001-0001-0001-000000000001',
  'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', '财务', '财务审批',
  E'同意，请尽快完成销售合同签署，注意把控执行风险。\n\n请确保所有成本已预估，损益表预估无遗漏，其他无异议。',
  'approved', 0, ARRAY[]::varchar[],
  '2026-02-05 16:03:18', '2026-04-09 15:32:12');

-- 曾硕 - approved
INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000006',
  'b0000001-0001-0001-0001-000000000001',
  'f9c21e4f-11eb-4793-b0f2-02219bcb4542', '销售', '销售确认',
  '无异议', 'approved', 0, ARRAY[]::varchar[],
  '2026-02-05 16:12:47', '2026-02-13 07:55:28');

-- ============ 3. 评审下的回复 ============

-- 赵迎春review下 - 王娅惠详细回复 (03/31)
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000001',
  'b0000001-0001-0001-0001-000000000001',
  'c0000001-0001-0001-0001-000000000003', NULL,
  'aebe2c36-6588-4613-9b35-8fcfe160562a',
  E'一、关于集成改造/安装部署及软件服务的成本说明\n1、集成与安装服务：浪潮采购合同仅包含少量集成服务，大部分集成及安装部署服务将通过与阿里另行签订合同实现。对应损益表中"外采服务2（10万元）"为安装服务费，已覆盖该部分成本。\n2、软件服务：需与阿里签订补充合同，费用分为外采软件产品3：15万元和外采软件产品4：3.792万元。\n\n二、关于保修条款的对应性说明\n客户要求5年原厂金牌服务+介质不返还，我司从阿里采购3年原厂基础维保+从浪潮采购3年金牌升级服务+2年金牌续保服务，最终合计满足客户5年金牌维保要求。\n\n三、关于违约及责任条款的差异说明\n销售合同违约扣罚比例为行内标准模版，无法单独调整。采购合同中责任限制等为供应商标准模版要求，我司销售合同为行内通用版本。',
  2, ARRAY[]::varchar[], '2026-03-31 10:41:04', '2026-03-31 10:41:04');

-- 赵迎春review下 - 王建磊标的物拆分 (04/17)
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000002',
  'b0000001-0001-0001-0001-000000000001',
  'c0000001-0001-0001-0001-000000000003', NULL,
  '39caab2c-d43c-4f89-88ed-02c53bcffe89',
  E'销售合同标的物包含硬件、硬件售后服务、软件、增值服务。其中硬件、硬件售后服务、软件部分已经完成合同签订，此次采购的为增值服务，包含通义灵码私有化和通义灵码公有云。\n上下游详细的标的物拆分及对应合同签署进度详见附件。',
  1, ARRAY[]::varchar[], '2026-04-17 08:22:22', '2026-04-17 08:22:22');

-- 赵迎春review下 - 常佳宇回复合同已修正 (04/17)
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000003',
  'b0000001-0001-0001-0001-000000000001',
  'c0000001-0001-0001-0001-000000000003', NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'1.采购阿里灵码私有云合同为供应商模板；\n2.采购阿里合同第10页，售后响应级别已勾选为7*24小时；\n3.采购阿里合同附件2验收报告模板中，乙方公司名称已更改为阿里云飞天（杭州）云计算技术有限公司；\n4.采购通义云合同与采购阿里云合同公司标识已问阿里云老师，没有问题。',
  0, ARRAY[]::varchar[], '2026-04-17 17:23:36', '2026-04-17 17:23:36');

-- 赵迎春review下 - 王建磊确认采购范围和损益 (04/20)
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000004',
  'b0000001-0001-0001-0001-000000000001',
  'c0000001-0001-0001-0001-000000000003', NULL,
  '39caab2c-d43c-4f89-88ed-02c53bcffe89',
  E'采购范围确认：核心内容（公共云灵码：40人年；灵码私有化：1500人/永久）与销售合同要求符合，确认没问题。销售合同要求后续维保费用不超过3万元，采购合同无此要求，请销售同事确认此风险。\n\n损益表确认：公共云灵码由原来预算的37,920.00元调整为实际的30,336.00元，毛利率由11.51%更新为11.61%，确认没问题。',
  2, ARRAY[]::varchar[], '2026-04-20 17:33:09', '2026-04-20 17:33:09');

-- 孟涛review下 - 常佳宇回应孟总问题 (04/22)
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000005',
  'b0000001-0001-0001-0001-000000000001',
  'c0000001-0001-0001-0001-000000000004', NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'对于孟总的问题作出以下回复：\n1.关于迎春老师提出的合同问题合同已更新。\n2.销售合同编号为YCHD2026-033。\n3.公共云没有版本限制。\n4.灵码私有化平台交付由阿里云老师现场进行安装部署；IDE插件交付由阿里云提供，通过下载连接和平台内置的插件安装包给到客户。',
  0, ARRAY[]::varchar[], '2026-04-22 15:35:17', '2026-04-22 15:35:17');

-- 孟涛review下 - 王娅惠确认软件已部署 (04/27)
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000006',
  'b0000001-0001-0001-0001-000000000001',
  'c0000001-0001-0001-0001-000000000004', 'd0000001-0001-0001-0001-000000000005',
  'aebe2c36-6588-4613-9b35-8fcfe160562a',
  '经确认，该合同中约定的所有软件已部署完成，谢谢！',
  0, ARRAY[]::varchar[], '2026-04-27 17:53:28', '2026-04-27 17:53:28');

-- ============ 4. 常佳宇的17条评论（后续发起邮件） ============

-- 评论1: 02/04 特批-添加乙方公司名称
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000010',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  '【特批申请】阿里云采购合同签署部分添加了乙方公司名称。合同已更新。请各位领导特批！',
  0, ARRAY[]::varchar[], '2026-02-04 16:54:22', '2026-02-04 16:54:22');

-- 评论2: 02/05 特批-阿里模板改了
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000011',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  '【特批申请】阿里模板改了，附件请以此为准。请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-02-05 11:40:28', '2026-02-05 11:40:28');

-- 评论3: 02/05 合同预审-阿里云采购合同
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000012',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【合同预审】附件为损益表和阿里云采购合同。预计销售金额为6,600,000.00元，阿里云采购成本为5,250,000.00元，税率13%。预计销售合同三月份签约，该项目还有其他采购合同，目前由于客户部分需求还未完全敲定，所以其他采购合同金额暂不确认，为了锁定低价货源，希望先审批阿里云的采购合同。请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-02-05 16:49:51', '2026-02-05 16:49:51');

-- 评论4: 02/12 投标申请
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000013',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【投标申请】附件为投标评审表，损益表，合同主要条款，招标文件等。预计销售合同金额为6,600,000.00元，采购总成本为5,806,000.00元，毛利率为10.50%。采购阿里云成本为5,350,000.00元（PPU5,250,000元税率13%、安装服务100,000元税率6%）。采购浪潮成本为450,000.00元（维保360,000元税率6%、配件90,000元税率13%）。采购耗材6,000元税率13%。请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-02-12 09:55:00', '2026-02-12 09:55:00');
-- 回复: 胡首同意投标
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000014',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000013',
  'a0000001-0000-0000-0000-000000000001',
  '同意投标！', 0, ARRAY[]::varchar[], '2026-02-12 15:16:12', '2026-02-12 15:16:12');

-- 评论5: 02/12 特批-增加维保及配件
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000015',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【特批申请】增加的内容包含挂网招标要求中增加额外的两年维保及配件，以及阿里原厂的模型安装调试服务，因此更新损益表。预计销售合同金额为6,600,000.00元，采购总成本为5,806,000.00元，毛利率为10.50%。请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-02-12 16:05:11', '2026-02-12 16:05:11');
-- 回复: 畅红霞
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000016',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000015',
  'e5cf05ea-df4f-47fc-9adf-2e0e231f5168',
  '请确保所有成本已预估，损益表预估无遗漏，其他无异议。', 0, ARRAY[]::varchar[], '2026-02-12 16:17:28', '2026-02-12 16:17:28');

-- 评论6: 02/12 合同预审-PPU合同条款修改
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000017',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【合同预审】阿里云采购PPU合同的付款及发票条款（2）分期付款①增加了乙方收到预付款后发货。请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-02-12 17:27:54', '2026-02-12 17:27:54');

-- 评论7: 03/23 特批-提前给耗材和浪潮盖章
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000018',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【特批申请】附件为损益表（3月6号最新中标价格已更新），江西蓝骏豫科采购合同，浪潮采购合同等。预计销售金额6,852,000.00元，采购合同金额5,956,465.00元，毛利率9.92%。申请提前给耗材和浪潮采购合同盖章和提交付款流程。请各位领导特批！',
  0, ARRAY[]::varchar[], '2026-03-23 16:20:03', '2026-03-23 16:20:03');

-- 评论8: 03/23 特批-不需要耗材了
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000019',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【特批申请】由于客户临时通知他们改了方案，不需要耗材了。附件为损益表（3月6号最新中标价格已更新），浪潮采购合同等。预计销售金额6,852,000.00元，采购合同金额5,951,593.00元，毛利率11.5%。申请提前给浪潮采购合同盖章和提前给浪潮付款。请各位领导特批！',
  0, ARRAY[]::varchar[], '2026-03-23 19:58:56', '2026-03-23 19:58:56');

-- 评论9: 03/24 用印特批
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000020',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【用印特批】由于这个项目是行领导盯着的项目，需要我们每天汇报进展，行里着急服务器上架，使用；现在只差浪潮的配件就可以上架了。现申请先给浪潮合同线下用印。请各位领导特批！',
  0, ARRAY[]::varchar[], '2026-03-24 10:28:15', '2026-03-24 10:28:15');
-- 回复: 胡首同意
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000021',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000020',
  'a0000001-0000-0000-0000-000000000001',
  '同意！', 0, ARRAY[]::varchar[], '2026-03-24 10:53:06', '2026-03-24 10:53:06');
-- 回复: 畅红霞同意
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000022',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000020',
  'e5cf05ea-df4f-47fc-9adf-2e0e231f5168',
  '同意', 0, ARRAY[]::varchar[], '2026-03-24 14:45:56', '2026-03-24 14:45:56');

-- 评论10: 03/24 合同预审-浪潮合同预审
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000023',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【合同预审】由于客户临时通知改了方案，不需要耗材了，附件为损益表（3月6号最新中标价格已更新），浪潮采购合同等。预计销售金额6,852,000.00元，采购合同金额5,951,593.00元，毛利率11.5%。采购浪潮成本413,673.00元（raid卡52,773元税率13%、维保服务360,900元税率6%）。现申请给浪潮合同预审！请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-03-24 15:30:02', '2026-03-24 15:30:02');

-- 评论11: 03/30 合同预审-销售合同预审
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000024',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【合同预审】附件为损益表，浪潮采购合同，销售合同，阿里采购合同等。预计销售金额6,852,000.00元，采购合同金额5,951,593.00元，毛利率11.51%。现申请销售合同预审（合同为电子合同，着急今天签约），请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-03-30 15:08:42', '2026-03-30 15:08:42');

-- 评论12: 03/30 回复赵老师问题
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000025',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【回复赵老师】软件工作说明书的软件灵码私有化，安装部署服务和集成改造之后会和阿里再签一个合同。请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-03-30 16:51:42', '2026-03-30 16:51:42');

-- 评论13: 04/08 开放权限申请
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000026',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【开放权限申请】由于阿里公共云灵码要先充值后会生成合同（金额为30,336.00元），与安装服务和灵码私有化版本不在一个合同，因此需要变更业务采购合同备案，申请打开销售合同备案变更权限。请胡总确认！',
  0, ARRAY[]::varchar[], '2026-04-08 17:04:18', '2026-04-08 17:04:18');
-- 回复: 胡首同意
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000027',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000026',
  'a0000001-0000-0000-0000-000000000001',
  '同意！', 0, ARRAY[]::varchar[], '2026-04-08 17:29:48', '2026-04-08 17:29:48');

-- 评论14: 04/09 特批-先付款再走盖章
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000028',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【特批申请】公共云灵码需要先付款，付款金额为30,336.00元。付款之后才可以下载合同，请各位领导特批先付款再走合同盖章流程！',
  0, ARRAY[]::varchar[], '2026-04-09 10:33:08', '2026-04-09 10:33:08');
-- 回复: 畅红霞
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000029',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000028',
  'e5cf05ea-df4f-47fc-9adf-2e0e231f5168',
  '无异议', 0, ARRAY[]::varchar[], '2026-04-09 15:32:12', '2026-04-09 15:32:12');

-- 评论15: 04/16 合同预审-灵码合同
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000030',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【合同预审-灵码】附件为损益表，阿里云采购合同，浪潮采购合同，阿里云公共云灵码采购合同和阿里云灵码私有云采购合同等。销售金额6,852,000.00元，采购合同金额5,944,009.00元，毛利率11.61%。采购阿里云成本5,530,336.00元（PPU5,250,000元税率13%、灵码私有化+安装250,000元税率13%、公共云灵码30,336元税率6%）。采购浪潮成本413,673.00元。请各位领导给阿里云公共云灵码合同和灵码私有化和安装合同预审！',
  0, ARRAY[]::varchar[], '2026-04-16 11:48:10', '2026-04-16 11:48:10');

-- 评论16: 04/17 回复迎春老师问题
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000031',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【回复迎春老师】1.采购阿里灵码私有云合同为供应商模板；2.采购阿里合同第10页，售后响应级别已勾选为7*24小时；3.采购阿里合同附件2验收报告模板中，乙方公司名称已更改为阿里云飞天（杭州）云计算技术有限公司；4.采购通义云合同与采购阿里云合同公司标识已问阿里云老师，没有问题。请各位领导审批！',
  0, ARRAY[]::varchar[], '2026-04-17 17:23:36', '2026-04-17 17:23:36');

-- 评论17: 04/22 回应孟总问题-灵码预审
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000032',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【灵码预审-回应孟总】1.关于迎春老师提出的合同问题合同已更新；2.销售合同编号为YCHD2026-033；3.公共云没有版本限制；4.灵码私有化平台交付由阿里云老师现场进行安装部署；IDE插件交付由阿里云提供，通过下载连接和平台内置的插件安装包给到客户。请审批！',
  0, ARRAY[]::varchar[], '2026-04-22 15:35:17', '2026-04-22 15:35:17');
-- 回复: 周喜春确认
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000033',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000032',
  'd09f90a5-7652-44e6-bf2b-4b9d13b04d56',
  '确认。', 0, ARRAY[]::varchar[], '2026-04-24 10:40:51', '2026-04-24 10:40:51');

-- 评论18: 04/27 灵码私有化合同修改
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000034',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【灵码私有化合同修改】合同修改了9.1，9.2，9.5，增加了14.3。请审批！\n\n另：合同写甲方及最终用户安装部署，但实际是由阿里负责，目前阿里安装部署服务已完成。由于这个服务是阿里销售个人协调的，所以合同只能写由甲方及最终用户安装部署。',
  0, ARRAY[]::varchar[], '2026-04-27 10:50:01', '2026-04-27 16:16:32');
-- 回复: 王娅惠确认
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000035',
  'b0000001-0001-0001-0001-000000000001', NULL, 'd0000001-0001-0001-0001-000000000034',
  'aebe2c36-6588-4613-9b35-8fcfe160562a',
  '经确认，该合同中约定的所有软件已部署完成，谢谢！', 0, ARRAY[]::varchar[], '2026-04-27 17:53:28', '2026-04-27 17:53:28');

-- 评论19: 05/14 供应商交付方式变更
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000001-0001-0001-0001-000000000036',
  'b0000001-0001-0001-0001-000000000001', NULL, NULL,
  'c75af014-ff4e-4720-8199-c779720cccb8',
  E'【灵码私有化交付变更】供应商提出交付方式选为其他。请审批！',
  0, ARRAY[]::varchar[], '2026-05-14 17:29:44', '2026-05-14 17:29:44');

-- ============ 验证 ============
SELECT 'contracts' AS t, COUNT(*) FROM contracts
UNION ALL SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL SELECT 'comments', COUNT(*) FROM comments
UNION ALL SELECT 'comments_top', COUNT(*) FROM comments WHERE parent_comment_id IS NULL AND review_id IS NULL
UNION ALL SELECT 'comments_review', COUNT(*) FROM comments WHERE review_id IS NOT NULL
UNION ALL SELECT 'comments_reply', COUNT(*) FROM comments WHERE parent_comment_id IS NOT NULL;
