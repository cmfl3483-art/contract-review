"""
测试 AI 顾问问答 API
验证 POST /api/ai/advisor 端点功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.contract import Contract
from app.models.review import Review
from app.models.user import User
from app.services.ai_service import AIService


async def test_ai_advisor():
    """测试 AI 顾问问答功能"""
    
    print("=" * 60)
    print("测试 AI 顾问问答 API")
    print("=" * 60)
    
    async with async_session_maker() as db:
        try:
            # 1. 查找测试合同
            print("\n1. 查找测试合同...")
            contract_query = select(Contract).limit(1)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()
            
            if not contract:
                print("❌ 没有找到测试合同")
                return
            
            print(f"✅ 找到合同: {contract.name} (ID: {contract.id})")
            
            # 2. 查找评审记录
            print("\n2. 查找评审记录...")
            reviews_query = select(Review).where(Review.contract_id == contract.id)
            reviews_result = await db.execute(reviews_query)
            reviews = reviews_result.scalars().all()
            
            print(f"✅ 找到 {len(reviews)} 条评审记录")
            for review in reviews:
                print(f"   - {review.role} ({review.status}): {review.opinion or '无意见'}")
            
            # 3. 查找测试用户
            print("\n3. 查找测试用户...")
            user_query = select(User).limit(1)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                print("❌ 没有找到测试用户")
                return
            
            print(f"✅ 找到用户: {user.name} (ID: {user.id})")
            
            # 4. 测试 AI 顾问服务
            print("\n4. 测试 AI 顾问服务...")
            ai_service = AIService()
            
            # 测试问题列表
            test_questions = [
                "法务意见是什么?",
                "有哪些风险项?",
                "待我处理的任务有哪些?",
                "合同的整体情况如何?"
            ]
            
            for question in test_questions:
                print(f"\n问题: {question}")
                answer = await ai_service.answer_question(
                    contract_id=contract.id,
                    question=question,
                    current_user_id=user.id,
                    db=db
                )
                print(f"回答: {answer}")
            
            print("\n" + "=" * 60)
            print("✅ AI 顾问问答 API 测试完成")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ai_advisor())
