# 后端镜像 - 针对腾讯云 + 国内网络优化
# 关键优化：
#   - apt 源切换为 mirrors.tencent.com（国内访问慢则在 build 时报错）
#   - pip 源切换为 mirrors.tencent.com（PyPI 直连慢得离奇）
#   - 移除不必要的 gcc / postgresql-client（slim 镜像 + asyncpg 已含驱动，不用编译）
#   - --no-install-recommends 减少冗余包
#   - PIP_DEFAULT_TIMEOUT=300 避免 PyPI 慢导致超时
#
# 历史教训：之前因 .gitignore 或其他原因这份优化没进 git，
#         本地 Dockerfile 是旧的、服务器上是优化的，导致 CI/CD 重 build 时
#         走老 Dockerfile，apt-get install 因网络慢卡 30+ 分钟。

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300

# 系统依赖：使用腾讯镜像源加速；slim + asyncpg 不需要 gcc / postgresql-client
RUN sed -i 's|deb.debian.org|mirrors.tencent.com|g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
        curl \
        antiword && \
    rm -rf /var/lib/apt/lists/*

# 先复制 requirements.txt 单独装，让 docker layer cache 在 requirements 不变时跳过 pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.tencent.com/pypi/simple/

# 复制项目文件
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
