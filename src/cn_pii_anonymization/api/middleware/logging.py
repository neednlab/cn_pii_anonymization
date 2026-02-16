"""
日志中间件

提供请求日志记录功能。
"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件

    记录所有HTTP请求的详细信息，包括请求方法、路径、状态码和处理时间。

    Example:
        >>> app = FastAPI()
        >>> app.add_middleware(LoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录日志

        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理函数

        Returns:
            HTTP响应对象
        """
        start_time = time.time()

        request_id = id(request)
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        logger.info(f"[{request_id}] 请求开始: {method} {url} - 客户端: {client_host}")

        try:
            response = await call_next(request)

            process_time = time.time() - start_time
            status_code = response.status_code

            log_level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"
            getattr(logger, log_level)(
                f"[{request_id}] 请求完成: {method} {url} - "
                f"状态码: {status_code} - 耗时: {process_time:.3f}s"
            )

            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-Request-ID"] = str(request_id)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] 请求异常: {method} {url} - 错误: {e} - 耗时: {process_time:.3f}s"
            )
            raise


class CORSMiddleware:
    """
    CORS中间件配置辅助类

    提供CORS中间件的配置选项。
    """

    @staticmethod
    def get_config() -> dict:
        """
        获取CORS配置

        Returns:
            CORS配置字典
        """
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
