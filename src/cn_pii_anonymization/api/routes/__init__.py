"""API路由模块"""

from cn_pii_anonymization.api.routes.image import router as image_router
from cn_pii_anonymization.api.routes.text import router as text_router

__all__ = ["text_router", "image_router"]
