"""
全局错误处理中间件
Global error handling middleware for FastAPI
"""
import logging
import traceback
import uuid
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, NoResultFound

from app.core.exceptions import (
    AppException,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    处理自定义应用异常
    
    Args:
        request: FastAPI请求对象
        exc: 自定义异常
        
    Returns:
        JSON响应
    """
    # 生成请求ID用于追踪
    request_id = str(uuid.uuid4())
    
    # 记录错误日志
    logger.error(
        f"AppException: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "status_code": exc.status_code,
            "error_code": exc.code,
            "details": exc.details
        }
    )
    
    # 构建响应
    response_data = {
        "success": False,
        "error": exc.message,
        "code": exc.code,
        "request_id": request_id
    }
    
    # 添加详细信息(如果有)
    if exc.details:
        response_data["details"] = exc.details
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理HTTP异常
    
    Args:
        request: FastAPI请求对象
        exc: HTTP异常
        
    Returns:
        JSON响应
    """
    # 生成请求ID用于追踪
    request_id = str(uuid.uuid4())
    
    # 记录错误日志
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    # 映射错误码
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "code": error_code,
            "request_id": request_id
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求验证异常
    
    Args:
        request: FastAPI请求对象
        exc: 验证异常
        
    Returns:
        JSON响应
    """
    # 生成请求ID用于追踪
    request_id = str(uuid.uuid4())
    
    # 提取验证错误信息
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    # 记录错误日志
    logger.warning(
        f"ValidationError: {len(errors)} validation errors",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "errors": errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": "请求参数验证失败",
            "code": "VALIDATION_ERROR",
            "request_id": request_id,
            "details": {"errors": errors}
        }
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    处理数据库异常
    
    Args:
        request: FastAPI请求对象
        exc: SQLAlchemy异常
        
    Returns:
        JSON响应
    """
    # 生成请求ID用于追踪
    request_id = str(uuid.uuid4())
    
    # 记录详细错误日志
    orig_detail = getattr(exc, 'orig', None)
    orig_str = f' | orig={repr(orig_detail)}' if orig_detail else ''
    # 使用 exc.__traceback__ 手动获取完整 traceback
    tb_list = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tb_str = ''.join(tb_list)
    # 同时输出到 stderr 确保 Docker 日志捕获
    import sys
    sys.stderr.write(f"[DB ERROR] {type(exc).__name__}{orig_str}\n{tb_str}\n")
    sys.stderr.flush()
    logger.error(
        f"DatabaseError: {type(exc).__name__}{orig_str}\n{tb_str}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "error": repr(exc),
            "traceback": tb_str
        }
    )
    
    # 处理特定的数据库错误
    if isinstance(exc, IntegrityError):
        # 唯一约束冲突
        error_message = "数据已存在或违反唯一性约束"
        error_code = "INTEGRITY_ERROR"
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, NoResultFound):
        # 记录不存在
        error_message = "请求的资源不存在"
        error_code = "NOT_FOUND"
        status_code = status.HTTP_404_NOT_FOUND
    else:
        # 其他数据库错误
        error_message = "数据库操作失败,请稍后重试"
        error_code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error_message,
            "code": error_code,
            "request_id": request_id
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的通用异常
    
    Args:
        request: FastAPI请求对象
        exc: 异常
        
    Returns:
        JSON响应
    """
    # 生成请求ID用于追踪
    request_id = str(uuid.uuid4())
    
    # 记录详细错误日志
    logger.error(
        f"UnhandledException: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "url": str(request.url),
            "method": request.method,
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "服务器内部错误,请稍后重试",
            "code": "INTERNAL_ERROR",
            "request_id": request_id
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    # 自定义应用异常
    app.add_exception_handler(AppException, app_exception_handler)
    
    # HTTP异常
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 请求验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 数据库异常
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # 通用异常(最后的兜底)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✅ 异常处理器注册完成")
