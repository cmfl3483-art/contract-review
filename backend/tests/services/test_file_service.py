"""
文件服务单元测试
Unit tests for FileService
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from io import BytesIO

from app.services.file_service import FileService
from app.models.attachment import Attachment


@pytest.fixture
def file_service():
    """创建文件服务实例"""
    return FileService()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def valid_pdf_file():
    """创建有效的PDF文件"""
    file_content = b"PDF file content"
    file = MagicMock(spec=UploadFile)
    file.filename = "test.pdf"
    file.content_type = "application/pdf"
    file.file = BytesIO(file_content)
    file.read = AsyncMock(return_value=file_content)
    return file


@pytest.fixture
def valid_docx_file():
    """创建有效的DOCX文件"""
    file_content = b"DOCX file content"
    file = MagicMock(spec=UploadFile)
    file.filename = "test.docx"
    file.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    file.file = BytesIO(file_content)
    file.read = AsyncMock(return_value=file_content)
    return file


@pytest.fixture
def invalid_type_file():
    """创建无效类型的文件"""
    file_content = b"ZIP file content"
    file = MagicMock(spec=UploadFile)
    file.filename = "test.zip"
    file.content_type = "application/zip"
    file.file = BytesIO(file_content)
    file.read = AsyncMock(return_value=file_content)
    return file


@pytest.fixture
def oversized_file():
    """创建超大文件"""
    # 创建一个超过20MB的文件
    file_content = b"x" * (21 * 1024 * 1024)
    file = MagicMock(spec=UploadFile)
    file.filename = "large.pdf"
    file.content_type = "application/pdf"
    file.file = BytesIO(file_content)
    file.read = AsyncMock(return_value=file_content)
    return file


class TestFileValidation:
    """测试文件验证功能"""
    
    def test_validate_valid_pdf(self, file_service, valid_pdf_file):
        """测试验证有效的PDF文件"""
        # 不应该抛出异常
        file_service.validate_file(valid_pdf_file)
    
    def test_validate_valid_docx(self, file_service, valid_docx_file):
        """测试验证有效的DOCX文件"""
        # 不应该抛出异常
        file_service.validate_file(valid_docx_file)
    
    def test_validate_invalid_type(self, file_service, invalid_type_file):
        """测试验证无效类型的文件"""
        with pytest.raises(ValueError) as exc_info:
            file_service.validate_file(invalid_type_file)
        
        assert "不支持的文件类型" in str(exc_info.value)
    
    def test_validate_oversized_file(self, file_service, oversized_file):
        """测试验证超大文件"""
        with pytest.raises(ValueError) as exc_info:
            file_service.validate_file(oversized_file)
        
        assert "文件大小不能超过" in str(exc_info.value)


class TestVersionManagement:
    """测试版本管理功能"""
    
    @pytest.mark.asyncio
    async def test_get_next_version_first_upload(self, file_service, mock_db):
        """测试首次上传文件的版本号"""
        # 模拟数据库查询返回None (没有同名文件)
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result
        
        version = await file_service.get_next_version(
            contract_id="contract-123",
            file_name="test.pdf",
            db=mock_db
        )
        
        assert version == "v1.0"
    
    @pytest.mark.asyncio
    async def test_get_next_version_second_upload(self, file_service, mock_db):
        """测试第二次上传同名文件的版本号"""
        # 模拟数据库查询返回v1.0
        mock_result = MagicMock()
        mock_result.scalar.return_value = "v1.0"
        mock_db.execute.return_value = mock_result
        
        version = await file_service.get_next_version(
            contract_id="contract-123",
            file_name="test.pdf",
            db=mock_db
        )
        
        assert version == "v2.0"
    
    @pytest.mark.asyncio
    async def test_get_next_version_third_upload(self, file_service, mock_db):
        """测试第三次上传同名文件的版本号"""
        # 模拟数据库查询返回v2.0
        mock_result = MagicMock()
        mock_result.scalar.return_value = "v2.0"
        mock_db.execute.return_value = mock_result
        
        version = await file_service.get_next_version(
            contract_id="contract-123",
            file_name="test.pdf",
            db=mock_db
        )
        
        assert version == "v3.0"
    
    @pytest.mark.asyncio
    async def test_get_next_version_invalid_format(self, file_service, mock_db):
        """测试处理无效版本号格式"""
        # 模拟数据库查询返回无效格式
        mock_result = MagicMock()
        mock_result.scalar.return_value = "invalid"
        mock_db.execute.return_value = mock_result
        
        version = await file_service.get_next_version(
            contract_id="contract-123",
            file_name="test.pdf",
            db=mock_db
        )
        
        # 应该返回v1.0作为默认值
        assert version == "v1.0"


class TestFileUpload:
    """测试文件上传功能"""
    
    @pytest.mark.asyncio
    @patch('app.services.file_service.minio_client')
    async def test_upload_file_success(
        self,
        mock_minio,
        file_service,
        mock_db,
        valid_pdf_file
    ):
        """测试成功上传文件"""
        # 模拟版本号查询
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 模拟MinIO上传成功
        mock_minio.upload_file_data.return_value = True
        
        # 模拟数据库操作
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        attachment = await file_service.upload_file(
            contract_id="contract-123",
            uploader_id="user-456",
            file=valid_pdf_file,
            db=mock_db
        )
        
        # 验证返回的附件对象
        assert attachment.file_name == "test.pdf"
        assert attachment.version == "v1.0"
        assert attachment.mime_type == "application/pdf"
        assert attachment.contract_id == "contract-123"
        assert attachment.uploader_id == "user-456"
        
        # 验证MinIO上传被调用
        mock_minio.upload_file_data.assert_called_once()
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_invalid_type(
        self,
        file_service,
        mock_db,
        invalid_type_file
    ):
        """测试上传无效类型文件"""
        with pytest.raises(ValueError) as exc_info:
            await file_service.upload_file(
                contract_id="contract-123",
                uploader_id="user-456",
                file=invalid_type_file,
                db=mock_db
            )
        
        assert "不支持的文件类型" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.services.file_service.minio_client')
    async def test_upload_file_minio_failure(
        self,
        mock_minio,
        file_service,
        mock_db,
        valid_pdf_file
    ):
        """测试MinIO上传失败"""
        # 模拟版本号查询
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result
        
        # 模拟MinIO上传失败
        mock_minio.upload_file_data.side_effect = Exception("MinIO error")
        
        with pytest.raises(Exception) as exc_info:
            await file_service.upload_file(
                contract_id="contract-123",
                uploader_id="user-456",
                file=valid_pdf_file,
                db=mock_db
            )
        
        assert "文件上传失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.services.file_service.minio_client')
    async def test_upload_file_version_increment(
        self,
        mock_minio,
        file_service,
        mock_db,
        valid_pdf_file
    ):
        """测试上传同名文件时版本号递增"""
        # 模拟已存在v1.0版本
        mock_result = MagicMock()
        mock_result.scalar.return_value = "v1.0"
        mock_db.execute.return_value = mock_result
        
        # 模拟MinIO上传成功
        mock_minio.upload_file_data.return_value = True
        
        # 模拟数据库操作
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        attachment = await file_service.upload_file(
            contract_id="contract-123",
            uploader_id="user-456",
            file=valid_pdf_file,
            db=mock_db
        )
        
        # 验证版本号递增
        assert attachment.version == "v2.0"


class TestDownloadURL:
    """测试下载URL生成功能"""
    
    @patch('app.services.file_service.minio_client')
    def test_generate_download_url_success(self, mock_minio, file_service):
        """测试成功生成下载URL"""
        mock_minio.get_presigned_url.return_value = "https://minio.example.com/presigned-url"
        
        url = file_service.generate_download_url(
            storage_key="contract-123/test.pdf/v1.0/file-id.pdf"
        )
        
        assert url == "https://minio.example.com/presigned-url"
        mock_minio.get_presigned_url.assert_called_once_with(
            object_name="contract-123/test.pdf/v1.0/file-id.pdf",
            expires=3600
        )
    
    @patch('app.services.file_service.minio_client')
    def test_generate_download_url_custom_expires(self, mock_minio, file_service):
        """测试自定义过期时间"""
        mock_minio.get_presigned_url.return_value = "https://minio.example.com/presigned-url"
        
        url = file_service.generate_download_url(
            storage_key="contract-123/test.pdf/v1.0/file-id.pdf",
            expires=7200
        )
        
        mock_minio.get_presigned_url.assert_called_once_with(
            object_name="contract-123/test.pdf/v1.0/file-id.pdf",
            expires=7200
        )
    
    @patch('app.services.file_service.minio_client')
    def test_generate_download_url_failure(self, mock_minio, file_service):
        """测试生成下载URL失败"""
        mock_minio.get_presigned_url.side_effect = Exception("MinIO error")
        
        with pytest.raises(Exception) as exc_info:
            file_service.generate_download_url(
                storage_key="contract-123/test.pdf/v1.0/file-id.pdf"
            )
        
        assert "生成下载链接失败" in str(exc_info.value)


class TestAccessPermission:
    """测试访问权限验证功能"""
    
    @pytest.mark.asyncio
    async def test_verify_access_initiator(self, file_service, mock_db):
        """测试发起人有访问权限"""
        # 模拟附件查询
        mock_attachment = MagicMock()
        mock_attachment.contract_id = "contract-123"
        
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = mock_attachment
        
        # 模拟合同查询
        mock_contract = MagicMock()
        mock_contract.id = "contract-123"
        mock_contract.initiator_id = "user-456"
        mock_contract.cc_users = []
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        # 模拟评审查询
        review_result = MagicMock()
        review_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            attachment_result,
            contract_result,
            review_result
        ]
        
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-789",
            user_id="user-456",
            db=mock_db
        )
        
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_verify_access_cc_user(self, file_service, mock_db):
        """测试抄送人有访问权限"""
        # 模拟附件查询
        mock_attachment = MagicMock()
        mock_attachment.contract_id = "contract-123"
        
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = mock_attachment
        
        # 模拟合同查询
        mock_contract = MagicMock()
        mock_contract.id = "contract-123"
        mock_contract.initiator_id = "user-111"
        mock_contract.cc_users = ["user-456", "user-789"]
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        mock_db.execute.side_effect = [
            attachment_result,
            contract_result
        ]
        
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-789",
            user_id="user-456",
            db=mock_db
        )
        
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_verify_access_reviewer(self, file_service, mock_db):
        """测试评审人有访问权限"""
        # 模拟附件查询
        mock_attachment = MagicMock()
        mock_attachment.contract_id = "contract-123"
        
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = mock_attachment
        
        # 模拟合同查询
        mock_contract = MagicMock()
        mock_contract.id = "contract-123"
        mock_contract.initiator_id = "user-111"
        mock_contract.cc_users = []
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        # 模拟评审查询 - 用户是评审人
        mock_review = MagicMock()
        review_result = MagicMock()
        review_result.scalar_one_or_none.return_value = mock_review
        
        mock_db.execute.side_effect = [
            attachment_result,
            contract_result,
            review_result
        ]
        
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-789",
            user_id="user-456",
            db=mock_db
        )
        
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_verify_access_no_permission(self, file_service, mock_db):
        """测试无权限用户"""
        # 模拟附件查询
        mock_attachment = MagicMock()
        mock_attachment.contract_id = "contract-123"
        
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = mock_attachment
        
        # 模拟合同查询
        mock_contract = MagicMock()
        mock_contract.id = "contract-123"
        mock_contract.initiator_id = "user-111"
        mock_contract.cc_users = ["user-222"]
        
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = mock_contract
        
        # 模拟评审查询 - 用户不是评审人
        review_result = MagicMock()
        review_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            attachment_result,
            contract_result,
            review_result
        ]
        
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-789",
            user_id="user-456",
            db=mock_db
        )
        
        assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_verify_access_attachment_not_found(self, file_service, mock_db):
        """测试附件不存在"""
        # 模拟附件查询返回None
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.return_value = attachment_result
        
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-789",
            user_id="user-456",
            db=mock_db
        )
        
        assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_verify_access_contract_not_found(self, file_service, mock_db):
        """测试合同不存在"""
        # 模拟附件查询
        mock_attachment = MagicMock()
        mock_attachment.contract_id = "contract-123"
        
        attachment_result = MagicMock()
        attachment_result.scalar_one_or_none.return_value = mock_attachment
        
        # 模拟合同查询返回None
        contract_result = MagicMock()
        contract_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            attachment_result,
            contract_result
        ]
        
        has_permission = await file_service.verify_access_permission(
            attachment_id="attachment-789",
            user_id="user-456",
            db=mock_db
        )
        
        assert has_permission is False
