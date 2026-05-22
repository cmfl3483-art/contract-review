"""
合同服务单元测试
Tests for Contract service filtering logic
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.services.contract_service import ContractService
from app.models.contract import Contract, ContractStatus
from app.models.review import Review, ReviewStatus
from app.models.user import User


@pytest.fixture
def contract_service():
    """创建合同服务实例"""
    return ContractService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    db = AsyncMock()
    db.begin = MagicMock()
    db.begin.return_value.__aenter__ = AsyncMock()
    db.begin.return_value.__aexit__ = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """创建模拟用户对象"""
    user = User(
        dingtalk_user_id="test_user_123",
        name="测试用户",
        role="业务"
    )
    user.id = uuid.uuid4()
    return user


@pytest.fixture
def sample_contract(mock_user):
    """创建示例合同"""
    return Contract(
        id=str(uuid.uuid4()),
        name="测试合同",
        description="测试描述",
        status=ContractStatus.PROGRESS,
        initiator_id=mock_user.id,
        cc_users=[],
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_contracts():
    """创建模拟合同列表"""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    user3_id = uuid.uuid4()
    
    contracts = [
        # 进行中的合同1 - 用户1发起
        Contract(
            id=uuid.uuid4(),
            name="合同A",
            description="测试合同A",
            status=ContractStatus.PROGRESS,
            initiator_id=user1_id,
            cc_users=[str(user2_id)],
            created_at=datetime(2025, 3, 1)
        ),
        # 进行中的合同2 - 用户2发起
        Contract(
            id=uuid.uuid4(),
            name="合同B",
            description="测试合同B",
            status=ContractStatus.PROGRESS,
            initiator_id=user2_id,
            cc_users=[str(user1_id), str(user3_id)],
            created_at=datetime(2025, 3, 2)
        ),
        # 已完成的合同1
        Contract(
            id=uuid.uuid4(),
            name="合同C",
            description="测试合同C",
            status=ContractStatus.COMPLETED,
            initiator_id=user1_id,
            cc_users=[],
            created_at=datetime(2025, 2, 28)
        ),
        # 已完成的合同2
        Contract(
            id=uuid.uuid4(),
            name="合同D",
            description="测试合同D",
            status=ContractStatus.COMPLETED,
            initiator_id=user3_id,
            cc_users=[str(user2_id)],
            created_at=datetime(2025, 2, 27)
        ),
    ]
    
    return contracts


class TestContractFilterLogic:
    """测试合同筛选逻辑"""
    
    @pytest.mark.asyncio
    async def test_filter_all(self, contract_service):
        """测试"全部"筛选 - 应该返回所有合同"""
        mock_db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        
        # 调用筛选方法
        result_query = await contract_service._apply_filter(
            mock_query,
            user_id,
            "all",
            mock_db
        )
        
        # "全部"筛选不应该添加任何where条件
        assert result_query == mock_query
        assert not mock_query.where.called
    
    @pytest.mark.asyncio
    async def test_filter_progress(self, contract_service):
        """测试"进行中"筛选 - 应该只返回status为progress的合同"""
        mock_db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        mock_query.where = MagicMock(return_value=mock_query)
        
        # 调用筛选方法
        result_query = await contract_service._apply_filter(
            mock_query,
            user_id,
            "进行中",
            mock_db
        )
        
        # 验证where方法被调用
        assert mock_query.where.called
        # 验证返回的是查询对象
        assert result_query == mock_query
    
    @pytest.mark.asyncio
    async def test_filter_completed(self, contract_service):
        """测试"已完成"筛选 - 应该只返回status为completed的合同"""
        mock_db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        mock_query.where = MagicMock(return_value=mock_query)
        
        # 调用筛选方法
        result_query = await contract_service._apply_filter(
            mock_query,
            user_id,
            "已完成",
            mock_db
        )
        
        # 验证where方法被调用
        assert mock_query.where.called
        assert result_query == mock_query
    
    @pytest.mark.asyncio
    async def test_filter_pending_for_me(self, contract_service):
        """测试"待我处理"筛选 - 应该只返回包含当前用户待处理评审项的合同"""
        mock_db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        mock_query.where = MagicMock(return_value=mock_query)
        
        # 调用筛选方法
        result_query = await contract_service._apply_filter(
            mock_query,
            user_id,
            "待我处理",
            mock_db
        )
        
        # 验证where方法被调用(使用子查询)
        assert mock_query.where.called
        assert result_query == mock_query
    
    @pytest.mark.asyncio
    async def test_filter_cc_me(self, contract_service):
        """测试"抄送我"筛选 - 应该只返回抄送给当前用户的合同"""
        mock_db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        mock_query.where = MagicMock(return_value=mock_query)
        
        # 调用筛选方法
        result_query = await contract_service._apply_filter(
            mock_query,
            user_id,
            "抄送我",
            mock_db
        )
        
        # 验证where方法被调用(使用PostgreSQL数组包含操作符)
        assert mock_query.where.called
        assert result_query == mock_query
    
    @pytest.mark.asyncio
    async def test_filter_unknown_type(self, contract_service):
        """测试未知筛选类型 - 应该不添加任何筛选条件"""
        mock_db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        
        # 调用筛选方法
        result_query = await contract_service._apply_filter(
            mock_query,
            user_id,
            "未知类型",
            mock_db
        )
        
        # 未知类型不应该添加任何where条件
        assert result_query == mock_query
        assert not mock_query.where.called


class TestContractSearchLogic:
    """测试合同搜索逻辑"""
    
    @pytest.mark.asyncio
    async def test_search_by_contract_name(self, contract_service):
        """测试按合同名称搜索"""
        mock_db = AsyncMock()
        keyword = "测试合同"
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        mock_query.join = MagicMock(return_value=mock_query)
        mock_query.where = MagicMock(return_value=mock_query)
        
        # 调用搜索方法
        result_query = await contract_service._apply_search(
            mock_query,
            keyword,
            mock_db
        )
        
        # 验证join和where方法被调用
        assert mock_query.join.called
        assert mock_query.where.called
        assert result_query == mock_query
    
    @pytest.mark.asyncio
    async def test_search_by_initiator_name(self, contract_service):
        """测试按发起人姓名搜索"""
        mock_db = AsyncMock()
        keyword = "张三"
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        mock_query.join = MagicMock(return_value=mock_query)
        mock_query.where = MagicMock(return_value=mock_query)
        
        # 调用搜索方法
        result_query = await contract_service._apply_search(
            mock_query,
            keyword,
            mock_db
        )
        
        # 验证join和where方法被调用
        assert mock_query.join.called
        assert mock_query.where.called
        assert result_query == mock_query
    
    @pytest.mark.asyncio
    async def test_search_empty_keyword(self, contract_service):
        """测试空关键词搜索 - 应该仍然执行搜索逻辑"""
        mock_db = AsyncMock()
        keyword = ""
        
        # 创建模拟查询对象
        mock_query = MagicMock()
        mock_query.join = MagicMock(return_value=mock_query)
        mock_query.where = MagicMock(return_value=mock_query)
        
        # 调用搜索方法
        result_query = await contract_service._apply_search(
            mock_query,
            keyword,
            mock_db
        )
        
        # 即使关键词为空,也应该执行join和where
        assert mock_query.join.called
        assert mock_query.where.called


class TestPendingCount:
    """测试待办数量统计"""
    
    @pytest.mark.asyncio
    async def test_get_pending_count_from_cache(self, contract_service):
        """测试从缓存获取待办数量"""
        user_id = str(uuid.uuid4())
        mock_db = AsyncMock()
        
        # Mock Redis返回缓存值
        with patch('app.services.contract_service.redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value="5")
            
            count = await contract_service.get_pending_count(user_id, mock_db)
            
            # 验证返回缓存的值
            assert count == 5
            # 验证没有查询数据库
            assert not mock_db.execute.called
    
    @pytest.mark.asyncio
    async def test_get_pending_count_from_database(self, contract_service):
        """测试从数据库获取待办数量"""
        user_id = str(uuid.uuid4())
        mock_db = AsyncMock()
        
        # Mock Redis返回None(缓存未命中)
        with patch('app.services.contract_service.redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.set = AsyncMock()
            
            # Mock数据库查询结果
            mock_result = MagicMock()
            mock_result.scalar.return_value = 3
            mock_db.execute = AsyncMock(return_value=mock_result)
            
            count = await contract_service.get_pending_count(user_id, mock_db)
            
            # 验证返回数据库查询的值
            assert count == 3
            # 验证查询了数据库
            assert mock_db.execute.called
            # 验证设置了缓存
            mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_pending_count_zero(self, contract_service):
        """测试待办数量为0的情况"""
        user_id = str(uuid.uuid4())
        mock_db = AsyncMock()
        
        with patch('app.services.contract_service.redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.set = AsyncMock()
            
            # Mock数据库查询结果为0
            mock_result = MagicMock()
            mock_result.scalar.return_value = 0
            mock_db.execute = AsyncMock(return_value=mock_result)
            
            count = await contract_service.get_pending_count(user_id, mock_db)
            
            # 验证返回0
            assert count == 0
            # 验证仍然设置了缓存
            mock_redis.set.assert_called_once()


class TestContractListIntegration:
    """测试合同列表获取的集成逻辑"""
    
    @pytest.mark.asyncio
    async def test_get_contract_list_with_filter_and_search(self, contract_service):
        """测试同时使用筛选和搜索"""
        user_id = str(uuid.uuid4())
        mock_db = AsyncMock()
        
        # Mock数据库查询结果
        mock_contracts = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_contracts
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Mock count查询
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        # Mock pending count
        with patch.object(contract_service, 'get_pending_count', AsyncMock(return_value=2)):
            # 设置execute返回不同的结果
            mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])
            
            result = await contract_service.get_contract_list(
                user_id=user_id,
                filter_type="进行中",
                search_keyword="测试",
                page=1,
                limit=20,
                db=mock_db
            )
            
            # 验证返回结果结构
            assert "contracts" in result
            assert "total" in result
            assert "page" in result
            assert "limit" in result
            assert "pending_count" in result
            assert result["pending_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_contract_list_pagination(self, contract_service):
        """测试分页功能"""
        user_id = str(uuid.uuid4())
        mock_db = AsyncMock()
        
        # Mock数据库查询结果
        mock_contracts = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_contracts
        
        # Mock count查询
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50
        
        with patch.object(contract_service, 'get_pending_count', AsyncMock(return_value=0)):
            mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_result])
            
            result = await contract_service.get_contract_list(
                user_id=user_id,
                filter_type="all",
                page=2,
                limit=10,
                db=mock_db
            )
            
            # 验证分页参数
            assert result["page"] == 2
            assert result["limit"] == 10
            assert result["total"] == 50


class TestCacheManagement:
    """测试缓存管理"""
    
    @pytest.mark.asyncio
    async def test_clear_contract_list_cache(self, contract_service):
        """测试清除合同列表缓存"""
        with patch('app.services.contract_service.redis_client') as mock_redis:
            mock_redis.delete_pattern = AsyncMock()
            
            await contract_service._clear_contract_list_cache()
            
            # 验证调用了delete_pattern
            mock_redis.delete_pattern.assert_called_once_with("contract:list:*")
    
    @pytest.mark.asyncio
    async def test_clear_pending_count_cache(self, contract_service):
        """测试清除待办数量缓存"""
        user_id = str(uuid.uuid4())
        
        with patch('app.services.contract_service.redis_client') as mock_redis:
            mock_redis.delete = AsyncMock()
            
            await contract_service._clear_pending_count_cache(user_id)
            
            # 验证调用了delete
            mock_redis.delete.assert_called_once_with(f"contract:pending:{user_id}")


class TestAttachmentGrouping:
    """测试附件分组逻辑"""
    
    def test_group_attachments_empty(self, contract_service):
        """测试空附件列表"""
        result = contract_service._group_attachments([])
        
        assert result == []
    
    def test_group_attachments_single_file(self, contract_service):
        """测试单个文件"""
        from app.models.attachment import Attachment
        
        attachment = Attachment(
            id=uuid.uuid4(),
            contract_id=uuid.uuid4(),
            file_name="test.pdf",
            version="v1.0",
            file_size=1024,
            mime_type="application/pdf",
            storage_key="key1",
            uploader_id=uuid.uuid4(),
            created_at=datetime(2025, 3, 1)
        )
        
        result = contract_service._group_attachments([attachment])
        
        assert len(result) == 1
        assert result[0]["file_name"] == "test.pdf"
        assert result[0]["version_count"] == 1
        assert len(result[0]["versions"]) == 1
    
    def test_group_attachments_multiple_versions(self, contract_service):
        """测试同一文件的多个版本"""
        from app.models.attachment import Attachment
        
        contract_id = uuid.uuid4()
        uploader_id = uuid.uuid4()
        
        attachments = [
            Attachment(
                id=uuid.uuid4(),
                contract_id=contract_id,
                file_name="test.pdf",
                version="v1.0",
                file_size=1024,
                mime_type="application/pdf",
                storage_key="key1",
                uploader_id=uploader_id,
                created_at=datetime(2025, 3, 1)
            ),
            Attachment(
                id=uuid.uuid4(),
                contract_id=contract_id,
                file_name="test.pdf",
                version="v2.0",
                file_size=2048,
                mime_type="application/pdf",
                storage_key="key2",
                uploader_id=uploader_id,
                created_at=datetime(2025, 3, 2)
            ),
            Attachment(
                id=uuid.uuid4(),
                contract_id=contract_id,
                file_name="test.pdf",
                version="v3.0",
                file_size=3072,
                mime_type="application/pdf",
                storage_key="key3",
                uploader_id=uploader_id,
                created_at=datetime(2025, 3, 3)
            ),
        ]
        
        result = contract_service._group_attachments(attachments)
        
        assert len(result) == 1
        assert result[0]["file_name"] == "test.pdf"
        assert result[0]["version_count"] == 3
        # 验证版本按时间倒序排列(最新的在前)
        assert result[0]["versions"][0].version == "v3.0"
        assert result[0]["versions"][1].version == "v2.0"
        assert result[0]["versions"][2].version == "v1.0"
        # 验证latest_version是最新的
        assert result[0]["latest_version"].version == "v3.0"
    
    def test_group_attachments_multiple_files(self, contract_service):
        """测试多个不同文件"""
        from app.models.attachment import Attachment
        
        contract_id = uuid.uuid4()
        uploader_id = uuid.uuid4()
        
        attachments = [
            Attachment(
                id=uuid.uuid4(),
                contract_id=contract_id,
                file_name="file1.pdf",
                version="v1.0",
                file_size=1024,
                mime_type="application/pdf",
                storage_key="key1",
                uploader_id=uploader_id,
                created_at=datetime(2025, 3, 1)
            ),
            Attachment(
                id=uuid.uuid4(),
                contract_id=contract_id,
                file_name="file2.docx",
                version="v1.0",
                file_size=2048,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                storage_key="key2",
                uploader_id=uploader_id,
                created_at=datetime(2025, 3, 2)
            ),
        ]
        
        result = contract_service._group_attachments(attachments)
        
        assert len(result) == 2
        # 验证按最新上传时间倒序排列
        assert result[0]["file_name"] == "file2.docx"
        assert result[1]["file_name"] == "file1.pdf"



class TestUpdateContractStatus:
    """测试更新合同状态功能"""
    
    @pytest.mark.asyncio
    async def test_update_contract_status_clears_cache(
        self,
        contract_service,
        mock_db,
        sample_contract
    ):
        """测试更新合同状态时清除缓存"""
        with patch('app.services.contract_service.redis_client') as mock_redis:
            mock_redis.delete_pattern = AsyncMock(return_value=5)
            mock_redis.delete = AsyncMock(return_value=True)
            
            # Mock 数据库查询
            mock_result = MagicMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=sample_contract)
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            await contract_service.update_contract_status(
                sample_contract.id,
                "completed",
                mock_db
            )
            
            # 验证清除了合同列表缓存
            mock_redis.delete_pattern.assert_called_once_with("contract:list:*")
            
            # 验证清除了待办数量缓存
            mock_redis.delete.assert_called_once_with(
                f"contract:pending:{sample_contract.initiator_id}"
            )
