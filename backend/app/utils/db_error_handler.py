"""
数据库错误处理工具
Database error handling utilities
"""
import logging
from typing import Optional
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

# 尝试导入 psycopg2 错误类型(可选)
try:
    from psycopg2.errors import UniqueViolation, ForeignKeyViolation, NotNullViolation
    PSYCOPG2_AVAILABLE = True
except ImportError:
    # 如果 psycopg2 不可用,定义占位符类型
    UniqueViolation = type('UniqueViolation', (Exception,), {})
    ForeignKeyViolation = type('ForeignKeyViolation', (Exception,), {})
    NotNullViolation = type('NotNullViolation', (Exception,), {})
    PSYCOPG2_AVAILABLE = False

from app.core.exceptions import (
    DatabaseError,
    NotFoundError,
    ConflictError,
    ValidationError
)

logger = logging.getLogger(__name__)


def handle_db_error(error: Exception, operation: str = "数据库操作") -> None:
    """
    处理数据库错误并抛出适当的自定义异常
    
    Args:
        error: 原始数据库异常
        operation: 操作描述(用于日志)
        
    Raises:
        NotFoundError: 记录不存在
        ConflictError: 唯一约束冲突
        ValidationError: 非空约束违反
        DatabaseError: 其他数据库错误
    """
    logger.error(f"{operation}失败: {type(error).__name__} - {str(error)}")
    
    # 处理 SQLAlchemy 异常
    if isinstance(error, NoResultFound):
        raise NotFoundError(f"{operation}失败: 记录不存在")
    
    if isinstance(error, IntegrityError):
        # 获取原始的 psycopg2 错误
        orig_error = getattr(error, 'orig', None)
        
        if orig_error:
            # 唯一约束冲突
            if isinstance(orig_error, UniqueViolation):
                # 尝试提取字段名
                error_msg = str(orig_error)
                if "dingtalk_user_id" in error_msg:
                    raise ConflictError("该钉钉用户已存在")
                elif "name" in error_msg:
                    raise ConflictError("名称已存在")
                else:
                    raise ConflictError(f"{operation}失败: 数据已存在")
            
            # 外键约束违反
            if isinstance(orig_error, ForeignKeyViolation):
                raise ValidationError(f"{operation}失败: 关联的记录不存在")
            
            # 非空约束违反
            if isinstance(orig_error, NotNullViolation):
                # 尝试提取字段名
                error_msg = str(orig_error)
                field = None
                if "column" in error_msg:
                    # 从错误消息中提取字段名
                    parts = error_msg.split('"')
                    if len(parts) >= 2:
                        field = parts[1]
                raise ValidationError(
                    f"{operation}失败: 必填字段不能为空",
                    field=field
                )
        
        # 其他完整性错误
        raise ConflictError(f"{operation}失败: 数据完整性约束违反")
    
    # 其他 SQLAlchemy 错误
    if isinstance(error, SQLAlchemyError):
        raise DatabaseError(f"{operation}失败", original_error=error)
    
    # 未知错误
    raise DatabaseError(f"{operation}失败: 未知错误", original_error=error)


async def safe_db_operation(operation_func, operation_name: str = "数据库操作"):
    """
    安全执行数据库操作的装饰器函数
    
    Args:
        operation_func: 要执行的数据库操作函数
        operation_name: 操作名称(用于日志)
        
    Returns:
        操作结果
        
    Raises:
        自定义异常
    """
    try:
        return await operation_func()
    except (NotFoundError, ConflictError, ValidationError, DatabaseError):
        # 已经是自定义异常,直接抛出
        raise
    except Exception as e:
        # 处理其他异常
        handle_db_error(e, operation_name)
