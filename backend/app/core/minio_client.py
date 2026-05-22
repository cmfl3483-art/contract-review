"""
MinIO 客户端配置
MinIO client configuration
"""

from typing import Optional
from minio import Minio
from minio.error import S3Error
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO 客户端封装类"""
    
    def __init__(self):
        self.client: Optional[Minio] = None
        self.bucket_name = settings.MINIO_BUCKET
    
    def connect(self) -> None:
        """连接到 MinIO"""
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            logger.info(f"Connected to MinIO at {settings.MINIO_ENDPOINT}")
        except Exception as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            raise
    
    def initialize_bucket(self) -> None:
        """初始化 bucket，如果不存在则创建"""
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            # 检查 bucket 是否存在
            if not self.client.bucket_exists(self.bucket_name):
                # 创建 bucket
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to initialize bucket: {e}")
            raise
    
    def upload_file(
        self,
        object_name: str,
        file_path: str,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """
        上传文件到 MinIO
        
        Args:
            object_name: 对象名称（存储路径）
            file_path: 本地文件路径
            content_type: 文件 MIME 类型
        
        Returns:
            bool: 上传是否成功
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type,
            )
            logger.info(f"Uploaded file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def upload_file_data(
        self,
        object_name: str,
        file_data: bytes,
        file_size: int,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """
        上传文件数据到 MinIO
        
        Args:
            object_name: 对象名称（存储路径）
            file_data: 文件数据
            file_size: 文件大小
            content_type: 文件 MIME 类型
        
        Returns:
            bool: 上传是否成功
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            from io import BytesIO
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                BytesIO(file_data),
                file_size,
                content_type=content_type,
            )
            logger.info(f"Uploaded file data: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to upload file data: {e}")
            return False
    
    def get_file(self, object_name: str) -> Optional[bytes]:
        """
        从 MinIO 获取文件
        
        Args:
            object_name: 对象名称（存储路径）
        
        Returns:
            Optional[bytes]: 文件数据，如果失败返回 None
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Failed to get file: {e}")
            return None
    
    def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600,
    ) -> Optional[str]:
        """
        生成预签名 URL
        
        Args:
            object_name: 对象名称（存储路径）
            expires: 过期时间（秒），默认 1 小时
        
        Returns:
            Optional[str]: 预签名 URL，如果失败返回 None
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            from datetime import timedelta
            
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires),
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: 对象名称（存储路径）
        
        Returns:
            bool: 删除是否成功
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称（存储路径）
        
        Returns:
            bool: 文件是否存在
        """
        if not self.client:
            raise RuntimeError("MinIO client not connected")
        
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False


# 创建全局 MinIO 客户端实例
minio_client = MinIOClient()
