"""
钉钉OAuth认证服务
实现钉钉授权登录、用户信息同步和JWT Token管理
"""
import os
import httpx
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.config import settings


class DingTalkAuthService:
    """钉钉授权认证服务"""
    
    def __init__(self):
        self.app_key = settings.DINGTALK_APP_KEY
        self.app_secret = settings.DINGTALK_APP_SECRET
        self.redirect_uri = settings.DINGTALK_REDIRECT_URI
        self.jwt_secret = settings.SECRET_KEY
        self.jwt_algorithm = settings.ALGORITHM
        self.jwt_expire_hours = settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60
        
    def get_authorization_url(self, state: str = "default") -> str:
        """
        生成钉钉授权登录URL
        
        Args:
            state: 状态参数,用于防止CSRF攻击
            
        Returns:
            钉钉授权页面URL
        """
        auth_url = (
            f"https://login.dingtalk.com/oauth2/auth"
            f"?client_id={self.app_key}"
            f"&response_type=code"
            f"&scope=openid"
            f"&state={state}"
            f"&redirect_uri={self.redirect_uri}"
            f"&prompt=consent"
        )
        return auth_url
    
    async def get_access_token(self, auth_code: str) -> Dict[str, Any]:
        """
        使用授权码获取访问令牌
        
        Args:
            auth_code: 钉钉授权码
            
        Returns:
            包含access_token的字典
            
        Raises:
            Exception: 获取token失败
        """
        url = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
        
        payload = {
            "clientId": self.app_key,
            "clientSecret": self.app_secret,
            "code": auth_code,
            "grantType": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"获取access token失败: {response.text}")
            
            data = response.json()
            return data
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        使用访问令牌获取用户信息
        
        Args:
            access_token: 钉钉访问令牌
            
        Returns:
            用户信息字典
            
        Raises:
            Exception: 获取用户信息失败
        """
        url = "https://api.dingtalk.com/v1.0/contact/users/me"
        
        headers = {
            "x-acs-dingtalk-access-token": access_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"获取用户信息失败: {response.text}")
            
            data = response.json()
            return data
    
    async def sync_user_info(
        self, 
        user_info: Dict[str, Any], 
        db: AsyncSession
    ) -> User:
        """
        同步钉钉用户信息到数据库

        身份匹配优先级 (重要):
        1. 优先按 dingtalk_union_id == unionId 匹配通讯录已 upsert 的记录,
           避免与 dingtalk_contact_service 产生身份分裂 (后者将钉钉 staff
           userid 写入 dingtalk_user_id, 而本服务历史上写入的是 unionId).
        2. 再回退到 dingtalk_user_id == unionId/openId, 兼容旧登录创建的记录.
        3. 最后才新建用户.

        Args:
            user_info: 钉钉用户信息
            db: 数据库会话

        Returns:
            User对象
        """
        union_id = user_info.get("unionId")
        # 兜底标识: 没有 unionId 时退回到 openId, 仅用于新建/回退查找
        fallback_id = union_id or user_info.get("openId")

        user: Optional[User] = None

        # 1) 优先按 union_id 匹配通讯录创建的记录
        if union_id:
            stmt = select(User).where(User.dingtalk_union_id == union_id).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

        # 2) 回退按 dingtalk_user_id 匹配 (历史登录路径写入的是 unionId)
        if user is None and fallback_id:
            stmt = select(User).where(User.dingtalk_user_id == fallback_id).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

        # 准备用户数据 (基础字段, 不覆盖 dingtalk_user_id)
        base_data = {
            "name": user_info.get("nick") or user_info.get("name", "未知用户"),
            "email": user_info.get("email"),
            "mobile": user_info.get("mobile"),
            "avatar": user_info.get("avatarUrl"),
            "department": user_info.get("deptName"),
        }

        if user:
            # 更新现有用户信息: 只覆盖非空字段, 不动 dingtalk_user_id (保持通讯录写入的 staff userid)
            for key, value in base_data.items():
                if value is not None:
                    setattr(user, key, value)
            # 补齐 union_id (老的通讯录记录可能没有, 或登录记录需要确认)
            if union_id and not user.dingtalk_union_id:
                user.dingtalk_union_id = union_id
        else:
            # 3) 新建用户: dingtalk_user_id 暂用 fallback_id, 后续通讯录同步会校正
            user = User(
                dingtalk_user_id=fallback_id,
                dingtalk_union_id=union_id,
                role=user_info.get("role", "业务"),
                **base_data,
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)

        return user
    
    def generate_jwt_token(self, user: User) -> str:
        """
        生成JWT Token
        
        Args:
            user: 用户对象
            
        Returns:
            JWT Token字符串
        """
        payload = {
            "user_id": str(user.id),
            "dingtalk_user_id": user.dingtalk_user_id,
            "name": user.name,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expire_hours),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT Token
        
        Args:
            token: JWT Token字符串
            
        Returns:
            解码后的payload,如果验证失败返回None
        """
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            # Token已过期
            return None
        except jwt.InvalidTokenError:
            # Token无效
            return None
    
    async def handle_callback(
        self, 
        auth_code: str, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        处理钉钉授权回调
        
        Args:
            auth_code: 钉钉授权码
            db: 数据库会话
            
        Returns:
            包含token和用户信息的字典
            
        Raises:
            Exception: 处理回调失败
        """
        # 1. 获取access token
        token_data = await self.get_access_token(auth_code)
        access_token = token_data.get("accessToken")
        
        if not access_token:
            raise Exception("未能获取access token")
        
        # 2. 获取用户信息
        user_info = await self.get_user_info(access_token)
        
        # 3. 同步用户信息到数据库
        user = await self.sync_user_info(user_info, db)
        
        # 4. 生成JWT Token
        jwt_token = self.generate_jwt_token(user)
        
        return {
            "token": jwt_token,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "role": user.role,
                "email": user.email,
                "mobile": user.mobile,
                "avatar": user.avatar,
                "department": user.department
            }
        }
