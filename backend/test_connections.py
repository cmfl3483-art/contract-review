"""
测试数据库、Redis 和 MinIO 连接
Test database, Redis and MinIO connections
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import engine
from app.core.redis_client import redis_client
from app.core.minio_client import minio_client


async def test_database():
    """测试数据库连接"""
    print("🔍 测试 PostgreSQL 连接...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()
        print("✅ PostgreSQL 连接成功")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        return False


async def test_redis():
    """测试 Redis 连接"""
    print("🔍 测试 Redis 连接...")
    try:
        await redis_client.connect()
        await redis_client.set("test_key", "test_value", expire=10)
        value = await redis_client.get("test_key")
        await redis_client.delete("test_key")
        
        if value == "test_value":
            print("✅ Redis 连接成功")
            return True
        else:
            print("❌ Redis 读写测试失败")
            return False
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return False
    finally:
        await redis_client.disconnect()


def test_minio():
    """测试 MinIO 连接"""
    print("🔍 测试 MinIO 连接...")
    try:
        minio_client.connect()
        minio_client.initialize_bucket()
        
        # 测试 bucket 是否存在
        if minio_client.client.bucket_exists(settings.MINIO_BUCKET):
            print("✅ MinIO 连接成功")
            print(f"✅ Bucket '{settings.MINIO_BUCKET}' 已就绪")
            return True
        else:
            print(f"❌ Bucket '{settings.MINIO_BUCKET}' 不存在")
            return False
    except Exception as e:
        print(f"❌ MinIO 连接失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("合同预审看板系统 - 基础设施连接测试")
    print("=" * 60)
    print()
    
    print(f"📝 配置信息:")
    print(f"  - 环境: {settings.ENVIRONMENT}")
    print(f"  - 数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"  - Redis: {settings.REDIS_URL}")
    print(f"  - MinIO: {settings.MINIO_ENDPOINT}")
    print()
    
    results = []
    
    # 测试数据库
    results.append(await test_database())
    print()
    
    # 测试 Redis
    results.append(await test_redis())
    print()
    
    # 测试 MinIO
    results.append(test_minio())
    print()
    
    # 总结
    print("=" * 60)
    if all(results):
        print("✅ 所有服务连接成功！")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分服务连接失败，请检查配置和服务状态")
        print("=" * 60)
        print()
        print("💡 提示:")
        print("  1. 确保 Docker 服务已启动: docker compose ps")
        print("  2. 查看服务日志: docker compose logs")
        print("  3. 检查 .env 配置文件")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
