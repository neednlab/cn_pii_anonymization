"""API模块 - FastAPI应用和路由"""

from cn_pii_anonymization.api.app import app, create_app
from cn_pii_anonymization.api.middleware import CORSMiddleware, LoggingMiddleware
from cn_pii_anonymization.api.routes import text_router
from cn_pii_anonymization.api.schemas import (
    APIResponse,
    ErrorResponse,
    HealthCheckData,
    HealthCheckRequest,
    OperatorConfigRequest,
    PIIEntityResponse,
    SupportedEntitiesData,
    TextAnalyzeData,
    TextAnalyzeRequest,
    TextAnonymizeData,
    TextAnonymizeRequest,
)

__all__ = [
    "APIResponse",
    "CORSMiddleware",
    "ErrorResponse",
    "HealthCheckData",
    "HealthCheckRequest",
    "LoggingMiddleware",
    "OperatorConfigRequest",
    "PIIEntityResponse",
    "SupportedEntitiesData",
    "TextAnalyzeData",
    "TextAnalyzeRequest",
    "TextAnonymizeData",
    "TextAnonymizeRequest",
    "app",
    "create_app",
    "text_router",
]
