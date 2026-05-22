"""
钉钉认证服务单元测试
Tests for DingTalk authentication service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import jwt

from app.services.dingtalk_auth_service import DingTalkAuthService
from app.models.user import User
from app.core.config import settings


@pytest.fixture
def auth_service():
    """创建认证服务实例"""
    return DingTalkAuthService()


@pytest.fixture
def mock_user():
    """创建模拟用户对象"""
    user = User(
        dingtalk_user_id="test_user_123",
        dingtalk_union_id="union_123",
        name="测试用户",
        role="业务",
        email="test@example.com",
        mobile="13800138000",
        avatar="https://example.com/avatar.jpg",
        department="技术部"
    )
    user.id = "550e8400-e29b-41d4-a716-446655440000"
    return user


class TestDingTalkAuthService:
    """钉钉认证服务测试类"""
    
    def test_get_authorization_url(self, auth_service):
        """测试生成授权URL"""
        state = "test_state"
        auth_url = auth_service.get_authorization_url(state)
        
        # 验证URL包含必要的参数
        assert "https://login.dingtalk.com/oauth2/auth" in auth_url
        assert f"client_id={settings.DINGTALK_APP_KEY}" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=openid" in auth_url
        assert f"state={state}" in auth_url
        assert f"redirect_uri={settings.DINGTALK_REDIRECT_URI}" in auth_url
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self, auth_service):
        """测试成功获取访问令牌"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessToken": "test_access_token",
            "refreshToken": "test_refresh_token",
            "expireIn": 7200
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await auth_service.get_access_token("test_auth_code")
            
            assert result["accessToken"] == "test_access_token"
            assert result["refreshToken"] == "test_refresh_token"
    
    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, auth_service):
        """测试获取访问令牌失败"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid auth code"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(Exception) as exc_info:
                await auth_service.get_access_token("invalid_code")
            
            assert "获取access token失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self, auth_service):
        """测试成功获取用户信息"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "unionId": "union_123",
            "openId": "open_123",
            "nick": "测试用户",
            "email": "test@example.com",
            "mobile": "13800138000",
            "avatarUrl": "https://example.com/avatar.jpg"
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await auth_service.get_user_info("test_access_token")
            
            assert result["unionId"] == "union_123"
            assert result["nick"] == "测试用户"
            assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_sync_user_info_new_user(self, auth_service):
        """测试同步新用户信息"""
        user_info = {
            "unionId": "union_123",
            "openId": "open_123",
            "nick": "测试用户",
            "email": "test@example.com",
            "mobile": "13800138000",
            "avatarUrl": "https://example.com/avatar.jpg",
            "deptName": "技术部"
        }
        
        # 模拟数据库会话
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # 用户不存在
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        user = await auth_service.sync_user_info(user_info, mock_db)
        
        # 验证用户信息
        assert mock_db.add.called
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_sync_user_info_existing_user(self, auth_service, mock_user):
        """测试同步现有用户信息"""
        user_info = {
            "unionId": "union_123",
            "openId": "open_123",
            "nick": "更新后的用户名",
            "email": "newemail@example.com"
        }
        
        # 模拟数据库会话
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user  # 用户已存在
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        user = await auth_service.sync_user_info(user_info, mock_db)
        
        # 验证用户信息已更新
        assert mock_db.commit.called
        assert not mock_db.add.called  # 不应该添加新用户
    
    def test_generate_jwt_token(self, auth_service, mock_user):
        """测试生成JWT Token"""
        token = auth_service.generate_jwt_token(mock_user)
        
        # 验证token不为空
        assert token is not None
        assert len(token) > 0
        
        # 解码token验证内容
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["user_id"] == str(mock_user.id)
        assert payload["dingtalk_user_id"] == mock_user.dingtalk_user_id
        assert payload["name"] == mock_user.name
        assert payload["role"] == mock_user.role
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_jwt_token_valid(self, auth_service, mock_user):
        """测试验证有效的JWT Token"""
        # 生成token
        token = auth_service.generate_jwt_token(mock_user)
        
        # 验证token
        payload = auth_service.verify_jwt_token(token)
        
        assert payload is not None
        assert payload["user_id"] == str(mock_user.id)
        assert payload["name"] == mock_user.name
    
    def test_verify_jwt_token_expired(self, auth_service):
        """测试验证过期的JWT Token"""
        # 生成一个已过期的token
        payload = {
            "user_id": "test_user_id",
            "exp": datetime.utcnow() - timedelta(hours=1),  # 1小时前过期
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        # 验证过期token应该返回None
        result = auth_service.verify_jwt_token(expired_token)
        assert result is None
    
    def test_verify_jwt_token_invalid(self, auth_service):
        """测试验证无效的JWT Token"""
        invalid_token = "invalid.token.string"
        
        result = auth_service.verify_jwt_token(invalid_token)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_callback_success(self, auth_service, mock_user):
        """测试成功处理授权回调"""
        # Mock get_access_token
        with patch.object(
            auth_service,
            "get_access_token",
            AsyncMock(return_value={"accessToken": "test_token"})
        ):
            # Mock get_user_info
            with patch.object(
                auth_service,
                "get_user_info",
                AsyncMock(return_value={
                    "unionId": "union_123",
                    "nick": "测试用户",
                    "email": "test@example.com"
                })
            ):
                # Mock sync_user_info
                with patch.object(
                    auth_service,
                    "sync_user_info",
                    AsyncMock(return_value=mock_user)
                ):
                    mock_db = AsyncMock()
                    result = await auth_service.handle_callback("test_code", mock_db)
                    
                    # 验证返回结果
                    assert "token" in result
                    assert "user" in result
                    assert result["user"]["id"] == str(mock_user.id)
                    assert result["user"]["name"] == mock_user.name
    
    @pytest.mark.asyncio
    async def test_handle_callback_no_access_token(self, auth_service):
        """测试回调处理时未获取到access token"""
        with patch.object(
            auth_service,
            "get_access_token",
            AsyncMock(return_value={})  # 没有accessToken
        ):
            mock_db = AsyncMock()
            
            with pytest.raises(Exception) as exc_info:
                await auth_service.handle_callback("test_code", mock_db)
            
            assert "未能获取access token" in str(exc_info.value)


class TestAuthServiceConfiguration:
    """测试认证服务配置"""
    
    def test_service_initialization(self, auth_service):
        """测试服务初始化"""
        assert auth_service.app_key == settings.DINGTALK_APP_KEY
        assert auth_service.app_secret == settings.DINGTALK_APP_SECRET
        assert auth_service.redirect_uri == settings.DINGTALK_REDIRECT_URI
        assert auth_service.jwt_secret == settings.SECRET_KEY
        assert auth_service.jwt_algorithm == settings.ALGORITHM
    
    def test_jwt_configuration(self, auth_service):
        """测试JWT配置"""
        assert auth_service.jwt_expire_hours == settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60
        assert auth_service.jwt_algorithm == "HS256"
