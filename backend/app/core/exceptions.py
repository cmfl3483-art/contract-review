"""
自定义异常类
Custom exception classes for better error handling
"""
from typing import Optional, Any


class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ValidationError(AppException):
    """验证错误 - 400"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else None
        )


class UnauthorizedError(AppException):
    """未授权错误 - 401"""
    
    def __init__(self, message: str = "未授权,请先登录"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401
        )


class ForbiddenError(AppException):
    """权限不足错误 - 403"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403
        )


class NotFoundError(AppException):
    """资源不存在错误 - 404"""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource} if resource else None
        )


class ConflictError(AppException):
    """冲突错误 - 409"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409
        )


class PayloadTooLargeError(AppException):
    """文件过大错误 - 413"""
    
    def __init__(self, message: str = "文件大小超过限制", max_size: Optional[int] = None):
        super().__init__(
            message=message,
            code="PAYLOAD_TOO_LARGE",
            status_code=413,
            details={"max_size": max_size} if max_size else None
        )


class DatabaseError(AppException):
    """数据库错误 - 500"""
    
    def __init__(self, message: str = "数据库操作失败", original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details={"original_error": str(original_error)} if original_error else None
        )


class ExternalServiceError(AppException):
    """外部服务错误 - 502"""
    
    def __init__(self, message: str, service: Optional[str] = None):
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service} if service else None
        )


class AIServiceError(ExternalServiceError):
    """AI服务错误 - 502"""
    
    def __init__(self, message: str = "AI服务暂时不可用,请稍后重试"):
        super().__init__(
            message=message,
            service="AI"
        )


class MinIOServiceError(ExternalServiceError):
    """MinIO服务错误 - 502"""
    
    def __init__(self, message: str = "文件存储服务暂时不可用,请稍后重试"):
        super().__init__(
            message=message,
            service="MinIO"
        )


class ServiceUnavailableError(AppException):
    """服务不可用错误 - 503"""
    
    def __init__(self, message: str = "服务暂时不可用,请稍后重试"):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503
        )
