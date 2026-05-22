"""
测试文件下载功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.file_service import FileService
from app.models.attachment import Attachment
from app.models.contract import Contract
from app.models.review import Review


@pytest.fixture
def file_service():
    """创建文件服务实例"""
    return FileService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def sample_attachment():
    """创建示例附件"""
    return Attachment(
        id="attachment-123",
        contract_id="contract-123",
        file_name="test.pdf",
        version="v1.0",
        file_size=1024,
        mime_type="application/pdf",
        storage_key="contract-123/test.pdf/v1.0/file-123.pdf",
        uploader_id="user-123"
    )


@pytest.fixture
def sample_contract():
    """创建示例合同"""
    return Contract(
        id="contract-123",
        name="测试合同",
        initiator_id="user-123",
        cc_users=["user-456"],
        status="progress"
    )


class TestFileDownload:
    """测试文件下载功能"""
    
    @pytest.mark.asyncio
    async def test_generate_download_url(self, file_service):
        """测试生成预签名URL"""
        with patch('app.services.file_service.minio_client') as mock_minio:
            # 模拟MinIO客户端返回预签名URL
            mock_minio.get_presigned_url.return_value = "https://minio.example.com/presigned-url"
            
            # 生成下载URL
            url = file_service.generate_download_url(
                storage_key="contract-123/test.pdf/v1.0/file-123.pdf",
                expires=3600
            )
            
            # 验证
            assert url == "https://minio.example.com/presigned-url"
            mock_minio.get_presigned_url.assert_called_once_with(
                object_name="contract-123/test.pdf/v1.0/file-123.pdf",
                expires=3600
            )
    
    @pytest.mark.asyncio
    async def test_generate_download_url_failure(self, file_service):
        """测试生成预签名URL失败"""
        with patch('app.services.file_service.minio_client') as mock_minio:
            # 模拟MinIO客户端返回None
            mock_minio.get_presigned_url.return_value = None
            
            # 验证抛出异常
            with pytest.raises(Exception, match="生成下载链接失败"):
                file_service.generate_download_url(
                    storage_key="contract-123/test.pdf/v1.0/file-123.pdf"
                )
    
    @pytest.mark.asyncio
    async def test_download_file_stream(self, file_service):
        """测试下载文件流"""
        with patch('app.services.file_service.minio_client') as mock_minio:
            # 模拟MinIO客户端返回文件数据
            mock_file_data = b"PDF file content"
            mock_minio.get_file.return_value = mock_file_data
            
            # 下载文件流
            file_data = file_service.download_file_stream(
                storage_key="contract-123/test.pdf/v1.0/file-123.pdf"
            )
            
            # 验证
            assert file_data == mock_file_data
            mock_minio.get_file.assert_called_once_with(
                object_name="contract-123/test.pdf/v1.0/file-123.pdf"
            )
    
    @pytest.mark.asyncio
    async def test_download_file_stream_failure(self, file_service):
        """测试下载文件流失败"""
        with patch('app.services.file_service.minio_client') as mock_minio:
            # 模拟MinIO客户端返回None
            mock_minio.get_file.return_value = None
            
            # 验证抛出异常
            with pytest.raises(Exception, match="下载文件失败"):
                file_service.download_file_stream(
                    storage_key="contract-123/test.pdf/v1.0/file-123.pdf"
                )
    
    @pytest.mark.asyncio
    async def test_verify_access_permission_initiator(
        self, 
        file_service, 
        mock_db, 
        sample_attachment, 
        sample_contract
    ):
        """测试发起人有权限访问附件"""
        # 模拟数据库查询
        mock_db.execute = AsyncMock()
        
        # 模拟查询附件
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = sample_attachment
        
        # 模拟查询合同
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = sample_contract
        
        # 设置execute返回值
        mock_db.execute.side_effect = [attachment_result, contract_result]
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-123",
            user_id="user-123",  # 发起人
            db=mock_db
        )
        
        # 验证
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_verify_access_permission_cc_user(
        self, 
        file_service, 
        mock_db, 
        sample_attachment, 
        sample_contract
    ):
        """测试抄送人有权限访问附件"""
        # 模拟数据库查询
        mock_db.execute = AsyncMock()
        
        # 模拟查询附件
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = sample_attachment
        
        # 模拟查询合同
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = sample_contract
        
        # 设置execute返回值
        mock_db.execute.side_effect = [attachment_result, contract_result]
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-123",
            user_id="user-456",  # 抄送人
            db=mock_db
        )
        
        # 验证
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_verify_access_permission_reviewer(
        self, 
        file_service, 
        mock_db, 
        sample_attachment, 
        sample_contract
    ):
        """测试评审人有权限访问附件"""
        # 模拟数据库查询
        mock_db.execute = AsyncMock()
        
        # 模拟查询附件
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = sample_attachment
        
        # 模拟查询合同
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = sample_contract
        
        # 模拟查询评审记录
        review_result = MagicMock()
        review_result.scalar_one_or_none.return_value = Review(
            id="review-123",
            contract_id="contract-123",
            reviewer_id="user-789",
            status="pending"
        )
        
        # 设置execute返回值
        mock_db.execute.side_effect = [attachment_result, contract_result, review_result]
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-123",
            user_id="user-789",  # 评审人
            db=mock_db
        )
        
        # 验证
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_verify_access_permission_denied(
        self, 
        file_service, 
        mock_db, 
        sample_attachment, 
        sample_contract
    ):
        """测试无关用户没有权限访问附件"""
        # 模拟数据库查询
        mock_db.execute = AsyncMock()
        
        # 模拟查询附件
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = sample_attachment
        
        # 模拟查询合同
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = sample_contract
        
        # 模拟查询评审记录 (无记录)
        review_result = MagicMock()
        review_result.scalar_one_or_none.return_value = None
        
        # 设置execute返回值
        mock_db.execute.side_effect = [attachment_result, contract_result, review_result]
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-123",
            user_id="user-999",  # 无关用户
            db=mock_db
        )
        
        # 验证
        assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_verify_access_permission_attachment_not_found(
        self, 
        file_service, 
        mock_db
    ):
        """测试附件不存在时返回False"""
        # 模拟数据库查询
        mock_db.execute = AsyncMock()
        
        # 模拟查询附件 (不存在)
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.return_value = attachment_result
        
        # 验证权限
        has_permission = await file_service.verify_access_permission(
            attachment_id="non-existent",
            user_id="user-123",
            db=mock_db
        )
        
        # 验证
        assert has_permission is False
