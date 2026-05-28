"""
应用配置
Application configuration
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "合同预审看板系统"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/contract_review"
    DATABASE_ECHO: bool = False
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5分钟
    
    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "contract-attachments"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # 钉钉配置
    DINGTALK_APP_KEY: str = ""
    DINGTALK_APP_SECRET: str = ""
    DINGTALK_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    
    # AI 配置
    AI_PROVIDER: str = "deepseek"  # deepseek 或 custom
    AI_API_BASE: str = "https://api.deepseek.com/v1"
    AI_API_KEY: str = ""
    AI_MODEL: str = "deepseek-chat"
    AI_TIMEOUT: int = 120
    
    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # CORS 配置
    # CORS (Cross-Origin Resource Sharing) 跨域资源共享配置
    # 允许指定的前端域名访问后端 API
    # 
    # 配置说明:
    # - 开发环境: 包含 localhost 的各种端口 (3000, 5173 等)
    # - 生产环境: 必须配置实际的前端域名,例如:
    #   CORS_ORIGINS=https://app.example.com,https://www.example.com
    # 
    # 安全提示:
    # - 不要在生产环境使用 "*" (允许所有域名)
    # - 只添加信任的前端域名
    # - 使用 HTTPS 协议 (生产环境)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",      # React 开发服务器 (CRA)
        "http://localhost:5173",      # Vite 开发服务器
        "http://127.0.0.1:3000",      # 本地回环地址
        "http://127.0.0.1:5173",      # 本地回环地址
    ]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# 创建全局配置实例
settings = Settings()
