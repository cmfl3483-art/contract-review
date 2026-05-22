"""
创建压力测试数据
Create Stress Test Data

生成大量测试数据用于压力测试:
- 测试用户
- 测试合同
- 测试评审记录
- 测试评论

运行方式:
python scripts/create_stress_test_data.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import random
from uuid import uuid4

from app.core.database import async_session_maker
from app.models.user import User
from app.models.contract import Contract
from app.models.review import Review
from app.models.comment import Comment


class StressTestDataGenerator:
    """压力测试数据生成器"""
    
    def __init__(self):
        self.users = []
        self.contracts = []
        self.reviews = []
    
    async def create_test_users(self, db: AsyncSession, count: int = 50):
        """创建测试用户"""
        print(f"\n创建 {count} 个测试用户...")
        
        roles = ["销售", "法务", "财务", "业务", "运营", "人事"]
        
        for i in range(1, count + 1):
            user = User(
                id=uuid4(),
                dingtalk_user_id=f"stress_test_user_{i}",
                dingtalk_union_id=f"stress_test_union_{i}",
                name=f"压力测试用户{i}",
                role=random.choice(roles),
                email=f"stress_test_{i}@example.com",
                mobile=f"1380000{i:04d}",
                department=f"测试部门{random.randint(1, 10)}",
            )
            db.add(user)
            self.users.append(user)
            
            if i % 10 == 0:
                await db.flush()
                print(f"  已创建 {i}/{count} 个用户")
        
        await db.commit()
        print(f"✅ 成功创建 {count} 个测试用户")
    
    async def create_test_contracts(self, db: AsyncSession, count: int = 1000):
        """创建测试合同"""
        print(f"\n创建 {count} 个测试合同...")
        
        if not self.users:
            # 加载已存在的用户
            result = await db.execute(
                select(User).where(User.dingtalk_user_id.like("stress_test_user_%"))
            )
            self.users = list(result.scalars().all())
        
        if not self.users:
            print("❌ 没有找到测试用户,请先创建测试用户")
            return
        
        statuses = ["progress", "completed"]
        contract_types = ["采购合同", "销售合同", "服务合同", "租赁合同", "劳动合同"]
        
        for i in range(1, count + 1):
            initiator = random.choice(self.users)
            cc_users = random.sample([u.id for u in self.users], k=random.randint(1, 5))
            
            # 随机生成创建时间 (过去 90 天内)
            days_ago = random.randint(0, 90)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            contract = Contract(
                id=uuid4(),
                name=f"{random.choice(contract_types)}_{i}_{created_at.strftime('%Y%m%d')}",
                description=f"这是第 {i} 个压力测试合同,用于测试系统性能。",
                status=random.choice(statuses),
                initiator_id=initiator.id,
                cc_users=cc_users,
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(contract)
            self.contracts.append(contract)
            
            if i % 100 == 0:
                await db.flush()
                print(f"  已创建 {i}/{count} 个合同")
        
        await db.commit()
        print(f"✅ 成功创建 {count} 个测试合同")
    
    async def create_test_reviews(self, db: AsyncSession, reviews_per_contract: int = 5):
        """创建测试评审记录"""
        print(f"\n为每个合同创建 {reviews_per_contract} 个评审记录...")
        
        if not self.contracts:
            # 加载已存在的合同
            result = await db.execute(
                select(Contract).where(Contract.name.like("%压力测试合同%"))
            )
            self.contracts = list(result.scalars().all())
        
        if not self.contracts:
            print("❌ 没有找到测试合同,请先创建测试合同")
            return
        
        if not self.users:
            # 加载已存在的用户
            result = await db.execute(
                select(User).where(User.dingtalk_user_id.like("stress_test_user_%"))
            )
            self.users = list(result.scalars().all())
        
        statuses = ["pending", "reviewing", "approved"]
        roles = ["销售", "法务", "财务", "业务", "运营", "人事"]
        steps = ["初审", "复审", "终审"]
        
        opinions = [
            "同意并通过",
            "建议修改合同条款第3条",
            "需要补充财务预算说明",
            "法务审核通过,无风险",
            "建议增加违约责任条款",
            "合同金额需要财务总监审批",
            "同意,但需要补充附件",
            "风险可控,同意签署",
        ]
        
        total_reviews = len(self.contracts) * reviews_per_contract
        created_count = 0
        
        for contract in self.contracts:
            reviewers = random.sample(self.users, k=reviews_per_contract)
            
            for reviewer in reviewers:
                # 随机生成创建时间 (合同创建后)
                hours_after = random.randint(1, 48)
                created_at = contract.created_at + timedelta(hours=hours_after)
                
                review = Review(
                    id=uuid4(),
                    contract_id=contract.id,
                    reviewer_id=reviewer.id,
                    role=random.choice(roles),
                    step=random.choice(steps),
                    opinion=random.choice(opinions),
                    status=random.choice(statuses),
                    likes=random.randint(0, 10),
                    liked_by=[],
                    created_at=created_at,
                    updated_at=created_at,
                )
                db.add(review)
                self.reviews.append(review)
                created_count += 1
                
                if created_count % 500 == 0:
                    await db.flush()
                    print(f"  已创建 {created_count}/{total_reviews} 个评审记录")
        
        await db.commit()
        print(f"✅ 成功创建 {total_reviews} 个评审记录")
    
    async def create_test_comments(self, db: AsyncSession, comments_per_review: int = 2):
        """创建测试评论"""
        print(f"\n为每个评审创建 {comments_per_review} 个评论...")
        
        if not self.reviews:
            # 加载已存在的评审
            result = await db.execute(
                select(Review)
                .join(Contract)
                .where(Contract.name.like("%压力测试合同%"))
            )
            self.reviews = list(result.scalars().all())
        
        if not self.reviews:
            print("❌ 没有找到测试评审,请先创建测试评审")
            return
        
        if not self.users:
            # 加载已存在的用户
            result = await db.execute(
                select(User).where(User.dingtalk_user_id.like("stress_test_user_%"))
            )
            self.users = list(result.scalars().all())
        
        comment_contents = [
            "同意你的意见",
            "这个问题需要进一步讨论",
            "已经修改,请查看最新版本",
            "感谢反馈,我会尽快处理",
            "这个条款确实需要优化",
            "已经和客户沟通过了",
            "财务部门已经审批通过",
            "法务意见已经采纳",
        ]
        
        total_comments = len(self.reviews) * comments_per_review
        created_count = 0
        
        for review in self.reviews:
            for _ in range(comments_per_review):
                author = random.choice(self.users)
                
                # 随机生成创建时间 (评审创建后)
                hours_after = random.randint(1, 24)
                created_at = review.created_at + timedelta(hours=hours_after)
                
                comment = Comment(
                    id=uuid4(),
                    contract_id=review.contract_id,
                    review_id=review.id,
                    parent_comment_id=None,
                    author_id=author.id,
                    content=random.choice(comment_contents),
                    likes=random.randint(0, 5),
                    liked_by=[],
                    created_at=created_at,
                    updated_at=created_at,
                )
                db.add(comment)
                created_count += 1
                
                if created_count % 1000 == 0:
                    await db.flush()
                    print(f"  已创建 {created_count}/{total_comments} 个评论")
        
        await db.commit()
        print(f"✅ 成功创建 {total_comments} 个评论")
    
    async def generate_all(
        self,
        user_count: int = 50,
        contract_count: int = 1000,
        reviews_per_contract: int = 5,
        comments_per_review: int = 2,
    ):
        """生成所有测试数据"""
        print("=" * 80)
        print("开始生成压力测试数据")
        print("=" * 80)
        print(f"\n配置:")
        print(f"  - 用户数: {user_count}")
        print(f"  - 合同数: {contract_count}")
        print(f"  - 每合同评审数: {reviews_per_contract}")
        print(f"  - 每评审评论数: {comments_per_review}")
        print(f"\n预计生成:")
        print(f"  - 评审记录: {contract_count * reviews_per_contract}")
        print(f"  - 评论: {contract_count * reviews_per_contract * comments_per_review}")
        
        async with async_session_maker() as db:
            try:
                # 创建用户
                await self.create_test_users(db, user_count)
                
                # 创建合同
                await self.create_test_contracts(db, contract_count)
                
                # 创建评审记录
                await self.create_test_reviews(db, reviews_per_contract)
                
                # 创建评论
                await self.create_test_comments(db, comments_per_review)
                
                print("\n" + "=" * 80)
                print("✅ 所有测试数据生成完成!")
                print("=" * 80)
                
            except Exception as e:
                print(f"\n❌ 生成测试数据失败: {e}")
                await db.rollback()
                raise
    
    async def cleanup(self):
        """清理测试数据"""
        print("\n" + "=" * 80)
        print("清理压力测试数据")
        print("=" * 80)
        
        async with async_session_maker() as db:
            try:
                # 删除评论
                result = await db.execute(
                    select(Comment)
                    .join(Contract)
                    .where(Contract.name.like("%压力测试合同%"))
                )
                comments = result.scalars().all()
                for comment in comments:
                    await db.delete(comment)
                print(f"✅ 删除 {len(comments)} 个评论")
                
                # 删除评审
                result = await db.execute(
                    select(Review)
                    .join(Contract)
                    .where(Contract.name.like("%压力测试合同%"))
                )
                reviews = result.scalars().all()
                for review in reviews:
                    await db.delete(review)
                print(f"✅ 删除 {len(reviews)} 个评审记录")
                
                # 删除合同
                result = await db.execute(
                    select(Contract).where(Contract.name.like("%压力测试合同%"))
                )
                contracts = result.scalars().all()
                for contract in contracts:
                    await db.delete(contract)
                print(f"✅ 删除 {len(contracts)} 个合同")
                
                # 删除用户
                result = await db.execute(
                    select(User).where(User.dingtalk_user_id.like("stress_test_user_%"))
                )
                users = result.scalars().all()
                for user in users:
                    await db.delete(user)
                print(f"✅ 删除 {len(users)} 个用户")
                
                await db.commit()
                
                print("\n" + "=" * 80)
                print("✅ 测试数据清理完成!")
                print("=" * 80)
                
            except Exception as e:
                print(f"\n❌ 清理测试数据失败: {e}")
                await db.rollback()
                raise


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成压力测试数据")
    parser.add_argument(
        "--action",
        choices=["generate", "cleanup"],
        default="generate",
        help="操作类型: generate (生成数据) 或 cleanup (清理数据)",
    )
    parser.add_argument("--users", type=int, default=50, help="用户数量")
    parser.add_argument("--contracts", type=int, default=1000, help="合同数量")
    parser.add_argument("--reviews", type=int, default=5, help="每合同评审数")
    parser.add_argument("--comments", type=int, default=2, help="每评审评论数")
    
    args = parser.parse_args()
    
    generator = StressTestDataGenerator()
    
    if args.action == "generate":
        await generator.generate_all(
            user_count=args.users,
            contract_count=args.contracts,
            reviews_per_contract=args.reviews,
            comments_per_review=args.comments,
        )
    elif args.action == "cleanup":
        await generator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
