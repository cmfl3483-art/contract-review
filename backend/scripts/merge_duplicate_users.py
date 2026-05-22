"""
合并钉钉重复用户记录 (一次性修复脚本)
Merge duplicate dingtalk users.

背景
====
登录路径 (dingtalk_auth_service.sync_user_info 旧版) 将 unionId 写入
users.dingtalk_user_id, 而通讯录路径 (dingtalk_contact_service.upsert_users)
将钉钉 staff userid 写入同一字段, 导致同一个真实人在 users 表里被创建为
两条记录 (UUID-A 登录创建 / UUID-B 通讯录创建). 前端 UserPicker 选人拿到
的是 UUID-B, 写入 reviews.reviewer_id 也是 UUID-B; 但用户登录后 JWT 里
的是 UUID-A, 导致 "待我处理" 查不到任何记录.

本脚本按 dingtalk_union_id 分组, 把所有 "登录创建的副本" 合并到
"通讯录创建的主记录" 上:
1. 把 contracts.initiator_id / reviews.reviewer_id / comments.author_id /
   attachments.uploader_id 等所有外键引用 update 到 keeper 上.
2. 用 array_replace 替换 contracts.cc_users / reviews.liked_by /
   comments.liked_by 数组中的旧 user_id.
3. 删除被合并的旧记录.
4. 清空相关 Redis 缓存.

执行方式
========
# 预览, 不写库
python -m scripts.merge_duplicate_users --dry-run

# 真正执行
python -m scripts.merge_duplicate_users
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

# 允许以 `python scripts/merge_duplicate_users.py` 直接执行
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.redis_client import redis_client  # noqa: E402


# ------------------------------------------------------------------
# 1. 找出需要合并的用户组
# ------------------------------------------------------------------

FIND_DUPLICATE_GROUPS_SQL = text(
    """
    SELECT dingtalk_union_id, COUNT(*) AS cnt
    FROM users
    WHERE dingtalk_union_id IS NOT NULL AND dingtalk_union_id <> ''
    GROUP BY dingtalk_union_id
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
    """
)

LIST_GROUP_USERS_SQL = text(
    """
    SELECT id, dingtalk_user_id, dingtalk_union_id, name, created_at
    FROM users
    WHERE dingtalk_union_id = :union_id
    ORDER BY created_at ASC
    """
)


def pick_keeper(rows: List[dict]) -> Tuple[dict, List[dict]]:
    """
    在一组重复记录中选出主记录 (keeper) 与待合并记录 (drops).

    选择规则:
    - 优先保留 dingtalk_user_id != dingtalk_union_id 的那条 (通讯录写入的
      是钉钉 staff userid, 与 unionId 不同, 业务数据指向它).
    - 若同组多条都满足, 保留 created_at 最早的.
    - 若同组都不满足 (全是登录路径写的), 保留 created_at 最早的.
    """
    contact_rows = [r for r in rows if r["dingtalk_user_id"] != r["dingtalk_union_id"]]
    if contact_rows:
        keeper = min(contact_rows, key=lambda r: r["created_at"])
    else:
        keeper = min(rows, key=lambda r: r["created_at"])
    drops = [r for r in rows if r["id"] != keeper["id"]]
    return keeper, drops


# ------------------------------------------------------------------
# 2. 迁移单条 drop 用户的所有引用
# ------------------------------------------------------------------

# 外键迁移 (UUID 列)
FK_MIGRATIONS = [
    ("contracts", "initiator_id"),
    ("reviews", "reviewer_id"),
    ("comments", "author_id"),
    ("attachments", "uploader_id"),
]

# 数组字段迁移 (ARRAY(String), 内容为字符串形式的 UUID)
ARRAY_MIGRATIONS = [
    ("contracts", "cc_users"),
    ("reviews", "liked_by"),
    ("comments", "liked_by"),
]


async def migrate_one(
    session: AsyncSession, keep_id, drop_id, dry_run: bool
) -> dict:
    """把 drop_id 的所有引用迁移到 keep_id. 返回受影响行数统计."""
    stats = {}

    for table, col in FK_MIGRATIONS:
        sql = text(
            f"UPDATE {table} SET {col} = :keep WHERE {col} = :drop"
        )
        if dry_run:
            count_sql = text(
                f"SELECT COUNT(*) FROM {table} WHERE {col} = :drop"
            )
            res = await session.execute(count_sql, {"drop": drop_id})
            stats[f"{table}.{col}"] = res.scalar() or 0
        else:
            res = await session.execute(sql, {"keep": keep_id, "drop": drop_id})
            stats[f"{table}.{col}"] = res.rowcount or 0

    keep_str = str(keep_id)
    drop_str = str(drop_id)
    for table, col in ARRAY_MIGRATIONS:
        sql = text(
            f"""
            UPDATE {table}
            SET {col} = array_replace({col}, :drop_str, :keep_str)
            WHERE :drop_str = ANY({col})
            """
        )
        if dry_run:
            count_sql = text(
                f"SELECT COUNT(*) FROM {table} WHERE :drop_str = ANY({col})"
            )
            res = await session.execute(count_sql, {"drop_str": drop_str})
            stats[f"{table}.{col}"] = res.scalar() or 0
        else:
            res = await session.execute(
                sql, {"keep_str": keep_str, "drop_str": drop_str}
            )
            stats[f"{table}.{col}"] = res.rowcount or 0

    if not dry_run:
        await session.execute(
            text("DELETE FROM users WHERE id = :drop"), {"drop": drop_id}
        )
        stats["users.deleted"] = 1
    else:
        stats["users.deleted"] = 1  # 仅展示意图

    return stats


# ------------------------------------------------------------------
# 3. 主流程
# ------------------------------------------------------------------

async def run(dry_run: bool) -> None:
    print(f"=== merge_duplicate_users (dry_run={dry_run}) ===")

    # Redis 客户端 (清缓存用); 即便连不上也不影响数据迁移
    try:
        await redis_client.connect()
        redis_ok = True
    except Exception as e:  # pragma: no cover
        print(f"[warn] Redis connect failed, skip cache cleanup: {e}")
        redis_ok = False

    async with AsyncSessionLocal() as session:
        # 1) 找出所有重复 union_id
        groups = (await session.execute(FIND_DUPLICATE_GROUPS_SQL)).all()
        if not groups:
            print("No duplicate users by dingtalk_union_id. Nothing to do.")
            if redis_ok:
                await redis_client.disconnect()
            return

        print(f"Found {len(groups)} duplicate union_id group(s).")

        affected_drop_ids: List[str] = []
        affected_keep_ids: List[str] = []

        for g in groups:
            union_id = g.dingtalk_union_id
            rows = (
                await session.execute(LIST_GROUP_USERS_SQL, {"union_id": union_id})
            ).mappings().all()
            rows = [dict(r) for r in rows]

            keeper, drops = pick_keeper(rows)
            print(
                f"\n[group] union_id={union_id} size={len(rows)} "
                f"keeper={keeper['id']} (dingtalk_user_id={keeper['dingtalk_user_id']}, "
                f"name={keeper['name']})"
            )
            for d in drops:
                print(
                    f"  drop {d['id']} (dingtalk_user_id={d['dingtalk_user_id']}, "
                    f"name={d['name']}, created_at={d['created_at']})"
                )
                stats = await migrate_one(
                    session, keeper["id"], d["id"], dry_run=dry_run
                )
                for k, v in stats.items():
                    if v:
                        print(f"    - {k}: {v}")
                affected_drop_ids.append(str(d["id"]))
                affected_keep_ids.append(str(keeper["id"]))

        if dry_run:
            await session.rollback()
            print("\n[dry-run] rolled back, no DB changes committed.")
        else:
            await session.commit()
            print("\n[done] DB changes committed.")

    # 2) 清缓存
    if redis_ok and not dry_run and affected_drop_ids:
        try:
            # 受影响用户的待办计数 (drop & keep 都清, 保险)
            pending_keys = [
                f"contract:pending:{uid}"
                for uid in set(affected_drop_ids + affected_keep_ids)
            ]
            if pending_keys:
                await redis_client.delete_many(pending_keys)
                print(f"[redis] cleared {len(pending_keys)} pending count keys")
            # 全局列表/详情/评审/AI 缓存全部失效, 避免脏读
            for pattern in (
                "contract:list:*",
                "contract:detail:*",
                "reviews:v2:*",
                "ai:summary:*",
            ):
                n = await redis_client.delete_pattern(pattern)
                print(f"[redis] cleared pattern {pattern}: {n} keys")
        except Exception as e:  # pragma: no cover
            print(f"[warn] redis cleanup failed: {e}")

    if redis_ok:
        await redis_client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要执行的合并, 不修改数据库",
    )
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
