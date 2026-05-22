"""
缓存失效策略工具
Cache Invalidation Strategy Utility

实现统一的缓存失效管理,确保数据一致性
"""
from typing import List, Optional, Set
from app.core.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)


class CacheInvalidationStrategy:
    """
    缓存失效策略类
    
    职责:
    1. 统一管理所有缓存键的失效逻辑
    2. 在写操作时主动清除相关缓存
    3. 支持批量清除和模式匹配清除
    4. 提供缓存预热功能
    """
    
    # 缓存键模式定义
    CACHE_PATTERNS = {
        "contract_list": "contract:list:*",
        "contract_detail": "contract:detail:{contract_id}",
        "contract_pending": "contract:pending:{user_id}",
        "reviews": "reviews:v2:{contract_id}",
        "ai_summary": "ai:summary:{contract_id}",
        "user_session": "user:session:{token}",
    }
    
    @staticmethod
    async def invalidate_contract_created(contract_id: str, initiator_id: str, reviewer_ids: List[str]):
        """
        合同创建时的缓存失效
        
        影响范围:
        - 所有用户的合同列表缓存
        - 所有评审人的待办数量缓存
        
        Args:
            contract_id: 合同ID
            initiator_id: 发起人ID
            reviewer_ids: 评审人ID列表
        """
        try:
            # 1. 清除所有合同列表缓存
            await redis_client.delete_pattern("contract:list:*")
            logger.info(f"Cleared contract list cache for contract creation: {contract_id}")
            
            # 2. 清除所有评审人的待办数量缓存
            pending_keys = [f"contract:pending:{reviewer_id}" for reviewer_id in reviewer_ids]
            if pending_keys:
                await redis_client.delete_many(pending_keys)
                logger.info(f"Cleared pending count cache for {len(reviewer_ids)} reviewers")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for contract creation: {e}")
    
    @staticmethod
    async def invalidate_contract_updated(contract_id: str, affected_user_ids: Optional[List[str]] = None):
        """
        合同更新时的缓存失效
        
        影响范围:
        - 所有用户的合同列表缓存
        - 合同详情缓存
        - 相关用户的待办数量缓存
        
        Args:
            contract_id: 合同ID
            affected_user_ids: 受影响的用户ID列表(可选)
        """
        try:
            # 1. 清除所有合同列表缓存
            await redis_client.delete_pattern("contract:list:*")
            
            # 2. 清除合同详情缓存
            detail_key = f"contract:detail:{contract_id}"
            await redis_client.delete(detail_key)
            
            # 3. 清除相关用户的待办数量缓存
            if affected_user_ids:
                pending_keys = [f"contract:pending:{user_id}" for user_id in affected_user_ids]
                await redis_client.delete_many(pending_keys)
            
            logger.info(f"Cleared cache for contract update: {contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for contract update: {e}")
    
    @staticmethod
    async def invalidate_review_approved(contract_id: str, reviewer_id: str, all_reviewer_ids: Optional[List[str]] = None):
        """
        评审通过时的缓存失效
        
        影响范围:
        - 所有用户的合同列表缓存(状态可能变化)
        - 评审记录缓存
        - 评审人的待办数量缓存
        - AI总结缓存(需要重新生成)
        
        Args:
            contract_id: 合同ID
            reviewer_id: 评审人ID
            all_reviewer_ids: 所有评审人ID列表(用于批量清除待办缓存)
        """
        try:
            # 1. 清除所有合同列表缓存
            await redis_client.delete_pattern("contract:list:*")
            
            # 2. 清除评审记录缓存 (与 review_service.get_contract_reviews 同步使用 v2 键)
            reviews_key = f"reviews:v2:{contract_id}"
            await redis_client.delete(reviews_key)
            
            # 3. 清除评审人的待办数量缓存
            pending_key = f"contract:pending:{reviewer_id}"
            await redis_client.delete(pending_key)
            
            # 4. 清除AI总结缓存(需要重新生成)
            ai_summary_key = f"ai:summary:{contract_id}"
            await redis_client.delete(ai_summary_key)
            
            # 5. 如果提供了所有评审人ID,批量清除待办缓存
            if all_reviewer_ids:
                pending_keys = [f"contract:pending:{uid}" for uid in all_reviewer_ids]
                await redis_client.delete_many(pending_keys)
            
            logger.info(f"Cleared cache for review approval: contract={contract_id}, reviewer={reviewer_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for review approval: {e}")
    
    @staticmethod
    async def invalidate_comment_added(contract_id: str):
        """
        评论添加时的缓存失效
        
        影响范围:
        - 评审记录缓存(包含评论数据)
        - AI总结缓存(关键问题的解决方案可能更新)
        
        Args:
            contract_id: 合同ID
        """
        try:
            # 1. 清除评审记录缓存 (v2: 含顶层游离评论)
            reviews_key = f"reviews:v2:{contract_id}"
            await redis_client.delete(reviews_key)
            
            # 2. 清除AI总结缓存
            ai_summary_key = f"ai:summary:{contract_id}"
            await redis_client.delete(ai_summary_key)
            
            logger.info(f"Cleared cache for comment addition: {contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for comment addition: {e}")
    
    @staticmethod
    async def invalidate_like_updated(contract_id: str):
        """
        点赞更新时的缓存失效
        
        影响范围:
        - 评审记录缓存(包含点赞数据)
        
        Args:
            contract_id: 合同ID
        """
        try:
            # 清除评审记录缓存 (v2)
            reviews_key = f"reviews:v2:{contract_id}"
            await redis_client.delete(reviews_key)
            
            logger.info(f"Cleared cache for like update: {contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for like update: {e}")
    
    @staticmethod
    async def invalidate_attachment_uploaded(contract_id: str):
        """
        附件上传时的缓存失效
        
        影响范围:
        - 合同详情缓存(包含附件列表)
        
        Args:
            contract_id: 合同ID
        """
        try:
            # 清除合同详情缓存
            detail_key = f"contract:detail:{contract_id}"
            await redis_client.delete(detail_key)
            
            logger.info(f"Cleared cache for attachment upload: {contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for attachment upload: {e}")
    
    @staticmethod
    async def invalidate_user_session(token: str):
        """
        用户会话失效
        
        Args:
            token: 会话token
        """
        try:
            session_key = f"user:session:{token}"
            await redis_client.delete(session_key)
            
            logger.info(f"Cleared user session cache")
            
        except Exception as e:
            logger.error(f"Failed to invalidate user session: {e}")
    
    @staticmethod
    async def invalidate_all_user_caches(user_id: str):
        """
        清除用户相关的所有缓存
        
        使用场景:
        - 用户登出
        - 用户权限变更
        
        Args:
            user_id: 用户ID
        """
        try:
            # 1. 清除用户的合同列表缓存
            await redis_client.delete_pattern(f"contract:list:{user_id}:*")
            
            # 2. 清除用户的待办数量缓存
            pending_key = f"contract:pending:{user_id}"
            await redis_client.delete(pending_key)
            
            logger.info(f"Cleared all caches for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to invalidate all user caches: {e}")
    
    @staticmethod
    async def warm_up_cache_for_user(user_id: str, db):
        """
        为用户预热缓存
        
        使用场景:
        - 用户登录后
        - 系统启动后
        
        Args:
            user_id: 用户ID
            db: 数据库会话
        """
        try:
            from app.services.contract_service import ContractService
            
            contract_service = ContractService()
            
            # 预热常用的筛选条件
            filters = ["all", "进行中", "待我处理"]
            
            for filter_type in filters:
                # 触发查询,自动缓存结果
                await contract_service.get_contract_list(
                    user_id=user_id,
                    filter_type=filter_type,
                    page=1,
                    limit=20,
                    db=db
                )
            
            # 预热待办数量
            await contract_service.get_pending_count(user_id, db)
            
            logger.info(f"Warmed up cache for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to warm up cache for user: {e}")
    
    @staticmethod
    async def warm_up_cache_for_contract(contract_id: str, db):
        """
        为合同预热缓存
        
        使用场景:
        - 合同创建后
        - 合同被频繁访问时
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
        """
        try:
            from app.services.contract_service import ContractService
            from app.services.review_service import ReviewService
            from app.services.ai_service import AIService
            
            contract_service = ContractService()
            review_service = ReviewService()
            ai_service = AIService()
            
            # 预热合同详情
            await contract_service.get_contract_detail(contract_id, db)
            
            # 预热评审记录
            await review_service.get_contract_reviews(contract_id, db)
            
            # 预热AI总结
            await ai_service.generate_summary(contract_id, db)
            
            logger.info(f"Warmed up cache for contract: {contract_id}")
            
        except Exception as e:
            logger.error(f"Failed to warm up cache for contract: {e}")
    
    @staticmethod
    async def clear_all_caches():
        """
        清除所有缓存
        
        使用场景:
        - 系统维护
        - 数据迁移后
        - 紧急情况
        
        警告: 此操作会清除所有缓存,可能导致短期性能下降
        """
        try:
            patterns = [
                "contract:list:*",
                "contract:detail:*",
                "contract:pending:*",
                "reviews:*",
                "ai:summary:*",
            ]
            
            for pattern in patterns:
                deleted = await redis_client.delete_pattern(pattern)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
            
            logger.warning("Cleared all application caches")
            
        except Exception as e:
            logger.error(f"Failed to clear all caches: {e}")
    
    @staticmethod
    async def get_cache_stats() -> dict:
        """
        获取缓存统计信息
        
        Returns:
            包含各类缓存数量的字典
        """
        try:
            stats = {}
            
            patterns = {
                "contract_list": "contract:list:*",
                "contract_detail": "contract:detail:*",
                "contract_pending": "contract:pending:*",
                "reviews": "reviews:*",
                "ai_summary": "ai:summary:*",
            }
            
            for name, pattern in patterns.items():
                count = 0
                async for _ in redis_client.redis.scan_iter(match=pattern, count=100):
                    count += 1
                stats[name] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# 创建全局实例
cache_invalidation = CacheInvalidationStrategy()
