"""
FastAPI应用入口

提供API服务的入口点，配置中间件和路由。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cn_pii_anonymization.api.middleware import LoggingMiddleware
from cn_pii_anonymization.api.routes import image_router, text_router
from cn_pii_anonymization.api.schemas import APIResponse, ErrorResponse, HealthCheckData
from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.utils.exceptions import CNPIIError
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    在应用启动时初始化资源，在应用关闭时清理资源。
    """
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    logger.info(f"调试模式: {settings.debug}")
    logger.info(f"日志级别: {settings.log_level}")

    yield

    logger.info(f"关闭 {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    description="中国个人信息脱敏API - 识别和处理中国大陆个人身份信息",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(text_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")


@app.exception_handler(CNPIIError)
async def pii_exception_handler(request: Request, exc: CNPIIError) -> JSONResponse:
    """
    PII异常处理器

    统一处理所有CNPIIError异常，返回标准错误响应。
    """
    logger.error(f"PII处理错误: {exc.message}")
    error_response = ErrorResponse(
        code=400,
        message=exc.message,
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=400,
        content=error_response.model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP异常处理器

    统一处理HTTPException异常。
    """
    error_response = ErrorResponse(
        code=exc.status_code,
        message=exc.detail,
        error_type="HTTPException",
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器

    处理所有未捕获的异常，返回标准错误响应。
    """
    logger.exception(f"未处理的异常: {exc}")
    error_response = ErrorResponse(
        code=500,
        message=str(exc) if settings.debug else "服务器内部错误",
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


@app.get(
    "/health",
    response_model=APIResponse,
    tags=["系统"],
    summary="健康检查",
    description="检查服务是否正常运行",
)
async def health_check() -> APIResponse:
    """
    健康检查接口

    Returns:
        APIResponse: 包含服务状态信息
    """
    data = HealthCheckData(
        status="healthy",
        version=settings.app_version,
        nlp_engine="loaded",
    )
    return APIResponse(code=200, message="success", data=data)


@app.get(
    "/",
    response_model=APIResponse,
    tags=["系统"],
    summary="根路径",
    description="返回API基本信息",
)
async def root() -> APIResponse:
    """
    根路径接口

    Returns:
        APIResponse: 包含API基本信息
    """
    return APIResponse(
        code=200,
        message="success",
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        },
    )


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例

    用于生产环境部署时使用。

    Returns:
        FastAPI: 应用实例
    """
    return app
