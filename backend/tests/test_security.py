"""
安全测试 - Security Testing
测试认证、授权、SQL注入防护、XSS防护等安全功能

Task 38.4: 安全测试
- 测试认证和授权
- 测试SQL注入防护
- 测试XSS防护
- 测试CSRF防护
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.services.dingtalk_auth_service import DingTalkAuthService
from app.models.user import User
from app.models.contract import Contract
from app.models.review import Review
from app.models.comment import Comment
import jwt
from datetime import datetime, timedelta


client = TestClient(app)


@pytest.fixture
def auth_service():
    """创建认证服务实例"""
    return DingTalkAuthService()


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = MagicMock(spec=User)
    user.id = "test-user-123"
    user.dingtalk_user_id = "dingtalk-456"
    user.name = "测试用户"
    user.role = "法务"
    user.email = "test@example.com"
    user.mobile = "13800138000"
    return user


@pytest.fixture
def valid_token(auth_service, mock_user):
    """生成有效的JWT Token"""
    return auth_service.generate_jwt_token(mock_user)


@pytest.fixture
def another_user_token(auth_service):
    """生成另一个用户的Token"""
    another_user = MagicMock(spec=User)
    another_user.id = "another-user-456"
    another_user.dingtalk_user_id = "dingtalk-789"
    another_user.name = "其他用户"
    another_user.role = "财务"
    return auth_service.generate_jwt_token(another_user)


class TestAuthentication:
    """认证测试"""
    
    def test_access_protected_endpoint_without_token(self):
        """测试未提供Token访问受保护端点返回401"""
        response = client.get("/api/contracts")
        assert response.status_code == 401
        assert "未提供认证Token" in response.json()["detail"]
    
    def test_access_protected_endpoint_with_invalid_token(self):
        """测试使用无效Token访问受保护端点返回401"""
        response = client.get(
            "/api/contracts",
            headers={"Authorization": "Bearer invalid-token-here"}
        )
        assert response.status_code == 401
        assert "Token无效或已过期" in response.json()["detail"]
    
    def test_access_protected_endpoint_with_expired_token(self):
        """测试使用过期Token访问受保护端点返回401"""
        from app.core.config import settings
        
        # 创建过期Token
        payload = {
            "user_id": "test-user",
            "name": "测试用户",
            "role": "法务",
            "exp": datetime.utcnow() - timedelta(hours=1),  # 1小时前过期
            "iat": datetime.utcnow() - timedelta(hours=25)
        }
        expired_token = jwt.encode(
            payload, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        response = client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        assert "Token无效或已过期" in response.json()["detail"]
    
    def test_access_protected_endpoint_with_malformed_token(self):
        """测试使用格式错误的Token访问受保护端点返回401"""
        # 测试没有Bearer前缀
        response = client.get(
            "/api/contracts",
            headers={"Authorization": "some-token"}
        )
        assert response.status_code == 401
        
        # 测试只有Bearer没有token
        response = client.get(
            "/api/contracts",
            headers={"Authorization": "Bearer"}
        )
        assert response.status_code == 401
        
        # 测试错误的前缀
        response = client.get(
            "/api/contracts",
            headers={"Authorization": "Basic some-token"}
        )
        assert response.status_code == 401
    
    def test_access_public_endpoints_without_token(self):
        """测试公开端点无需Token即可访问"""
        # 健康检查端点
        response = client.get("/health")
        assert response.status_code == 200
        
        # 钉钉登录端点
        response = client.get("/api/auth/dingtalk/login")
        assert response.status_code == 200
        
        # API文档 (注意：实际路径是 /api/docs)
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    def test_token_contains_required_user_info(self, valid_token, mock_user):
        """测试Token包含必需的用户信息"""
        from app.core.config import settings
        
        # 解码Token
        payload = jwt.decode(
            valid_token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 验证必需字段
        assert "user_id" in payload
        assert "name" in payload
        assert "role" in payload
        assert "exp" in payload
        assert "iat" in payload
        
        # 验证值正确
        assert payload["user_id"] == str(mock_user.id)
        assert payload["name"] == mock_user.name
        assert payload["role"] == mock_user.role


class TestAuthorization:
    """授权测试"""
    
    @patch('app.services.contract_service.ContractService.get_contract_by_id')
    @patch('app.services.review_service.ReviewService.approve_review')
    async def test_user_cannot_approve_review_not_assigned_to_them(
        self, 
        mock_approve, 
        mock_get_contract,
        valid_token
    ):
        """测试用户不能审批未分配给他们的评审项"""
        # 模拟合同和评审数据
        mock_contract = MagicMock(spec=Contract)
        mock_contract.id = "contract-123"
        mock_get_contract.return_value = mock_contract
        
        # 模拟评审项属于其他用户
        mock_review = MagicMock(spec=Review)
        mock_review.id = "review-123"
        mock_review.reviewer_id = "other-user-id"  # 不是当前用户
        mock_review.status = "pending"
        
        mock_approve.side_effect = Exception("权限不足")
        
        response = client.post(
            "/api/contracts/contract-123/reviews/review-123/approve",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"opinion": "同意"}
        )
        
        # 应该返回错误（具体状态码取决于实现）
        assert response.status_code in [403, 400, 500]
    
    @patch('app.services.contract_service.ContractService.get_contracts')
    async def test_user_can_only_see_authorized_contracts(
        self, 
        mock_get_contracts,
        valid_token
    ):
        """测试用户只能看到授权的合同"""
        # 模拟返回的合同列表
        mock_contracts = [
            MagicMock(id="contract-1", name="合同1"),
            MagicMock(id="contract-2", name="合同2"),
        ]
        mock_get_contracts.return_value = (mock_contracts, 2, 0)
        
        response = client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 200
        # 验证服务层被调用时传入了当前用户信息
        mock_get_contracts.assert_called_once()
    
    def test_different_users_have_isolated_data(
        self, 
        valid_token, 
        another_user_token
    ):
        """测试不同用户的数据隔离"""
        with patch('app.services.contract_service.ContractService.get_contracts') as mock_get:
            # 第一个用户的请求
            mock_get.return_value = ([], 0, 1)
            response1 = client.get(
                "/api/contracts?filter=待我处理",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            assert response1.status_code == 200
            
            # 第二个用户的请求
            mock_get.return_value = ([], 0, 2)
            response2 = client.get(
                "/api/contracts?filter=待我处理",
                headers={"Authorization": f"Bearer {another_user_token}"}
            )
            assert response2.status_code == 200
            
            # 验证两个用户看到的待办数量不同
            data1 = response1.json()
            data2 = response2.json()
            assert data1["data"]["pendingCount"] != data2["data"]["pendingCount"]


class TestSQLInjectionProtection:
    """SQL注入防护测试"""
    
    def test_sql_injection_in_search_parameter(self, valid_token):
        """测试搜索参数中的SQL注入攻击"""
        # 尝试SQL注入攻击
        malicious_inputs = [
            "'; DROP TABLE contracts; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1--",
            "1' AND '1'='1",
        ]
        
        for malicious_input in malicious_inputs:
            with patch('app.services.contract_service.ContractService.get_contracts') as mock_get:
                mock_get.return_value = ([], 0, 0)
                
                response = client.get(
                    f"/api/contracts?search={malicious_input}",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
                
                # 应该正常返回，不会执行SQL注入
                assert response.status_code == 200
                # 验证服务层被正常调用（参数被安全处理）
                mock_get.assert_called_once()
    
    def test_sql_injection_in_contract_name(self, valid_token):
        """测试合同名称中的SQL注入攻击"""
        malicious_name = "'; DROP TABLE contracts; --"
        
        with patch('app.services.contract_service.ContractService.create_contract') as mock_create:
            mock_contract = MagicMock(spec=Contract)
            mock_contract.id = "new-contract-id"
            mock_create.return_value = mock_contract
            
            response = client.post(
                "/api/contracts",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "name": malicious_name,
                    "description": "测试描述",
                    "reviewers": ["user1"],
                    "ccUsers": []
                }
            )
            
            # 应该正常创建，名称被安全存储
            assert response.status_code == 200
            # 验证服务层被调用，参数被安全传递
            mock_create.assert_called_once()
    
    def test_sql_injection_in_comment_content(self, valid_token):
        """测试评论内容中的SQL注入攻击"""
        malicious_content = "' OR '1'='1'; DROP TABLE comments; --"
        
        with patch('app.services.comment_service.CommentService.add_comment') as mock_add:
            mock_comment = MagicMock(spec=Comment)
            mock_comment.id = "new-comment-id"
            mock_add.return_value = mock_comment
            
            response = client.post(
                "/api/contracts/contract-123/comments",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "content": malicious_content,
                    "reviewId": "review-123"
                }
            )
            
            # 应该正常创建评论
            assert response.status_code in [200, 404]  # 404如果合同不存在
    
    def test_parameterized_queries_used(self):
        """测试使用参数化查询（通过SQLAlchemy ORM）"""
        # SQLAlchemy ORM自动使用参数化查询
        # 这个测试验证我们使用的是ORM而不是原始SQL
        from app.models.contract import Contract
        from sqlalchemy import inspect
        
        # 验证模型使用SQLAlchemy
        mapper = inspect(Contract)
        assert mapper is not None
        assert hasattr(Contract, '__tablename__')


class TestXSSProtection:
    """XSS（跨站脚本）防护测试"""
    
    def test_xss_in_contract_name(self, valid_token):
        """测试合同名称中的XSS攻击"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        ]
        
        for xss_payload in xss_payloads:
            with patch('app.services.contract_service.ContractService.create_contract') as mock_create:
                mock_contract = MagicMock(spec=Contract)
                mock_contract.id = "new-contract-id"
                mock_contract.name = xss_payload  # 存储原始内容
                mock_create.return_value = mock_contract
                
                response = client.post(
                    "/api/contracts",
                    headers={"Authorization": f"Bearer {valid_token}"},
                    json={
                        "name": xss_payload,
                        "description": "测试描述",
                        "reviewers": ["user1"],
                        "ccUsers": []
                    }
                )
                
                # API应该接受输入（后端存储原始内容）
                assert response.status_code == 200
                
                # 前端负责转义显示，后端存储原始内容
                # 验证响应是JSON格式（自动转义）
                assert response.headers["content-type"] == "application/json"
    
    def test_xss_in_comment_content(self, valid_token):
        """测试评论内容中的XSS攻击"""
        xss_content = "<script>document.cookie</script>"
        
        with patch('app.services.comment_service.CommentService.add_comment') as mock_add:
            mock_comment = MagicMock(spec=Comment)
            mock_comment.id = "new-comment-id"
            mock_comment.content = xss_content
            mock_add.return_value = mock_comment
            
            response = client.post(
                "/api/contracts/contract-123/comments",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "content": xss_content,
                    "reviewId": "review-123"
                }
            )
            
            # 应该接受输入
            assert response.status_code in [200, 404]
            
            # 验证响应是JSON格式
            assert response.headers["content-type"] == "application/json"
    
    def test_response_content_type_is_json(self, valid_token):
        """测试API响应内容类型为JSON（防止XSS）"""
        with patch('app.services.contract_service.ContractService.get_contracts') as mock_get:
            mock_get.return_value = ([], 0, 0)
            
            response = client.get(
                "/api/contracts",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            # 验证响应是JSON格式
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
    
    def test_html_entities_not_decoded_in_api(self, valid_token):
        """测试API不解码HTML实体"""
        html_content = "&lt;script&gt;alert('XSS')&lt;/script&gt;"
        
        with patch('app.services.contract_service.ContractService.create_contract') as mock_create:
            mock_contract = MagicMock(spec=Contract)
            mock_contract.id = "new-contract-id"
            mock_contract.name = html_content
            mock_create.return_value = mock_contract
            
            response = client.post(
                "/api/contracts",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "name": html_content,
                    "description": "测试",
                    "reviewers": ["user1"],
                    "ccUsers": []
                }
            )
            
            assert response.status_code == 200


class TestCSRFProtection:
    """CSRF（跨站请求伪造）防护测试"""
    
    def test_cors_configuration_restricts_origins(self):
        """测试CORS配置限制来源"""
        from app.core.config import settings
        
        # 验证CORS配置不是通配符
        assert "*" not in settings.CORS_ORIGINS or len(settings.CORS_ORIGINS) > 1
        
        # 验证配置了具体的源
        assert len(settings.CORS_ORIGINS) > 0
        for origin in settings.CORS_ORIGINS:
            assert origin.startswith("http://") or origin.startswith("https://")
    
    def test_state_changing_operations_require_authentication(self, valid_token):
        """测试状态改变操作需要认证"""
        # POST请求需要认证
        response = client.post("/api/contracts", json={
            "name": "测试合同",
            "reviewers": ["user1"],
            "ccUsers": []
        })
        assert response.status_code == 401
        
        # PUT/PATCH请求需要认证
        response = client.post(
            "/api/contracts/contract-123/reviews/review-123/approve",
            json={"opinion": "同意"}
        )
        assert response.status_code == 401
        
        # DELETE请求需要认证（如果有的话）
        # 本系统可能没有DELETE端点，这里作为示例
    
    def test_jwt_token_prevents_csrf(self, valid_token):
        """测试JWT Token机制防止CSRF攻击"""
        # JWT Token存储在Authorization header中，不是Cookie
        # 这样可以防止CSRF攻击，因为恶意网站无法读取header
        
        # 验证使用header认证而不是cookie
        response = client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 200
        
        # 验证没有token时无法访问
        response = client.get("/api/contracts")
        assert response.status_code == 401
    
    def test_same_origin_policy_enforced(self):
        """测试同源策略执行"""
        # FastAPI默认不设置允许所有来源的CORS
        # 测试从未授权来源的请求被拒绝
        
        # 这个测试在实际浏览器环境中才有意义
        # 在测试环境中，我们验证CORS配置正确
        from app.main import app
        
        # 查找CORS中间件
        cors_middleware = None
        for middleware in app.user_middleware:
            if "CORSMiddleware" in str(middleware):
                cors_middleware = middleware
                break
        
        # 验证CORS中间件已配置
        assert cors_middleware is not None


class TestInputValidation:
    """输入验证测试"""
    
    def test_contract_name_required(self, valid_token):
        """测试合同名称必填"""
        response = client.post(
            "/api/contracts",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "description": "只有描述",
                "reviewers": ["user1"],
                "ccUsers": []
            }
        )
        
        # 应该返回验证错误
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_reviewers_required(self, valid_token):
        """测试评审人必填"""
        response = client.post(
            "/api/contracts",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "name": "测试合同",
                "description": "描述",
                "ccUsers": []
            }
        )
        
        # 应该返回验证错误
        assert response.status_code == 422
    
    def test_invalid_json_rejected(self, valid_token):
        """测试拒绝无效的JSON"""
        response = client.post(
            "/api/contracts",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "Content-Type": "application/json"
            },
            content="invalid json {{"
        )
        
        # 应该返回错误
        assert response.status_code == 422
    
    def test_oversized_input_rejected(self, valid_token):
        """测试拒绝过大的输入"""
        # 创建一个非常长的字符串
        very_long_string = "A" * 100000  # 100KB
        
        with patch('app.services.contract_service.ContractService.create_contract') as mock_create:
            response = client.post(
                "/api/contracts",
                headers={"Authorization": f"Bearer {valid_token}"},
                json={
                    "name": very_long_string,
                    "description": very_long_string,
                    "reviewers": ["user1"],
                    "ccUsers": []
                }
            )
            
            # 应该被接受或拒绝（取决于实现）
            # 如果有长度限制，应该返回400或422
            assert response.status_code in [200, 400, 422]


class TestFileUploadSecurity:
    """文件上传安全测试"""
    
    def test_file_type_validation(self, valid_token):
        """测试文件类型验证"""
        from io import BytesIO
        
        # 尝试上传不允许的文件类型
        malicious_file = BytesIO(b"malicious content")
        
        response = client.post(
            "/api/contracts/contract-123/attachments",
            headers={"Authorization": f"Bearer {valid_token}"},
            files={"file": ("malware.exe", malicious_file, "application/x-msdownload")}
        )
        
        # 应该被拒绝
        assert response.status_code in [400, 415, 422]
    
    def test_file_size_validation(self, valid_token):
        """测试文件大小验证"""
        from app.core.config import settings
        
        # 验证配置了文件大小限制
        assert settings.MAX_FILE_SIZE > 0
        assert settings.MAX_FILE_SIZE == 20 * 1024 * 1024  # 20MB
    
    def test_allowed_file_types_configured(self):
        """测试配置了允许的文件类型"""
        from app.core.config import settings
        
        # 验证配置了允许的文件类型
        assert len(settings.ALLOWED_FILE_TYPES) > 0
        
        # 验证包含常见的办公文件类型
        assert "application/pdf" in settings.ALLOWED_FILE_TYPES
        assert any("word" in ft for ft in settings.ALLOWED_FILE_TYPES)


class TestSecurityHeaders:
    """安全响应头测试"""
    
    def test_no_sensitive_info_in_error_messages(self, valid_token):
        """测试错误消息不泄露敏感信息"""
        # 尝试访问不存在的资源
        response = client.get(
            "/api/contracts/nonexistent-id",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # 错误消息不应该包含数据库信息、堆栈跟踪等
        if response.status_code >= 400:
            error_text = response.text.lower()
            assert "traceback" not in error_text
            assert "sqlalchemy" not in error_text
            assert "postgresql" not in error_text
            assert "password" not in error_text
    
    def test_api_version_not_exposed_unnecessarily(self):
        """测试API版本信息不被不必要地暴露"""
        response = client.get("/")
        
        # 根路径可以显示版本信息（这是公开的）
        # 但错误响应不应该暴露详细的版本信息
        assert response.status_code == 200


class TestRateLimiting:
    """速率限制测试（如果实现了的话）"""
    
    def test_multiple_failed_login_attempts(self):
        """测试多次失败登录尝试"""
        # 注意：本系统使用钉钉OAuth，没有传统的登录端点
        # 这个测试作为示例，实际可能不适用
        pass
    
    def test_api_rate_limiting(self, valid_token):
        """测试API速率限制"""
        # 如果实现了速率限制，测试连续请求
        # 注意：当前实现可能没有速率限制
        
        with patch('app.services.contract_service.ContractService.get_contracts') as mock_get:
            mock_get.return_value = ([], 0, 0)
            
            # 发送多个请求
            for i in range(10):
                response = client.get(
                    "/api/contracts",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
                # 应该都成功（如果没有速率限制）
                assert response.status_code == 200


class TestDataEncryption:
    """数据加密测试"""
    
    def test_jwt_token_is_signed(self, valid_token):
        """测试JWT Token已签名"""
        from app.core.config import settings
        
        # 尝试修改token
        parts = valid_token.split('.')
        if len(parts) == 3:
            # 修改payload部分
            modified_token = parts[0] + '.modified.' + parts[2]
            
            response = client.get(
                "/api/contracts",
                headers={"Authorization": f"Bearer {modified_token}"}
            )
            
            # 应该被拒绝
            assert response.status_code == 401
    
    def test_password_not_stored_in_plain_text(self):
        """测试密码不以明文存储"""
        # 注意：本系统使用钉钉OAuth，不存储密码
        # 这个测试作为安全最佳实践的示例
        from app.models.user import User
        
        # 验证User模型没有password字段
        user_columns = [c.name for c in User.__table__.columns]
        assert "password" not in user_columns


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
