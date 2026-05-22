"""
Redis 客户端配置
Redis client configuration

性能优化:
1. 连接池管理 - 复用连接减少开销
2. 批量操作 - 使用pipeline减少网络往返
3. 缓存预热 - 提前加载热点数据
4. 智能过期 - 根据数据类型设置不同TTL
"""

import json
from typing import Any, Optional, List, Dict
import redis.asyncio as redis
from functools import wraps
import hashlib

from app.core.config import settings


class RedisClient:
    """Redis 客户端封装类 - 性能优化版"""
    
    # 缓存TTL配置(秒)
    TTL_SHORT = 60  # 1分钟 - 用于频繁变化的数据(待办数量)
    TTL_MEDIUM = 300  # 5分钟 - 用于中等频率变化的数据(合同列表)
    TTL_LONG = 1800  # 30分钟 - 用于较少变化的数据(AI总结)
    TTL_VERY_LONG = 3600  # 1小时 - 用于很少变化的数据(用户信息)
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """连接到 Redis - 使用连接池"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,  # 连接池大小
            socket_keepalive=True,  # 保持连接活跃
            socket_connect_timeout=5,  # 连接超时
            retry_on_timeout=True,  # 超时重试
        )
    
    async def disconnect(self) -> None:
        """断开 Redis 连接"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ex: 过期时间(秒),None则使用默认TTL
        """
        if not self.redis:
            return False
        
        if ex is None:
            ex = settings.REDIS_CACHE_TTL
        
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            await self.redis.set(key, serialized_value, ex=ex)
            return True
        except Exception as e:
            print(f"Redis set error for key {key}: {e}")
            return False
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """
        批量获取缓存值
        
        Args:
            keys: 缓存键列表
            
        Returns:
            值列表,顺序与keys对应
        """
        if not self.redis or not keys:
            return [None] * len(keys)
        
        try:
            values = await self.redis.mget(keys)
            result = []
            for value in values:
                if value:
                    try:
                        result.append(json.loads(value))
                    except json.JSONDecodeError:
                        result.append(value)
                else:
                    result.append(None)
            return result
        except Exception as e:
            print(f"Redis mget error: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """
        批量设置缓存值
        
        Args:
            mapping: 键值对字典
            ex: 过期时间(秒)
            
        Returns:
            是否成功
        """
        if not self.redis or not mapping:
            return False
        
        if ex is None:
            ex = settings.REDIS_CACHE_TTL
        
        try:
            # 使用pipeline批量操作
            async with self.redis.pipeline(transaction=True) as pipe:
                for key, value in mapping.items():
                    serialized_value = json.dumps(value) if not isinstance(value, str) else value
                    pipe.set(key, serialized_value, ex=ex)
                await pipe.execute()
            return True
        except Exception as e:
            print(f"Redis mset error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error for key {key}: {e}")
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """
        批量删除缓存
        
        Args:
            keys: 缓存键列表
            
        Returns:
            删除的键数量
        """
        if not self.redis or not keys:
            return 0
        
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            print(f"Redis delete_many error: {e}")
            return 0
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有键
        
        Args:
            pattern: 匹配模式(如 "contract:list:*")
            
        Returns:
            删除的键数量
        """
        if not self.redis:
            return 0
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                # 批量删除,每次最多1000个
                deleted = 0
                for i in range(0, len(keys), 1000):
                    batch = keys[i:i+1000]
                    deleted += await self.redis.delete(*batch)
                return deleted
            return 0
        except Exception as e:
            print(f"Redis delete pattern error for pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        if not self.redis:
            return False
        
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            print(f"Redis expire error for key {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        原子递增
        
        Args:
            key: 缓存键
            amount: 递增量
            
        Returns:
            递增后的值
        """
        if not self.redis:
            return None
        
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            print(f"Redis incr error for key {key}: {e}")
            return None
    
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        原子递减
        
        Args:
            key: 缓存键
            amount: 递减量
            
        Returns:
            递减后的值
        """
        if not self.redis:
            return None
        
        try:
            return await self.redis.decrby(key, amount)
        except Exception as e:
            print(f"Redis decr error for key {key}: {e}")
            return None
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键字符串
        """
        # 将参数转换为字符串并排序
        parts = [prefix]
        parts.extend(str(arg) for arg in args)
        
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
        
        # 如果键太长,使用hash
        key = ":".join(parts)
        if len(key) > 200:
            hash_suffix = hashlib.md5(key.encode()).hexdigest()[:8]
            key = f"{prefix}:hash:{hash_suffix}"
        
        return key


# 创建全局 Redis 客户端实例
redis_client = RedisClient()


def cache_result(ttl: int = None, key_prefix: str = "cache"):
    """
    缓存装饰器 - 自动缓存函数结果
    
    Args:
        ttl: 缓存过期时间(秒)
        key_prefix: 缓存键前缀
        
    Usage:
        @cache_result(ttl=300, key_prefix="user")
        async def get_user(user_id: str):
            return await db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = redis_client.generate_cache_key(key_prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                await redis_client.set(cache_key, result, ex=ttl)
            
            return result
        
        return wrapper
    return decorator


# 创建全局 Redis 客户端实例
redis_client = RedisClient()
