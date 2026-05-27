"""
JWT认证中间件
从请求头中提取和验证JWT Token,将当前用户信息注入到请求上下文
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Optional
from app.services.dingtalk_auth_service import DingTalkAuthService


security = HTTPBearer()


class AuthMiddleware:
    """JWT认证中间件"""
    
    def __init__(self):
        self.auth_service = DingTalkAuthService()
    
    async def __call__(self, request: Request, call_next):
        """
        中间件处理函数
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            响应对象
        """
        # 跳过不需要认证的路径
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # 从请求头中提取Token
        token = self._extract_token(request)
        
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "error": "未提供认证Token", "code": "UNAUTHORIZED"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 验证Token
        payload = self.auth_service.verify_jwt_token(token)
        
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "error": "Token无效或已过期", "code": "UNAUTHORIZED"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 将用户信息注入到请求状态中
        request.state.user = payload
        
        response = await call_next(request)
        return response
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        从请求头中提取Token
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Token字符串,如果不存在返回None
        """
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return None
        
        # 支持 "Bearer <token>" 格式
        parts = authorization.split()
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    def _is_public_path(self, path: str) -> bool:
        """
        判断路径是否为公开路径(不需要认证)
        
        Args:
            path: 请求路径
            
        Returns:
            是否为公开路径
        """
        public_paths = [
            "/api/auth/dingtalk/login",
            "/api/auth/dingtalk/callback",
            "/api/auth/login",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            # Socket.IO 走自己的 auth 协议（前端 io(...) 的 auth: { token } 字段，
            # 由 socketio_server.py 的 connect handler 在 verify_token 中校验）。
            # HTTP Authorization header 在 WebSocket 握手时浏览器原生不支持自定义 header，
            # 故必须放行此路径让 socket.io 内部协议处理鉴权，否则所有 WS 连接 401。
            "/socket.io/",
            "/socket.io",
        ]
        
        for public_path in public_paths:
            if path.startswith(public_path):
                return True
        
        return False


def get_current_user(request: Request) -> dict:
    """
    从请求上下文中获取当前用户信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        当前用户信息字典
        
    Raises:
        HTTPException: 如果用户未认证
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未认证"
        )
    
    return request.state.user
