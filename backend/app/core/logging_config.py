"""
日志配置
Logging configuration

本模块配置应用的日志系统,包括:
- 日志格式和级别
- 控制台输出
- 文件输出
- 第三方库日志级别

日志级别说明:
- DEBUG: 详细的调试信息
- INFO: 一般信息 (默认)
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

配置方式:
在 .env 文件中设置:
- LOG_LEVEL: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- LOG_FILE: 日志文件路径 (默认: logs/app.log)
"""

import logging
import sys
from pathlib import Path
from app.core.config import settings


def setup_logging() -> None:
    """
    配置应用日志系统
    
    功能:
    1. 创建日志目录 (如果不存在)
    2. 配置日志格式 (时间、模块、级别、消息)
    3. 配置输出目标 (控制台 + 文件)
    4. 设置第三方库日志级别 (避免过多日志)
    
    日志格式示例:
    2025-03-15 10:30:45 - app.main - INFO - 应用启动成功
    """
    
    # 创建日志目录
    log_file_path = Path(settings.LOG_FILE)
    log_dir = log_file_path.parent
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # 配置日志格式
    # 格式: 时间 - 模块名 - 日志级别 - 消息内容
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 获取日志级别 (从环境变量读取)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 控制台输出 (stdout)
            logging.StreamHandler(sys.stdout),
            # 文件输出 (追加模式)
            logging.FileHandler(log_file_path, encoding="utf-8"),
        ],
    )
    
    # 设置第三方库日志级别
    # 避免第三方库产生过多日志,影响阅读
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # 不显示 SQL 语句
    logging.getLogger("httpx").setLevel(logging.WARNING)  # HTTP 客户端
    logging.getLogger("httpcore").setLevel(logging.WARNING)  # HTTP 核心
    
    # 记录日志系统初始化信息
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成 - 级别: {settings.LOG_LEVEL}, 文件: {settings.LOG_FILE}")
