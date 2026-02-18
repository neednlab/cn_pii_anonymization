"""
日志配置模块

使用Loguru配置统一的日志管理。
"""

import sys

from loguru import logger

from cn_pii_anonymization.config.settings import settings


def setup_logging() -> None:
    """
    配置日志系统

    移除默认处理器，添加控制台和文件处理器。
    如果 DEBUG=true，自动使用 DEBUG 日志级别。
    """
    logger.remove()

    log_level = "DEBUG" if settings.debug else settings.log_level

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        enqueue=True,
    )

    log_path = settings.log_file_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
    )

    logger.info(f"日志系统初始化完成，日志级别: {log_level}")


def get_logger(name: str = __name__):
    """
    获取带有模块名称的logger实例

    Args:
        name: 模块名称

    Returns:
        logger实例
    """
    return logger.bind(name=name)
