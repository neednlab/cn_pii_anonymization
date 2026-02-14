"""处理器模块 - 文本和图像PII处理"""

from cn_pii_anonymization.processors.image_processor import (
    ImagePIIEntity,
    ImageProcessor,
    ImageProcessResult,
)
from cn_pii_anonymization.processors.text_processor import (
    PIIEntity,
    TextProcessor,
    TextProcessResult,
)

__all__ = [
    "ImagePIIEntity",
    "ImageProcessResult",
    "ImageProcessor",
    "PIIEntity",
    "TextProcessResult",
    "TextProcessor",
]
