"""
OCR模块

提供OCR识别能力，封装Tesseract OCR引擎。
"""

from cn_pii_anonymization.ocr.ocr_engine import CNTesseractOCREngine, OCREngine

__all__ = ["CNTesseractOCREngine", "OCREngine"]
