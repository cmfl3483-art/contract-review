"""
测试合同管理API端点
Tests for contract management API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
from app.services.dingtalk_auth_service import DingTalkAuthService


client = TestClient(app)


class TestGetContractList:
    """测试获取合同列表API (Task 6.2)"""
    
    def _create_auth_token(self):
        """创建认证token"""
        auth_service = DingTalkAuthService()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.dingtalk_user_id = "test-dingtalk-id"
        mock_user.name = "测试用户"
        mock_user.role = "业务"
        return auth_service.generate_jwt_token(mock_user)
    
    @patch('app.routes.contracts.contract_service.get_contract_list')
    def test_get_contract_list_all(self, mock_get_list):
        """测试获取所有合同列表"""
        # Mock返回数据
        mock_contract = MagicMock()
        mock_contract.id = "contract-1"
        mock_contract.name = "测试合同"
        mock_contract.description = "测试描述"
        mock_contract.status = "progress"
        mock_contract.created_at = MagicMock()
        mock_contract.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_contract.updated_at = MagicMock()
        mock_contract.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_initiator = MagicMock()
        mock_initiator.id = "user-1"
        mock_initiator.name = "张三"
        mock_initiator.avatar = "https://example.com/avatar.jpg"
        mock_contract.initiator = mock_initiator
        
        mock_contract.reviews = []
        
        mock_get_list.return_value = {
            "contracts": [mock_contract],
            "total": 1,
            "page": 1,
            "limit": 20,
            "pending_count": 0
        }
        
        # 发送请求
        token = self._create_auth_token()
        response = client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contracts" in data["data"]
        assert "total" in data["data"]
        assert "pendingCount" in data["data"]
        
        contracts = data["data"]["contracts"]
        assert len(contracts) == 1
        assert contracts[0]["id"] == "contract-1"
        assert contracts[0]["name"] == "测试合同"
        assert contracts[0]["status"] == "progress"
    
    @patch('app.routes.contracts.contract_service.get_contract_list')
    def test_get_contract_list_with_filter(self, mock_get_list):
        """测试使用筛选条件获取合同列表"""
        mock_get_list.return_value = {
            "contracts": [],
            "total": 0,
            "page": 1,
            "limit": 20,
            "pending_count": 0
        }
        
        token = self._create_auth_token()
        
        # 测试不同的筛选条件
        filters = ["all", "进行中", "已完成", "待我处理", "抄送我"]
        
        for filter_type in filters:
            response = client.get(
                f"/api/contracts?filter={filter_type}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # 验证调用了正确的筛选参数
            mock_get_list.assert_called()
            call_args = mock_get_list.call_args
            assert call_args.kwargs["filter_type"] == filter_type
    
    @patch('app.routes.contracts.contract_service.get_contract_list')
    def test_get_contract_list_with_search(self, mock_get_list):
        """测试使用搜索关键词获取合同列表"""
        mock_get_list.return_value = {
            "contracts": [],
            "total": 0,
            "page": 1,
            "limit": 20,
            "pending_count": 0
        }
        
        token = self._create_auth_token()
        search_keyword = "测试合同"
        
        response = client.get(
            f"/api/contracts?search={search_keyword}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 验证调用了正确的搜索参数
        mock_get_list.assert_called()
        call_args = mock_get_list.call_args
        assert call_args.kwargs["search_keyword"] == search_keyword
    
    @patch('app.routes.contracts.contract_service.get_contract_list')
    def test_get_contract_list_with_pagination(self, mock_get_list):
        """测试分页参数"""
        mock_get_list.return_value = {
            "contracts": [],
            "total": 100,
            "page": 2,
            "limit": 10,
            "pending_count": 0
        }
        
        token = self._create_auth_token()
        
        response = client.get(
            "/api/contracts?page=2&limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page"] == 2
        assert data["data"]["limit"] == 10
        assert data["data"]["total"] == 100
        
        # 验证调用了正确的分页参数
        mock_get_list.assert_called()
        call_args = mock_get_list.call_args
        assert call_args.kwargs["page"] == 2
        assert call_args.kwargs["limit"] == 10
    
    @patch('app.routes.contracts.contract_service.get_contract_list')
    def test_get_contract_list_includes_pending_count(self, mock_get_list):
        """测试返回待办数量"""
        mock_get_list.return_value = {
            "contracts": [],
            "total": 0,
            "page": 1,
            "limit": 20,
            "pending_count": 5
        }
        
        token = self._create_auth_token()
        
        response = client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["pendingCount"] == 5
    
    def test_get_contract_list_no_token(self):
        """测试未提供token时返回401错误"""
        response = client.get("/api/contracts")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_contract_list_invalid_token(self):
        """测试无效token时返回401错误"""
        response = client.get(
            "/api/contracts",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @patch('app.routes.contracts.contract_service.get_contract_list')
    def test_get_contract_list_with_reviews(self, mock_get_list):
        """测试返回包含评审信息的合同"""
        # Mock返回数据
        mock_contract = MagicMock()
        mock_contract.id = "contract-1"
        mock_contract.name = "测试合同"
        mock_contract.description = "测试描述"
        mock_contract.status = "progress"
        mock_contract.created_at = MagicMock()
        mock_contract.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_contract.updated_at = MagicMock()
        mock_contract.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_initiator = MagicMock()
        mock_initiator.id = "user-1"
        mock_initiator.name = "张三"
        mock_initiator.avatar = "https://example.com/avatar.jpg"
        mock_contract.initiator = mock_initiator
        
        # 添加评审记录
        mock_review1 = MagicMock()
        mock_review1.status = "approved"
        mock_review2 = MagicMock()
        mock_review2.status = "pending"
        mock_review3 = MagicMock()
        mock_review3.status = "pending"
        
        mock_contract.reviews = [mock_review1, mock_review2, mock_review3]
        
        mock_get_list.return_value = {
            "contracts": [mock_contract],
            "total": 1,
            "page": 1,
            "limit": 20,
            "pending_count": 2
        }
        
        # 发送请求
        token = self._create_auth_token()
        response = client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        contracts = data["data"]["contracts"]
        assert len(contracts) == 1
        assert contracts[0]["review_count"] == 3
        assert contracts[0]["pending_review_count"] == 2


class TestGetContractDetail:
    """测试获取合同详情API (Task 6.3)"""
    
    def _create_auth_token(self):
        """创建认证token"""
        auth_service = DingTalkAuthService()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.dingtalk_user_id = "test-dingtalk-id"
        mock_user.name = "测试用户"
        mock_user.role = "业务"
        return auth_service.generate_jwt_token(mock_user)
    
    @patch('app.routes.contracts.contract_service.get_contract_detail')
    def test_get_contract_detail_success(self, mock_get_detail):
        """测试成功获取合同详情"""
        # Mock返回数据
        mock_contract = MagicMock()
        mock_contract.id = "contract-1"
        mock_contract.name = "测试合同"
        mock_contract.description = "测试描述"
        mock_contract.status = "progress"
        mock_contract.cc_users = ["user-2", "user-3"]
        mock_contract.created_at = MagicMock()
        mock_contract.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_contract.updated_at = MagicMock()
        mock_contract.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_initiator = MagicMock()
        mock_initiator.id = "user-1"
        mock_initiator.name = "张三"
        mock_initiator.avatar = "https://example.com/avatar.jpg"
        mock_contract.initiator = mock_initiator
        
        mock_get_detail.return_value = {
            "contract": mock_contract,
            "attachments": [],
            "reviewers": []
        }
        
        # 发送请求
        token = self._create_auth_token()
        response = client.get(
            "/api/contracts/contract-1",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contract" in data["data"]
        assert "attachments" in data["data"]
        assert "reviewers" in data["data"]
        
        contract = data["data"]["contract"]
        assert contract["id"] == "contract-1"
        assert contract["name"] == "测试合同"
        assert contract["status"] == "progress"
    
    @patch('app.routes.contracts.contract_service.get_contract_detail')
    def test_get_contract_detail_not_found(self, mock_get_detail):
        """测试合同不存在时返回404错误"""
        mock_get_detail.return_value = None
        
        token = self._create_auth_token()
        response = client.get(
            "/api/contracts/non-existent-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_contract_detail_no_token(self):
        """测试未提供token时返回401错误"""
        response = client.get("/api/contracts/contract-1")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestCreateContract:
    """测试创建合同API (Task 6.1)"""
    
    def _create_auth_token(self):
        """创建认证token"""
        auth_service = DingTalkAuthService()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.dingtalk_user_id = "test-dingtalk-id"
        mock_user.name = "测试用户"
        mock_user.role = "业务"
        return auth_service.generate_jwt_token(mock_user)
    
    @patch('app.routes.contracts.contract_service.create_contract')
    def test_create_contract_success(self, mock_create):
        """测试成功创建合同"""
        # Mock返回数据
        mock_contract = MagicMock()
        mock_contract.id = "new-contract-id"
        mock_create.return_value = mock_contract
        
        token = self._create_auth_token()
        
        request_data = {
            "name": "新合同",
            "description": "合同描述",
            "reviewers": [
                {"user_id": "user-1", "role": "法务", "step": "法务初审"},
                {"user_id": "user-2", "role": "财务", "step": "财务审核"}
            ],
            "cc_users": ["user-3", "user-4"]
        }
        
        response = client.post(
            "/api/contracts",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["contractId"] == "new-contract-id"
    
    def test_create_contract_missing_name(self):
        """测试缺少合同名称时返回错误"""
        token = self._create_auth_token()
        
        request_data = {
            "reviewers": [
                {"user_id": "user-1", "role": "法务", "step": "法务初审"}
            ]
        }
        
        response = client.post(
            "/api/contracts",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # FastAPI会返回422 Unprocessable Entity当缺少必需字段
        assert response.status_code == 422
    
    def test_create_contract_empty_reviewers(self):
        """测试评审人列表为空时返回错误"""
        token = self._create_auth_token()
        
        request_data = {
            "name": "新合同",
            "reviewers": []
        }
        
        response = client.post(
            "/api/contracts",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Pydantic会验证min_items=1
        assert response.status_code == 422
    
    def test_create_contract_no_token(self):
        """测试未提供token时返回401错误"""
        request_data = {
            "name": "新合同",
            "reviewers": [
                {"user_id": "user-1", "role": "法务", "step": "法务初审"}
            ]
        }
        
        response = client.post(
            "/api/contracts",
            json=request_data
        )
        
        assert response.status_code == 401



class TestAddComment:
    """测试添加评论API (Task 9.3)"""
    
    def _create_auth_token(self):
        """创建认证token"""
        auth_service = DingTalkAuthService()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.dingtalk_user_id = "test-dingtalk-id"
        mock_user.name = "测试用户"
        mock_user.role = "业务"
        return auth_service.generate_jwt_token(mock_user)
    
    @patch('app.routes.contracts.comment_service.create_comment')
    def test_add_comment_to_contract(self, mock_create_comment):
        """测试直接评论合同(不回复评审意见或其他评论)"""
        # Mock返回数据
        mock_comment = MagicMock()
        mock_comment.id = "comment-1"
        mock_comment.contract_id = "contract-1"
        mock_comment.review_id = None
        mock_comment.parent_comment_id = None
        mock_comment.content = "这是一条评论"
        mock_comment.likes = 0
        mock_comment.liked_by = []
        mock_comment.created_at = MagicMock()
        mock_comment.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_comment.updated_at = MagicMock()
        mock_comment.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_author = MagicMock()
        mock_author.id = "test-user-id"
        mock_author.name = "测试用户"
        mock_author.avatar = "https://example.com/avatar.jpg"
        mock_comment.author = mock_author
        
        mock_create_comment.return_value = mock_comment
        
        token = self._create_auth_token()
        
        request_data = {
            "content": "这是一条评论"
        }
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "comment" in data["data"]
        
        comment = data["data"]["comment"]
        assert comment["id"] == "comment-1"
        assert comment["contract_id"] == "contract-1"
        assert comment["review_id"] is None
        assert comment["parent_comment_id"] is None
        assert comment["content"] == "这是一条评论"
        assert comment["author"]["name"] == "测试用户"
        
        # 验证调用了正确的参数
        mock_create_comment.assert_called_once()
        call_args = mock_create_comment.call_args
        assert call_args.kwargs["contract_id"] == "contract-1"
        assert call_args.kwargs["author_id"] == "test-user-id"
        assert call_args.kwargs["content"] == "这是一条评论"
        assert call_args.kwargs["review_id"] is None
        assert call_args.kwargs["parent_comment_id"] is None
    
    @patch('app.routes.contracts.comment_service.create_comment')
    def test_add_comment_reply_to_review(self, mock_create_comment):
        """测试回复评审意见"""
        # Mock返回数据
        mock_comment = MagicMock()
        mock_comment.id = "comment-2"
        mock_comment.contract_id = "contract-1"
        mock_comment.review_id = "review-1"
        mock_comment.parent_comment_id = None
        mock_comment.content = "回复评审意见"
        mock_comment.likes = 0
        mock_comment.liked_by = []
        mock_comment.created_at = MagicMock()
        mock_comment.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_comment.updated_at = MagicMock()
        mock_comment.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_author = MagicMock()
        mock_author.id = "test-user-id"
        mock_author.name = "测试用户"
        mock_author.avatar = "https://example.com/avatar.jpg"
        mock_comment.author = mock_author
        
        mock_create_comment.return_value = mock_comment
        
        token = self._create_auth_token()
        
        request_data = {
            "content": "回复评审意见",
            "review_id": "review-1"
        }
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        comment = data["data"]["comment"]
        assert comment["review_id"] == "review-1"
        assert comment["parent_comment_id"] is None
        
        # 验证调用了正确的参数
        mock_create_comment.assert_called_once()
        call_args = mock_create_comment.call_args
        assert call_args.kwargs["review_id"] == "review-1"
    
    @patch('app.routes.contracts.comment_service.create_comment')
    def test_add_comment_nested_reply(self, mock_create_comment):
        """测试嵌套回复(回复其他评论)"""
        # Mock返回数据
        mock_comment = MagicMock()
        mock_comment.id = "comment-3"
        mock_comment.contract_id = "contract-1"
        mock_comment.review_id = None
        mock_comment.parent_comment_id = "comment-1"
        mock_comment.content = "嵌套回复"
        mock_comment.likes = 0
        mock_comment.liked_by = []
        mock_comment.created_at = MagicMock()
        mock_comment.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_comment.updated_at = MagicMock()
        mock_comment.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_author = MagicMock()
        mock_author.id = "test-user-id"
        mock_author.name = "测试用户"
        mock_author.avatar = "https://example.com/avatar.jpg"
        mock_comment.author = mock_author
        
        mock_create_comment.return_value = mock_comment
        
        token = self._create_auth_token()
        
        request_data = {
            "content": "嵌套回复",
            "parent_comment_id": "comment-1"
        }
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        comment = data["data"]["comment"]
        assert comment["parent_comment_id"] == "comment-1"
        assert comment["review_id"] is None
        
        # 验证调用了正确的参数
        mock_create_comment.assert_called_once()
        call_args = mock_create_comment.call_args
        assert call_args.kwargs["parent_comment_id"] == "comment-1"
    
    def test_add_comment_missing_content(self):
        """测试缺少评论内容时返回错误"""
        token = self._create_auth_token()
        
        request_data = {}
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # FastAPI会返回422 Unprocessable Entity当缺少必需字段
        assert response.status_code == 422
    
    def test_add_comment_empty_content(self):
        """测试空评论内容时返回错误"""
        token = self._create_auth_token()
        
        request_data = {
            "content": ""
        }
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Pydantic会验证min_length=1
        assert response.status_code == 422
    
    @patch('app.routes.contracts.comment_service.create_comment')
    def test_add_comment_contract_not_found(self, mock_create_comment):
        """测试合同不存在时返回400错误"""
        mock_create_comment.side_effect = ValueError("合同不存在")
        
        token = self._create_auth_token()
        
        request_data = {
            "content": "测试评论"
        }
        
        response = client.post(
            "/api/contracts/non-existent-id/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "合同不存在" in data["detail"]
    
    def test_add_comment_no_token(self):
        """测试未提供token时返回401错误"""
        request_data = {
            "content": "测试评论"
        }
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data
        )
        
        assert response.status_code == 401
    
    @patch('app.routes.contracts.comment_service.create_comment')
    def test_add_comment_auto_sets_author(self, mock_create_comment):
        """测试自动设置作者为当前用户"""
        mock_comment = MagicMock()
        mock_comment.id = "comment-1"
        mock_comment.contract_id = "contract-1"
        mock_comment.review_id = None
        mock_comment.parent_comment_id = None
        mock_comment.content = "测试评论"
        mock_comment.likes = 0
        mock_comment.liked_by = []
        mock_comment.created_at = MagicMock()
        mock_comment.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        mock_comment.updated_at = MagicMock()
        mock_comment.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
        
        mock_author = MagicMock()
        mock_author.id = "test-user-id"
        mock_author.name = "测试用户"
        mock_author.avatar = "https://example.com/avatar.jpg"
        mock_comment.author = mock_author
        
        mock_create_comment.return_value = mock_comment
        
        token = self._create_auth_token()
        
        request_data = {
            "content": "测试评论"
        }
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # 验证author_id被设置为当前用户ID
        mock_create_comment.assert_called_once()
        call_args = mock_create_comment.call_args
        assert call_args.kwargs["author_id"] == "test-user-id"
    
    @patch('app.routes.contracts.comment_service.create_comment')
    def test_add_comment_auto_generates_timestamp(self, mock_create_comment):
        """测试自动生成时间戳"""
        mock_comment = MagicMock()
        mock_comment.id = "comment-1"
        mock_comment.contract_id = "contract-1"
        mock_comment.review_id = None
        mock_comment.parent_comment_id = None
        mock_comment.content = "测试评论"
        mock_comment.likes = 0
        mock_comment.liked_by = []
        mock_comment.created_at = MagicMock()
        mock_comment.created_at.isoformat.return_value = "2025-01-01T12:00:00"
        mock_comment.updated_at = MagicMock()
        mock_comment.updated_at.isoformat.return_value = "2025-01-01T12:00:00"
        
        mock_author = MagicMock()
        mock_author.id = "test-user-id"
        mock_author.name = "测试用户"
        mock_author.avatar = "https://example.com/avatar.jpg"
        mock_comment.author = mock_author
        
        mock_create_comment.return_value = mock_comment
        
        token = self._create_auth_token()
        
        request_data = {
            "content": "测试评论"
        }
        
        response = client.post(
            "/api/contracts/contract-1/comments",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回了时间戳
        comment = data["data"]["comment"]
        assert "created_at" in comment
        assert "updated_at" in comment
        assert comment["created_at"] == "2025-01-01T12:00:00"
        assert comment["updated_at"] == "2025-01-01T12:00:00"
