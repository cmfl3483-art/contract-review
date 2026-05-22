"""
文件服务层
实现文件上传、下载、版本管理功能
"""
from typing import Optional, BinaryIO, List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from collections import defaultdict
import uuid
import os

from app.models.attachment import Attachment
from app.core.minio_client import minio_client
from app.core.config import settings
from app.utils.cache_invalidation import cache_invalidation


class FileService:
    """文件服务类"""
    
    ALLOWED_MIME_TYPES = settings.ALLOWED_FILE_TYPES
    MAX_FILE_SIZE = settings.MAX_FILE_SIZE
    
    def validate_file(self, file: UploadFile) -> None:
        """
        验证文件类型和大小
        
        Args:
            file: 上传的文件
            
        Raises:
            ValueError: 如果文件不符合要求
        """
        # 验证文件类型
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            raise ValueError(
                f"不支持的文件类型: {file.content_type}。"
                f"支持的类型: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX"
            )
        
        # 验证文件大小
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise ValueError(f"文件大小不能超过{max_size_mb}MB")
    
    async def get_next_version(
        self,
        contract_id: str,
        file_name: str,
        db: AsyncSession
    ) -> str:
        """
        获取文件的下一个版本号
        
        Args:
            contract_id: 合同ID
            file_name: 文件名
            db: 数据库会话
            
        Returns:
            版本号字符串 (如 "v1.0", "v2.0")
        """
        # 查询同名文件的最大版本号
        query = select(func.max(Attachment.version)).where(
            Attachment.contract_id == contract_id,
            Attachment.file_name == file_name
        )
        
        result = await db.execute(query)
        max_version = result.scalar()
        
        if not max_version:
            return "v1.0"
        
        # 解析版本号并递增
        try:
            version_num = int(max_version.replace("v", "").split(".")[0])
            return f"v{version_num + 1}.0"
        except:
            return "v1.0"
    
    async def upload_file(
        self,
        contract_id: str,
        uploader_id: str,
        file: UploadFile,
        db: AsyncSession
    ) -> Attachment:
        """
        上传文件到MinIO并保存记录
        
        Args:
            contract_id: 合同ID
            uploader_id: 上传人ID
            file: 上传的文件
            db: 数据库会话
            
        Returns:
            创建的附件对象
            
        Raises:
            ValueError: 如果文件验证失败
            Exception: 如果上传失败
        """
        # 1. 验证文件
        self.validate_file(file)
        
        # 2. 获取版本号
        version = await self.get_next_version(contract_id, file.filename, db)
        
        # 3. 生成存储键
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        storage_key = f"{contract_id}/{file.filename}/{version}/{file_id}{file_ext}"
        
        # 4. 上传到MinIO
        try:
            file.file.seek(0)
            file_data = await file.read()
            file_size = len(file_data)
            
            minio_client.upload_file_data(
                object_name=storage_key,
                file_data=file_data,
                file_size=file_size,
                content_type=file.content_type
            )
        except Exception as e:
            raise Exception(f"文件上传失败: {str(e)}")
        
        # 5. 保存附件记录
        attachment = Attachment(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            file_name=file.filename,
            version=version,
            file_size=file_size,
            mime_type=file.content_type,
            storage_key=storage_key,
            uploader_id=uploader_id
        )
        
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        
        # 清除缓存 - 使用统一的缓存失效策略
        await cache_invalidation.invalidate_attachment_uploaded(contract_id)
        
        return attachment
    
    def generate_download_url(
        self,
        storage_key: str,
        expires: int = 3600
    ) -> str:
        """
        生成MinIO预签名下载URL
        
        Args:
            storage_key: 存储键
            expires: 有效期(秒),默认1小时
            
        Returns:
            预签名URL
        """
        try:
            url = minio_client.get_presigned_url(
                object_name=storage_key,
                expires=expires
            )
            if url is None:
                raise Exception("生成预签名URL失败")
            return url
        except Exception as e:
            raise Exception(f"生成下载链接失败: {str(e)}")
    
    async def get_attachment(
        self,
        attachment_id: str,
        db: AsyncSession
    ) -> Optional[Attachment]:
        """
        获取附件信息
        
        Args:
            attachment_id: 附件ID
            db: 数据库会话
            
        Returns:
            附件对象
        """
        query = select(Attachment).where(Attachment.id == attachment_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    def download_file_stream(
        self,
        storage_key: str
    ) -> Optional[bytes]:
        """
        从MinIO下载文件流
        
        Args:
            storage_key: 存储键
            
        Returns:
            文件数据字节流
            
        Raises:
            Exception: 如果下载失败
        """
        try:
            file_data = minio_client.get_file(
                object_name=storage_key
            )
            
            if file_data is None:
                raise Exception("文件不存在或下载失败")
            
            return file_data
        except Exception as e:
            raise Exception(f"下载文件失败: {str(e)}")
    
    async def verify_access_permission(
        self,
        attachment_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """
        验证用户是否有权限访问附件
        
        Args:
            attachment_id: 附件ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            是否有权限
        """
        # 获取附件
        attachment = await self.get_attachment(attachment_id, db)
        
        if not attachment:
            return False
        
        # 查询合同信息
        from app.models.contract import Contract
        from app.models.review import Review
        
        query = select(Contract).where(Contract.id == attachment.contract_id)
        result = await db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            return False
        
        # 检查用户是否为发起人、评审人或抄送人
        if contract.initiator_id == user_id:
            return True
        
        if user_id in (contract.cc_users or []):
            return True
        
        # 检查是否为评审人
        review_query = select(Review).where(
            Review.contract_id == contract.id,
            Review.reviewer_id == user_id
        )
        review_result = await db.execute(review_query)
        if review_result.scalar_one_or_none():
            return True
        
        return False
    
    async def get_attachments_by_contract(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> List[Attachment]:
        """
        获取合同的所有附件
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            附件列表
        """
        query = select(Attachment).where(
            Attachment.contract_id == contract_id
        ).order_by(Attachment.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    def group_attachments_by_filename(
        self,
        attachments: List[Attachment]
    ) -> Dict[str, List[Attachment]]:
        """
        按文件名分组附件
        
        Args:
            attachments: 附件列表
            
        Returns:
            按文件名分组的字典,键为文件名,值为附件列表
        """
        grouped = defaultdict(list)
        
        for attachment in attachments:
            grouped[attachment.file_name].append(attachment)
        
        return dict(grouped)
    
    def sort_versions_by_time_desc(
        self,
        versions: List[Attachment]
    ) -> List[Attachment]:
        """
        按时间倒序排列版本
        
        Args:
            versions: 同一文件的版本列表
            
        Returns:
            按创建时间倒序排列的版本列表
        """
        return sorted(versions, key=lambda v: v.created_at, reverse=True)
    
    def mark_latest_version(
        self,
        versions: List[Attachment]
    ) -> List[Dict[str, Any]]:
        """
        标记最新版本
        
        Args:
            versions: 已按时间倒序排列的版本列表
            
        Returns:
            包含is_latest标记的版本字典列表
        """
        result = []
        
        for i, version in enumerate(versions):
            version_dict = {
                "id": str(version.id),
                "file_name": version.file_name,
                "version": version.version,
                "file_size": version.file_size,
                "mime_type": version.mime_type,
                "storage_key": version.storage_key,
                "uploader_id": str(version.uploader_id),
                "uploader_name": version.uploader.name if version.uploader else None,
                "created_at": version.created_at.isoformat(),
                "is_latest": i == 0  # 第一个版本是最新的
            }
            result.append(version_dict)
        
        return result
    
    async def get_grouped_attachments(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        获取按文件名分组的附件,每组按时间倒序排列,并标记最新版本
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            分组后的附件列表,每组包含文件名、版本数量和版本列表
        """
        # 1. 获取所有附件
        attachments = await self.get_attachments_by_contract(contract_id, db)
        
        if not attachments:
            return []
        
        # 2. 按文件名分组
        grouped = self.group_attachments_by_filename(attachments)
        
        # 3. 处理每个分组
        result = []
        for file_name, versions in grouped.items():
            # 按时间倒序排列
            sorted_versions = self.sort_versions_by_time_desc(versions)
            
            # 标记最新版本
            marked_versions = self.mark_latest_version(sorted_versions)
            
            # 获取最新上传时间(用于排序文件组)
            latest_upload_time = sorted_versions[0].created_at
            
            result.append({
                "file_name": file_name,
                "version_count": len(versions),
                "versions": marked_versions,
                "latest_upload_time": latest_upload_time
            })
        
        # 4. 按最新上传时间倒序排列不同文件组
        result.sort(key=lambda g: g["latest_upload_time"], reverse=True)
        
        return result
