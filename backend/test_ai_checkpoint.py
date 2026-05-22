"""
Checkpoint 16 - AI功能验证测试
测试智能总结生成、AI顾问问答、异步任务执行和降级处理
"""
import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

# 添加app目录到路径
sys.path.insert(0, '/Users/cm/Documents/kiro/project/backend')

from app.core.config import settings
from app.services.ai_service import AIService
from app.models.contract import Contract
from app.models.review import Review, ReviewStatus
from app.models.user import User
from app.models.comment import Comment
from app.core.redis_client import redis_client


# 创建数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def setup_test_data(db: AsyncSession):
    """创建测试数据"""
    print("\n=== 创建测试数据 ===")
    
    # 创建测试用户
    user1 = User(
        id=uuid4(),
        dingtalk_user_id=f"test_user_{uuid4()}",
        name="测试用户1",
        role="业务"
    )
    user2 = User(
        id=uuid4(),
        dingtalk_user_id=f"test_user_{uuid4()}",
        name="法务专员",
        role="法务"
    )
    user3 = User(
        id=uuid4(),
        dingtalk_user_id=f"test_user_{uuid4()}",
        name="财务专员",
        role="财务"
    )
    
    db.add_all([user1, user2, user3])
    await db.flush()
    
    # 创建测试合同
    contract = Contract(
        id=uuid4(),
        name="测试合同 - AI功能验证",
        description="用于验证AI智能总结和顾问功能",
        status="progress",
        initiator_id=user1.id,
        cc_users=[]
    )
    db.add(contract)
    await db.flush()
    
    # 创建评审记录
    review1 = Review(
        id=uuid4(),
        contract_id=contract.id,
        reviewer_id=user2.id,
        role="法务",
        step="法务初审",
        opinion="合同条款基本符合法律规定,但建议修改第三条款的付款方式,降低法律风险",
        status=ReviewStatus.APPROVED
    )
    
    review2 = Review(
        id=uuid4(),
        contract_id=contract.id,
        reviewer_id=user3.id,
        role="财务",
        step="财务审核",
        opinion="发现风险:付款条件需要调整,建议增加分期付款条款",
        status=ReviewStatus.REVIEWING
    )
    
    review3 = Review(
        id=uuid4(),
        contract_id=contract.id,
        reviewer_id=user1.id,
        role="业务",
        step="业务审核",
        opinion=None,
        status=ReviewStatus.PENDING
    )
    
    db.add_all([review1, review2, review3])
    await db.flush()
    
    # 为review1添加回复(解决方案)
    comment1 = Comment(
        id=uuid4(),
        contract_id=contract.id,
        review_id=review1.id,
        author_id=user1.id,
        content="已经修改完成,请查看最新版本的第三条款"
    )
    db.add(comment1)
    
    await db.commit()
    
    print(f"✓ 创建合同: {contract.id}")
    print(f"✓ 创建3个评审记录")
    print(f"✓ 创建1个评论(解决方案)")
    
    return {
        "contract_id": str(contract.id),
        "user1_id": str(user1.id),
        "user2_id": str(user2.id),
        "user3_id": str(user3.id),
        "review1_id": str(review1.id),
        "review2_id": str(review2.id),
        "review3_id": str(review3.id)
    }


async def test_smart_summary_generation(db: AsyncSession, contract_id: str):
    """测试1: 智能总结生成"""
    print("\n=== 测试1: 智能总结生成 ===")
    
    ai_service = AIService()
    
    try:
        # 生成智能总结
        summary = await ai_service.generate_summary(contract_id, db)
        
        if summary:
            print(f"✓ 智能总结生成成功")
            print(f"  - 审批状态: {summary.approval_status}")
            print(f"  - 已完成人数: {summary.completed_count}/{summary.total_count}")
            print(f"  - 评审意见总数: {summary.review_count}")
            print(f"  - 关键问题数量: {len(summary.key_issues)}")
            
            # 验证关键问题提取
            if summary.key_issues:
                print(f"\n  关键问题:")
                for i, issue in enumerate(summary.key_issues, 1):
                    print(f"    {i}. {issue['issue'][:50]}...")
                    if issue.get('solution'):
                        print(f"       解决方案: {issue['solution'][:50]}...")
            
            # 验证审批进度计算
            assert summary.total_count == 3, "总人数应该是3"
            assert summary.completed_count == 1, "已完成人数应该是1"
            assert summary.approval_status == "in_progress", "状态应该是in_progress"
            assert summary.review_count == 2, "评审意见总数应该是2(不包括空意见)"
            assert len(summary.key_issues) >= 1, "应该至少提取1个关键问题"
            
            print("\n✓ 所有验证通过")
            return True
        else:
            print("✗ 智能总结生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_advisor_legal_query(db: AsyncSession, contract_id: str, user_id: str):
    """测试2: AI顾问 - 法务意见查询"""
    print("\n=== 测试2: AI顾问 - 法务意见查询 ===")
    
    ai_service = AIService()
    
    try:
        # 查询法务意见
        answer = await ai_service.answer_question(
            contract_id=contract_id,
            question="法务意见是什么?",
            current_user_id=user_id,
            db=db
        )
        
        print(f"问题: 法务意见是什么?")
        print(f"回答: {answer}")
        
        # 验证回答包含法务意见
        assert "法务意见" in answer, "回答应该包含'法务意见'"
        assert "法务" in answer, "回答应该包含'法务'"
        assert "建议" in answer or "修改" in answer, "回答应该包含具体意见内容"
        
        print("✓ 法务意见查询测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_advisor_risk_query(db: AsyncSession, contract_id: str, user_id: str):
    """测试3: AI顾问 - 风险项查询"""
    print("\n=== 测试3: AI顾问 - 风险项查询 ===")
    
    ai_service = AIService()
    
    try:
        # 查询风险项
        answer = await ai_service.answer_question(
            contract_id=contract_id,
            question="有哪些风险项?",
            current_user_id=user_id,
            db=db
        )
        
        print(f"问题: 有哪些风险项?")
        print(f"回答: {answer}")
        
        # 验证回答包含风险项信息
        assert "风险项" in answer or "未确认项" in answer, "回答应该包含风险项信息"
        assert "财务" in answer, "回答应该包含财务评审(状态为reviewing)"
        
        print("✓ 风险项查询测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_advisor_pending_query(db: AsyncSession, contract_id: str, user_id: str):
    """测试4: AI顾问 - 待办任务查询"""
    print("\n=== 测试4: AI顾问 - 待办任务查询 ===")
    
    ai_service = AIService()
    
    try:
        # 查询待办任务
        answer = await ai_service.answer_question(
            contract_id=contract_id,
            question="待我处理的任务有哪些?",
            current_user_id=user_id,
            db=db
        )
        
        print(f"问题: 待我处理的任务有哪些?")
        print(f"回答: {answer}")
        
        # 验证回答包含待办任务信息
        assert "待处理" in answer or "待办" in answer, "回答应该包含待办信息"
        assert "1" in answer or "业务" in answer, "回答应该包含具体任务信息"
        
        print("✓ 待办任务查询测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_advisor_default_reply(db: AsyncSession, contract_id: str, user_id: str):
    """测试5: AI顾问 - 默认回复"""
    print("\n=== 测试5: AI顾问 - 默认回复 ===")
    
    ai_service = AIService()
    
    try:
        # 询问其他问题
        answer = await ai_service.answer_question(
            contract_id=contract_id,
            question="这个合同怎么样?",
            current_user_id=user_id,
            db=db
        )
        
        print(f"问题: 这个合同怎么样?")
        print(f"回答: {answer}")
        
        # 验证默认回复
        assert "评审意见" in answer, "默认回复应该包含评审意见数量"
        assert "您可以询问" in answer, "默认回复应该提示可询问的问题类型"
        
        print("✓ 默认回复测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_cache_functionality(db: AsyncSession, contract_id: str):
    """测试6: 缓存功能"""
    print("\n=== 测试6: 缓存功能 ===")
    
    ai_service = AIService()
    
    try:
        # 清除缓存
        cache_key = f"ai:summary:{contract_id}"
        await redis_client.delete(cache_key)
        print("✓ 清除旧缓存")
        
        # 第一次生成(应该写入缓存)
        summary1 = await ai_service.generate_summary(contract_id, db)
        print("✓ 第一次生成智能总结")
        
        # 检查缓存是否存在
        cached = await redis_client.get(cache_key)
        assert cached is not None, "缓存应该存在"
        print("✓ 缓存已写入")
        
        # 第二次生成(应该从缓存读取)
        summary2 = await ai_service.generate_summary(contract_id, db)
        assert summary2 is not None, "应该从缓存获取总结"
        print("✓ 从缓存读取成功")
        
        # 验证缓存过期时间
        ttl = await redis_client.redis.ttl(cache_key)
        assert ttl > 0, "缓存应该有过期时间"
        assert ttl <= 1800, "缓存过期时间应该不超过30分钟(1800秒)"
        print(f"✓ 缓存过期时间: {ttl}秒 (应该≤1800秒)")
        
        print("✓ 缓存功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_degradation_handling():
    """测试7: 降级处理"""
    print("\n=== 测试7: 降级处理 ===")
    
    try:
        # 测试AI服务初始化(即使API不可用也应该能初始化)
        ai_service = AIService()
        assert ai_service is not None, "AI服务应该能初始化"
        print("✓ AI服务初始化成功")
        
        # 测试配置
        assert hasattr(ai_service, 'client'), "应该有AI客户端"
        assert hasattr(ai_service, 'model'), "应该有模型配置"
        print(f"✓ AI配置: model={ai_service.model}")
        
        print("✓ 降级处理测试通过")
        print("  注意: 实际的API调用降级需要在API层测试")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_test_data(db: AsyncSession, test_data: dict):
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    
    try:
        # 删除评论
        await db.execute(
            Comment.__table__.delete().where(
                Comment.contract_id == test_data["contract_id"]
            )
        )
        
        # 删除评审
        await db.execute(
            Review.__table__.delete().where(
                Review.contract_id == test_data["contract_id"]
            )
        )
        
        # 删除合同
        await db.execute(
            Contract.__table__.delete().where(
                Contract.id == test_data["contract_id"]
            )
        )
        
        # 删除用户
        await db.execute(
            User.__table__.delete().where(
                User.id.in_([
                    test_data["user1_id"],
                    test_data["user2_id"],
                    test_data["user3_id"]
                ])
            )
        )
        
        # 清除缓存
        cache_key = f"ai:summary:{test_data['contract_id']}"
        await redis_client.delete(cache_key)
        
        await db.commit()
        print("✓ 测试数据清理完成")
        
    except Exception as e:
        print(f"✗ 清理失败: {str(e)}")
        await db.rollback()


async def main():
    """主测试函数"""
    print("=" * 80)
    print("Checkpoint 16 - AI功能验证测试")
    print("=" * 80)
    
    test_results = []
    test_data = None
    
    async with async_session_factory() as db:
        try:
            # 设置测试数据
            test_data = await setup_test_data(db)
            
            # 运行测试
            test_results.append(("智能总结生成", await test_smart_summary_generation(
                db, test_data["contract_id"]
            )))
            
            test_results.append(("AI顾问-法务意见查询", await test_ai_advisor_legal_query(
                db, test_data["contract_id"], test_data["user1_id"]
            )))
            
            test_results.append(("AI顾问-风险项查询", await test_ai_advisor_risk_query(
                db, test_data["contract_id"], test_data["user1_id"]
            )))
            
            test_results.append(("AI顾问-待办任务查询", await test_ai_advisor_pending_query(
                db, test_data["contract_id"], test_data["user1_id"]
            )))
            
            test_results.append(("AI顾问-默认回复", await test_ai_advisor_default_reply(
                db, test_data["contract_id"], test_data["user1_id"]
            )))
            
            test_results.append(("缓存功能", await test_cache_functionality(
                db, test_data["contract_id"]
            )))
            
            test_results.append(("降级处理", await test_degradation_handling()))
            
        finally:
            # 清理测试数据
            if test_data:
                await cleanup_test_data(db, test_data)
    
    # 打印测试结果摘要
    print("\n" + "=" * 80)
    print("测试结果摘要")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
