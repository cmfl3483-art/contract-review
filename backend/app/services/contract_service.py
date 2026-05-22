"""
合同服务层
实现合同CRUD、筛选、搜索和待办统计功能
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid
import logging

from app.models.contract import Contract
from app.models.review import Review
from app.models.user import User
from app.models.attachment import Attachment
from app.core.redis_client import redis_client
from app.services.notification_service import notification_service
from app.utils.cache_invalidation import cache_invalidation
from app.core.exceptions import ConflictError

# 配置日志
logger = logging.getLogger(__name__)
class ContractService:
    """合同服务类"""
    
    async def create_contract(
        self,
        name: str,
        initiator_id: str,
        reviewers: List[Dict[str, str]],
        description: Optional[str] = None,
        cc_users: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> Contract:
        """
        创建合同(使用事务处理确保数据一致性)
        
        事务包含以下操作:
        1. 创建合同记录
        2. 创建所有评审记录
        3. 如果任何操作失败,自动回滚所有更改
        
        Args:
            name: 合同名称
            initiator_id: 发起人ID
            reviewers: 评审人列表 [{"user_id": "xxx", "role": "法务", "step": "法务初审"}]
            description: 合同描述
            cc_users: 抄送人ID列表
            db: 数据库会话
            
        Returns:
            创建的合同对象
            
        Raises:
            ValueError: 如果参数验证失败
            Exception: 数据库操作失败时回滚事务
        """
        # 参数验证
        if not name or not name.strip():
            raise ValueError("合同名称不能为空")
        
        if not reviewers or len(reviewers) == 0:
            raise ValueError("至少需要一个评审人")
        
        try:
            async with db.begin():
                # 1. 创建合同
                contract = Contract(
                    id=str(uuid.uuid4()),
                    name=name,
                    description=description,
                    status="progress",
                    initiator_id=initiator_id,
                    cc_users=cc_users or []
                )
                db.add(contract)
                await db.flush()  # 获取contract.id
                
                # 2. 创建评审记录
                for reviewer in reviewers:
                    if not reviewer.get("user_id"):
                        raise ValueError("评审人ID不能为空")
                    
                    review = Review(
                        id=str(uuid.uuid4()),
                        contract_id=contract.id,
                        reviewer_id=reviewer["user_id"],
                        role=reviewer.get("role", "业务"),
                        step=reviewer.get("step", "评审"),
                        status="pending",
                        likes=0,
                        liked_by=[]
                    )
                    db.add(review)
                
                # 事务提交点 - 如果上述操作有任何失败,事务会自动回滚
                await db.commit()
                
            # 事务成功提交后,执行后续操作
            await db.refresh(contract)
            
            # 3. 清除相关缓存 - 使用统一的缓存失效策略
            reviewer_ids = [r["user_id"] for r in reviewers]
            await cache_invalidation.invalidate_contract_created(
                contract_id=contract.id,
                initiator_id=initiator_id,
                reviewer_ids=reviewer_ids
            )
            
            return contract
            
        except ValueError as e:
            # 业务逻辑错误,直接抛出
            raise e
        except Exception as e:
            # 数据库操作失败,事务已自动回滚
            # 记录错误日志
            logger.error(f"创建合同失败,事务已回滚: name={name}, initiator_id={initiator_id}, error={str(e)}")
            raise Exception(f"创建合同失败: {str(e)}")
    
    async def get_contract_list(
        self,
        user_id: str,
        filter_type: str = "all",
        search_keyword: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        获取合同列表(支持筛选和搜索)
        性能优化:
        1. 使用Redis缓存列表结果
        2. 使用selectinload预加载关联数据,避免N+1查询
        3. 使用复合索引加速查询
        
        Args:
            user_id: 当前用户ID
            filter_type: 筛选类型 (all/进行中/已完成/待我处理/抄送我/我发起的)
            search_keyword: 搜索关键词
            page: 页码
            limit: 每页数量
            db: 数据库会话
            
        Returns:
            包含合同列表、总数和待办数量的字典
        """
        # 生成缓存键
        cache_key = redis_client.generate_cache_key(
            "contract:list",
            user_id,
            filter_type,
            search_keyword or "",
            page,
            limit
        )
        
        # 尝试从缓存获取
        cached_result = await redis_client.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 构建基础查询 - 使用selectinload预加载关联数据
        query = select(Contract).options(
            selectinload(Contract.initiator),
            selectinload(Contract.reviews).selectinload(Review.reviewer)
        )
        
        # 应用筛选条件
        query = await self._apply_filter(query, user_id, filter_type, db)
        
        # 应用搜索条件
        if search_keyword:
            query = await self._apply_search(query, search_keyword, db)
        
        # 排序 - 使用索引 ix_contracts_created_at_desc
        query = query.order_by(Contract.created_at.desc())
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        contracts = result.scalars().all()
        
        # 获取待办数量(使用缓存)
        pending_count = await self.get_pending_count(user_id, db)
        
        # 构建返回结果
        result_data = {
            "contracts": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "description": c.description,
                    "status": c.status,
                    "version": c.version,
                    "initiator": {
                        "id": str(c.initiator.id),
                        "name": c.initiator.name,
                        "avatar": c.initiator.avatar
                    } if c.initiator else None,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                    "review_count": len(c.reviews),
                    "approved_count": sum(1 for r in c.reviews if r.status == "approved"),
                    "hasPendingReview": any(
                        str(r.reviewer_id) == str(user_id) and r.status != "approved"
                        for r in c.reviews
                    )
                }
                for c in contracts
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "pending_count": pending_count
        }
        
        # 缓存结果 - 使用中等TTL(5分钟)
        await redis_client.set(cache_key, result_data, ex=redis_client.TTL_MEDIUM)
        
        return result_data
    
    async def get_contract_detail(
        self,
        contract_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        获取合同详情
        
        Args:
            contract_id: 合同ID
            db: 数据库会话
            
        Returns:
            包含合同信息、附件和评审人状态的字典
        """
        # 查询合同
        query = select(Contract).options(
            selectinload(Contract.initiator),
            selectinload(Contract.reviews).selectinload(Review.reviewer),
            selectinload(Contract.attachments).selectinload(Attachment.uploader)
        ).where(Contract.id == contract_id)
        
        result = await db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            return None
        
        # 按文件名分组附件
        attachments_grouped = self._group_attachments(contract.attachments)
        
        # 整理评审人状态
        reviewers_status = [
            {
                "id": review.id,
                "reviewer": {
                    "id": review.reviewer.id,
                    "name": review.reviewer.name,
                    "role": review.role,
                    "avatar": review.reviewer.avatar
                },
                "status": review.status,
                "step": review.step,
                "updated_at": review.updated_at
            }
            for review in contract.reviews
        ]
        
        return {
            "contract": contract,
            "attachments": attachments_grouped,
            "reviewers": reviewers_status
        }
    
    async def update_contract_status(
        self,
        contract_id: str,
        status: str,
        expected_version: Optional[int] = None,
        db: AsyncSession = None
    ) -> Optional[Contract]:
        """
        更新合同状态(使用乐观锁)
        
        Args:
            contract_id: 合同ID
            status: 新状态
            expected_version: 期望的版本号(用于乐观锁)
            db: 数据库会话
            
        Returns:
            更新后的合同对象
            
        Raises:
            ConflictError: 当版本号不匹配时(并发更新冲突)
        """
        query = select(Contract).where(Contract.id == contract_id)
        result = await db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            return None
        
        # 乐观锁检查
        if expected_version is not None and contract.version != expected_version:
            raise ConflictError(
                f"合同已被其他用户修改,请刷新后重试。当前版本: {contract.version}, 期望版本: {expected_version}"
            )
        
        # 更新状态和版本号
        contract.status = status
        contract.version += 1
        
        await db.commit()
        await db.refresh(contract)
        
        # 发送合同更新通知
        await notification_service.notify_contract_updated(
            contract_id=contract_id,
            contract_data={
                "id": str(contract.id),
                "name": contract.name,
                "status": contract.status,
                "version": contract.version,
                "updated_at": contract.updated_at.isoformat()
            }
        )
        
        # 清除缓存 - 使用统一的缓存失效策略
        # 获取所有相关用户ID(发起人、评审人、抄送人)
        affected_user_ids = [contract.initiator_id]
        if contract.reviews:
            affected_user_ids.extend([r.reviewer_id for r in contract.reviews])
        if contract.cc_users:
            affected_user_ids.extend(contract.cc_users)
        
        await cache_invalidation.invalidate_contract_updated(
            contract_id=contract_id,
            affected_user_ids=list(set(affected_user_ids))  # 去重
        )
        
        return contract
    
    async def update_contract(
        self,
        contract_id: str,
        updates: Dict[str, Any],
        expected_version: Optional[int] = None,
        db: AsyncSession = None
    ) -> Optional[Contract]:
        """
        更新合同信息(使用乐观锁)
        
        Args:
            contract_id: 合同ID
            updates: 要更新的字段字典
            expected_version: 期望的版本号(用于乐观锁)
            db: 数据库会话
            
        Returns:
            更新后的合同对象
            
        Raises:
            ConflictError: 当版本号不匹配时(并发更新冲突)
        """
        query = select(Contract).where(Contract.id == contract_id)
        result = await db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            return None
        
        # 乐观锁检查
        if expected_version is not None and contract.version != expected_version:
            raise ConflictError(
                f"合同已被其他用户修改,请刷新后重试。当前版本: {contract.version}, 期望版本: {expected_version}"
            )
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(contract, key) and key not in ['id', 'version', 'created_at']:
                setattr(contract, key, value)
        
        # 递增版本号
        contract.version += 1
        
        await db.commit()
        await db.refresh(contract)
        
        # 发送合同更新通知
        await notification_service.notify_contract_updated(
            contract_id=contract_id,
            contract_data={
                "id": str(contract.id),
                "name": contract.name,
                "status": contract.status,
                "version": contract.version,
                "updated_at": contract.updated_at.isoformat()
            }
        )
        
        # 清除缓存
        await self._clear_contract_list_cache()
        await self._clear_pending_count_cache(contract.initiator_id)
        
        return contract
    
    async def get_pending_count(
        self,
        user_id: str,
        db: AsyncSession
    ) -> int:
        """
        获取用户待办数量(使用Redis缓存)
        性能优化:
        1. 使用短TTL缓存(1分钟)
        2. 使用复合索引 ix_reviews_reviewer_status 加速查询
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            待办数量
        """
        # 尝试从缓存获取
        cache_key = f"contract:pending:{user_id}"
        cached_count = await redis_client.get(cache_key)
        
        if cached_count is not None:
            return int(cached_count)
        
        # 查询待办数量 - 使用索引 ix_reviews_reviewer_status
        query = select(func.count()).select_from(Review).where(
            and_(
                Review.reviewer_id == user_id,
                Review.status == "pending"
            )
        )
        
        result = await db.execute(query)
        count = result.scalar()
        
        # 缓存结果 - 使用短TTL(1分钟)
        await redis_client.set(cache_key, str(count), ex=redis_client.TTL_SHORT)
        
        return count
    
    async def _apply_filter(
        self,
        query,
        user_id: str,
        filter_type: str,
        db: AsyncSession
    ):
        """
        应用筛选条件
        性能优化: 使用复合索引加速查询
        """
        if filter_type == "进行中":
            # 使用索引 ix_contracts_status
            query = query.where(Contract.status == "progress")
        elif filter_type == "已完成":
            # 使用索引 ix_contracts_status
            query = query.where(Contract.status == "completed")
        elif filter_type == "待我处理":
            # 使用索引 ix_reviews_reviewer_status_contract
            # 查询包含当前用户待处理评审项的合同
            subquery = select(Review.contract_id).where(
                and_(
                    Review.reviewer_id == user_id,
                    Review.status == "pending"
                )
            ).distinct()
            query = query.where(Contract.id.in_(subquery))
        elif filter_type == "抄送我":
            # 使用PostgreSQL的数组包含操作符
            query = query.where(Contract.cc_users.contains([user_id]))
        elif filter_type == "我发起的":
            # 筛选由当前用户发起的合同
            query = query.where(Contract.initiator_id == user_id)
        
        return query
    
    async def _apply_search(
        self,
        query,
        keyword: str,
        db: AsyncSession
    ):
        """应用搜索条件"""
        # 联接用户表以搜索发起人姓名
        query = query.join(User, Contract.initiator_id == User.id)
        
        # 搜索合同名称或发起人姓名
        query = query.where(
            or_(
                Contract.name.ilike(f"%{keyword}%"),
                User.name.ilike(f"%{keyword}%")
            )
        )
        
        return query
    
    def _group_attachments(self, attachments: List[Attachment]) -> List[Dict[str, Any]]:
        """按文件名分组附件"""
        grouped = {}
        
        for attachment in attachments:
            if attachment.file_name not in grouped:
                grouped[attachment.file_name] = []
            grouped[attachment.file_name].append(attachment)
        
        # 按时间倒序排列版本
        result = []
        for file_name, versions in grouped.items():
            versions.sort(key=lambda x: x.created_at, reverse=True)
            result.append({
                "file_name": file_name,
                "version_count": len(versions),
                "versions": versions,
                "latest_version": versions[0] if versions else None
            })
        
        # 按最新上传时间倒序排列文件组
        result.sort(
            key=lambda x: x["latest_version"].created_at if x["latest_version"] else datetime.min,
            reverse=True
        )
        
        return result
    
    async def _clear_contract_list_cache(self):
        """清除合同列表缓存"""
        # 清除所有用户的合同列表缓存
        pattern = "contract:list:*"
        await redis_client.delete_pattern(pattern)
    
    async def _clear_pending_count_cache(self, user_id: str):
        """清除待办数量缓存"""
        cache_key = f"contract:pending:{user_id}"
        await redis_client.delete(cache_key)
