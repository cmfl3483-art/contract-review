"""
外部服务错误处理工具
External service error handling utilities
"""
import logging
import asyncio
from typing import Optional, Callable, Any, TypeVar
from functools import wraps

from app.core.exceptions import (
    AIServiceError,
    MinIOServiceError,
    ExternalServiceError,
    ServiceUnavailableError
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def handle_ai_service_call(
    operation_func: Callable,
    operation_name: str = "AI服务调用",
    timeout: float = 30.0,
    fallback_value: Optional[Any] = None,
    raise_on_error: bool = False
) -> Optional[Any]:
    """
    处理AI服务调用,包含超时和错误处理
    
    Args:
        operation_func: AI服务调用函数
        operation_name: 操作名称(用于日志)
        timeout: 超时时间(秒)
        fallback_value: 失败时的降级返回值
        raise_on_error: 是否在错误时抛出异常(False则返回fallback_value)
        
    Returns:
        操作结果或降级值
        
    Raises:
        AIServiceError: 如果raise_on_error=True且发生错误
    """
    try:
        # 设置超时
        result = await asyncio.wait_for(
            operation_func(),
            timeout=timeout
        )
        return result
        
    except asyncio.TimeoutError:
        logger.warning(f"{operation_name}超时 (timeout={timeout}s)")
        if raise_on_error:
            raise AIServiceError(f"{operation_name}超时,请稍后重试")
        return fallback_value
        
    except Exception as e:
        # 检查是否是限流错误
        if hasattr(e, 'status_code') and e.status_code == 429:
            logger.warning(f"{operation_name}被限流: {str(e)}")
            if raise_on_error:
                raise AIServiceError(f"{operation_name}请求过于频繁,请稍后重试")
            return fallback_value
        
        # 检查是否是认证错误
        if hasattr(e, 'status_code') and e.status_code == 401:
            logger.error(f"{operation_name}认证失败: {str(e)}")
            if raise_on_error:
                raise AIServiceError(f"{operation_name}认证失败,请检查配置")
            return fallback_value
        
        # 其他错误
        logger.error(f"{operation_name}失败: {type(e).__name__} - {str(e)}")
        if raise_on_error:
            raise AIServiceError(f"{operation_name}失败: {str(e)}")
        return fallback_value


async def handle_minio_operation(
    operation_func: Callable,
    operation_name: str = "MinIO操作",
    raise_on_error: bool = True
) -> Optional[Any]:
    """
    处理MinIO操作,包含错误处理
    
    Args:
        operation_func: MinIO操作函数
        operation_name: 操作名称(用于日志)
        raise_on_error: 是否在错误时抛出异常
        
    Returns:
        操作结果
        
    Raises:
        MinIOServiceError: 如果raise_on_error=True且发生错误
    """
    try:
        result = await operation_func()
        return result
        
    except Exception as e:
        logger.error(f"{operation_name}失败: {type(e).__name__} - {str(e)}")
        
        # 检查是否是连接错误
        if "Connection" in str(e) or "timeout" in str(e).lower():
            if raise_on_error:
                raise MinIOServiceError(f"{operation_name}失败: 文件存储服务连接超时")
            return None
        
        # 检查是否是认证错误
        if "Access Denied" in str(e) or "InvalidAccessKeyId" in str(e):
            if raise_on_error:
                raise MinIOServiceError(f"{operation_name}失败: 文件存储服务认证失败")
            return None
        
        # 检查是否是空间不足
        if "No space" in str(e) or "quota" in str(e).lower():
            if raise_on_error:
                raise MinIOServiceError(f"{operation_name}失败: 存储空间不足")
            return None
        
        # 其他错误
        if raise_on_error:
            raise MinIOServiceError(f"{operation_name}失败: {str(e)}")
        return None


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器,用于外部服务调用
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟时间的倍增因子
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"函数 {func.__name__} 执行失败 (尝试 {attempt + 1}/{max_retries + 1}), "
                            f"{current_delay}秒后重试: {str(e)}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"函数 {func.__name__} 执行失败,已达到最大重试次数 ({max_retries}): {str(e)}"
                        )
            
            # 所有重试都失败,抛出最后一个异常
            raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    熔断器,用于保护外部服务调用
    当失败率超过阈值时,暂时停止调用外部服务
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败次数阈值
            recovery_timeout: 恢复超时时间(秒)
            expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数
        
        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
            
        Raises:
            ServiceUnavailableError: 熔断器打开时
            原始异常: 函数执行失败时
        """
        # 检查熔断器状态
        if self.state == "OPEN":
            # 检查是否可以尝试恢复
            if self.last_failure_time:
                import time
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info("熔断器进入半开状态,尝试恢复")
                    self.state = "HALF_OPEN"
                else:
                    raise ServiceUnavailableError(
                        f"服务暂时不可用,请 {int(self.recovery_timeout - elapsed)} 秒后重试"
                    )
        
        try:
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 成功,重置失败计数
            if self.state == "HALF_OPEN":
                logger.info("熔断器恢复正常,关闭熔断器")
                self.state = "CLOSED"
            self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            # 失败,增加失败计数
            self.failure_count += 1
            
            if self.failure_count >= self.failure_threshold:
                import time
                self.state = "OPEN"
                self.last_failure_time = time.time()
                logger.error(
                    f"熔断器打开,失败次数: {self.failure_count}, "
                    f"将在 {self.recovery_timeout} 秒后尝试恢复"
                )
            
            raise e
