"""
认证中间件单元测试
测试JWT Token验证、用户信息注入和错误处理
"""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from app.core.auth_middleware import AuthMiddleware, get_current_user
from app.services.dingtalk_auth_service import DingTalkAuthService
from app.models.user import User
from datetime import datetime, timedelta
import jwt


@pytest.fixture
def app():
    """创建测试用的FastAPI应用"""
    app = FastAPI()
    
    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}
    
    @app.get("/protected")
    async def protected_endpoint(request: Request):
        user = get_current_user(request)
        return {"message": "protected", "user": user}
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    from starlette.middleware.base import BaseHTTPMiddleware
    app.add_middleware(BaseHTTPMiddleware, dispatch=AuthMiddleware())
    return TestClient(app)


@pytest.fixture
def mock_user():
    """创建模拟用户对象"""
    user = Mock(spec=User)
    user.id = "user-123"
    user.dingtalk_user_id = "dingtalk-456"
    user.name = "测试用户"
    user.role = "法务"
    return user


@pytest.fixture
def valid_token(mock_user):
    """生成有效的JWT Token"""
    from app.core.config import settings
    
    payload = {
        "user_id": str(mock_user.id),
        "dingtalk_user_id": mock_user.dingtalk_user_id,
        "name": mock_user.name,
        "role": mock_user.role,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def expired_token(mock_user):
    """生成过期的JWT Token"""
    from app.core.config import settings
    
    payload = {
        "user_id": str(mock_user.id),
        "dingtalk_user_id": mock_user.dingtalk_user_id,
        "name": mock_user.name,
        "role": mock_user.role,
        "exp": datetime.utcnow() - timedelta(hours=1),  # 1小时前过期
        "iat": datetime.utcnow() - timedelta(hours=25)
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


class TestAuthMiddleware:
    """认证中间件测试类"""
    
    def test_public_path_no_auth_required(self, client):
        """测试公开路径不需要认证"""
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json() == {"message": "public"}
    
    def test_protected_path_without_token(self, client):
        """测试受保护路径没有Token时返回401"""
        response = client.get("/protected")
        assert response.status_code == 401
        assert "未提供认证Token" in response.json()["detail"]
    
    def test_protected_path_with_invalid_token_format(self, client):
        """测试受保护路径使用无效Token格式时返回401"""
        # 测试没有Bearer前缀
        response = client.get("/protected", headers={"Authorization": "invalid-token"})
        assert response.status_code == 401
        
        # 测试错误的Bearer格式
        response = client.get("/protected", headers={"Authorization": "Bearer"})
        assert response.status_code == 401
    
    def test_protected_path_with_valid_token(self, client, valid_token):
        """测试受保护路径使用有效Token时成功访问"""
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "protected"
        assert data["user"]["name"] == "测试用户"
        assert data["user"]["role"] == "法务"
    
    def test_protected_path_with_expired_token(self, client, expired_token):
        """测试受保护路径使用过期Token时返回401"""
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        assert "Token无效或已过期" in response.json()["detail"]
    
    def test_protected_path_with_invalid_token(self, client):
        """测试受保护路径使用无效Token时返回401"""
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401
        assert "Token无效或已过期" in response.json()["detail"]
    
    def test_extract_token_from_header(self):
        """测试从请求头中提取Token"""
        middleware = AuthMiddleware()
        
        # 创建模拟请求
        request = Mock(spec=Request)
        
        # 测试正确的Bearer Token格式
        request.headers.get.return_value = "Bearer test-token-123"
        token = middleware._extract_token(request)
        assert token == "test-token-123"
        
        # 测试没有Authorization头
        request.headers.get.return_value = None
        token = middleware._extract_token(request)
        assert token is None
        
        # 测试错误的格式
        request.headers.get.return_value = "Basic test-token"
        token = middleware._extract_token(request)
        assert token is None
    
    def test_is_public_path(self):
        """测试公开路径判断"""
        middleware = AuthMiddleware()
        
        # 测试公开路径
        assert middleware._is_public_path("/api/auth/dingtalk/login") is True
        assert middleware._is_public_path("/api/auth/dingtalk/callback") is True
        assert middleware._is_public_path("/docs") is True
        assert middleware._is_public_path("/redoc") is True
        assert middleware._is_public_path("/openapi.json") is True
        assert middleware._is_public_path("/health") is True
        
        # 测试受保护路径
        assert middleware._is_public_path("/api/contracts") is False
        assert middleware._is_public_path("/api/reviews") is False
        assert middleware._is_public_path("/api/files") is False


class TestGetCurrentUser:
    """测试get_current_user辅助函数"""
    
    def test_get_current_user_success(self):
        """测试成功获取当前用户"""
        request = Mock(spec=Request)
        request.state.user = {
            "user_id": "user-123",
            "name": "测试用户",
            "role": "法务"
        }
        
        user = get_current_user(request)
        assert user["user_id"] == "user-123"
        assert user["name"] == "测试用户"
        assert user["role"] == "法务"
    
    def test_get_current_user_not_authenticated(self):
        """测试未认证时抛出异常"""
        request = Mock(spec=Request)
        # 没有设置request.state.user
        
        with pytest.raises(Exception) as exc_info:
            get_current_user(request)
        
        assert exc_info.value.status_code == 401
        assert "用户未认证" in str(exc_info.value.detail)


class TestAuthMiddlewareIntegration:
    """认证中间件集成测试"""
    
    def test_middleware_injects_user_into_request_state(self, client, valid_token):
        """测试中间件将用户信息注入到请求状态中"""
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 200
        user_data = response.json()["user"]
        
        # 验证用户信息被正确注入
        assert "user_id" in user_data
        assert "name" in user_data
        assert "role" in user_data
        assert user_data["name"] == "测试用户"
    
    def test_multiple_requests_with_different_tokens(self, client, mock_user):
        """测试多个请求使用不同Token"""
        from app.core.config import settings
        
        # 创建两个不同的用户Token
        payload1 = {
            "user_id": "user-1",
            "name": "用户1",
            "role": "法务",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        token1 = jwt.encode(payload1, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        payload2 = {
            "user_id": "user-2",
            "name": "用户2",
            "role": "财务",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        token2 = jwt.encode(payload2, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # 第一个请求
        response1 = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert response1.status_code == 200
        assert response1.json()["user"]["name"] == "用户1"
        assert response1.json()["user"]["role"] == "法务"
        
        # 第二个请求
        response2 = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response2.status_code == 200
        assert response2.json()["user"]["name"] == "用户2"
        assert response2.json()["user"]["role"] == "财务"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
