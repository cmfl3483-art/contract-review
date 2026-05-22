"""
合同API集成测试
Tests for Contract API endpoints
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime

from app.main import app
from app.models.contract import Contract, ContractStatus
from app.models.user import User
from app.models.review import Review


@pytest.fixture
def mock_current_user():
    """创建模拟当前用户"""
    return {
        "user_id": str(uuid.uuid4()),
        "name": "测试用户",
        "role": "业务"
    }


@pytest.fixture
def sample_contract_data():
    """创建示例合同数据"""
    return {
        "name": "测试合同",
        "description": "这是一个测试合同",
        "reviewers": [
            {
                "user_id": str(uuid.uuid4()),
                "role": "法务",
                "step": "法务初审"
            },
            {
                "user_id": str(uuid.uuid4()),
                "role": "财务",
                "step": "财务审核"
            }
        ],
        "cc_users": [str(uuid.uuid4())]
    }


class TestCreateContractAPI:
    """测试创建合同API"""
    
    @pytest.mark.asyncio
    async def test_create_contract_success(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试成功创建合同"""
        # Mock get_current_user
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            # Mock ContractService.create_contract
            mock_contract = Contract(
                id=str(uuid.uuid4()),
                name=sample_contract_data["name"],
                description=sample_contract_data["description"],
                status=ContractStatus.PROGRESS,
                initiator_id=mock_current_user["user_id"],
                cc_users=sample_contract_data["cc_users"],
                created_at=datetime.utcnow()
            )
            
            with patch('app.routes.contracts.contract_service.create_contract', 
                      AsyncMock(return_value=mock_contract)):
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/contracts",
                        json=sample_contract_data
                    )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "contractId" in data["data"]
        assert data["data"]["contractId"] == mock_contract.id
    
    @pytest.mark.asyncio
    async def test_create_contract_missing_name(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试缺少合同名称时返回400错误"""
        # 移除name字段
        invalid_data = sample_contract_data.copy()
        del invalid_data["name"]
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/contracts",
                    json=invalid_data
                )
        
        # 验证返回422错误(FastAPI的验证错误)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_contract_empty_name(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试空合同名称时返回400错误"""
        # 设置name为空字符串
        invalid_data = sample_contract_data.copy()
        invalid_data["name"] = ""
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/contracts",
                    json=invalid_data
                )
        
        # 验证返回422错误(FastAPI的验证错误)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_contract_empty_reviewers(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试空评审人列表时返回400错误"""
        # 设置reviewers为空列表
        invalid_data = sample_contract_data.copy()
        invalid_data["reviewers"] = []
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/contracts",
                    json=invalid_data
                )
        
        # 验证返回422错误(FastAPI的验证错误)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_contract_without_description(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试不提供描述时仍能成功创建合同"""
        # 移除description字段
        data_without_desc = sample_contract_data.copy()
        del data_without_desc["description"]
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            mock_contract = Contract(
                id=str(uuid.uuid4()),
                name=data_without_desc["name"],
                description=None,
                status=ContractStatus.PROGRESS,
                initiator_id=mock_current_user["user_id"],
                cc_users=data_without_desc["cc_users"],
                created_at=datetime.utcnow()
            )
            
            with patch('app.routes.contracts.contract_service.create_contract',
                      AsyncMock(return_value=mock_contract)):
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/contracts",
                        json=data_without_desc
                    )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_contract_without_cc_users(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试不提供抄送人时仍能成功创建合同"""
        # 移除cc_users字段
        data_without_cc = sample_contract_data.copy()
        del data_without_cc["cc_users"]
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            mock_contract = Contract(
                id=str(uuid.uuid4()),
                name=data_without_cc["name"],
                description=data_without_cc["description"],
                status=ContractStatus.PROGRESS,
                initiator_id=mock_current_user["user_id"],
                cc_users=[],
                created_at=datetime.utcnow()
            )
            
            with patch('app.routes.contracts.contract_service.create_contract',
                      AsyncMock(return_value=mock_contract)):
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/contracts",
                        json=data_without_cc
                    )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_contract_unauthorized(
        self,
        sample_contract_data
    ):
        """测试未授权时返回401错误"""
        # Mock get_current_user抛出HTTPException
        from fastapi import HTTPException
        
        def mock_get_current_user_unauthorized(request):
            raise HTTPException(status_code=401, detail="未授权")
        
        with patch('app.routes.contracts.get_current_user', 
                  side_effect=mock_get_current_user_unauthorized):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/contracts",
                    json=sample_contract_data
                )
        
        # 验证返回401错误
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_contract_service_error(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试服务层错误时返回500错误"""
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            # Mock ContractService.create_contract抛出异常
            with patch('app.routes.contracts.contract_service.create_contract',
                      AsyncMock(side_effect=Exception("数据库错误"))):
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/contracts",
                        json=sample_contract_data
                    )
        
        # 验证返回500错误
        assert response.status_code == 500
        data = response.json()
        assert "创建合同失败" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_create_contract_with_multiple_reviewers(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试创建包含多个评审人的合同"""
        # 添加更多评审人
        data_with_many_reviewers = sample_contract_data.copy()
        data_with_many_reviewers["reviewers"] = [
            {"user_id": str(uuid.uuid4()), "role": "法务", "step": "法务初审"},
            {"user_id": str(uuid.uuid4()), "role": "财务", "step": "财务审核"},
            {"user_id": str(uuid.uuid4()), "role": "业务", "step": "业务审批"},
            {"user_id": str(uuid.uuid4()), "role": "运营", "step": "运营确认"},
        ]
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            mock_contract = Contract(
                id=str(uuid.uuid4()),
                name=data_with_many_reviewers["name"],
                description=data_with_many_reviewers["description"],
                status=ContractStatus.PROGRESS,
                initiator_id=mock_current_user["user_id"],
                cc_users=data_with_many_reviewers["cc_users"],
                created_at=datetime.utcnow()
            )
            
            with patch('app.routes.contracts.contract_service.create_contract',
                      AsyncMock(return_value=mock_contract)) as mock_create:
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/contracts",
                        json=data_with_many_reviewers
                    )
                
                # 验证create_contract被调用时传入了正确的评审人数量
                call_args = mock_create.call_args
                assert len(call_args.kwargs["reviewers"]) == 4
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_contract_long_name(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试超长合同名称时返回422错误"""
        # 创建超过200字符的名称
        invalid_data = sample_contract_data.copy()
        invalid_data["name"] = "A" * 201
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/contracts",
                    json=invalid_data
                )
        
        # 验证返回422错误(FastAPI的验证错误)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_contract_long_description(
        self,
        mock_current_user,
        sample_contract_data
    ):
        """测试超长描述时返回422错误"""
        # 创建超过2000字符的描述
        invalid_data = sample_contract_data.copy()
        invalid_data["description"] = "A" * 2001
        
        with patch('app.routes.contracts.get_current_user', return_value=mock_current_user):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/contracts",
                    json=invalid_data
                )
        
        # 验证返回422错误(FastAPI的验证错误)
        assert response.status_code == 422
