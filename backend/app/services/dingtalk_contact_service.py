"""
钉钉通讯录服务
- 获取企业级 access_token (基于 AppKey/AppSecret)
- 递归抓取所有部门成员
- upsert 到本地 users 表 (保持现有外键关系不破)
- 返回与 /api/users/list 兼容的数据结构 (id 仍然是本地 users.id UUID)
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_client import redis_client
from app.models.user import User

logger = logging.getLogger(__name__)

# 钉钉旧版 OpenAPI (oapi.dingtalk.com), 文档完整、稳定
DINGTALK_OAPI_BASE = "https://oapi.dingtalk.com"
GET_TOKEN_URL = f"{DINGTALK_OAPI_BASE}/gettoken"
DEPT_LIST_SUB_URL = f"{DINGTALK_OAPI_BASE}/topapi/v2/department/listsub"
DEPT_GET_URL = f"{DINGTALK_OAPI_BASE}/topapi/v2/department/get"
USER_LIST_URL = f"{DINGTALK_OAPI_BASE}/topapi/v2/user/list"

# Redis cache key
CACHE_KEY_CORP_TOKEN = "dingtalk:corp_access_token"
CACHE_KEY_USERS = "dingtalk:contact_users"
CACHE_KEY_CONTACTS = "dingtalk:contacts_full"
CORP_TOKEN_TTL = 6900  # 钉钉返回的 token 有效期 7200 秒, 提前 5 分钟刷新
USERS_CACHE_TTL = 7200  # 通讯录列表缓存 2 小时, 减少钉钉接口调用频率

# 角色映射: 把钉钉 position(职位) 关键字粗略归类到本系统使用的 6 大角色
ROLE_KEYWORDS = [
    ("销售", "销售"),
    ("法务", "法务"),
    ("财务", "财务"),
    ("运营", "运营"),
    ("人事", "人事"),
    ("hr", "人事"),
    ("业务", "业务"),
]


def _map_role(position: Optional[str]) -> str:
    if not position:
        return "业务"
    p = position.lower()
    for kw, role in ROLE_KEYWORDS:
        if kw in p:
            return role
    return "业务"


class DingTalkContactService:
    def __init__(self) -> None:
        self.app_key = settings.DINGTALK_APP_KEY
        self.app_secret = settings.DINGTALK_APP_SECRET

    async def get_corp_access_token(self) -> str:
        """获取企业级 access_token, 走 Redis 缓存."""
        cached = await redis_client.get(CACHE_KEY_CORP_TOKEN)
        if cached:
            return cached if isinstance(cached, str) else str(cached)

        if not self.app_key or not self.app_secret:
            raise RuntimeError("DINGTALK_APP_KEY / DINGTALK_APP_SECRET 未配置")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                GET_TOKEN_URL,
                params={"appkey": self.app_key, "appsecret": self.app_secret},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("errcode") != 0:
            raise RuntimeError(
                f"获取钉钉企业 access_token 失败: errcode={data.get('errcode')}, "
                f"errmsg={data.get('errmsg')}"
            )

        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"钉钉返回无 access_token: {data}")

        await redis_client.set(CACHE_KEY_CORP_TOKEN, token, ex=CORP_TOKEN_TTL)
        return token

    async def _post_oapi(
        self, url: str, access_token: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                params={"access_token": access_token},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(
                f"钉钉接口 {url} 调用失败: errcode={data.get('errcode')}, "
                f"errmsg={data.get('errmsg')}"
            )
        return data

    async def list_sub_dept_ids(self, access_token: str, dept_id: int) -> List[int]:
        """获取直接子部门 ID 列表 (兼容旧调用)."""
        items = await self.list_sub_depts(access_token, dept_id)
        return [it["id"] for it in items if it.get("id")]

    async def list_sub_depts(
        self, access_token: str, dept_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取直接子部门列表, 统一返回 [{id, name?, parent_id?}, ...].
        钉钉 listsub 接口在不同权限/版本下可能返回:
          - List[int]   (仅部门 ID)
          - List[dict]  (含 dept_id/name/parent_id 详情)
        这里处理为统一格式, 供上层减少 dept/get 调用.
        """
        data = await self._post_oapi(
            DEPT_LIST_SUB_URL, access_token, {"dept_id": dept_id}
        )
        raw = data.get("result") or []
        result: List[Dict[str, Any]] = []
        for item in raw:
            if isinstance(item, int):
                result.append({"id": item, "name": None, "parent_id": dept_id})
            elif isinstance(item, dict):
                result.append(
                    {
                        "id": item.get("dept_id") or item.get("id"),
                        "name": item.get("name"),
                        "parent_id": item.get("parent_id") or dept_id,
                    }
                )
        return [r for r in result if r.get("id")]

    async def get_dept_name(self, access_token: str, dept_id: int) -> Optional[str]:
        try:
            data = await self._post_oapi(
                DEPT_GET_URL, access_token, {"dept_id": dept_id}
            )
            return (data.get("result") or {}).get("name")
        except Exception as e:  # noqa: BLE001
            logger.warning("获取部门 %s 名称失败: %s", dept_id, e)
            return None

    async def list_users_in_dept(
        self, access_token: str, dept_id: int
    ) -> List[Dict[str, Any]]:
        """分页拉取某部门所有用户."""
        users: List[Dict[str, Any]] = []
        cursor = 0
        page_size = 100
        while True:
            data = await self._post_oapi(
                USER_LIST_URL,
                access_token,
                {"dept_id": dept_id, "cursor": cursor, "size": page_size},
            )
            result = data.get("result") or {}
            users.extend(result.get("list") or [])
            if not result.get("has_more"):
                break
            cursor = result.get("next_cursor", 0)
            if cursor == 0:
                break
        return users

    async def fetch_contacts(self) -> Dict[str, Any]:
        """
        从根部门 1 开始 BFS, 一次性拾取:
          - 部门树 (id/name/parent_id/children)
          - 全部成员 (包含 _dept_ids / _department_name 补充字段)
        权限不足 (errcode=88) 时走 try/except 静默降级, 不中断主流程.
        返回: {"departments": [tree], "users": [...]}
        """
        token = await self.get_corp_access_token()

        dept_nodes: Dict[int, Dict[str, Any]] = {}
        all_users: Dict[str, Dict[str, Any]] = {}
        visited_dept: Set[int] = set()
        queue: List[int] = [1]

        # 预插入根节点 (钉钉根部门 id 固定为 1)
        try:
            root_data = await self._post_oapi(DEPT_GET_URL, token, {"dept_id": 1})
            root_info = root_data.get("result") or {}
            root_name = root_info.get("name") or "全公司"
        except Exception as e:  # noqa: BLE001
            logger.warning("获取根部门 1 名称失败: %s", e)
            root_name = "全公司"
        dept_nodes[1] = {
            "id": 1,
            "name": root_name,
            "parent_id": 0,
            "children": [],
        }

        while queue:
            current = queue.pop(0)
            if current in visited_dept:
                continue
            visited_dept.add(current)

            # 1) 拉子部门 (兼容 listsub 两种返回格式)
            try:
                sub_items = await self.list_sub_depts(token, current)
            except Exception as e:  # noqa: BLE001
                logger.warning("拉取部门 %s 子部门失败: %s", current, e)
                sub_items = []
            for sub in sub_items:
                sub_id = sub["id"]
                if sub_id in dept_nodes:
                    continue
                sub_name = sub.get("name")
                # 如果 listsub 返回中不含 name, 再调 dept/get 拿名称
                if not sub_name:
                    try:
                        sub_data = await self._post_oapi(
                            DEPT_GET_URL, token, {"dept_id": sub_id}
                        )
                        sub_name = (sub_data.get("result") or {}).get("name")
                    except Exception as e:  # noqa: BLE001
                        logger.warning("获取部门 %s 名称失败: %s", sub_id, e)
                dept_nodes[sub_id] = {
                    "id": sub_id,
                    "name": sub_name or f"部门{sub_id}",
                    "parent_id": sub.get("parent_id") or current,
                    "children": [],
                }
                queue.append(sub_id)

            # 2) 拉当前部门成员
            try:
                items = await self.list_users_in_dept(token, current)
            except Exception as e:  # noqa: BLE001
                logger.warning("拉取部门 %s 成员失败: %s", current, e)
                items = []
            for u in items:
                uid = u.get("userid")
                if not uid:
                    continue
                u_dept_ids = u.get("dept_id_list") or [current]
                if uid not in all_users:
                    u["_dept_ids"] = list(u_dept_ids)
                    all_users[uid] = u
                else:
                    merged = set(all_users[uid].get("_dept_ids") or [])
                    merged.update(u_dept_ids)
                    all_users[uid]["_dept_ids"] = list(merged)

        # 3) 为每个用户填主部门名 (取第一个)
        for u in all_users.values():
            dept_ids = u.get("_dept_ids") or []
            primary_dept = dept_ids[0] if dept_ids else None
            u["_primary_dept_id"] = primary_dept
            if primary_dept and primary_dept in dept_nodes:
                u["_department_name"] = dept_nodes[primary_dept]["name"]
            else:
                u["_department_name"] = None

        # 4) 组装部门树
        for d in dept_nodes.values():
            if d["id"] == 1:
                continue
            parent_id = d["parent_id"]
            if parent_id in dept_nodes:
                dept_nodes[parent_id]["children"].append(d)

        # 对每个层级的 children 按 name 排序以保证稳定顺序
        def _sort_children(node: Dict[str, Any]) -> None:
            node["children"].sort(key=lambda x: x["name"])
            for c in node["children"]:
                _sort_children(c)

        if 1 in dept_nodes:
            _sort_children(dept_nodes[1])

        departments = [dept_nodes[1]] if 1 in dept_nodes else []
        return {"departments": departments, "users": list(all_users.values())}

    async def fetch_all_users(self) -> List[Dict[str, Any]]:
        """兼容旧调用: 仅返回成员列表."""
        contacts = await self.fetch_contacts()
        return contacts["users"]

    async def upsert_users(
        self, db: AsyncSession, dingtalk_users: List[Dict[str, Any]]
    ) -> List[User]:
        """
        将钉钉用户 upsert 到本地 users 表.
        - 按 dingtalk_user_id 唯一约束查找
        - 找到则更新基础字段, 不存在则创建
        - 返回 [(User, raw_dingtalk_dict), ...], 有助于上层取到原始 _dept_ids
        """
        if not dingtalk_users:
            return []

        userids = [u["userid"] for u in dingtalk_users if u.get("userid")]
        existing_q = select(User).where(User.dingtalk_user_id.in_(userids))
        existing_rows = (await db.execute(existing_q)).scalars().all()
        existing_map = {u.dingtalk_user_id: u for u in existing_rows}

        result: List[User] = []
        for raw in dingtalk_users:
            uid = raw.get("userid")
            if not uid:
                continue
            name = raw.get("name") or "未命名"
            position = raw.get("position") or raw.get("title")
            role = _map_role(position)
            email = raw.get("email") or raw.get("org_email")
            mobile = raw.get("mobile")
            avatar = raw.get("avatar")
            department = raw.get("_department_name")
            union_id = raw.get("unionid")

            user = existing_map.get(uid)
            if user is None:
                user = User(
                    dingtalk_user_id=uid,
                    dingtalk_union_id=union_id,
                    name=name,
                    role=role,
                    email=email,
                    mobile=mobile,
                    avatar=avatar,
                    department=department,
                )
                db.add(user)
            else:
                user.name = name
                if union_id:
                    user.dingtalk_union_id = union_id
                # role 字段允许人工调整, 不覆盖已有的非"业务"值
                if user.role in (None, "", "业务"):
                    user.role = role
                if email:
                    user.email = email
                if mobile:
                    user.mobile = mobile
                if avatar:
                    user.avatar = avatar
                if department:
                    user.department = department
            result.append(user)

        await db.commit()
        for u in result:
            await db.refresh(u)
        return result

    def _serialize_user(
        self, user: User, raw: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "id": str(user.id),
            "name": user.name,
            "role": user.role,
            "email": user.email,
            "mobile": user.mobile,
            "avatar": user.avatar,
            "department": user.department,
            "dept_ids": list((raw or {}).get("_dept_ids") or []),
        }

    async def get_contacts_for_form(
        self, db: AsyncSession, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        返回完整通讯录: {departments: tree, users: [...]}
        - users 已 upsert 到本地, id 为 UUID, 包含 dept_ids
        - 根据 dept_ids 前端可按部门过滤、全量搜索
        """
        if not force_refresh:
            cached = await redis_client.get(CACHE_KEY_CONTACTS)
            if cached and isinstance(cached, dict):
                return cached

        contacts = await self.fetch_contacts()
        raw_users = contacts["users"]
        local_users = await self.upsert_users(db, raw_users)

        # 按 userid 对齐 raw_users, 以依赖 _dept_ids
        raw_by_uid = {r.get("userid"): r for r in raw_users}

        users_payload: List[Dict[str, Any]] = []
        for u in local_users:
            raw = raw_by_uid.get(u.dingtalk_user_id)
            users_payload.append(self._serialize_user(u, raw))
        users_payload.sort(
            key=lambda x: ((x.get("department") or ""), x.get("name") or "")
        )

        result = {
            "departments": contacts["departments"],
            "users": users_payload,
        }
        await redis_client.set(CACHE_KEY_CONTACTS, result, ex=USERS_CACHE_TTL)
        return result

    async def get_users_for_form(
        self, db: AsyncSession, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """兼容旧调用: 仅返回成员列表 (不含部门树)."""
        contacts = await self.get_contacts_for_form(db, force_refresh=force_refresh)
        return contacts["users"]


dingtalk_contact_service = DingTalkContactService()
