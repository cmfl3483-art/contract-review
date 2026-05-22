"""
实时通知服务
Real-time Notification Service

提供实时通知推送功能,封装 Socket.IO 事件发送逻辑
"""
from typing import Dict, Any, Optional, List
import logging

from app.core.socketio_server import (
    emit_contract_updated,
    emit_review_added,
    emit_comment_added,
    emit_reply_added,
    emit_like_updated,
    emit_pending_changed,
    emit_to_user
)

logger = logging.getLogger(__name__)


class NotificationService:
    """实时通知服务类"""
    
    async def notify_contract_updated(
        self,
        contract_id: str,
        contract_data: Dict[str, Any]
    ) -> None:
        """
        发送合同更新通知
        
        当合同信息发生变化时调用此方法,通知所有关注该合同的用户
        
        Args:
            contract_id: 合同 ID
            contract_data: 合同数据,包含:
                - id: 合同 ID
                - name: 合同名称
                - status: 合同状态
                - updated_at: 更新时间
                - 其他合同字段
        """
        try:
            await emit_contract_updated(contract_id, {
                "contract_id": contract_id,
                "contract": contract_data
            })
            logger.info(f"合同更新通知已发送: contract_id={contract_id}")
        except Exception as e:
            logger.error(f"发送合同更新通知失败: contract_id={contract_id}, error={e}")
    
    async def notify_review_added(
        self,
        contract_id: str,
        review_data: Dict[str, Any]
    ) -> None:
        """
        发送评审添加通知
        
        当新增评审意见或评审状态变更时调用此方法
        
        Args:
            contract_id: 合同 ID
            review_data: 评审数据,包含:
                - id: 评审 ID
                - contract_id: 合同 ID
                - reviewer_id: 评审人 ID
                - reviewer_name: 评审人姓名
                - role: 评审人角色
                - opinion: 评审意见
                - status: 评审状态
                - created_at: 创建时间
        """
        try:
            await emit_review_added(contract_id, {
                "contract_id": contract_id,
                "review": review_data
            })
            logger.info(f"评审添加通知已发送: contract_id={contract_id}, review_id={review_data.get('id')}")
        except Exception as e:
            logger.error(f"发送评审添加通知失败: contract_id={contract_id}, error={e}")
    
    async def notify_comment_added(
        self,
        contract_id: str,
        comment_data: Dict[str, Any]
    ) -> None:
        """
        发送评论添加通知
        
        当用户添加新评论时调用此方法
        
        Args:
            contract_id: 合同 ID
            comment_data: 评论数据,包含:
                - id: 评论 ID
                - contract_id: 合同 ID
                - review_id: 评审 ID (可选)
                - author_id: 作者 ID
                - author_name: 作者姓名
                - content: 评论内容
                - created_at: 创建时间
        """
        try:
            await emit_comment_added(contract_id, {
                "contract_id": contract_id,
                "comment": comment_data
            })
            logger.info(f"评论添加通知已发送: contract_id={contract_id}, comment_id={comment_data.get('id')}")
        except Exception as e:
            logger.error(f"发送评论添加通知失败: contract_id={contract_id}, error={e}")
    
    async def notify_reply_added(
        self,
        contract_id: str,
        reply_data: Dict[str, Any]
    ) -> None:
        """
        发送回复添加通知
        
        当用户回复评论时调用此方法
        
        Args:
            contract_id: 合同 ID
            reply_data: 回复数据,包含:
                - id: 回复 ID
                - contract_id: 合同 ID
                - parent_comment_id: 父评论 ID
                - author_id: 作者 ID
                - author_name: 作者姓名
                - content: 回复内容
                - created_at: 创建时间
        """
        try:
            await emit_reply_added(contract_id, {
                "contract_id": contract_id,
                "reply": reply_data
            })
            logger.info(f"回复添加通知已发送: contract_id={contract_id}, reply_id={reply_data.get('id')}")
        except Exception as e:
            logger.error(f"发送回复添加通知失败: contract_id={contract_id}, error={e}")
    
    async def notify_like_updated(
        self,
        contract_id: str,
        like_data: Dict[str, Any]
    ) -> None:
        """
        发送点赞更新通知
        
        当用户点赞或取消点赞时调用此方法
        
        Args:
            contract_id: 合同 ID
            like_data: 点赞数据,包含:
                - target_type: 目标类型 ('review' 或 'comment')
                - target_id: 目标 ID (评审 ID 或评论 ID)
                - likes: 点赞数
                - user_id: 操作用户 ID
                - action: 操作类型 ('like' 或 'unlike')
        """
        try:
            await emit_like_updated(contract_id, {
                "contract_id": contract_id,
                "like": like_data
            })
            logger.info(f"点赞更新通知已发送: contract_id={contract_id}, target_id={like_data.get('target_id')}")
        except Exception as e:
            logger.error(f"发送点赞更新通知失败: contract_id={contract_id}, error={e}")
    
    async def notify_pending_changed(
        self,
        user_id: str,
        pending_count: int,
        contract_id: Optional[str] = None
    ) -> None:
        """
        发送待办数量变化通知
        
        当用户的待办数量发生变化时调用此方法
        
        Args:
            user_id: 用户 ID
            pending_count: 待办数量
            contract_id: 合同 ID (可选,用于标识是哪个合同导致的变化)
        """
        try:
            await emit_pending_changed(user_id, {
                "user_id": user_id,
                "pending_count": pending_count,
                "contract_id": contract_id
            })
            logger.info(f"待办变化通知已发送: user_id={user_id}, pending_count={pending_count}")
        except Exception as e:
            logger.error(f"发送待办变化通知失败: user_id={user_id}, error={e}")
    
    async def notify_multiple_users_pending_changed(
        self,
        user_ids: List[str],
        pending_counts: Dict[str, int],
        contract_id: Optional[str] = None
    ) -> None:
        """
        批量发送待办数量变化通知
        
        当一个操作影响多个用户的待办数量时调用此方法
        
        Args:
            user_ids: 用户 ID 列表
            pending_counts: 用户待办数量字典 {user_id: pending_count}
            contract_id: 合同 ID (可选)
        """
        for user_id in user_ids:
            pending_count = pending_counts.get(user_id, 0)
            await self.notify_pending_changed(user_id, pending_count, contract_id)
    
    async def send_custom_notification(
        self,
        user_id: str,
        event: str,
        data: Dict[str, Any]
    ) -> None:
        """
        发送自定义通知给特定用户
        
        用于发送特殊类型的通知
        
        Args:
            user_id: 用户 ID
            event: 事件名称
            data: 通知数据
        """
        try:
            await emit_to_user(user_id, event, data)
            logger.info(f"自定义通知已发送: user_id={user_id}, event={event}")
        except Exception as e:
            logger.error(f"发送自定义通知失败: user_id={user_id}, event={event}, error={e}")


# 创建全局通知服务实例
notification_service = NotificationService()
