"""
导入邮件往来记录到合同预审系统
"""
import sys
import os
sys.path.insert(0, '/app')

import asyncio
from datetime import datetime
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.contract import Contract, ContractStatus
from app.models.review import Review, ReviewStatus
from app.models.comment import Comment

# === 用户映射 ===
# 已存在的用户
EXISTING_USERS = {
    '胡首': 'c3f56e8c-ad8a-4b9d-8485-d4e836dc88f8',
    '孔繁强': 'c8d2f101-e9d5-4c22-ac69-ee8ae5d29964',
    '王朋': '4198cc78-39ca-4169-bf3d-87bde4a59b42',
    '陈敏': '671c7caf-1042-4755-94fd-db87b8c0042e',
    '谢明宇': '5a81730a-0421-40f8-af82-bb25436c4ec5',
}

# 需要创建的用户 (name -> role, dingtalk_id, email)
USERS_TO_CREATE = {
    '常佳宇': ('销售', 'mock_changjy', 'changjy@belink.com'),
    '赵迎春': ('法务', 'mock_zhaoyc1', 'zhaoyc1@belink.com'),
    '孟涛': ('法务', 'mock_mengtao', 'mengtao@belink.com'),
    '畅红霞': ('财务', 'mock_changhx', 'changhx@belink.com'),
    '周喜春': ('销售', 'mock_zhouxc', 'zhouxc@belink.com'),
    '王建磊': ('业务', 'mock_wangjl1', 'wangjl1@belink.com'),
    '王娅惠': ('销售', 'mock_wangyh', 'wangyh@belink.com'),
    '吕海青': ('业务', 'mock_lvhq', 'lvhq@belink.com'),
    '吴起玥': ('业务', 'mock_wuqy', 'wuqy@belink.com'),
    '王宇航': ('业务', 'mock_wangyh3', 'wangyh3@belink.com'),
    '边莹': ('业务', 'mock_bianying', 'bianying@belink.com'),
    '陈宇': ('业务', 'mock_chenyu', 'chenyu@belink.com'),
    '毛福建': ('业务', 'mock_maofj', 'maofj@belink.com'),
    '曾硕': ('业务', 'mock_zengshuo', 'zengshuo@belink.com'),
}

async def main():
    async with AsyncSessionLocal() as session:
        # === 1. 创建缺失的用户 ===
        print("=== 创建缺失用户 ===")
        user_map = dict(EXISTING_USERS)  # name -> uuid string

        for name, (role, dingtalk_id, email) in USERS_TO_CREATE.items():
            # 检查是否已存在
            result = await session.execute(
                select(User).where(User.name == name)
            )
            existing = result.scalar_one_or_none()
            if existing:
                user_map[name] = str(existing.id)
                print(f"  用户 {name} 已存在: {existing.id}")
                continue

            from uuid import uuid4
            uid = str(uuid4())
            await session.execute(text("""
                INSERT INTO users (id, dingtalk_user_id, name, role, email, created_at, updated_at)
                VALUES (:id, :dingtalk_id, :name, :role, :email, NOW(), NOW())
            """), {
                'id': uid,
                'dingtalk_id': dingtalk_id,
                'name': name,
                'role': role,
                'email': email,
            })
            user_map[name] = uid
            print(f"  创建用户: {name} ({role}) -> {uid}")

        await session.commit()
        print()

        # === 2. 创建合同 ===
        print("=== 创建合同 ===")
        from uuid import uuid4

        contracts = {}

        # 合同1: YCHD2026-033 主合同
        c1_id = str(uuid4())
        cc_users_1 = [user_map['陈敏'], user_map['谢明宇'], user_map['周喜春'], user_map['王娅惠'], user_map['孔繁强'], user_map['王朋']]
        await session.execute(text("""
            INSERT INTO contracts (id, name, description, status, initiator_id, cc_users, version, created_at, updated_at)
            VALUES (:id, :name, :desc, 'progress', :initiator, :cc_users, 1, '2026-02-05 16:49:00', '2026-05-14 17:29:00')
        """), {
            'id': c1_id,
            'name': 'YCHD2026-033 九江银行鄱阳湖数据中心灾备完善项目-GPU算力服务器',
            'desc': '商机编号: XS-2026_0122\n\n预计销售金额: 6,852,000.00元\n采购合同金额: 5,944,009.00元\n毛利率: 11.61%\n\n采购明细:\n- 阿里云PPU采购: 5,250,000.00元(税率13%)\n- 灵码私有化版本及安装: 250,000.00元(税率13%)\n- 公共云灵码企业标准版: 30,336.00元(税率6%)\n- 浪潮RAID卡: 52,773.00元(税率13%)\n- 浪潮维保服务: 360,900.00元(税率6%)\n\n共经历5轮合同预审，涉及特批申请、投标申请、用印特批等流程。',
            'initiator': user_map['常佳宇'],
            'cc_users': cc_users_1,
        })
        contracts['YCHD2026-033'] = c1_id
        print(f"  合同1: YCHD2026-033 -> {c1_id}")

        # 合同2: YCHD-ZB-2026-037 采购公共云灵码
        c2_id = str(uuid4())
        cc_users_2 = [user_map['陈敏'], user_map['谢明宇'], user_map['周喜春'], user_map['胡首']]
        await session.execute(text("""
            INSERT INTO contracts (id, name, description, status, initiator_id, cc_users, version, created_at, updated_at)
            VALUES (:id, :name, :desc, 'progress', :initiator, :cc_users, 1, '2026-04-22 15:35:00', '2026-05-14 17:29:00')
        """), {
            'id': c2_id,
            'name': 'YCHD-ZB-2026-037 采购公共云灵码',
            'desc': '商机编号: XS-2026_0122\n\n采购通义云启公共云灵码，40人年版本。\n采购金额: 30,336.00元(税率6%)\n\n需先充值后生成合同，已通过特批先付款再走盖章流程。',
            'initiator': user_map['常佳宇'],
            'cc_users': cc_users_2,
        })
        contracts['YCHD-ZB-2026-037'] = c2_id
        print(f"  合同2: YCHD-ZB-2026-037 -> {c2_id}")

        # 合同3: YCHD-ZB-2026-048 采购灵码私有化
        c3_id = str(uuid4())
        cc_users_3 = [user_map['陈敏'], user_map['谢明宇'], user_map['周喜春'], user_map['胡首']]
        await session.execute(text("""
            INSERT INTO contracts (id, name, description, status, initiator_id, cc_users, version, created_at, updated_at)
            VALUES (:id, :name, :desc, 'progress', :initiator, :cc_users, 1, '2026-04-22 15:35:00', '2026-05-14 17:29:00')
        """), {
            'id': c3_id,
            'name': 'YCHD-ZB-2026-048 采购灵码私有化',
            'desc': '商机编号: XS-2026_0122\n\n采购阿里云灵码私有化平台，1500人/永久版本。\n采购金额: 250,000.00元(税率13%)\n\n含灵码私有化平台交付及IDE插件交付。供应商提出交付方式选为"其他"，待审批。',
            'initiator': user_map['常佳宇'],
            'cc_users': cc_users_3,
        })
        contracts['YCHD-ZB-2026-048'] = c3_id
        print(f"  合同3: YCHD-ZB-2026-048 -> {c3_id}")

        await session.commit()
        print()

        # === 3. 创建评审记录 ===
        print("=== 创建评审记录 ===")

        # 合同1的评审人
        c1_reviewers = [
            ('赵迎春', '法务', '内核审核', 'approved',
             '就合同文本：当前无上游合同，无法评估条款对应性，请注意相关内容的对应与风险防范；\n'
             '另，合同第20页明确约定，乙方不承担安装部署服务，损益表显示该合同为硬件产品销售、无实施工作量，请关注该合同是否不涉及安装部署服务。\n\n'
             '第二轮意见：采购阿里合同第2页合同约定有甲方及最终用户安装部署，与邮件描述不符；上下游合同条款及标的物描述存在出入。请各位领导复审评估。',
             '2026-02-05 16:49:00'),
            ('孟涛', '法务', '内核复核', 'approved',
             '鉴于此合同倒置问题跟付款模式已经经过特批。但预审的上下游对应现在无法全面评估。'
             '此次仅为了采购行为本身做了责任分解跟落实。在此之前请做好风险防控跟责任落实，变动的条款请及时记录并落实防控措施。其他无异议。',
             '2026-02-13 12:32:00'),
            ('王建磊', '业务', '交付确认', 'approved',
             '针对此项目，销售合同里的硬件部分已经签约（阿里的整机采购及浪潮采购），此次为增值服务的采购，包含公共云灵码和灵码私有化。'
             '采购范围确认：核心内容（公共云灵码：40人年；灵码私有化：1500人/永久）与销售合同要求符合。'
             '损益表确认：公共云灵码由原来预算的37,920.00元调整为实际的30,336.00元，毛利率由11.51%更新为11.61%，确认没问题。',
             '2026-04-20 17:33:00'),
            ('胡首', '业务', '管理层审批', 'approved',
             '同意！',
             '2026-04-21 11:03:00'),
            ('周喜春', '销售', '销售确认', 'approved',
             '确认。采购合同与招标要求不符，经销售沟通，目前采购阿里的整机+拿到的浪潮原厂邮件附件与招标要求已符合。',
             '2026-03-31 17:40:00'),
        ]

        review_ids = {}
        for name, role, step, status, opinion, created_at in c1_reviewers:
            r_id = str(uuid4())
            await session.execute(text("""
                INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
                VALUES (:id, :contract_id, :reviewer_id, :role, :step, :opinion, :status, 0, '{}', :created_at, :updated_at)
            """), {
                'id': r_id,
                'contract_id': c1_id,
                'reviewer_id': user_map[name],
                'role': role,
                'step': step,
                'opinion': opinion,
                'status': status,
                'created_at': created_at,
                'updated_at': created_at,
            })
            review_ids[f'c1_{name}'] = r_id
            print(f"  评审: {name} ({step}) -> {status}")

        # 合同2的评审人
        c2_reviewers = [
            ('赵迎春', '法务', '内核审核', 'pending',
             '该合同孟总已多次与相关责任人就标的物、合同内应勾选内容、合同编号补充等事宜进行充分沟通，当前无明确反馈。请各位领导复审批示。',
             '2026-04-22 16:16:00'),
            ('孟涛', '法务', '内核复核', 'pending',
             '合同基础性错误为啥就都无视了？这些不修改是不行的。',
             '2026-04-21 11:23:00'),
            ('胡首', '业务', '管理层审批', 'approved',
             '同意！',
             '2026-04-22 15:54:00'),
        ]

        for name, role, step, status, opinion, created_at in c2_reviewers:
            r_id = str(uuid4())
            await session.execute(text("""
                INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
                VALUES (:id, :contract_id, :reviewer_id, :role, :step, :opinion, :status, 0, '{}', :created_at, :updated_at)
            """), {
                'id': r_id,
                'contract_id': c2_id,
                'reviewer_id': user_map[name],
                'role': role,
                'step': step,
                'opinion': opinion,
                'status': status,
                'created_at': created_at,
                'updated_at': created_at,
            })
            review_ids[f'c2_{name}'] = r_id
            print(f"  评审: {name} ({step}) -> {status}")

        # 合同3的评审人
        c3_reviewers = [
            ('赵迎春', '法务', '内核审核', 'pending',
             '采购阿里合同第2页，合同约定有甲方及最终用户安装部署，与邮件描述不符；上下游合同条款及标的物描述存在出入。请各位领导复审评估。',
             '2026-04-27 15:06:00'),
            ('孟涛', '法务', '内核复核', 'pending',
             '情况特殊。请bd跟交付切实落实风险控制。其他无异议。',
             '2026-03-31 18:06:00'),
            ('胡首', '业务', '管理层审批', 'approved',
             '同意！',
             '2026-04-27 18:25:00'),
        ]

        for name, role, step, status, opinion, created_at in c3_reviewers:
            r_id = str(uuid4())
            await session.execute(text("""
                INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)
                VALUES (:id, :contract_id, :reviewer_id, :role, :step, :opinion, :status, 0, '{}', :created_at, :updated_at)
            """), {
                'id': r_id,
                'contract_id': c3_id,
                'reviewer_id': user_map[name],
                'role': role,
                'step': step,
                'opinion': opinion,
                'status': status,
                'created_at': created_at,
                'updated_at': created_at,
            })
            review_ids[f'c3_{name}'] = r_id
            print(f"  评审: {name} ({step}) -> {status}")

        await session.commit()
        print()

        # === 4. 创建评论 ===
        print("=== 创建评论 ===")

        # 合同1的关键评论
        c1_comments = [
            # 常佳宇发起预审
            (user_map['常佳宇'], None, None,
             '各位领导好：\n\n九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器，附件为损益表和阿里云采购合同。\n预计销售金额为6,600,000.00元，阿里云采购成本为5,250,000.00元，税率13%。\n为了锁定低价货源，希望先审批阿里云的采购合同。请各位领导审批！',
             '2026-02-05 16:49:00'),
            # 赵迎春第四轮详细审核意见
            (user_map['赵迎春'], None, None,
             '1.采购阿里、浪潮合同，均未涉及安装部署责任，销售合同提及了"集成改造"、"安装部署"等附件"软件工作说明书"等服务内容；请复核损益是否为纯代理合同。\n'
             '2.销售合同保修条款的具体要求，采购合同未明确，内容对应性无法评估。\n'
             '3.销售合同违约扣罚比例高，且采购合同未同步；采购合同设有责任限制等条款，销售合同未同步。\n'
             '4.销售合同14.5款约定的增值服务，未见采购合同中的对应内容。\n'
             '5.销售合同标的物为"浪潮英政服务器3台"，与采购2合同标的物无法书面对应。\n'
             '6.销售合同约定永久保密，采购合同未对应。\n'
             '综上，上下游合同有多项核心条款及大量其他条款无法对应，请各位领导复审批示。',
             '2026-03-30 16:24:00'),
            # 王娅惠的六点回复
            (user_map['王娅惠'], None, None,
             '一、集成与安装服务：大部分集成及安装部署服务将通过与阿里另行签订合同实现，已覆盖该部分成本。\n'
             '二、保修条款：从阿里采购3年原厂基础维保+从浪潮采购3年金牌升级+2年金牌续保，合计满足5年金牌维保要求。\n'
             '三、违约及责任条款差异为硬件行业代理模式下的常规情况，特申请特批。\n'
             '四、增值服务对应待与阿里签订的软件服务合同。\n'
             '五、"浪潮英政服务器3台"与阿里采购合同中"浪潮AIstack一体机"为同一硬件设备的不同表述。\n'
             '六、保密条款差异为供应商合规要求导致，特申请特批。',
             '2026-03-31 10:41:00'),
            # 孟涛第五轮意见
            (user_map['孟涛'], None, None,
             '合同基础性错误为啥就都无视了？这些不修改是不行的。',
             '2026-04-21 11:23:00'),
            # 常佳宇回复
            (user_map['常佳宇'], None, None,
             '对于孟总的问题作出以下回复：\n1.关于迎春老师提出的合同问题合同已更新。\n2.销售合同编号为YCHD2026-033。\n3.公共云没有版本限制。\n4.灵码私有化平台交付由阿里云老师现场进行安装部署；IDE插件交付由阿里云提供，通过下载连接和平台内置的插件安装包给到客户。',
             '2026-04-22 15:35:00'),
            # 王娅惠确认部署完成
            (user_map['王娅惠'], None, None,
             '经确认，该合同中约定的所有软件已部署完成！',
             '2026-04-27 17:53:00'),
        ]

        for author_id, review_id, parent_id, content, created_at in c1_comments:
            cm_id = str(uuid4())
            await session.execute(text("""
                INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
                VALUES (:id, :contract_id, :review_id, :parent_id, :author_id, :content, 0, '{}', :created_at, :updated_at)
            """), {
                'id': cm_id,
                'contract_id': c1_id,
                'review_id': review_id,
                'parent_id': parent_id,
                'author_id': author_id,
                'content': content,
                'created_at': created_at,
                'updated_at': created_at,
            })
            print(f"  评论已添加: {created_at}")

        # 合同2/3的关键评论
        c23_comments = [
            # 合同2 - 赵迎春意见
            (user_map['赵迎春'], c2_id,
             '进度表显示25万合同签署方为通义云，但采购合同文本为阿里云，请复核实际情况；采购阿里合同售后响应级别未勾选，应勾选为7*24小时；验收报告模板中乙方公司名称填写错误。',
             '2026-04-17 14:48:00'),
            # 合同2 - 王建磊回复
            (user_map['王建磊'], c2_id,
             '经核实，此合同签署方为：阿里云飞天（杭州）云计算技术有限公司，已更新进度表。',
             '2026-04-17 15:46:00'),
            # 合同3 - 常佳宇说明
            (user_map['常佳宇'], c3_id,
             '对于迎春老师提出的问题：合同写甲方及最终用户安装部署，但实际是由阿里负责，目前阿里安装部署服务已完成。由于这个服务是阿里销售个人协调的，所以合同只能写由甲方及最终用户安装部署。请各位领导审批！',
             '2026-04-27 16:16:00'),
            # 合同3 - 常佳宇最新更新
            (user_map['常佳宇'], c3_id,
             '灵码私有化供应商提出交付方式选为"其他"。请审批！',
             '2026-05-14 17:29:00'),
        ]

        for author_id, contract_id, content, created_at in c23_comments:
            cm_id = str(uuid4())
            await session.execute(text("""
                INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)
                VALUES (:id, :contract_id, NULL, NULL, :author_id, :content, 0, '{}', :created_at, :updated_at)
            """), {
                'id': cm_id,
                'contract_id': contract_id,
                'author_id': author_id,
                'content': content,
                'created_at': created_at,
                'updated_at': created_at,
            })
            print(f"  评论已添加: {created_at}")

        await session.commit()
        print()

        # === 5. 统计结果 ===
        print("=== 导入完成，统计结果 ===")
        for table in ['users', 'contracts', 'reviews', 'comments']:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table}: {count} 条记录")


if __name__ == '__main__':
    asyncio.run(main())
