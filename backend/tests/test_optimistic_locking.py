"""
测试乐观锁功能
Test optimistic locking functionality
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.contract_service import ContractService
from app.models.contract import Contract
from app.core.exceptions import ConflictError
import uuid


@pytest.fixture
async def contract_service():
    """创建合同服务实例"""
    return ContractService()


@pytest.fixture
async def sample_contract(db_session: AsyncSession):
    """创建测试合同"""
    contract = Contract(
        id=str(uuid.uuid4()),
        name="测试合同",
        description="测试描述",
        status="progress",
        initiator_id=str(uuid.uuid4()),
        cc_users=[],
        version=1
    )
    db_session.add(contract)
    await db_session.commit()
    await db_session.refresh(contract)
    return contract


class TestOptimisticLocking:
    """乐观锁测试类"""
    
    @pytest.mark.asyncio
    async def test_update_with_correct_version(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """测试使用正确版本号更新合同"""
        # 使用正确的版本号更新
        updated_contract = await contract_service.update_contract_status(
            contract_id=str(sample_contract.id),
            status="completed",
            expected_version=1,
            db=db_session
        )
        
        # 验证更新成功
        assert updated_contract is not None
        assert updated_contract.status == "completed"
        assert updated_contract.version == 2  # 版本号应该递增
    
    @pytest.mark.asyncio
    async def test_update_with_wrong_version(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """测试使用错误版本号更新合同(应该抛出冲突异常)"""
        # 使用错误的版本号更新
        with pytest.raises(ConflictError) as exc_info:
            await contract_service.update_contract_status(
                contract_id=str(sample_contract.id),
                status="completed",
                expected_version=999,  # 错误的版本号
                db=db_session
            )
        
        # 验证异常信息
        assert "合同已被其他用户修改" in str(exc_info.value)
        assert "当前版本: 1" in str(exc_info.value)
        assert "期望版本: 999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_without_version_check(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """测试不进行版本检查的更新(向后兼容)"""
        # 不提供版本号,应该正常更新
        updated_contract = await contract_service.update_contract_status(
            contract_id=str(sample_contract.id),
            status="completed",
            expected_version=None,  # 不检查版本
            db=db_session
        )
        
        # 验证更新成功
        assert updated_contract is not None
        assert updated_contract.status == "completed"
        assert updated_contract.version == 2  # 版本号仍然递增
    
    @pytest.mark.asyncio
    async def test_concurrent_update_simulation(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """模拟并发更新场景"""
        # 用户A读取合同(版本1)
        contract_version_a = sample_contract.version
        
        # 用户B读取合同(版本1)
        contract_version_b = sample_contract.version
        
        # 用户A先更新成功(版本1 -> 2)
        updated_a = await contract_service.update_contract_status(
            contract_id=str(sample_contract.id),
            status="completed",
            expected_version=contract_version_a,
            db=db_session
        )
        assert updated_a.version == 2
        
        # 用户B尝试更新(使用旧版本1),应该失败
        with pytest.raises(ConflictError):
            await contract_service.update_contract_status(
                contract_id=str(sample_contract.id),
                status="progress",
                expected_version=contract_version_b,  # 仍然是版本1
                db=db_session
            )
    
    @pytest.mark.asyncio
    async def test_update_contract_general_method(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """测试通用更新方法的乐观锁"""
        # 使用正确版本号更新
        updated_contract = await contract_service.update_contract(
            contract_id=str(sample_contract.id),
            updates={"name": "更新后的合同名称", "description": "更新后的描述"},
            expected_version=1,
            db=db_session
        )
        
        # 验证更新成功
        assert updated_contract is not None
        assert updated_contract.name == "更新后的合同名称"
        assert updated_contract.description == "更新后的描述"
        assert updated_contract.version == 2
    
    @pytest.mark.asyncio
    async def test_update_contract_with_wrong_version(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """测试通用更新方法使用错误版本号"""
        # 使用错误版本号更新
        with pytest.raises(ConflictError):
            await contract_service.update_contract(
                contract_id=str(sample_contract.id),
                updates={"name": "更新后的合同名称"},
                expected_version=999,
                db=db_session
            )
    
    @pytest.mark.asyncio
    async def test_version_increment_on_multiple_updates(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """测试多次更新时版本号正确递增"""
        # 第一次更新: 版本 1 -> 2
        updated_1 = await contract_service.update_contract_status(
            contract_id=str(sample_contract.id),
            status="completed",
            expected_version=1,
            db=db_session
        )
        assert updated_1.version == 2
        
        # 第二次更新: 版本 2 -> 3
        updated_2 = await contract_service.update_contract_status(
            contract_id=str(sample_contract.id),
            status="progress",
            expected_version=2,
            db=db_session
        )
        assert updated_2.version == 3
        
        # 第三次更新: 版本 3 -> 4
        updated_3 = await contract_service.update_contract(
            contract_id=str(sample_contract.id),
            updates={"name": "第三次更新"},
            expected_version=3,
            db=db_session
        )
        assert updated_3.version == 4
    
    @pytest.mark.asyncio
    async def test_version_field_not_updatable_directly(
        self,
        contract_service: ContractService,
        sample_contract: Contract,
        db_session: AsyncSession
    ):
        """测试版本字段不能直接更新"""
        # 尝试直接更新version字段(应该被忽略)
        updated_contract = await contract_service.update_contract(
            contract_id=str(sample_contract.id),
            updates={"name": "新名称", "version": 999},  # 尝试直接设置version
            expected_version=1,
            db=db_session
        )
        
        # 验证version字段没有被直接设置,而是正常递增
        assert updated_contract.version == 2  # 应该是2,不是999
        assert updated_contract.name == "新名称"
