"""
测试认证API端点
Tests for authentication API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.dingtalk_auth_service import DingTalkAuthService


client = TestClient(app)


class TestGetCurrentUserInfo:
    """测试获取当前用户信息API"""
    
    def test_get_current_user_success(self):
        """测试成功获取当前用户信息"""
        # 创建一个有效的JWT token
        auth_service = DingTalkAuthService()
        
        # 模拟用户对象
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.dingtalk_user_id = "test-dingtalk-id"
        mock_user.name = "测试用户"
        mock_user.role = "业务"
        
        # 生成token
        token = auth_service.generate_jwt_token(mock_user)
        
        # 发送请求
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        
        user = data["data"]["user"]
        assert user["user_id"] == "test-user-id"
        assert user["name"] == "测试用户"
        assert user["role"] == "业务"
    
    def test_get_current_user_no_token(self):
        """测试未提供token时返回401错误"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_current_user_invalid_token(self):
        """测试无效token时返回401错误"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_current_user_expired_token(self):
        """测试过期token时返回401错误"""
        # 创建一个已过期的token
        import jwt
        from datetime import datetime, timedelta
        from app.core.config import settings
        
        payload = {
            "user_id": "test-user-id",
            "name": "测试用户",
            "role": "业务",
            "exp": datetime.utcnow() - timedelta(hours=1),  # 1小时前过期
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(
            payload, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestDingTalkLogin:
    """测试钉钉登录API"""
    
    def test_get_authorization_url(self):
        """测试获取钉钉授权URL"""
        response = client.get("/api/auth/dingtalk/login")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "authUrl" in data["data"]
        
        auth_url = data["data"]["authUrl"]
        assert "login.dingtalk.com" in auth_url
        assert "client_id" in auth_url
        assert "redirect_uri" in auth_url
    
    def test_get_authorization_url_with_state(self):
        """测试带state参数获取授权URL"""
        response = client.get("/api/auth/dingtalk/login?state=custom-state")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        auth_url = data["data"]["authUrl"]
        assert "state=custom-state" in auth_url


class TestDingTalkCallback:
    """测试钉钉授权回调API"""
    
    @pytest.mark.asyncio
    async def test_callback_success(self):
        """测试成功处理授权回调"""
        # Mock钉钉API响应
        with patch.object(
            DingTalkAuthService, 
            'handle_callback'
        ) as mock_handle:
            mock_handle.return_value = {
                "token": "test-jwt-token",
                "user": {
                    "id": "test-user-id",
                    "name": "测试用户",
                    "role": "业务",
                    "email": "test@example.com",
                    "mobile": "13800138000",
                    "avatar": "https://example.com/avatar.jpg",
                    "department": "测试部门"
                }
            }
            
            response = client.get(
                "/api/auth/dingtalk/callback?code=test-auth-code&state=default"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "token" in data["data"]
            assert "user" in data["data"]
    
    def test_callback_missing_code(self):
        """测试缺少授权码时返回错误"""
        response = client.get("/api/auth/dingtalk/callback")
        
        # FastAPI会返回422 Unprocessable Entity当缺少必需参数
        assert response.status_code == 422


class TestLogout:
    """测试登出API"""
    
    def test_logout_success(self):
        """测试成功登出"""
        # 创建一个有效的JWT token
        auth_service = DingTalkAuthService()
        
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.dingtalk_user_id = "test-dingtalk-id"
        mock_user.name = "测试用户"
        mock_user.role = "业务"
        
        token = auth_service.generate_jwt_token(mock_user)
        
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data["data"]
    
    def test_logout_no_token(self):
        """测试未认证时登出返回401错误"""
        response = client.post("/api/auth/logout")
        
        assert response.status_code == 401
