"""
测试上传附件 API
Test upload attachment API
"""

import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.models.user import User
from app.models.contract import Contract


@pytest.mark.asyncio
async def test_upload_attachment_success(async_client, test_user: User, test_contract: Contract, auth_headers):
    """测试成功上传附件"""
    
    # Mock MinIO 客户端
    with patch('app.services.file_service.minio_client') as mock_minio:
        mock_minio.upload_file_data = MagicMock()
        
        # 创建测试文件
        file_content = b"Test PDF content"
        file_data = BytesIO(file_content)
        
        # 发送上传请求
        response = await async_client.post(
            f"/api/contracts/{test_contract.id}/attachments",
            headers=auth_headers,
            files={
                "file": ("test.pdf", file_data, "application/pdf")
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "attachment" in data["data"]
        
        attachment = data["data"]["attachment"]
        assert attachment["file_name"] == "test.pdf"
        assert attachment["version"] == "v1.0"
        assert attachment["mime_type"] == "application/pdf"
        assert "id" in attachment
        assert "created_at" in attachment


@pytest.mark.asyncio
async def test_upload_attachment_invalid_file_type(async_client, test_user: User, test_contract: Contract, auth_headers):
    """测试上传不支持的文件类型"""
    
    # 创建测试文件 (不支持的类型)
    file_content = b"Test ZIP content"
    file_data = BytesIO(file_content)
    
    # 发送上传请求
    response = await async_client.post(
        f"/api/contracts/{test_contract.id}/attachments",
        headers=auth_headers,
        files={
            "file": ("test.zip", file_data, "application/zip")
        }
    )
    
    # 验证响应
    assert response.status_code == 400
    assert "不支持的文件类型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_attachment_file_too_large(async_client, test_user: User, test_contract: Contract, auth_headers):
    """测试上传超过大小限制的文件"""
    
    # 创建超大文件 (21MB)
    file_content = b"x" * (21 * 1024 * 1024)
    file_data = BytesIO(file_content)
    
    # 发送上传请求
    response = await async_client.post(
        f"/api/contracts/{test_contract.id}/attachments",
        headers=auth_headers,
        files={
            "file": ("large.pdf", file_data, "application/pdf")
        }
    )
    
    # 验证响应
    assert response.status_code == 400
    assert "文件大小不能超过" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_attachment_version_increment(async_client, test_user: User, test_contract: Contract, auth_headers, db_session):
    """测试同名文件版本号递增"""
    
    # Mock MinIO 客户端
    with patch('app.services.file_service.minio_client') as mock_minio:
        mock_minio.upload_file_data = MagicMock()
        
        # 第一次上传
        file_data1 = BytesIO(b"Version 1")
        response1 = await async_client.post(
            f"/api/contracts/{test_contract.id}/attachments",
            headers=auth_headers,
            files={
                "file": ("contract.pdf", file_data1, "application/pdf")
            }
        )
        
        assert response1.status_code == 200
        attachment1 = response1.json()["data"]["attachment"]
        assert attachment1["version"] == "v1.0"
        
        # 第二次上传同名文件
        file_data2 = BytesIO(b"Version 2")
        response2 = await async_client.post(
            f"/api/contracts/{test_contract.id}/attachments",
            headers=auth_headers,
            files={
                "file": ("contract.pdf", file_data2, "application/pdf")
            }
        )
        
        assert response2.status_code == 200
        attachment2 = response2.json()["data"]["attachment"]
        assert attachment2["version"] == "v2.0"


@pytest.mark.asyncio
async def test_upload_attachment_unauthorized(async_client, test_contract: Contract):
    """测试未授权上传附件"""
    
    file_data = BytesIO(b"Test content")
    
    # 不提供认证头
    response = await async_client.post(
        f"/api/contracts/{test_contract.id}/attachments",
        files={
            "file": ("test.pdf", file_data, "application/pdf")
        }
    )
    
    # 验证响应
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_attachment_contract_not_found(async_client, auth_headers):
    """测试上传到不存在的合同"""
    
    # Mock MinIO 客户端
    with patch('app.services.file_service.minio_client') as mock_minio:
        mock_minio.upload_file_data = MagicMock()
        
        file_data = BytesIO(b"Test content")
        fake_contract_id = str(uuid4())
        
        response = await async_client.post(
            f"/api/contracts/{fake_contract_id}/attachments",
            headers=auth_headers,
            files={
                "file": ("test.pdf", file_data, "application/pdf")
            }
        )
        
        # 应该返回错误 (可能是 404 或 500)
        assert response.status_code in [404, 500]
