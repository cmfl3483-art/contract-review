-- 第一封邮件作为合同描述
UPDATE contracts SET description = E'各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，附件为损益表和阿里云采购合同。

预计销售金额为6,600,000.00元，采购合同金额为5,250,000.00元，税率13%，毛利率18.71%。

预计销售合同三月份签约，为了锁定低价的货源，申请提前采购合同的盖章和付款流程。

请各位领导特批！' WHERE id = 'b0000001-0001-0001-0001-000000000001';

DELETE FROM comments WHERE contract_id = 'b0000001-0001-0001-0001-000000000001';

-- ============ 评审记录 ============
INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000001', 'b0000001-0001-0001-0001-000000000001', 'a0000001-0000-0000-0000-000000000001', '副总裁', '领导审批', E'同意！', 'approved', 0, ARRAY[]::varchar[], '2026-02-04 16:41:12', '2026-04-27 18:25:11');

INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000002', 'b0000001-0001-0001-0001-000000000001', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', '项目管理', '业务确认', E'确认，已与客户沟通目标成交价，为锁定硬件采购价，提前采购阿里GPU设备。', 'approved', 0, ARRAY[]::varchar[], '2026-02-04 16:41:12', '2026-02-05 09:03:36');

INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000003', 'b0000001-0001-0001-0001-000000000001', '6216d133-4017-41e4-8f27-b714cd72ab25', '内核部', '法务审核', E'1.采购阿里、浪潮合同，均未涉及安装部署责任，销售合同提及了“集成改造”、“安装部署”、另有附件“软件工作说明书”等服务内容；
      问题：损益显示该合同为纯代理合同，不涉及内部人员成本，请复核上述内容的实际情况；

2.销售合同保修条款的具体要求，采购合同未明确，内容对应性无法评估；

3.销售合同违约扣罚比例高，且采购合同未同步；采购合同设有责任限制、保管责任、进出口管制等多项条款，销售合同未同步；

4.销售合同14.5款约定的增值服务，未见采购合同中的对应内容；

5.销售合同标的物为“浪潮英政服务器3台 ”，与采购2合同标的物无法书面对应；

6.销售合同约定永久保密，采购合同未对应；

综上，上下游合同有多项核心条款及大量其他条款无法对应，请各位领导复审批示。', 'pending', 0, ARRAY[]::varchar[], '2026-02-04 16:41:12', '2026-03-30 16:24:01');

INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000004', 'b0000001-0001-0001-0001-000000000001', '15f0dc3b-1473-4523-b698-4419ea5f45ef', '内核部', '内核审核', E'合同基础性错误为啥就都无视了？这些不修改是不行的', 'pending', 0, ARRAY[]::varchar[], '2026-02-04 16:41:12', '2026-04-21 11:23:26');

INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000005', 'b0000001-0001-0001-0001-000000000001', 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', '财务', '财务审批', E'请确保所有成本已预估￥损益表预估无遗漏，其他无异议', 'approved', 0, ARRAY[]::varchar[], '2026-02-04 16:41:12', '2026-02-12 16:17:28');

INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
VALUES ('c0000001-0001-0001-0001-000000000006', 'b0000001-0001-0001-0001-000000000001', 'f9c21e4f-11eb-4793-b0f2-02219bcb4542', '销售', '销售确认', E'无异议', 'approved', 0, ARRAY[]::varchar[], '2026-02-04 16:41:12', '2026-02-05 16:12:47');

-- ============ 评审下的回复 ============
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000010-0001-0001-0001-000000000101', 'b0000001-0001-0001-0001-000000000001', 'c0000001-0001-0001-0001-000000000003', NULL, 'aebe2c36-6588-4613-9b35-8fcfe160562a', E'一、关于集成改造 / 安装部署及软件服务的成本说明

1、集成与安装服务：浪潮采购合同仅包含少量集成服务，大部分集成及安装部署服务将通过与阿里另行签订合同实现。对应损益表中 “外采服务 2（10 万元）” 为安装服务费，已覆盖该部分成本，不存在内部人员成本投入。

2、软件服务：软件相关服务需与阿里签订补充合同，费用分为两部分：
外采软件产品 3：15 万元（软件产品采购）

外采软件产品 4：3.792 万元（阿里云公有云服务充值）

二、关于保修条款的对应性说明

客户要求的服务器保修为5 年原厂金牌服务 + 介质不返还，我司采购链路如下：

1、从阿里采购：3 年原厂基础维保（不含金牌服务）
2、从浪潮采购：
3 年金牌升级服务：将基础维保升级为金牌级别
2 年金牌续保服务：额外延长 2 年金牌维保
最终合计满足客户 5 年金牌维保要求，保修条款已通过组合采购实现覆盖。

三、关于违约及责任条款的差异说明
销售合同违约扣罚比例为行内标准模版，无法单独调整。
采购合同中责任限制、保管责任、进出口管制等条款，均为供应商标准模版要求，我司销售合同为行内通用版本，未同步此类条款。
以上条款差异为硬件行业代理模式下的常规情况，特申请领导特批。

四、关于增值服务的对应说明
销售合同 14.5 款约定的增值服务，对应待与阿里签订的软件服务合同（即外采软件产品 3、4），后续将通过补充合同签约（阿里内部还在拟合同条款，多次催促仍未拿到该合同）。

五、关于合同销售产品的对应说明
销售合同标的物 “浪潮英政服务器 3 台”，与阿里采购合同中 “浪潮 AIstack 一体机” 产品对应，为同一硬件设备的不同表述。

六、关于保密条款的差异说明
销售合同约定永久保密，而阿里、浪潮等供应商均要求采用自身标准合同模版，无法同步永久保密条款。该差异为供应商合规要求导致，特申请领导特批。

本次销售合同与采购合同因硬件代理业务的复杂性（多供应商组合采购、服务拆分签约），确实存在部分条款无法一一对应的情况，相关差异均有合理业务背景及解决方案。恳请各位领导予以特批！感谢！', 0, ARRAY[]::varchar[], '2026-03-31 10:41:04', '2026-03-31 10:41:04');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000010-0001-0001-0001-000000000102', 'b0000001-0001-0001-0001-000000000001', 'c0000001-0001-0001-0001-000000000003', NULL, '39caab2c-d43c-4f89-88ed-02c53bcffe89', E'你好：

    销售合同（YCHD2026-033九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器）标的物包含硬件、硬件售后服务、软件、增值服务。其中硬件、硬件售后服务、软件部分已经完成合同签订，此次采购的为增值服务，包含通义灵码私有化和通义灵码公有云。
    上下游详细的标的物拆分及对应合同签署进度详见附件。
    
    谢谢！', 0, ARRAY[]::varchar[], '2026-04-17 08:22:22', '2026-04-17 08:22:22');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000010-0001-0001-0001-000000000103', 'b0000001-0001-0001-0001-000000000001', 'c0000001-0001-0001-0001-000000000003', NULL, '39caab2c-d43c-4f89-88ed-02c53bcffe89', E'你好：
    关于进度表签署方与合同不一致问题答复如下：
    
    问题：进度表显示25万合同签署方为通义云，但采购合同文本为阿里云，请复核实际情况；
    答复：经核实，此合同签署方为：阿里云飞天（杭州）云计算技术有限公司，已更新【上下游合同标的物拆分及签署进度表】
    
    谢谢！', 0, ARRAY[]::varchar[], '2026-04-17 15:46:42', '2026-04-17 15:46:42');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000010-0001-0001-0001-000000000104', 'b0000001-0001-0001-0001-000000000001', 'c0000001-0001-0001-0001-000000000003', NULL, '39caab2c-d43c-4f89-88ed-02c53bcffe89', E'各位领导好：

    针对此项目，销售合同里的硬件部分已经签约（阿里的整机采购及浪潮采购），此次为增值服务的采购，包含公共云灵码和灵码私有化。
    采购范围确认：
核心内容（公共云灵码：40人年；灵码私有化：1500人/永久）与销售合同要求符合，确认没问题。
其他：销售合同要求后续维保费用不超过3万元，采购合同无此要求，请销售同事确认此风险。
    损益表确认：
        公共云灵码由原来预算的37,920.00元调整为实际的30,336.00元，并有税率的更新，毛利率由11.51%更新为11.61%，确认没问题。

    请领导复核。

    谢谢！', 0, ARRAY[]::varchar[], '2026-04-20 17:33:09', '2026-04-20 17:33:09');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000010-0001-0001-0001-000000000105', 'b0000001-0001-0001-0001-000000000001', 'c0000001-0001-0001-0001-000000000004', NULL, 'aebe2c36-6588-4613-9b35-8fcfe160562a', E'经确认，该合同中约定的所有软件已部署完成，谢谢！', 0, ARRAY[]::varchar[], '2026-04-27 17:53:28', '2026-04-27 17:53:28');

-- ============ 常佳宇的评论（后续发起邮件） ============
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000201', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【特批申请】各位领导好：

阿里云采购合同签署部分添加了乙方公司名称。

合同已更新。请各位领导特批！', 0, ARRAY[]::varchar[], '2026-02-04 16:54:22', '2026-02-04 16:54:22');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000202', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【特批申请】各位领导好：

阿里模板改了，附件请以此为准。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-02-05 11:40:28', '2026-02-05 11:40:28');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000203', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，附件为损益表和阿里云采购合同。

预计销售金额为6,600,000.00元，阿里云采购成本为5,250,000.00元，税率13%。

预计销售合同三月份签约，该项目还有其他采购合同，目前由于客户部分需求还未完全敲定，所以其他采购合同金额暂不确认，为了锁定低价货源，希望先审批阿里云的采购合同。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-02-05 16:49:51', '2026-02-05 16:49:51');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000204', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【投标申请】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，附件为投标评审表，损益表，合同主要条款，招标文件等。

预计销售合同金额为6,600,000.00元，采购总成本为5,806,000.00元，毛利率为10.50%。

采购阿里云成本为5,350,000.00元，其中PPU成本为5,250,000.00元，税率为13%，安装服务成本为100,000.00元，税率为6%。

采购浪潮成本为450,000.00元，其中维保成本为360,000.00元，税率为6%，配件成本为90,000.00元，税率为13%。

采购耗材成本为6,000.00元，税率为13%。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-02-12 09:55:00', '2026-02-12 09:55:00');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000205', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【特批申请】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器增加的内容包含挂网招标要求中增加额外的两年维保及配件，以及阿里原厂的模型安装调试服务，因此更新损益表。

预计销售合同金额为6,600,000.00元，采购总成本为5,806,000.00元，毛利率为10.50%。
采购阿里云成本为5,350,000.00元，其中PPU成本为5,250,000.00元，税率为13%，安装服务成本为100,000.00元，税率为6%。
采购浪潮成本为450,000.00元，其中维保成本为360,000.00元，税率为6%，配件成本为90,000.00元，税率为13%。
采购耗材成本为6,000.00元，税率为13%。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-02-12 16:05:11', '2026-02-12 16:05:11');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000206', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审】各位领导好：

阿里云采购PPU合同的付款及发票条款（2）分期付款①增加了乙方收到预付款后发货。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-02-12 17:27:54', '2026-02-12 17:27:54');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000207', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【特批申请】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，附件为损益表（3月6号最新中标价格已更新），江西蓝骏豫科采购合同，浪潮采购合同等。

预计销售金额为6,852,000.00元，采购合同金额为5,956,465.00元，毛利率9.92%。

采购阿里云成本5,537,920.00元，其中PPU采购成本5,250,000.00元，税率为13%；灵码私有化版本成本150,000.00元，税率13%；

公共云灵码企业标准版本37,920.00元，税率13%，安装服务成本100,000.00元，税率6%。

采购浪潮成本413,673.00元，其中raid卡成本52,773.00元，税率13%；维保服务成本360,900.00元，税率6%。

采购江西蓝骏豫科耗材成本4,872.00元，税率13%。

预计销售合同三月份签约，为了不影响给客户交付，申请提前给耗材和浪潮采购合同盖章和提交付款流程。

请各位领导特批！', 0, ARRAY[]::varchar[], '2026-03-23 16:20:03', '2026-03-23 16:20:03');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000208', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【特批申请】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，由于客户临时通知他们改了方案，不需要耗材了，附件为损益表（3月6号最新中标价格已更新），浪潮采购合同等。

预计销售金额为6,852,000.00元，采购合同金额为5,951,593.00元，毛利率11.5%。

采购阿里云成本5,537,920.00元，其中PPU采购成本5,250,000.00元，税率为13%；灵码私有化版本成本150,000.00元，税率13%；

公共云灵码企业标准版本37,920.00元，税率13%，安装服务成本100,000.00元，税率6%。

采购浪潮成本413,673.00元，其中raid卡成本52,773.00元，税率13%；维保服务成本360,900.00元，税率6%。

预计销售合同三月底签约，预计客户在五月中旬付首款，为了不影响给客户交付，申请提前给浪潮采购合同盖章和提前给浪潮付款（发货前付款，付全款413,673.00元）。

请各位领导特批！', 0, ARRAY[]::varchar[], '2026-03-23 19:58:56', '2026-03-23 19:58:56');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000209', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【用印特批】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，由于这个项目是行领导盯着的项目，需要我们每天汇报进展，行里着急服务器上架，使用；现在只差浪潮的配件就可以上架了。现申请先给浪潮合同线下用印，预计今天会发起合同盖章流程。请各位领导特批！', 0, ARRAY[]::varchar[], '2026-03-24 10:28:15', '2026-03-24 10:28:15');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000210', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，由于客户临时通知他们改了方案，不需要耗材了，附件为损益表（3月6号最新中标价格已更新），浪潮采购合同等。
预计销售金额为6,852,000.00元，采购合同金额为5,951,593.00元，毛利率11.5%。
采购阿里云成本5,537,920.00元，其中PPU采购成本5,250,000.00元，税率为13%；灵码私有化版本成本150,000.00元，税率13%；
公共云灵码企业标准版本37,920.00元，税率13%，安装服务成本100,000.00元，税率6%。
采购浪潮成本413,673.00元，其中raid卡成本52,773.00元，税率13%；维保服务成本360,900.00元，税率6%。
预计销售合同三月底签约，预计客户在五月中旬付首款，为了不影响给客户交付，现申请给浪潮合同预审！
请各位领导审批！', 0, ARRAY[]::varchar[], '2026-03-24 15:30:02', '2026-03-24 15:30:02');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000211', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审】各位领导好：
九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，附件为损益表，浪潮采购合同，销售合同，阿里采购合同等。
预计销售金额为6,852,000.00元，采购合同金额为5,951,593.00元，毛利率11.51%。
采购阿里云成本5,537,920.00元，其中PPU采购成本5,250,000.00元，税率为13%；灵码私有化版本成本150,000.00元，税率13%；
公共云灵码企业标准版本37,920.00元，税率13%，安装服务成本100,000.00元，税率6%。
采购浪潮成本413,673.00元，其中raid卡成本52,773.00元，税率13%；维保服务成本360,900.00元，税率6%。
现申请销售合同预审（合同为电子合同，着急今天签约），请各位领导审批！', 0, ARRAY[]::varchar[], '2026-03-30 15:08:42', '2026-03-30 15:08:42');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000212', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审】各位领导好：

对于赵老师的问题作出以下回复：

软件工作说明书的软件灵码私有化，安装部署服务和集成改造之后会和阿里再签一个合同。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-03-30 16:51:42', '2026-03-30 16:51:42');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000213', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【开放权限申请】各位领导好：

由于阿里公共云灵码要先充值后会生成合同（金额为30,336.00元），与安装服务和灵码私有化版本不在一个合同，因此需要变更业务采购合同备案，申请打开销售合同备案变更权限。

请胡总确认！', 0, ARRAY[]::varchar[], '2026-04-08 17:04:18', '2026-04-08 17:04:18');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000214', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【特批申请】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器（采购阿里云-公共云灵码）需要先付款，付款金额为30,336.00元。

付款之后才可以下载合同，请各位领导特批先付款再走合同盖章流程！', 0, ARRAY[]::varchar[], '2026-04-09 10:33:08', '2026-04-09 10:33:08');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000215', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审】各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，附件为损益表，阿里云采购合同，浪潮采购合同，阿里云公共云灵码采购合同和阿里云灵码私有云采购合同等。
销售金额为6,852,000.00元，采购合同金额为5,944,009.00元，毛利率11.61%。
采购阿里云成本5,530,336.00元，其中PPU采购成本5,250,000.00元，税率为13%；灵码私有化版本和安装成本250,000.00元，税率13%；
公共云灵码企业标准版本30,336.00元，税率6%。
采购浪潮成本413,673.00元，其中raid卡成本52,773.00元，税率13%；维保服务成本360,900.00元，税率6%。
请各位领导给阿里云公共云灵码合同和阿里云灵码私有化和安装合同预审！', 0, ARRAY[]::varchar[], '2026-04-16 11:48:10', '2026-04-16 11:48:10');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000216', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审】各位领导好：

对于迎春老师的问题作出以下说明和回复：

1.采购阿里灵码私有云合同为供应商模板：

2.采购阿里合同第10页，售后响应级别未勾选，已勾选为7*24小时；
3.采购阿里合同附件2验收报告模板中，乙方公司名称已更改为阿里云飞天（杭州）云计算技术有限公司。
4.采购通义云合同与采购阿里云合同公司标识已问阿里云老师，没有问题。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-04-17 17:23:36', '2026-04-17 17:23:36');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000020-0001-0001-0001-000000000217', 'b0000001-0001-0001-0001-000000000001', NULL, NULL, 'c75af014-ff4e-4720-8199-c779720cccb8', E'【合同预审-灵码】各位领导好：

对于孟总的问题作出以下回复：

1.关于迎春老师提出的合同问题合同已更新。

2.销售合同九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器合同编号为YCHD2026-033。

3.公共云没有版本限制。

4.1）灵码私有化平台交付 - 这个是由阿里云老师现场进行安装部署

 2）IDE插件交付 - 这个是由阿里云提供，通过下载连接和平台内置的插件安装包(.zip)文件给到客户，然后客户在自己电脑安装插件即可。

请审批！', 0, ARRAY[]::varchar[], '2026-04-22 15:35:17', '2026-04-22 15:35:17');

-- ============ 评论回复 ============
INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000301', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000201', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', E'确认，已与客户沟通目标成交价，为锁定硬件采购价，提前采购阿里GPU设备。', 0, ARRAY[]::varchar[], '2026-02-05 09:03:36', '2026-02-05 09:03:36');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000302', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000202', 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', E'同意，请尽快完成销售合同签署，注意把控执行风险。', 0, ARRAY[]::varchar[], '2026-02-05 16:03:18', '2026-02-05 16:03:18');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000303', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000202', 'f9c21e4f-11eb-4793-b0f2-02219bcb4542', E'无异议', 0, ARRAY[]::varchar[], '2026-02-05 16:12:47', '2026-02-05 16:12:47');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000304', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000202', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-02-05 16:24:27', '2026-02-05 16:24:27');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000305', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000203', '6216d133-4017-41e4-8f27-b714cd72ab25', E'就合同文本：当前无上游合同，无法评估条款对应性，请注意相关内容的对应与风险防范；

另，合同第20页明确约定，乙方不承担安装部署服务，损益表显示该合同为硬件产品销售、无实施工作量，请关注该合同是否不涉及安装部署服务。', 0, ARRAY[]::varchar[], '2026-02-06 09:01:05', '2026-02-06 09:01:05');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000306', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000204', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-02-12 10:32:10', '2026-02-12 10:32:10');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000307', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000204', '6216d133-4017-41e4-8f27-b714cd72ab25', E'当前损益与此前申请采购先签时提供的损益有巨大出入，包括采购内容、供应商、利润率等，均出现大幅变动；

基于当前显示，合同为一对多的纯代理合同，请关注上下游合同对应性。', 0, ARRAY[]::varchar[], '2026-02-12 14:03:52', '2026-02-12 14:03:52');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000308', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000204', 'a0000001-0000-0000-0000-000000000001', E'同意投标！', 0, ARRAY[]::varchar[], '2026-02-12 15:16:12', '2026-02-12 15:16:12');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000309', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000205', 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', E'请确保所有成本已预估￥损益表预估无遗漏，其他无异议', 0, ARRAY[]::varchar[], '2026-02-12 16:17:28', '2026-02-12 16:17:28');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000310', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000206', 'f9c21e4f-11eb-4793-b0f2-02219bcb4542', E'无异议', 0, ARRAY[]::varchar[], '2026-02-13 07:55:28', '2026-02-13 07:55:28');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000311', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000206', 'c75af014-ff4e-4720-8199-c779720cccb8', E'各位领导好：

阿里云采购合同在附件：商务条款5.其他约定增加了本合同一式肆份，甲乙双方各执贰份，具有同等法律效力（如图）。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-02-13 10:47:15', '2026-02-13 10:47:15');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000312', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000206', 'c75af014-ff4e-4720-8199-c779720cccb8', E'各位领导好：

需要先盖章的阿里云采购合同是(YCHD-ZB-2026-015)九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器(采购阿里云)

请胡总确认一下。', 0, ARRAY[]::varchar[], '2026-02-13 10:53:53', '2026-02-13 10:53:53');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000313', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000206', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', E'确认。', 0, ARRAY[]::varchar[], '2026-02-13 11:25:42', '2026-02-13 11:25:42');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000314', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000206', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-02-13 11:38:26', '2026-02-13 11:38:26');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000315', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000206', 'a0000001-0000-0000-0000-000000000001', E'确认！', 0, ARRAY[]::varchar[], '2026-02-13 11:38:57', '2026-02-13 11:38:57');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000316', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000206', '15f0dc3b-1473-4523-b698-4419ea5f45ef', E'鉴于此合同倒置问题跟付款模式已经经过特批。但是预审的上下游对应现在无法全面评估。
此次仅为了采购行为本身做了责任分解跟落实。临近年底硬件市场价格波动大，等上下游合同都到齐之后再做正式审定。
在此之前请做好风险防控跟责任落实，变动的条款请及时记录并落实防控措施。

其他无异议。', 0, ARRAY[]::varchar[], '2026-02-13 12:32:42', '2026-02-13 12:32:42');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000317', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000208', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-03-23 20:08:47', '2026-03-23 20:08:47');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000318', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000208', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', E'确认。', 0, ARRAY[]::varchar[], '2026-03-24 08:27:21', '2026-03-24 08:27:21');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000319', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000208', 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', E'无异议', 0, ARRAY[]::varchar[], '2026-03-24 09:45:13', '2026-03-24 09:45:13');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000320', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000209', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-03-24 10:53:06', '2026-03-24 10:53:06');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000321', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000209', 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', E'同意', 0, ARRAY[]::varchar[], '2026-03-24 14:45:56', '2026-03-24 14:45:56');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000322', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000210', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-03-24 15:47:44', '2026-03-24 15:47:44');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000323', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000210', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', E'确认，减少了耗材采购。', 0, ARRAY[]::varchar[], '2026-03-24 15:48:58', '2026-03-24 15:48:58');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000324', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000210', '15f0dc3b-1473-4523-b698-4419ea5f45ef', E'请做好执行风险，保留关键的变更证据。

其他无异议。', 0, ARRAY[]::varchar[], '2026-03-24 16:03:02', '2026-03-24 16:03:02');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000325', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000212', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-03-31 15:08:10', '2026-03-31 15:08:10');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000326', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000212', 'aebe2c36-6588-4613-9b35-8fcfe160562a', E'各位领导，

      附件为浪潮合同里具体报价及相关配件，详情见附件合同。', 0, ARRAY[]::varchar[], '2026-03-31 15:29:46', '2026-03-31 15:29:46');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000327', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000212', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', E'采购合同与招标要求不符，经销售沟通，目前采购阿里的整机+拿到的浪潮原厂邮件附件与招标要求已符合。', 0, ARRAY[]::varchar[], '2026-03-31 17:40:45', '2026-03-31 17:40:45');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000328', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000212', '15f0dc3b-1473-4523-b698-4419ea5f45ef', E'情况特殊。请bd跟交付切实落实风险控制。
其他无异议。', 0, ARRAY[]::varchar[], '2026-03-31 18:06:08', '2026-03-31 18:06:08');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000329', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000213', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-04-08 17:29:48', '2026-04-08 17:29:48');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000330', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000214', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-04-09 10:36:50', '2026-04-09 10:36:50');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000331', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000214', 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', E'无异议', 0, ARRAY[]::varchar[], '2026-04-09 15:32:12', '2026-04-09 15:32:12');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000332', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000215', '6216d133-4017-41e4-8f27-b714cd72ab25', E'请提供全套上下游合同标的物拆分、及签署进度表。', 0, ARRAY[]::varchar[], '2026-04-16 13:54:27', '2026-04-16 13:54:27');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000333', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000215', '6216d133-4017-41e4-8f27-b714cd72ab25', E'进度表显示25万合同签署方为通义云，但采购合同文本为阿里云，请复核实际情况；

采购阿里合同第10页，售后响应级别未勾选，应勾选为7*24小时；

采购阿里合同附件2验收报告模板中，乙方公司名称填写错误；

采购通义云合同与采购阿里云合同疑似标识错误；

综上，合同基础问题过多，请先行清晰梳理。', 0, ARRAY[]::varchar[], '2026-04-17 14:48:49', '2026-04-17 14:48:49');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000335', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000216', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-04-21 11:03:21', '2026-04-21 11:03:21');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000336', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000216', '15f0dc3b-1473-4523-b698-4419ea5f45ef', E'合同基础性错误为啥就都无视了？这些不修改是不行的', 0, ARRAY[]::varchar[], '2026-04-21 11:23:26', '2026-04-21 11:23:26');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000337', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-04-22 15:54:08', '2026-04-22 15:54:08');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000338', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', '6216d133-4017-41e4-8f27-b714cd72ab25', E'该合同孟总已多次与相关责任人就标的物、合同内应勾选内容、合同编号补充等事宜进行充分沟通，当前无明确反馈；

请各位领导复审批示。', 0, ARRAY[]::varchar[], '2026-04-22 16:16:01', '2026-04-22 16:16:01');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000339', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'c75af014-ff4e-4720-8199-c779720cccb8', E'各位领导好：

关于合同作出以下回复：

1.合同对应标的物在王建磊老师之前回复的邮件中已回复（如图），相关附件上下游合同标的物拆分及签署进度表已附上。2.关于九江银行2026年算力服务器（采购阿里云灵码私有化）合同内应勾选内容已于下图邮件更新（如图所示），已附上pdf版合同。

3.如无特别说明没有勾起来是因为，已问过阿里云的老师，这是软件合同不需要勾起来(如图）。

4.通义云启公共云灵码合同对应合同编号为YCHD-ZB-2026-037，九江银行2026年算力服务器（采购阿里云灵码私有化）对应合同编号为YCHD-ZB-2026-048。

请各位领导复审！', 0, ARRAY[]::varchar[], '2026-04-23 10:09:06', '2026-04-23 10:09:06');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000340', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', E'确认。', 0, ARRAY[]::varchar[], '2026-04-24 10:40:51', '2026-04-24 10:40:51');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000341', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-04-24 10:46:03', '2026-04-24 10:46:03');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000342', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'c75af014-ff4e-4720-8199-c779720cccb8', E'各位领导好：

九江银行2026年算力服务器（采购阿里云灵码私有化）合同修改了9.1，9.2，9.5（如图所示）。 

 

增加了14.3

请审批！', 0, ARRAY[]::varchar[], '2026-04-27 10:50:01', '2026-04-27 10:50:01');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000343', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', '6216d133-4017-41e4-8f27-b714cd72ab25', E'采购阿里合同第2页，合同约定有甲方及最终用户安装部署，与邮件描述不符；

上下游合同条款及标的物描述存在出入；

综上，请各位领导复审评估。', 0, ARRAY[]::varchar[], '2026-04-27 15:06:24', '2026-04-27 15:06:24');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000344', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'c75af014-ff4e-4720-8199-c779720cccb8', E'各位领导好：

对于迎春老师提出的问题作出以下回复：

1.合同写甲方及最终用户安装部署，但实际是由阿里负责，目前阿里安装部署服务已完成。由于这个服务是阿里销售个人协调的，所以合同只能写由甲方及最终用户安装部署。

请各位领导审批！', 0, ARRAY[]::varchar[], '2026-04-27 16:16:32', '2026-04-27 16:16:32');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000345', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', E'确认。', 0, ARRAY[]::varchar[], '2026-04-27 18:01:15', '2026-04-27 18:01:15');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000346', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'a0000001-0000-0000-0000-000000000001', E'同意！', 0, ARRAY[]::varchar[], '2026-04-27 18:25:11', '2026-04-27 18:25:11');

INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
VALUES ('d0000030-0001-0001-0001-000000000347', 'b0000001-0001-0001-0001-000000000001', NULL, 'd0000020-0001-0001-0001-000000000217', 'c75af014-ff4e-4720-8199-c779720cccb8', E'各位领导好：

九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器（采购灵码私有化）供应商提出交付方式选为其他（如图所示）。

请审批！', 0, ARRAY[]::varchar[], '2026-05-14 17:29:44', '2026-05-14 17:29:44');
