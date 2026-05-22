"""
Socket.IO 服务器配置
Socket.IO Server Configuration

提供实时通信功能,支持以下事件:
- contract:updated - 合同信息更新
- review:added - 新增评审意见
- comment:added - 新增评论
- reply:added - 新增回复
- like:updated - 点赞更新
- pending:changed - 待办数量变化
"""

import socketio
from typing import Optional, Dict, Any
import logging
from jose import jwt, JWTError

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建 Socket.IO 服务器实例
# async_mode='asgi' 用于与 FastAPI 集成
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,  # 使用与 FastAPI 相同的 CORS 配置
    logger=True,
    engineio_logger=True,
)

# 创建 ASGI 应用
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='socket.io'
)

# 存储用户会话信息
# key: session_id (sid), value: user_id
user_sessions: Dict[str, str] = {}


async def verify_token(token: str) -> Optional[str]:
    """
    验证 JWT Token 并返回用户 ID
    
    Args:
        token: JWT Token
        
    Returns:
        用户 ID,如果验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError as e:
        logger.warning(f"Token 验证失败: {e}")
        return None


@sio.event
async def connect(sid: str, environ: dict, auth: Optional[dict] = None):
    """
    客户端连接事件处理
    
    Args:
        sid: Session ID
        environ: WSGI 环境变量
        auth: 认证信息 (包含 token)
    """
    logger.info(f"客户端尝试连接: sid={sid}")
    
    # 验证认证信息
    if not auth or 'token' not in auth:
        logger.warning(f"连接被拒绝 (缺少 token): sid={sid}")
        return False
    
    token = auth['token']
    user_id = await verify_token(token)
    
    if not user_id:
        logger.warning(f"连接被拒绝 (token 无效): sid={sid}")
        return False
    
    # 保存用户会话信息
    user_sessions[sid] = user_id
    
    # 将用户加入到个人房间 (用于发送个人通知)
    await sio.enter_room(sid, f"user:{user_id}")
    
    logger.info(f"客户端连接成功: sid={sid}, user_id={user_id}")
    
    # 发送连接成功消息
    await sio.emit('connected', {
        'message': '连接成功',
        'user_id': user_id
    }, room=sid)
    
    return True


@sio.event
async def disconnect(sid: str):
    """
    客户端断开连接事件处理
    
    Args:
        sid: Session ID
    """
    user_id = user_sessions.get(sid)
    
    if user_id:
        # 离开个人房间
        await sio.leave_room(sid, f"user:{user_id}")
        
        # 清除会话信息
        del user_sessions[sid]
        
        logger.info(f"客户端断开连接: sid={sid}, user_id={user_id}")
    else:
        logger.info(f"客户端断开连接: sid={sid}")


@sio.event
async def join_contract(sid: str, data: dict):
    """
    加入合同房间 (用于接收特定合同的实时更新)
    
    Args:
        sid: Session ID
        data: 包含 contract_id 的字典
    """
    contract_id = data.get('contract_id')
    
    if not contract_id:
        logger.warning(f"加入合同房间失败 (缺少 contract_id): sid={sid}")
        return
    
    user_id = user_sessions.get(sid)
    
    if not user_id:
        logger.warning(f"加入合同房间失败 (未认证): sid={sid}")
        return
    
    # 加入合同房间
    await sio.enter_room(sid, f"contract:{contract_id}")
    
    logger.info(f"用户加入合同房间: sid={sid}, user_id={user_id}, contract_id={contract_id}")
    
    # 发送确认消息
    await sio.emit('joined_contract', {
        'contract_id': contract_id
    }, room=sid)


@sio.event
async def leave_contract(sid: str, data: dict):
    """
    离开合同房间
    
    Args:
        sid: Session ID
        data: 包含 contract_id 的字典
    """
    contract_id = data.get('contract_id')
    
    if not contract_id:
        logger.warning(f"离开合同房间失败 (缺少 contract_id): sid={sid}")
        return
    
    user_id = user_sessions.get(sid)
    
    if not user_id:
        logger.warning(f"离开合同房间失败 (未认证): sid={sid}")
        return
    
    # 离开合同房间
    await sio.leave_room(sid, f"contract:{contract_id}")
    
    logger.info(f"用户离开合同房间: sid={sid}, user_id={user_id}, contract_id={contract_id}")
    
    # 发送确认消息
    await sio.emit('left_contract', {
        'contract_id': contract_id
    }, room=sid)


# 辅助函数:发送实时通知

async def emit_contract_updated(contract_id: str, data: Dict[str, Any]):
    """
    发送合同更新通知
    
    Args:
        contract_id: 合同 ID
        data: 更新数据
    """
    await sio.emit('contract:updated', data, room=f"contract:{contract_id}")
    logger.info(f"发送合同更新通知: contract_id={contract_id}")


async def emit_review_added(contract_id: str, data: Dict[str, Any]):
    """
    发送评审添加通知
    
    Args:
        contract_id: 合同 ID
        data: 评审数据
    """
    await sio.emit('review:added', data, room=f"contract:{contract_id}")
    logger.info(f"发送评审添加通知: contract_id={contract_id}")


async def emit_comment_added(contract_id: str, data: Dict[str, Any]):
    """
    发送评论添加通知
    
    Args:
        contract_id: 合同 ID
        data: 评论数据
    """
    await sio.emit('comment:added', data, room=f"contract:{contract_id}")
    logger.info(f"发送评论添加通知: contract_id={contract_id}")


async def emit_reply_added(contract_id: str, data: Dict[str, Any]):
    """
    发送回复添加通知
    
    Args:
        contract_id: 合同 ID
        data: 回复数据
    """
    await sio.emit('reply:added', data, room=f"contract:{contract_id}")
    logger.info(f"发送回复添加通知: contract_id={contract_id}")


async def emit_like_updated(contract_id: str, data: Dict[str, Any]):
    """
    发送点赞更新通知
    
    Args:
        contract_id: 合同 ID
        data: 点赞数据
    """
    await sio.emit('like:updated', data, room=f"contract:{contract_id}")
    logger.info(f"发送点赞更新通知: contract_id={contract_id}")


async def emit_pending_changed(user_id: str, data: Dict[str, Any]):
    """
    发送待办数量变化通知 (发送给特定用户)
    
    Args:
        user_id: 用户 ID
        data: 待办数据
    """
    await sio.emit('pending:changed', data, room=f"user:{user_id}")
    logger.info(f"发送待办变化通知: user_id={user_id}")


async def emit_to_user(user_id: str, event: str, data: Dict[str, Any]):
    """
    发送通知给特定用户
    
    Args:
        user_id: 用户 ID
        event: 事件名称
        data: 数据
    """
    await sio.emit(event, data, room=f"user:{user_id}")
    logger.info(f"发送通知给用户: user_id={user_id}, event={event}")
