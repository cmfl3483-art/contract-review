"""
AI服务测试
Tests for AI service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.services.ai_service import AIService
from app.models.ai_summary import AISummary, ApprovalStatus
from app.models.review import Review, ReviewStatus
from app.models.contract import Contract
from app.models.comment import Comment


@pytest.fixture
def ai_service():
    """创建AI服务实例"""
    return AIService()


@pytest.fixture
def mock_contract():
    """创建模拟合同"""
    contract = MagicMock(spec=Contract)
    contract.id = uuid.uuid4()
    contract.name = "测试合同"
    contract.description = "测试描述"
    return contract


@pytest.fixture
def mock_reviews():
    """创建模拟评审记录列表"""
    review1 = MagicMock(spec=Review)
    review1.id = uuid.uuid4()
    review1.opinion = "建议修改第三条款的付款方式"
    review1.role = "法务"
    review1.status = ReviewStatus.APPROVED
    
    review2 = MagicMock(spec=Review)
    review2.id = uuid.uuid4()
    review2.opinion = "存在风险,需要补充担保条款"
    review2.role = "财务"
    review2.status = ReviewStatus.REVIEWING
    
    review3 = MagicMock(spec=Review)
    review3.id = uuid.uuid4()
    review3.opinion = "同意并通过"
    review3.role = "业务"
    review3.status = ReviewStatus.APPROVED
    
    review4 = MagicMock(spec=Review)
    review4.id = uuid.uuid4()
    review4.opinion = None
    review4.role = "运营"
    review4.status = ReviewStatus.PENDING
    
    return [review1, review2, review3, review4]


@pytest.fixture
def mock_comments():
    """创建模拟评论列表"""
    comment1 = MagicMock(spec=Comment)
    comment1.content = "已经修改完成,请查看最新版本"
    comment1.created_at = datetime.utcnow()
    
    comment2 = MagicMock(spec=Comment)
    comment2.content = "担保条款已补充在第五条"
    comment2.created_at = datetime.utcnow()
    
    return [comment1, comment2]


class TestGenerateSummary:
    """测试生成AI智能总结"""
    
    @pytest.mark.asyncio
    async def test_generate_summary_success(
        self,
        ai_service,
        mock_contract,
        mock_reviews
    ):
        """应该成功生成AI总结"""
        # 准备模拟数据库
        mock_db = AsyncMock()
        
        # 模拟合同查询
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        mock_db.execute.side_effect = [
            contract_result,  # 合同查询
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_reviews)))),  # 评审查询
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # 评论查询1
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),  # 评论查询2
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))  # 总结查询
        ]
        
        # 模拟Redis缓存
        with patch('app.services.ai_service.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.set.return_value = True
            
            # 执行测试
            summary = await ai_service.generate_summary(str(mock_contract.id), mock_db)
            
            # 验证结果
            assert summary is not None
            assert summary.contract_id == mock_contract.id
            assert summary.total_count == 4
            assert summary.completed_count == 2
            assert summary.approval_status == ApprovalStatus.IN_PROGRESS
            assert summary.review_count == 3  # 只有3个有意见的评审
            
            # 验证数据库操作
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            
            # 验证缓存操作
            mock_redis.get.assert_called_once()
            mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_summary_all_approved(
        self,
        ai_service,
        mock_contract
    ):
        """当所有评审都通过时,状态应该是completed"""
        # 创建全部通过的评审
        approved_reviews = []
        for i in range(3):
            review = MagicMock(spec=Review)
            review.id = uuid.uuid4()
            review.opinion = f"同意并通过 {i}"
            review.role = f"角色{i}"
            review.status = ReviewStatus.APPROVED
            approved_reviews.append(review)
        
        mock_db = AsyncMock()
        
        # 模拟查询
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        mock_db.execute.side_effect = [
            contract_result,
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=approved_reviews)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        ]
        
        with patch('app.services.ai_service.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.set.return_value = True
            
            summary = await ai_service.generate_summary(str(mock_contract.id), mock_db)
            
            assert summary.approval_status == ApprovalStatus.COMPLETED
            assert summary.completed_count == 3
            assert summary.total_count == 3
    
    @pytest.mark.asyncio
    async def test_generate_summary_from_cache(
        self,
        ai_service,
        mock_contract
    ):
        """应该从缓存中获取总结"""
        mock_db = AsyncMock()
        
        # 创建已存在的总结
        existing_summary = MagicMock(spec=AISummary)
        existing_summary.contract_id = mock_contract.id
        existing_summary.approval_status = ApprovalStatus.IN_PROGRESS
        
        # 模拟缓存命中
        with patch('app.services.ai_service.redis_client') as mock_redis:
            mock_redis.get.return_value = "1"
            
            # 模拟数据库查询
            summary_result = MagicMock()
            summary_result.scalar_one_or_none.return_value = existing_summary
            mock_db.execute.return_value = summary_result
            
            summary = await ai_service.generate_summary(str(mock_contract.id), mock_db)
            
            # 验证从缓存获取
            assert summary == existing_summary
            mock_redis.get.assert_called_once()
            # 不应该调用set(因为是从缓存获取)
            mock_redis.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_summary_contract_not_found(
        self,
        ai_service
    ):
        """当合同不存在时应该返回None"""
        mock_db = AsyncMock()
        
        # 模拟合同不存在
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = contract_result
        
        with patch('app.services.ai_service.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            
            summary = await ai_service.generate_summary("non-existent-id", mock_db)
            
            assert summary is None
    
    @pytest.mark.asyncio
    async def test_generate_summary_update_existing(
        self,
        ai_service,
        mock_contract,
        mock_reviews
    ):
        """应该更新已存在的总结"""
        mock_db = AsyncMock()
        
        # 创建已存在的总结
        existing_summary = MagicMock(spec=AISummary)
        existing_summary.contract_id = mock_contract.id
        existing_summary.approval_status = ApprovalStatus.IN_PROGRESS
        existing_summary.completed_count = 1
        existing_summary.total_count = 3
        
        # 模拟查询
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        summary_result = MagicMock()
        summary_result.scalar_one_or_none.return_value = existing_summary
        
        mock_db.execute.side_effect = [
            contract_result,
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_reviews)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            summary_result
        ]
        
        with patch('app.services.ai_service.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.set.return_value = True
            
            summary = await ai_service.generate_summary(str(mock_contract.id), mock_db)
            
            # 验证更新了现有总结
            assert summary == existing_summary
            assert summary.completed_count == 2
            assert summary.total_count == 4
            mock_db.add.assert_not_called()  # 不应该添加新记录


class TestExtractKeyIssues:
    """测试提取关键问题"""
    
    @pytest.mark.asyncio
    async def test_extract_key_issues_with_keywords(
        self,
        ai_service,
        mock_reviews
    ):
        """应该提取包含关键词的问题"""
        mock_db = AsyncMock()
        
        # 模拟评论查询
        comment1 = MagicMock(spec=Comment)
        comment1.content = "已经修改完成"
        comment1.created_at = datetime.utcnow()
        
        comment2 = MagicMock(spec=Comment)
        comment2.content = "担保条款已补充"
        comment2.created_at = datetime.utcnow()
        
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[comment1])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[comment2])))),
        ]
        
        key_issues = await ai_service._extract_key_issues(mock_reviews[:2], mock_db)
        
        # 验证提取了2个关键问题
        assert len(key_issues) == 2
        assert key_issues[0]["issue"] == "建议修改第三条款的付款方式"
        assert key_issues[0]["reviewer"] == "法务"
        assert key_issues[0]["solution"] == "已经修改完成"
        assert key_issues[1]["issue"] == "存在风险,需要补充担保条款"
        assert key_issues[1]["reviewer"] == "财务"
        assert key_issues[1]["solution"] == "担保条款已补充"
    
    @pytest.mark.asyncio
    async def test_extract_key_issues_max_three(
        self,
        ai_service
    ):
        """应该最多返回3个关键问题"""
        # 创建5个包含关键词的评审
        reviews = []
        for i in range(5):
            review = MagicMock(spec=Review)
            review.id = uuid.uuid4()
            review.opinion = f"建议修改第{i}条款"
            review.role = f"角色{i}"
            reviews.append(review)
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
        
        key_issues = await ai_service._extract_key_issues(reviews, mock_db)
        
        # 验证只返回3个
        assert len(key_issues) == 3
    
    @pytest.mark.asyncio
    async def test_extract_key_issues_no_keywords(
        self,
        ai_service
    ):
        """当没有关键词时应该返回空列表"""
        reviews = []
        for i in range(3):
            review = MagicMock(spec=Review)
            review.id = uuid.uuid4()
            review.opinion = f"同意并通过 {i}"
            review.role = f"角色{i}"
            reviews.append(review)
        
        mock_db = AsyncMock()
        
        key_issues = await ai_service._extract_key_issues(reviews, mock_db)
        
        assert len(key_issues) == 0
    
    @pytest.mark.asyncio
    async def test_extract_key_issues_no_solution(
        self,
        ai_service
    ):
        """当没有回复时solution应该是None"""
        review = MagicMock(spec=Review)
        review.id = uuid.uuid4()
        review.opinion = "存在问题需要解决"
        review.role = "法务"
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
        
        key_issues = await ai_service._extract_key_issues([review], mock_db)
        
        assert len(key_issues) == 1
        assert key_issues[0]["solution"] is None
    
    @pytest.mark.asyncio
    async def test_extract_key_issues_all_keywords(
        self,
        ai_service
    ):
        """应该识别所有关键词"""
        keywords = ["建议", "需要", "问题", "风险", "隐患"]
        reviews = []
        
        for keyword in keywords:
            review = MagicMock(spec=Review)
            review.id = uuid.uuid4()
            review.opinion = f"这里有{keyword}需要处理"
            review.role = "测试角色"
            reviews.append(review)
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
        
        key_issues = await ai_service._extract_key_issues(reviews, mock_db)
        
        # 应该提取3个(最多3个)
        assert len(key_issues) == 3


class TestAnswerQuestion:
    """测试AI合同顾问问答"""
    
    @pytest.mark.asyncio
    async def test_answer_legal_question(
        self,
        ai_service,
        mock_contract,
        mock_reviews
    ):
        """应该返回法务意见"""
        mock_db = AsyncMock()
        
        # 模拟查询
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        reviews_result = MagicMock()
        reviews_result.scalars.return_value.all.return_value = mock_reviews
        
        mock_db.execute.side_effect = [contract_result, reviews_result]
        
        answer = await ai_service.answer_question(
            str(mock_contract.id),
            "法务意见是什么?",
            mock_db
        )
        
        assert "法务意见如下" in answer
        assert "建议修改第三条款的付款方式" in answer
    
    @pytest.mark.asyncio
    async def test_answer_risk_question(
        self,
        ai_service,
        mock_contract,
        mock_reviews
    ):
        """应该返回风险项"""
        mock_db = AsyncMock()
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        reviews_result = MagicMock()
        reviews_result.scalars.return_value.all.return_value = mock_reviews
        
        mock_db.execute.side_effect = [contract_result, reviews_result]
        
        answer = await ai_service.answer_question(
            str(mock_contract.id),
            "有哪些风险项?",
            mock_db
        )
        
        assert "风险项" in answer or "未确认项" in answer
    
    @pytest.mark.asyncio
    async def test_answer_pending_question(
        self,
        ai_service,
        mock_contract,
        mock_reviews
    ):
        """应该返回待办任务数量"""
        mock_db = AsyncMock()
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        reviews_result = MagicMock()
        reviews_result.scalars.return_value.all.return_value = mock_reviews
        
        mock_db.execute.side_effect = [contract_result, reviews_result]
        
        answer = await ai_service.answer_question(
            str(mock_contract.id),
            "待我处理的任务有哪些?",
            mock_db
        )
        
        assert "待处理" in answer
        assert "1" in answer  # 有1个pending状态的评审
    
    @pytest.mark.asyncio
    async def test_answer_default_question(
        self,
        ai_service,
        mock_contract,
        mock_reviews
    ):
        """对于其他问题应该返回默认回复"""
        mock_db = AsyncMock()
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        reviews_result = MagicMock()
        reviews_result.scalars.return_value.all.return_value = mock_reviews
        
        mock_db.execute.side_effect = [contract_result, reviews_result]
        
        answer = await ai_service.answer_question(
            str(mock_contract.id),
            "这个合同怎么样?",
            mock_db
        )
        
        assert "评审意见" in answer
        assert "您可以询问" in answer
    
    @pytest.mark.asyncio
    async def test_answer_contract_not_found(
        self,
        ai_service
    ):
        """当合同不存在时应该返回错误信息"""
        mock_db = AsyncMock()
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = contract_result
        
        answer = await ai_service.answer_question(
            "non-existent-id",
            "测试问题",
            mock_db
        )
        
        assert answer == "合同不存在"


class TestCacheExpiry:
    """测试缓存过期时间"""
    
    @pytest.mark.asyncio
    async def test_cache_expiry_30_minutes(
        self,
        ai_service,
        mock_contract,
        mock_reviews
    ):
        """缓存应该设置为30分钟(1800秒)"""
        mock_db = AsyncMock()
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        mock_db.execute.side_effect = [
            contract_result,
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_reviews)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        ]
        
        with patch('app.services.ai_service.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.set.return_value = True
            
            await ai_service.generate_summary(str(mock_contract.id), mock_db)
            
            # 验证缓存过期时间是1800秒(30分钟)
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert call_args[1]['expire'] == 1800
