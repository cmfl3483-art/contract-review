"""
测试文件服务的附件分组逻辑
Test file service attachment grouping logic
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from app.services.file_service import FileService
from app.models.attachment import Attachment
from app.models.user import User


@pytest.fixture
def file_service():
    """创建文件服务实例"""
    return FileService()


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.name = "测试用户"
    return user


@pytest.fixture
def sample_attachments(mock_user):
    """创建示例附件列表"""
    now = datetime.utcnow()
    
    # 创建三个文件,每个文件有不同数量的版本
    attachments = []
    
    # 文件1: 采购清单.pdf - 3个版本
    for i in range(3):
        attachment = MagicMock(spec=Attachment)
        attachment.id = uuid4()
        attachment.file_name = "采购清单.pdf"
        attachment.version = f"v{3-i}.0"
        attachment.file_size = 1024 * 1024 * (i + 1)
        attachment.mime_type = "application/pdf"
        attachment.storage_key = f"contract-123/采购清单.pdf/v{3-i}.0/{uuid4()}.pdf"
        attachment.uploader_id = mock_user.id
        attachment.uploader = mock_user
        attachment.created_at = now - timedelta(days=i)
        attachments.append(attachment)
    
    # 文件2: 合同草稿.docx - 2个版本
    for i in range(2):
        attachment = MagicMock(spec=Attachment)
        attachment.id = uuid4()
        attachment.file_name = "合同草稿.docx"
        attachment.version = f"v{2-i}.0"
        attachment.file_size = 1024 * 512 * (i + 1)
        attachment.mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        attachment.storage_key = f"contract-123/合同草稿.docx/v{2-i}.0/{uuid4()}.docx"
        attachment.uploader_id = mock_user.id
        attachment.uploader = mock_user
        attachment.created_at = now - timedelta(days=i + 5)
        attachments.append(attachment)
    
    # 文件3: 预算表.xlsx - 1个版本
    attachment = MagicMock(spec=Attachment)
    attachment.id = uuid4()
    attachment.file_name = "预算表.xlsx"
    attachment.version = "v1.0"
    attachment.file_size = 1024 * 256
    attachment.mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    attachment.storage_key = f"contract-123/预算表.xlsx/v1.0/{uuid4()}.xlsx"
    attachment.uploader_id = mock_user.id
    attachment.uploader = mock_user
    attachment.created_at = now - timedelta(days=10)
    attachments.append(attachment)
    
    return attachments


class TestFileServiceGrouping:
    """测试文件服务分组功能"""
    
    def test_group_attachments_by_filename(self, file_service, sample_attachments):
        """测试按文件名分组附件"""
        grouped = file_service.group_attachments_by_filename(sample_attachments)
        
        # 验证分组数量
        assert len(grouped) == 3
        
        # 验证每个分组的版本数量
        assert len(grouped["采购清单.pdf"]) == 3
        assert len(grouped["合同草稿.docx"]) == 2
        assert len(grouped["预算表.xlsx"]) == 1
    
    def test_sort_versions_by_time_desc(self, file_service, sample_attachments):
        """测试按时间倒序排列版本"""
        # 获取采购清单的所有版本
        purchase_list_versions = [
            att for att in sample_attachments 
            if att.file_name == "采购清单.pdf"
        ]
        
        # 排序
        sorted_versions = file_service.sort_versions_by_time_desc(purchase_list_versions)
        
        # 验证排序结果
        assert len(sorted_versions) == 3
        assert sorted_versions[0].version == "v3.0"  # 最新的
        assert sorted_versions[1].version == "v2.0"
        assert sorted_versions[2].version == "v1.0"  # 最旧的
        
        # 验证时间顺序
        for i in range(len(sorted_versions) - 1):
            assert sorted_versions[i].created_at >= sorted_versions[i + 1].created_at
    
    def test_mark_latest_version(self, file_service, sample_attachments):
        """测试标记最新版本"""
        # 获取采购清单的所有版本并排序
        purchase_list_versions = [
            att for att in sample_attachments 
            if att.file_name == "采购清单.pdf"
        ]
        sorted_versions = file_service.sort_versions_by_time_desc(purchase_list_versions)
        
        # 标记最新版本
        marked_versions = file_service.mark_latest_version(sorted_versions)
        
        # 验证结果
        assert len(marked_versions) == 3
        
        # 验证第一个版本被标记为最新
        assert marked_versions[0]["is_latest"] is True
        assert marked_versions[0]["version"] == "v3.0"
        
        # 验证其他版本未被标记为最新
        assert marked_versions[1]["is_latest"] is False
        assert marked_versions[2]["is_latest"] is False
        
        # 验证包含必要字段
        for version in marked_versions:
            assert "id" in version
            assert "file_name" in version
            assert "version" in version
            assert "file_size" in version
            assert "mime_type" in version
            assert "uploader_id" in version
            assert "uploader_name" in version
            assert "created_at" in version
            assert "is_latest" in version
    
    @pytest.mark.asyncio
    async def test_get_grouped_attachments(self, file_service, sample_attachments):
        """测试获取分组附件的完整流程"""
        # 创建模拟数据库会话
        mock_db = AsyncMock()
        
        # 模拟 get_attachments_by_contract 方法
        file_service.get_attachments_by_contract = AsyncMock(return_value=sample_attachments)
        
        # 调用方法
        result = await file_service.get_grouped_attachments("contract-123", mock_db)
        
        # 验证结果
        assert len(result) == 3
        
        # 验证文件组按最新上传时间倒序排列
        # 采购清单.pdf 最新(0天前) -> 合同草稿.docx (5天前) -> 预算表.xlsx (10天前)
        assert result[0]["file_name"] == "采购清单.pdf"
        assert result[1]["file_name"] == "合同草稿.docx"
        assert result[2]["file_name"] == "预算表.xlsx"
        
        # 验证每个文件组的结构
        for group in result:
            assert "file_name" in group
            assert "version_count" in group
            assert "versions" in group
            assert "latest_upload_time" in group
        
        # 验证采购清单的版本信息
        purchase_list_group = result[0]
        assert purchase_list_group["version_count"] == 3
        assert len(purchase_list_group["versions"]) == 3
        assert purchase_list_group["versions"][0]["is_latest"] is True
        assert purchase_list_group["versions"][0]["version"] == "v3.0"
        
        # 验证合同草稿的版本信息
        contract_draft_group = result[1]
        assert contract_draft_group["version_count"] == 2
        assert len(contract_draft_group["versions"]) == 2
        assert contract_draft_group["versions"][0]["is_latest"] is True
        assert contract_draft_group["versions"][0]["version"] == "v2.0"
        
        # 验证预算表的版本信息
        budget_group = result[2]
        assert budget_group["version_count"] == 1
        assert len(budget_group["versions"]) == 1
        assert budget_group["versions"][0]["is_latest"] is True
        assert budget_group["versions"][0]["version"] == "v1.0"
    
    @pytest.mark.asyncio
    async def test_get_grouped_attachments_empty(self, file_service):
        """测试获取空附件列表"""
        # 创建模拟数据库会话
        mock_db = AsyncMock()
        
        # 模拟返回空列表
        file_service.get_attachments_by_contract = AsyncMock(return_value=[])
        
        # 调用方法
        result = await file_service.get_grouped_attachments("contract-123", mock_db)
        
        # 验证返回空列表
        assert result == []
    
    def test_group_attachments_single_file_multiple_versions(self, file_service, mock_user):
        """测试单个文件多个版本的分组"""
        now = datetime.utcnow()
        
        # 创建同一文件的5个版本
        attachments = []
        for i in range(5):
            attachment = MagicMock(spec=Attachment)
            attachment.id = uuid4()
            attachment.file_name = "测试文件.pdf"
            attachment.version = f"v{5-i}.0"
            attachment.file_size = 1024 * (i + 1)
            attachment.mime_type = "application/pdf"
            attachment.storage_key = f"contract-123/测试文件.pdf/v{5-i}.0/{uuid4()}.pdf"
            attachment.uploader_id = mock_user.id
            attachment.uploader = mock_user
            attachment.created_at = now - timedelta(hours=i)
            attachments.append(attachment)
        
        # 分组
        grouped = file_service.group_attachments_by_filename(attachments)
        
        # 验证只有一个分组
        assert len(grouped) == 1
        assert len(grouped["测试文件.pdf"]) == 5
        
        # 排序
        sorted_versions = file_service.sort_versions_by_time_desc(grouped["测试文件.pdf"])
        
        # 验证排序正确
        assert sorted_versions[0].version == "v5.0"
        assert sorted_versions[4].version == "v1.0"
        
        # 标记最新版本
        marked_versions = file_service.mark_latest_version(sorted_versions)
        
        # 验证只有第一个被标记为最新
        assert marked_versions[0]["is_latest"] is True
        for i in range(1, 5):
            assert marked_versions[i]["is_latest"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
