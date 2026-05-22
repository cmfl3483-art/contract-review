"""
FastAPI 应用主入口
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.redis_client import redis_client
from app.core.minio_client import minio_client
from app.core.auth_middleware import AuthMiddleware
from app.core.socketio_server import socket_app
from app.core.error_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logging()
    print(f"🚀 {settings.PROJECT_NAME} 启动中...")
    print(f"📝 环境: {settings.ENVIRONMENT}")
    print(f"🔗 数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    
    # 连接 Redis
    try:
        await redis_client.connect()
        print(f"✅ Redis 连接成功: {settings.REDIS_URL}")
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
    
    # 连接 MinIO 并初始化 bucket
    try:
        minio_client.connect()
        minio_client.initialize_bucket()
        print(f"✅ MinIO 连接成功: {settings.MINIO_ENDPOINT}")
        print(f"✅ Bucket 初始化成功: {settings.MINIO_BUCKET}")
    except Exception as e:
        print(f"❌ MinIO 连接失败: {e}")
    
    yield
    
    # 关闭时执行
    print(f"👋 {settings.PROJECT_NAME} 关闭中...")
    
    # 断开 Redis 连接
    try:
        await redis_client.disconnect()
        print("✅ Redis 连接已关闭")
    except Exception as e:
        print(f"❌ Redis 关闭失败: {e}")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="合同预审看板系统 API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# 配置 CORS 中间件
# CORS (Cross-Origin Resource Sharing) 允许前端应用跨域访问 API
# 
# 配置说明:
# - allow_origins: 允许的前端源列表,从环境变量 CORS_ORIGINS 读取
#   开发环境: http://localhost:3000, http://localhost:5173 等
#   生产环境: 配置实际的前端域名,不要使用 "*"
# - allow_credentials: 允许携带 Cookie 和认证信息
# - allow_methods: 允许的 HTTP 方法 (GET, POST, PUT, DELETE 等)
# - allow_headers: 允许的 HTTP 头 (Authorization, Content-Type 等)
#
# 安全提示:
# 生产环境必须配置具体的前端域名,不要使用 allow_origins=["*"]
# 这样可以防止未授权的网站访问你的 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 允许的源列表
    allow_credentials=True,  # 允许携带 Cookie
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 头
)

# 注册全局异常处理器
# 统一处理各种异常,返回标准化的错误响应
# 包括: 自定义异常、HTTP异常、验证异常、数据库异常等
# 注意: 必须在中间件之前注册,以便能捕获中间件抛出的异常
register_exception_handlers(app)

# 配置认证中间件
# JWT Token 验证中间件,用于保护需要认证的 API 端点
# 
# 功能说明:
# - 从请求头 Authorization 中提取 Bearer Token
# - 验证 JWT Token 的有效性和过期时间
# - 将当前用户信息注入到 request.state.user
# - 对于公开路径 (登录、回调、文档等) 跳过认证
#
# 使用方式:
# 在路由处理函数中使用 get_current_user(request) 获取当前用户信息
#
# 安全提示:
# - Token 过期时间在 config.py 中配置 (默认 24 小时)
# - 生产环境必须使用强密钥 (SECRET_KEY)
# - 建议使用 HTTPS 传输 Token
app.add_middleware(BaseHTTPMiddleware, dispatch=AuthMiddleware())


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "合同预审看板系统 API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# 导入路由
from app.routes import auth, contracts, reviews, files, ai, users, dingtalk

# 注册路由
app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(reviews.router)
app.include_router(files.router)
app.include_router(ai.router)
app.include_router(users.router)
app.include_router(dingtalk.router)

# 挂载 Socket.IO 应用
# Socket.IO 服务器挂载到 /socket.io 路径
# 客户端连接时使用: io('http://localhost:8000', { path: '/socket.io' })
app.mount('/socket.io', socket_app)
