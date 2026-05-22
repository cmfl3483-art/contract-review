"""
性能监控工具
Performance monitoring utilities

提供查询性能监控、慢查询日志等功能
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


def monitor_performance(threshold_ms: float = 1000.0):
    """
    性能监控装饰器
    记录函数执行时间,超过阈值时记录警告日志
    
    Args:
        threshold_ms: 阈值(毫秒),超过此时间记录警告
        
    Usage:
        @monitor_performance(threshold_ms=500)
        async def slow_function():
            await asyncio.sleep(1)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation detected: {func.__name__} took {elapsed_ms:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"{func.__name__} took {elapsed_ms:.2f}ms")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation detected: {func.__name__} took {elapsed_ms:.2f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"{func.__name__} took {elapsed_ms:.2f}ms")
        
        # 根据函数类型返回对应的wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def query_timer(query_name: str, threshold_ms: float = 100.0):
    """
    查询计时器上下文管理器
    用于监控数据库查询性能
    
    Args:
        query_name: 查询名称
        threshold_ms: 阈值(毫秒)
        
    Usage:
        async with query_timer("get_contracts", threshold_ms=50):
            result = await db.execute(query)
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > threshold_ms:
            logger.warning(
                f"Slow query detected: {query_name} took {elapsed_ms:.2f}ms "
                f"(threshold: {threshold_ms}ms)"
            )
        else:
            logger.debug(f"Query {query_name} took {elapsed_ms:.2f}ms")


class PerformanceStats:
    """
    性能统计类
    收集和报告性能指标
    """
    
    def __init__(self):
        self.stats = {}
    
    def record(self, operation: str, duration_ms: float):
        """
        记录操作耗时
        
        Args:
            operation: 操作名称
            duration_ms: 耗时(毫秒)
        """
        if operation not in self.stats:
            self.stats[operation] = {
                "count": 0,
                "total_ms": 0,
                "min_ms": float('inf'),
                "max_ms": 0,
                "avg_ms": 0
            }
        
        stat = self.stats[operation]
        stat["count"] += 1
        stat["total_ms"] += duration_ms
        stat["min_ms"] = min(stat["min_ms"], duration_ms)
        stat["max_ms"] = max(stat["max_ms"], duration_ms)
        stat["avg_ms"] = stat["total_ms"] / stat["count"]
    
    def get_stats(self, operation: str = None):
        """
        获取性能统计
        
        Args:
            operation: 操作名称,None则返回所有统计
            
        Returns:
            统计数据字典
        """
        if operation:
            return self.stats.get(operation)
        return self.stats
    
    def reset(self):
        """重置统计数据"""
        self.stats = {}
    
    def report(self):
        """生成性能报告"""
        if not self.stats:
            return "No performance data collected"
        
        lines = ["Performance Report:", "=" * 80]
        for operation, stat in sorted(self.stats.items()):
            lines.append(
                f"{operation:40s} | "
                f"Count: {stat['count']:6d} | "
                f"Avg: {stat['avg_ms']:8.2f}ms | "
                f"Min: {stat['min_ms']:8.2f}ms | "
                f"Max: {stat['max_ms']:8.2f}ms"
            )
        lines.append("=" * 80)
        return "\n".join(lines)


# 全局性能统计实例
perf_stats = PerformanceStats()


def track_performance(operation: str):
    """
    性能跟踪装饰器
    自动记录函数执行时间到全局统计
    
    Args:
        operation: 操作名称
        
    Usage:
        @track_performance("get_contract_list")
        async def get_contract_list():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                perf_stats.record(operation, elapsed_ms)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                perf_stats.record(operation, elapsed_ms)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
