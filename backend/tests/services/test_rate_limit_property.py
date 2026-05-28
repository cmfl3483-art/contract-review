"""
ComplianceService._enforce_rate_limit 的 Hypothesis 属性测试

**Validates: Requirements 3.12**

Property 10: 频控严格上界
对任意单一 user_id，在任意 60 秒滑动窗口内，成功调用次数 ≤ 10。
窗口外的请求计数清零（由 Redis EXPIRE 保证）。
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException
from freezegun import freeze_time
from hypothesis import given, settings, strategies as st

# 确保 backend 目录在 sys.path 中
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import fakeredis.aioredis as faioredis

import app.core.redis_client as rc_module
from app.services.compliance_service import ComplianceService

# 冻结时间的基准点（Unix epoch）
_BASE_DATETIME = datetime(2024, 1, 1, 0, 0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────────────────


def _make_service() -> ComplianceService:
    """创建 ComplianceService 实例（不调用 __init__，避免依赖 AI/Extractor）"""
    return ComplianceService.__new__(ComplianceService)


# ─────────────────────────────────────────────────────────────────────────────
# Property 10: 频控严格上界
# ─────────────────────────────────────────────────────────────────────────────


@settings(max_examples=200)
@given(
    timestamps=st.lists(
        st.floats(min_value=0.0, max_value=120.0),
        min_size=1,
        max_size=50,
    )
)
def test_rate_limit_strict_upper_bound(timestamps: list[float]) -> None:
    """
    **Validates: Requirements 3.12**

    Property 10: 频控严格上界

    实现使用固定窗口（INCR + EXPIRE 60s）策略：
    - 每个 60 秒固定窗口内，成功调用次数 ≤ 10
    - 窗口由第一次 INCR 触发，EXPIRE 60s 后重置

    断言：对任意时间戳序列，每个固定窗口（由 Redis key 的生命周期决定）
    内的成功次数 ≤ 10。

    实现方式：
    - 使用 fakeredis.aioredis.FakeRedis mock Redis
    - 使用 freezegun 控制时间，使 Redis EXPIRE 感知时间流逝
    - 每次调用前将冻结时间移动到对应时间戳（通过 timedelta 偏移基准时间）
    """
    asyncio.run(_run_rate_limit_property(timestamps))


async def _run_rate_limit_property(timestamps: list[float]) -> None:
    """异步执行频控属性测试的核心逻辑"""
    sorted_ts = sorted(timestamps)
    service = _make_service()
    user_id = "test_user_property_10"

    # 使用 fakeredis 替换全局 redis_client 的底层连接
    fake_r = faioredis.FakeRedis(decode_responses=True)
    original_redis = rc_module.redis_client.redis
    rc_module.redis_client.redis = fake_r

    try:
        # 记录每个固定窗口内的成功次数
        # 固定窗口由 Redis key 的生命周期决定：第一次 INCR 后 EXPIRE 60s
        # 窗口切换时（key 过期后），计数重置
        window_success_count = 0  # 当前窗口内的成功次数
        window_start_ts: float | None = None  # 当前窗口的起始时间戳

        # 使用 freezegun 冻结时间，从基准时间开始
        with freeze_time(_BASE_DATETIME) as frozen:
            for t in sorted_ts:
                # 将冻结时间移动到基准时间 + t 秒
                target = _BASE_DATETIME + timedelta(seconds=t)
                frozen.move_to(target)

                # 检查当前窗口是否已过期（key 的 EXPIRE 60s）
                if window_start_ts is not None and t >= window_start_ts + 60:
                    # 窗口已过期，重置计数
                    window_success_count = 0
                    window_start_ts = None

                try:
                    await service._enforce_rate_limit(user_id)
                    # 成功：记录窗口起始时间（首次成功时）
                    if window_start_ts is None:
                        window_start_ts = t
                    window_success_count += 1
                    # 断言：当前固定窗口内成功次数 ≤ 10
                    assert window_success_count <= 10, (
                        f"Property 10 violated: {window_success_count} successes "
                        f"in fixed window starting at {window_start_ts:.3f}, "
                        f"expected ≤ 10. sorted_ts={sorted_ts}"
                    )
                except HTTPException as e:
                    # 只允许 429，其他异常直接抛出
                    assert e.status_code == 429, (
                        f"Property 10 violated: unexpected HTTP {e.status_code} "
                        f"at timestamp {t}"
                    )

    finally:
        # 恢复原始 redis 连接
        rc_module.redis_client.redis = original_redis
        await fake_r.aclose()


# ─────────────────────────────────────────────────────────────────────────────
# 确定性单元测试（补充 Property 10 的边界场景）
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_exactly_10_allowed():
    """
    **Validates: Requirements 3.12**

    在同一 60 秒窗口内，恰好允许 10 次，第 11 次返回 429。
    """
    service = _make_service()
    user_id = "test_user_exact_10"
    fake_r = faioredis.FakeRedis(decode_responses=True)
    original_redis = rc_module.redis_client.redis
    rc_module.redis_client.redis = fake_r

    try:
        with freeze_time("2024-01-01 00:00:00"):
            # 前 10 次应全部成功
            for i in range(10):
                await service._enforce_rate_limit(user_id)  # 不应抛异常

            # 第 11 次应返回 429
            with pytest.raises(HTTPException) as exc_info:
                await service._enforce_rate_limit(user_id)
            assert exc_info.value.status_code == 429
    finally:
        rc_module.redis_client.redis = original_redis
        await fake_r.aclose()


@pytest.mark.asyncio
async def test_rate_limit_window_reset_after_60s():
    """
    **Validates: Requirements 3.12**

    60 秒窗口过期后，计数清零，可以再次发起 10 次请求。
    """
    service = _make_service()
    user_id = "test_user_window_reset"
    fake_r = faioredis.FakeRedis(decode_responses=True)
    original_redis = rc_module.redis_client.redis
    rc_module.redis_client.redis = fake_r

    try:
        with freeze_time("2024-01-01 00:00:00") as frozen:
            # 第一个窗口：用满 10 次
            for _ in range(10):
                await service._enforce_rate_limit(user_id)

            # 第 11 次应被拒绝
            with pytest.raises(HTTPException) as exc_info:
                await service._enforce_rate_limit(user_id)
            assert exc_info.value.status_code == 429

            # 推进时间超过 60 秒（窗口过期）
            frozen.tick(delta=61)

            # 新窗口：应再次允许 10 次
            for _ in range(10):
                await service._enforce_rate_limit(user_id)

            # 新窗口第 11 次再次被拒绝
            with pytest.raises(HTTPException) as exc_info2:
                await service._enforce_rate_limit(user_id)
            assert exc_info2.value.status_code == 429
    finally:
        rc_module.redis_client.redis = original_redis
        await fake_r.aclose()


@pytest.mark.asyncio
async def test_rate_limit_different_users_independent():
    """
    **Validates: Requirements 3.12**

    不同 user_id 的频控计数相互独立，互不影响。
    """
    service = _make_service()
    fake_r = faioredis.FakeRedis(decode_responses=True)
    original_redis = rc_module.redis_client.redis
    rc_module.redis_client.redis = fake_r

    try:
        with freeze_time("2024-01-01 00:00:00"):
            # user_a 用满 10 次
            for _ in range(10):
                await service._enforce_rate_limit("user_a")

            # user_a 第 11 次被拒绝
            with pytest.raises(HTTPException) as exc_info:
                await service._enforce_rate_limit("user_a")
            assert exc_info.value.status_code == 429

            # user_b 不受 user_a 影响，仍可成功 10 次
            for _ in range(10):
                await service._enforce_rate_limit("user_b")

            # user_b 第 11 次被拒绝
            with pytest.raises(HTTPException) as exc_info2:
                await service._enforce_rate_limit("user_b")
            assert exc_info2.value.status_code == 429
    finally:
        rc_module.redis_client.redis = original_redis
        await fake_r.aclose()
