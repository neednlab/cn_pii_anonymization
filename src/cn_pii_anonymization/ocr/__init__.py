"""
OCR模块

提供OCR识别能力，封装PaddleOCR引擎。
"""

from cn_pii_anonymization.ocr.ocr_engine import (
    BaseOCREngine,
    CNTesseractOCREngine,
    OCRResult,
    PaddleOCREngine,
)

__all__ = ["BaseOCREngine", "CNTesseractOCREngine", "OCRResult", "PaddleOCREngine"]
