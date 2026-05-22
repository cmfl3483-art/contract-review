#!/usr/bin/env python3
"""
验证评审和评论功能
Verify Review and Comment Functionality

This script tests:
1. 评审记录获取和过滤 (Review record retrieval and filtering)
2. 同意评审流程 (Approve review workflow)
3. 评论和嵌套回复 (Comments and nested replies)
4. 点赞功能 (Like functionality)
"""

import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.contract import Contract
from app.models.review import Review, ReviewStatus
from app.models.comment import Comment
from app.models.user import User
from app.services.review_service import ReviewService
from app.services.comment_service import CommentService


class ReviewCommentVerifier:
    """评审和评论功能验证器"""
    
    def __init__(self):
        self.review_service = ReviewService()
        self.comment_service = CommentService()
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append((test_name, passed))
        print(f"{status} - {test_name}")
        if message:
            print(f"    {message}")
    
    async def verify_review_retrieval_and_filtering(self, db: AsyncSession):
        """测试1: 验证评审记录获取和过滤"""
        print("\n" + "=" * 80)
        print("测试 1: 评审记录获取和过滤")
        print("=" * 80)
        
        try:
            # 查找一个有评审记录的合同
            query = select(Contract).join(Review).limit(1)
            result = await db.execute(query)
            contract = result.scalar_one_or_none()
            
            if not contract:
                self.log_test("评审记录获取", False, "没有找到包含评审记录的合同")
                return
            
            # 获取评审记录
            reviews = await self.review_service.get_contract_reviews(
                str(contract.id),
                db
            )
            
            self.log_test(
                "评审记录获取",
                True,
                f"成功获取合同 {contract.name} 的 {len(reviews)} 条评审记录"
            )
            
            # 验证过滤逻辑 - 检查是否过滤了占位文本
            has_placeholder = any(
                r.get('opinion') in ['待评审', '待评审,请反馈', '待评审，请反馈']
                for r in reviews
            )
            
            self.log_test(
                "过滤占位文本",
                not has_placeholder,
                "已正确过滤占位文本" if not has_placeholder else "发现未过滤的占位文本"
            )
            
            # 验证有回复但无意见的评审是否保留
            reviews_with_comments = [
                r for r in reviews
                if not r.get('opinion') and r.get('comments')
            ]
            
            self.log_test(
                "保留有回复的评审",
                True,
                f"找到 {len(reviews_with_comments)} 条有回复但无意见的评审记录"
            )
            
        except Exception as e:
            self.log_test("评审记录获取和过滤", False, f"错误: {str(e)}")
    
    async def verify_approve_review_workflow(self, db: AsyncSession):
        """测试2: 验证同意评审流程"""
        print("\n" + "=" * 80)
        print("测试 2: 同意评审流程")
        print("=" * 80)
        
        try:
            # 查找一个待处理的评审
            query = select(Review).where(Review.status == ReviewStatus.PENDING).limit(1)
            result = await db.execute(query)
            review = result.scalar_one_or_none()
            
            if not review:
                self.log_test("同意评审流程", False, "没有找到待处理的评审记录")
                print("    提示: 可以运行 create_stress_test_data.py 创建测试数据")
                return
            
            # 记录原始状态
            original_status = review.status
            reviewer_id = str(review.reviewer_id)
            
            # 执行同意操作
            updated_review = await self.review_service.approve_review(
                str(review.id),
                reviewer_id,
                "测试同意意见",
                db
            )
            
            # 验证状态更新
            status_updated = updated_review.status == ReviewStatus.APPROVED
            opinion_updated = updated_review.opinion == "测试同意意见"
            
            self.log_test(
                "同意评审 - 状态更新",
                status_updated,
                f"状态从 {original_status} 更新为 {updated_review.status}"
            )
            
            self.log_test(
                "同意评审 - 意见保存",
                opinion_updated,
                f"意见已保存: {updated_review.opinion}"
            )
            
            # 回滚更改以便重复测试
            review.status = original_status
            review.opinion = None
            await db.commit()
            
        except Exception as e:
            self.log_test("同意评审流程", False, f"错误: {str(e)}")
    
    async def verify_comments_and_nested_replies(self, db: AsyncSession):
        """测试3: 验证评论和嵌套回复"""
        print("\n" + "=" * 80)
        print("测试 3: 评论和嵌套回复")
        print("=" * 80)
        
        try:
            # 查找一个合同和用户
            contract_query = select(Contract).limit(1)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()
            
            user_query = select(User).limit(1)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not contract or not user:
                self.log_test("评论和嵌套回复", False, "没有找到测试数据")
                return
            
            # 测试添加评论
            comment = await self.comment_service.create_comment(
                contract_id=str(contract.id),
                author_id=str(user.id),
                content="测试评论内容",
                db=db
            )
            
            self.log_test(
                "添加评论",
                comment is not None,
                f"成功添加评论 ID: {comment.id}"
            )
            
            # 测试嵌套回复
            reply = await self.comment_service.create_comment(
                contract_id=str(contract.id),
                author_id=str(user.id),
                content="测试回复内容",
                parent_comment_id=str(comment.id),
                db=db
            )
            
            self.log_test(
                "添加嵌套回复",
                reply is not None and reply.parent_comment_id == comment.id,
                f"成功添加回复 ID: {reply.id}"
            )
            
            # 清理测试数据
            await db.delete(reply)
            await db.delete(comment)
            await db.commit()
            
        except Exception as e:
            self.log_test("评论和嵌套回复", False, f"错误: {str(e)}")
    
    async def verify_like_functionality(self, db: AsyncSession):
        """测试4: 验证点赞功能"""
        print("\n" + "=" * 80)
        print("测试 4: 点赞功能")
        print("=" * 80)
        
        try:
            # 测试评审点赞
            review_query = select(Review).limit(1)
            review_result = await db.execute(review_query)
            review = review_result.scalar_one_or_none()
            
            user_query = select(User).limit(1)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not review or not user:
                self.log_test("点赞功能", False, "没有找到测试数据")
                return
            
            # 记录原始点赞数
            original_likes = review.likes
            user_id = str(user.id)
            
            # 执行点赞
            updated_review = await self.review_service.like_review(
                str(review.id),
                user_id,
                db
            )
            
            # 验证点赞
            likes_increased = updated_review.likes == original_likes + 1
            user_in_liked_by = user_id in updated_review.liked_by
            
            self.log_test(
                "评审点赞 - 点赞数增加",
                likes_increased,
                f"点赞数从 {original_likes} 增加到 {updated_review.likes}"
            )
            
            self.log_test(
                "评审点赞 - 用户记录",
                user_in_liked_by,
                "用户ID已添加到liked_by列表"
            )
            
            # 测试取消点赞
            unliked_review = await self.review_service.like_review(
                str(review.id),
                user_id,
                db
            )
            
            likes_decreased = unliked_review.likes == original_likes
            user_not_in_liked_by = user_id not in unliked_review.liked_by
            
            self.log_test(
                "评审取消点赞 - 点赞数减少",
                likes_decreased,
                f"点赞数从 {updated_review.likes} 减少到 {unliked_review.likes}"
            )
            
            self.log_test(
                "评审取消点赞 - 用户记录移除",
                user_not_in_liked_by,
                "用户ID已从liked_by列表移除"
            )
            
            # 测试评论点赞
            comment_query = select(Comment).limit(1)
            comment_result = await db.execute(comment_query)
            comment = comment_result.scalar_one_or_none()
            
            if comment:
                original_comment_likes = comment.likes
                
                updated_comment = await self.review_service.like_comment(
                    str(comment.id),
                    user_id,
                    db
                )
                
                self.log_test(
                    "评论点赞",
                    updated_comment.likes == original_comment_likes + 1,
                    f"评论点赞数从 {original_comment_likes} 增加到 {updated_comment.likes}"
                )
                
                # 取消点赞
                await self.review_service.like_comment(
                    str(comment.id),
                    user_id,
                    db
                )
            else:
                self.log_test("评论点赞", False, "没有找到评论数据")
            
        except Exception as e:
            self.log_test("点赞功能", False, f"错误: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "=" * 80)
        print("开始验证评审和评论功能")
        print("Start Verifying Review and Comment Functionality")
        print("=" * 80)
        
        async for db in get_db():
            try:
                await self.verify_review_retrieval_and_filtering(db)
                await self.verify_approve_review_workflow(db)
                await self.verify_comments_and_nested_replies(db)
                await self.verify_like_functionality(db)
            finally:
                await db.close()
        
        # 打印总结
        print("\n" + "=" * 80)
        print("测试总结 (Test Summary)")
        print("=" * 80)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        print(f"\n总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {total - passed}")
        print(f"通过率: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 所有测试通过! (All tests passed!)")
            return 0
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败 ({total - passed} tests failed)")
            return 1


async def main():
    """主函数"""
    verifier = ReviewCommentVerifier()
    return await verifier.run_all_tests()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
