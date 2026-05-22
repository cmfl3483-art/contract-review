"""
AI合同顾问服务单元测试
测试问题分类和回答逻辑
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.ai_service import AIService
from app.models.review import Review, ReviewStatus


@pytest.fixture
def ai_service():
    """创建AI服务实例"""
    return AIService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def sample_contract_id():
    """示例合同ID"""
    return str(uuid4())


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return str(uuid4())


@pytest.fixture
def sample_reviews(sample_contract_id, sample_user_id):
    """创建示例评审记录"""
    other_user_id = str(uuid4())
    
    return [
        # 法务评审 - 已通过
        MagicMock(
            id=uuid4(),
            contract_id=sample_contract_id,
            reviewer_id=uuid4(),
            role="法务",
            step="法务初审",
            opinion="合同条款符合法律规定,建议通过",
            status=ReviewStatus.APPROVED
        ),
        # 财务评审 - 评审中
        MagicMock(
            id=uuid4(),
            contract_id=sample_contract_id,
            reviewer_id=uuid4(),
            role="财务",
            step="财务审核",
            opinion="发现风险:付款条件需要调整",
            status=ReviewStatus.REVIEWING
        ),
        # 当前用户的待处理任务
        MagicMock(
            id=uuid4(),
            contract_id=sample_contract_id,
            reviewer_id=sample_user_id,
            role="业务",
            step="业务审核",
            opinion=None,
            status=ReviewStatus.PENDING
        ),
        # 其他用户的待处理任务
        MagicMock(
            id=uuid4(),
            contract_id=sample_contract_id,
            reviewer_id=other_user_id,
            role="运营",
            step="运营审核",
            opinion=None,
            status=ReviewStatus.PENDING
        ),
    ]


class TestAIAdvisorQuestionClassification:
    """测试问题分类逻辑"""
    
    @pytest.mark.asyncio
    async def test_legal_opinion_query(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id,
        sample_reviews
    ):
        """测试法务意见查询 (需求 7.4)"""
        # 模拟数据库查询
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_reviews))))
        ])
        
        # 测试包含"法务"关键词的问题
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="法务意见是什么?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 验证返回法务意见
        assert "法务意见如下" in answer
        assert "法务" in answer
        assert "合同条款符合法律规定" in answer
    
    @pytest.mark.asyncio
    async def test_legal_opinion_query_no_results(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id
    ):
        """测试法务意见查询 - 无法务意见"""
        # 模拟数据库查询 - 无法务评审
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        reviews_without_legal = [
            MagicMock(
                role="财务",
                step="财务审核",
                opinion="财务意见",
                status=ReviewStatus.APPROVED
            )
        ]
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=reviews_without_legal))))
        ])
        
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="法务意见是什么?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        assert "暂无法务意见" in answer
    
    @pytest.mark.asyncio
    async def test_risk_items_query(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id,
        sample_reviews
    ):
        """测试风险项查询 (需求 7.5)"""
        # 模拟数据库查询
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_reviews))))
        ])
        
        # 测试"风险"关键词
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="有哪些风险项?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 验证返回评审中的项目
        assert "当前风险项/未确认项" in answer
        assert "财务" in answer
        assert "发现风险" in answer
    
    @pytest.mark.asyncio
    async def test_unconfirmed_items_query(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id,
        sample_reviews
    ):
        """测试未确认项查询 (需求 7.5)"""
        # 模拟数据库查询
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_reviews))))
        ])
        
        # 测试"未确认"关键词
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="有哪些未确认的项目?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 验证返回评审中的项目
        assert "当前风险项/未确认项" in answer
    
    @pytest.mark.asyncio
    async def test_risk_items_query_all_confirmed(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id
    ):
        """测试风险项查询 - 所有项目已确认"""
        # 模拟数据库查询 - 所有评审都已通过
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        all_approved_reviews = [
            MagicMock(
                role="法务",
                step="法务初审",
                opinion="同意",
                status=ReviewStatus.APPROVED
            ),
            MagicMock(
                role="财务",
                step="财务审核",
                opinion="同意",
                status=ReviewStatus.APPROVED
            )
        ]
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=all_approved_reviews))))
        ])
        
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="有哪些风险项?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        assert "所有评审项已确认,无风险项" in answer
    
    @pytest.mark.asyncio
    async def test_pending_tasks_query(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id,
        sample_reviews
    ):
        """测试待我处理任务查询 (需求 7.6)"""
        # 模拟数据库查询
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_reviews))))
        ])
        
        # 测试"待我处理"关键词
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="待我处理的任务有哪些?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 验证只返回当前用户的待处理任务
        assert "您有 1 个待处理任务" in answer
        assert "业务审核" in answer
        # 不应包含其他用户的任务
        assert "运营审核" not in answer
    
    @pytest.mark.asyncio
    async def test_pending_tasks_query_no_tasks(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id
    ):
        """测试待我处理任务查询 - 无待处理任务"""
        # 模拟数据库查询 - 当前用户无待处理任务
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        other_user_id = str(uuid4())
        reviews_no_user_pending = [
            MagicMock(
                reviewer_id=other_user_id,
                role="法务",
                step="法务初审",
                opinion=None,
                status=ReviewStatus.PENDING
            )
        ]
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=reviews_no_user_pending))))
        ])
        
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="待我处理的任务有哪些?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        assert "您暂无待处理任务" in answer
    
    @pytest.mark.asyncio
    async def test_default_reply(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id,
        sample_reviews
    ):
        """测试默认回复 (需求 7.7)"""
        # 模拟数据库查询
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_reviews))))
        ])
        
        # 测试不包含特定关键词的问题
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="这个合同怎么样?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 验证返回评审数量和可询问的问题类型
        assert "条评审意见" in answer
        assert "您可以询问" in answer
        assert "法务意见是什么" in answer
        assert "有哪些风险项" in answer
        assert "待我处理的任务有哪些" in answer
    
    @pytest.mark.asyncio
    async def test_contract_not_found(
        self,
        ai_service,
        mock_db,
        sample_user_id
    ):
        """测试合同不存在的情况"""
        # 模拟数据库查询 - 合同不存在
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        ))
        
        answer = await ai_service.answer_question(
            contract_id=str(uuid4()),
            question="法务意见是什么?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        assert "合同不存在" in answer
    
    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id
    ):
        """测试错误处理"""
        # 模拟数据库查询失败
        mock_db.execute = AsyncMock(side_effect=Exception("数据库错误"))
        
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="法务意见是什么?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        assert "抱歉" in answer
        assert "错误" in answer


class TestAIAdvisorEdgeCases:
    """测试边界情况"""
    
    @pytest.mark.asyncio
    async def test_multiple_legal_opinions(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id
    ):
        """测试多个法务意见"""
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        reviews_multiple_legal = [
            MagicMock(
                role="法务初审",
                step="法务初审",
                opinion="初审意见:需要修改第3条",
                status=ReviewStatus.APPROVED
            ),
            MagicMock(
                role="法务复审",
                step="法务复审",
                opinion="复审意见:修改后可以通过",
                status=ReviewStatus.APPROVED
            )
        ]
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=reviews_multiple_legal))))
        ])
        
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="法务意见是什么?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 应该包含所有法务意见
        assert "初审意见" in answer
        assert "复审意见" in answer
    
    @pytest.mark.asyncio
    async def test_multiple_pending_tasks(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id
    ):
        """测试多个待处理任务"""
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        reviews_multiple_pending = [
            MagicMock(
                reviewer_id=sample_user_id,
                role="业务",
                step="业务初审",
                opinion=None,
                status=ReviewStatus.PENDING
            ),
            MagicMock(
                reviewer_id=sample_user_id,
                role="业务",
                step="业务复审",
                opinion=None,
                status=ReviewStatus.PENDING
            )
        ]
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=reviews_multiple_pending))))
        ])
        
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="待我处理的任务有哪些?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 应该显示正确的任务数量
        assert "您有 2 个待处理任务" in answer
        assert "业务初审" in answer
        assert "业务复审" in answer
    
    @pytest.mark.asyncio
    async def test_empty_reviews(
        self,
        ai_service,
        mock_db,
        sample_contract_id,
        sample_user_id
    ):
        """测试无评审记录的情况"""
        mock_contract = MagicMock(id=sample_contract_id, name="测试合同")
        mock_db.execute = AsyncMock(side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_contract)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        ])
        
        answer = await ai_service.answer_question(
            contract_id=sample_contract_id,
            question="这个合同怎么样?",
            current_user_id=sample_user_id,
            db=mock_db
        )
        
        # 应该返回默认回复,显示0条评审意见
        assert "0 条评审意见" in answer
