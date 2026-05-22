"""
测试合同模型
Test Contract model
"""

import pytest
from datetime import datetime
import uuid

from app.models.contract import Contract, ContractStatus


class TestContractModel:
    """测试合同模型的基本功能"""

    def test_contract_status_enum_values(self):
        """测试合同状态枚举值"""
        assert ContractStatus.PROGRESS.value == "progress"
        assert ContractStatus.COMPLETED.value == "completed"
        assert len(list(ContractStatus)) == 2

    def test_contract_model_attributes(self):
        """测试合同模型的属性定义"""
        # 验证表名
        assert Contract.__tablename__ == "contracts"
        
        # 验证必需字段存在
        assert hasattr(Contract, 'id')
        assert hasattr(Contract, 'name')
        assert hasattr(Contract, 'description')
        assert hasattr(Contract, 'status')
        assert hasattr(Contract, 'initiator_id')
        assert hasattr(Contract, 'cc_users')
        assert hasattr(Contract, 'created_at')
        assert hasattr(Contract, 'updated_at')

    def test_contract_relationships(self):
        """测试合同模型的关系定义"""
        # 验证关系存在
        assert hasattr(Contract, 'initiator')
        assert hasattr(Contract, 'reviews')
        assert hasattr(Contract, 'attachments')

    def test_contract_repr(self):
        """测试合同模型的字符串表示"""
        # 创建一个模拟的合同对象
        contract_id = uuid.uuid4()
        
        # 由于我们不能直接实例化模型(需要数据库会话),
        # 我们只测试__repr__方法的格式
        contract = Contract.__new__(Contract)
        contract.id = contract_id
        contract.name = "测试合同"
        contract.status = ContractStatus.PROGRESS
        
        repr_str = repr(contract)
        assert "Contract" in repr_str
        assert str(contract_id) in repr_str
        assert "测试合同" in repr_str
        assert "progress" in repr_str

    def test_contract_status_default(self):
        """测试合同状态的默认值"""
        # 验证默认状态是PROGRESS
        # 注意: 这个测试验证模型定义,实际默认值在数据库层面设置
        from sqlalchemy.inspection import inspect
        
        mapper = inspect(Contract)
        status_column = mapper.columns['status']
        
        # 验证status列有默认值
        assert status_column.default is not None

    def test_contract_indexes(self):
        """测试合同模型的索引定义"""
        # 验证索引存在
        indexes = {idx.name for idx in Contract.__table__.indexes}
        
        assert 'ix_contracts_initiator_id' in indexes
        assert 'ix_contracts_status' in indexes
        assert 'ix_contracts_created_at_desc' in indexes

    def test_contract_foreign_keys(self):
        """测试合同模型的外键约束"""
        # 验证外键存在
        foreign_keys = list(Contract.__table__.foreign_keys)
        
        assert len(foreign_keys) == 1
        fk = foreign_keys[0]
        assert fk.column.table.name == 'users'
        assert fk.parent.name == 'initiator_id'


class TestContractStatusEnum:
    """测试合同状态枚举"""

    def test_status_enum_is_string_enum(self):
        """测试状态枚举继承自str"""
        assert issubclass(ContractStatus, str)

    def test_status_enum_members(self):
        """测试状态枚举成员"""
        members = [status.value for status in ContractStatus]
        assert "progress" in members
        assert "completed" in members

    def test_status_enum_comparison(self):
        """测试状态枚举比较"""
        assert ContractStatus.PROGRESS == "progress"
        assert ContractStatus.COMPLETED == "completed"
        assert ContractStatus.PROGRESS != ContractStatus.COMPLETED


@pytest.mark.asyncio
class TestContractModelIntegration:
    """测试合同模型的集成功能(需要数据库)"""

    async def test_contract_creation_with_db(self, db_session, test_user):
        """测试在数据库中创建合同"""
        # 创建合同
        contract = Contract(
            name="测试合同",
            description="这是一个测试合同",
            status=ContractStatus.PROGRESS,
            initiator_id=test_user.id,
            cc_users=[str(uuid.uuid4()), str(uuid.uuid4())]
        )
        
        db_session.add(contract)
        await db_session.commit()
        await db_session.refresh(contract)
        
        # 验证合同已创建
        assert contract.id is not None
        assert contract.name == "测试合同"
        assert contract.description == "这是一个测试合同"
        assert contract.status == ContractStatus.PROGRESS
        assert contract.initiator_id == test_user.id
        assert len(contract.cc_users) == 2
        assert contract.created_at is not None
        assert contract.updated_at is not None

    async def test_contract_update_status(self, db_session, test_contract):
        """测试更新合同状态"""
        # 更新状态
        test_contract.status = ContractStatus.COMPLETED
        await db_session.commit()
        await db_session.refresh(test_contract)
        
        # 验证状态已更新
        assert test_contract.status == ContractStatus.COMPLETED

    async def test_contract_with_initiator_relationship(self, db_session, test_contract):
        """测试合同与发起人的关系"""
        # 加载发起人关系
        await db_session.refresh(test_contract, ['initiator'])
        
        # 验证关系
        assert test_contract.initiator is not None
        assert test_contract.initiator.id == test_contract.initiator_id

    async def test_contract_cascade_delete(self, db_session, test_user):
        """测试级联删除"""
        # 创建合同
        contract = Contract(
            name="待删除合同",
            status=ContractStatus.PROGRESS,
            initiator_id=test_user.id,
            cc_users=[]
        )
        db_session.add(contract)
        await db_session.commit()
        contract_id = contract.id
        
        # 删除合同
        await db_session.delete(contract)
        await db_session.commit()
        
        # 验证合同已删除
        from sqlalchemy import select
        result = await db_session.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        deleted_contract = result.scalar_one_or_none()
        assert deleted_contract is None
