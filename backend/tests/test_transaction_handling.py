"""
测试事务处理功能
验证创建合同和审批评审时的事务处理和回滚逻辑
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.services.contract_service import ContractService
from app.services.review_service import ReviewService
from app.models.contract import Contract
from app.models.review import Review


class TestTransactionHandling:
    """测试事务处理"""
    
    @pytest.mark.asyncio
    async def test_create_contract_transaction_success(self):
        """测试创建合同事务成功"""
        # 准备测试数据
        name = "测试合同"
        initiator_id = "user-123"
        reviewers = [
            {"user_id": "reviewer-1", "role": "法务", "step": "法务初审"},
            {"user_id": "reviewer-2", "role": "财务", "step": "财务审核"}
        ]
        
        # Mock数据库会话
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin = AsyncMock()
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 创建服务实例
        service = ContractService()
        
        # Mock缓存清除
        with patch.object(service, '_clear_contract_list_cache', new_callable=AsyncMock):
            # 执行创建合同
            contract = await service.create_contract(
                name=name,
                initiator_id=initiator_id,
                reviewers=reviewers,
                db=mock_db
            )
            
            # 验证结果
            assert contract is not None
            assert contract.name == name
            assert contract.initiator_id == initiator_id
            assert contract.status == "progress"
            
            # 验证事务操作被调用
            mock_db.begin.assert_called_once()
            mock_db.add.assert_called()
            mock_db.flush.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_contract_validation_error(self):
        """测试创建合同参数验证失败"""
        mock_db = AsyncMock(spec=AsyncSession)
        service = ContractService()
        
        # 测试空名称
        with pytest.raises(ValueError, match="合同名称不能为空"):
            await service.create_contract(
                name="",
                initiator_id="user-123",
                reviewers=[{"user_id": "reviewer-1"}],
                db=mock_db
            )
        
        # 测试空评审人列表
        with pytest.raises(ValueError, match="至少需要一个评审人"):
            await service.create_contract(
                name="测试合同",
                initiator_id="user-123",
                reviewers=[],
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_create_contract_transaction_rollback(self):
        """测试创建合同事务回滚"""
        # Mock数据库会话,模拟数据库错误
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin = AsyncMock()
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock(
            side_effect=SQLAlchemyError("Database error")
        )
        
        service = ContractService()
        
        # 执行创建合同,应该抛出异常
        with pytest.raises(Exception, match="创建合同失败"):
            await service.create_contract(
                name="测试合同",
                initiator_id="user-123",
                reviewers=[{"user_id": "reviewer-1"}],
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_approve_review_transaction_success(self):
        """测试审批评审事务成功"""
        # 准备测试数据
        review_id = "review-123"
        reviewer_id = "user-123"
        opinion = "同意并通过"
        
        # Mock评审记录
        mock_review = MagicMock(spec=Review)
        mock_review.id = review_id
        mock_review.reviewer_id = reviewer_id
        mock_review.contract_id = "contract-123"
        mock_review.status = "pending"
        mock_review.reviewer = MagicMock()
        mock_review.reviewer.name = "张三"
        
        # Mock数据库会话
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin = AsyncMock()
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        
        # Mock查询结果
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # 创建服务实例
        service = ReviewService()
        
        # Mock内部方法
        with patch.object(service, '_check_and_update_contract_status_in_transaction', new_callable=AsyncMock), \
             patch.object(service, '_clear_review_cache', new_callable=AsyncMock), \
             patch.object(service, '_clear_pending_count_cache', new_callable=AsyncMock), \
             patch.object(service, '_get_pending_count', new_callable=AsyncMock, return_value=0), \
             patch('app.services.review_service.notification_service') as mock_notification:
            
            mock_notification.notify_review_added = AsyncMock()
            mock_notification.notify_pending_changed = AsyncMock()
            
            # 执行审批
            result = await service.approve_review(
                review_id=review_id,
                reviewer_id=reviewer_id,
                opinion=opinion,
                db=mock_db
            )
            
            # 验证结果
            assert result is not None
            assert result.status == "approved"
            assert result.opinion == opinion
            
            # 验证事务操作被调用
            mock_db.begin.assert_called_once()
            mock_db.flush.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_review_permission_error(self):
        """测试审批评审权限错误"""
        # Mock评审记录
        mock_review = MagicMock(spec=Review)
        mock_review.id = "review-123"
        mock_review.reviewer_id = "user-456"  # 不同的用户
        
        # Mock数据库会话
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin = AsyncMock()
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = ReviewService()
        
        # 执行审批,应该抛出权限错误
        with pytest.raises(ValueError, match="您没有权限审批此评审项"):
            await service.approve_review(
                review_id="review-123",
                reviewer_id="user-123",  # 不同的用户ID
                opinion="同意",
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_approve_review_not_found(self):
        """测试审批不存在的评审"""
        # Mock数据库会话
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin = AsyncMock()
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = ReviewService()
        
        # 执行审批,应该抛出错误
        with pytest.raises(ValueError, match="评审记录不存在"):
            await service.approve_review(
                review_id="non-existent",
                reviewer_id="user-123",
                opinion="同意",
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_approve_review_transaction_rollback(self):
        """测试审批评审事务回滚"""
        # Mock评审记录
        mock_review = MagicMock(spec=Review)
        mock_review.id = "review-123"
        mock_review.reviewer_id = "user-123"
        mock_review.contract_id = "contract-123"
        
        # Mock数据库会话,模拟数据库错误
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.begin = AsyncMock()
        mock_db.begin.return_value.__aenter__ = AsyncMock()
        mock_db.begin.return_value.__aexit__ = AsyncMock(
            side_effect=SQLAlchemyError("Database error")
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_review
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = ReviewService()
        
        # Mock内部方法
        with patch.object(service, '_check_and_update_contract_status_in_transaction', new_callable=AsyncMock):
            # 执行审批,应该抛出异常
            with pytest.raises(Exception, match="审批评审失败"):
                await service.approve_review(
                    review_id="review-123",
                    reviewer_id="user-123",
                    opinion="同意",
                    db=mock_db
                )
    
    @pytest.mark.asyncio
    async def test_check_and_update_contract_status_in_transaction(self):
        """测试在事务中更新合同状态"""
        contract_id = "contract-123"
        
        # Mock所有评审都已通过
        mock_reviews = [
            MagicMock(status="approved"),
            MagicMock(status="approved"),
            MagicMock(status="approved")
        ]
        
        # Mock合同
        mock_contract = MagicMock(spec=Contract)
        mock_contract.id = contract_id
        mock_contract.status = "progress"
        
        # Mock数据库会话
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock评审查询
        mock_review_result = MagicMock()
        mock_review_result.scalars.return_value.all.return_value = mock_reviews
        
        # Mock合同查询
        mock_contract_result = MagicMock()
        mock_contract_result.scalar_one_or_none.return_value = mock_contract
        
        # 设置execute返回不同的结果
        mock_db.execute = AsyncMock(side_effect=[mock_review_result, mock_contract_result])
        
        service = ReviewService()
        
        # 执行状态检查和更新
        await service._check_and_update_contract_status_in_transaction(
            contract_id=contract_id,
            db=mock_db
        )
        
        # 验证合同状态被更新
        assert mock_contract.status == "completed"
        
        # 验证没有调用commit(由外层事务控制)
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_and_update_contract_status_not_all_approved(self):
        """测试合同未全部通过时不更新状态"""
        contract_id = "contract-123"
        
        # Mock部分评审未通过
        mock_reviews = [
            MagicMock(status="approved"),
            MagicMock(status="pending"),  # 还有待处理的
            MagicMock(status="approved")
        ]
        
        # Mock数据库会话
        mock_db = AsyncMock(spec=AsyncSession)
        
        mock_review_result = MagicMock()
        mock_review_result.scalars.return_value.all.return_value = mock_reviews
        mock_db.execute = AsyncMock(return_value=mock_review_result)
        
        service = ReviewService()
        
        # 执行状态检查
        await service._check_and_update_contract_status_in_transaction(
            contract_id=contract_id,
            db=mock_db
        )
        
        # 验证只查询了评审记录,没有查询合同(因为未全部通过)
        assert mock_db.execute.call_count == 1
