"""
OCR引擎单元测试

测试PaddleOCR引擎的功能。
"""

from dataclasses import asdict
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from cn_pii_anonymization.ocr.ocr_engine import (
    CNTesseractOCREngine,
    OCRResult,
    PaddleOCREngine,
)
from cn_pii_anonymization.utils.exceptions import OCRError


class TestOCRResult:
    """OCR结果数据类测试"""

    def test_init(self):
        """测试初始化"""
        result = OCRResult(
            text="测试文本",
            bounding_boxes=[("测试", 10, 20, 30, 40)],
            confidence=0.9,
        )

        assert result.text == "测试文本"
        assert len(result.bounding_boxes) == 1
        assert result.confidence == 0.9

    def test_to_dict(self):
        """测试转换为字典"""
        result = OCRResult(
            text="测试文本",
            bounding_boxes=[("测试", 10, 20, 30, 40)],
            confidence=0.9,
        )

        result_dict = result.to_dict()

        assert result_dict["text"] == "测试文本"
        assert result_dict["confidence"] == 0.9
        assert len(result_dict["bounding_boxes"]) == 1
        assert result_dict["bounding_boxes"][0]["text"] == "测试"
        assert result_dict["bounding_boxes"][0]["left"] == 10

    def test_default_confidence(self):
        """测试默认置信度"""
        result = OCRResult(text="测试", bounding_boxes=[])

        assert result.confidence == 0.0


class TestPaddleOCREngine:
    """PaddleOCR引擎测试"""

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """创建测试图像"""
        return Image.new("RGB", (200, 100), color=(255, 255, 255))

    @pytest.fixture
    def mock_ocr_result(self) -> list:
        """创建模拟OCR结果"""
        return [
            [
                [
                    [[10, 10], [50, 10], [50, 30], [10, 30]],
                    ["测试文本", 0.95],
                ],
                [
                    [[60, 10], [140, 10], [140, 30], [60, 30]],
                    ["13812345678", 0.98],
                ],
            ]
        ]

    def test_init(self):
        """测试初始化"""
        engine = PaddleOCREngine()

        assert engine._language == "ch"
        assert engine._use_gpu is False
        assert engine._use_angle_cls is True

    def test_init_with_custom_params(self):
        """测试自定义参数初始化"""
        engine = PaddleOCREngine(
            language="en",
            use_gpu=True,
            use_angle_cls=False,
        )

        assert engine._language == "en"
        assert engine._use_gpu is True
        assert engine._use_angle_cls is False

    def test_is_available_true(self):
        """测试OCR引擎可用"""
        mock_paddleocr = MagicMock()

        with patch.dict(
            "sys.modules",
            {"paddleocr": MagicMock(PaddleOCR=mock_paddleocr)},
        ):
            engine = PaddleOCREngine()
            engine._available = None
            result = engine.is_available()

            assert result is True

    def test_is_available_false(self):
        """测试OCR引擎不可用"""
        with patch.dict(
            "sys.modules",
            {
                "paddleocr": MagicMock(
                    PaddleOCR=MagicMock(side_effect=Exception("Not found"))
                )
            },
        ):
            engine = PaddleOCREngine()
            engine._available = None
            result = engine.is_available()

            assert result is False

    def test_recognize(self, sample_image, mock_ocr_result):
        """测试OCR识别"""
        mock_paddle_instance = MagicMock()
        mock_paddle_instance.ocr.return_value = mock_ocr_result

        with patch.dict(
            "sys.modules",
            {"paddleocr": MagicMock(PaddleOCR=MagicMock(return_value=mock_paddle_instance))},
        ):
            engine = PaddleOCREngine()
            result = engine.recognize(sample_image)

            assert "测试文本" in result.text
            assert len(result.bounding_boxes) == 2
            assert result.bounding_boxes[0][0] == "测试文本"
            assert result.confidence > 0

    def test_recognize_empty_result(self, sample_image):
        """测试OCR识别空结果"""
        mock_paddle_instance = MagicMock()
        mock_paddle_instance.ocr.return_value = [None]

        with patch.dict(
            "sys.modules",
            {"paddleocr": MagicMock(PaddleOCR=MagicMock(return_value=mock_paddle_instance))},
        ):
            engine = PaddleOCREngine()
            result = engine.recognize(sample_image)

            assert result.text == ""
            assert len(result.bounding_boxes) == 0
            assert result.confidence == 0.0

    def test_recognize_with_error(self, sample_image):
        """测试OCR识别错误"""
        mock_paddle_instance = MagicMock()
        mock_paddle_instance.ocr.side_effect = Exception("OCR Error")

        with patch.dict(
            "sys.modules",
            {"paddleocr": MagicMock(PaddleOCR=MagicMock(return_value=mock_paddle_instance))},
        ):
            engine = PaddleOCREngine()

            with pytest.raises(OCRError):
                engine.recognize(sample_image)

    def test_parse_result(self):
        """测试结果解析"""
        engine = PaddleOCREngine()

        result = [
            [
                [
                    [[10, 10], [50, 10], [50, 30], [10, 30]],
                    ["测试", 0.95],
                ],
                [
                    [[60, 10], [140, 10], [140, 30], [60, 30]],
                    ["文本", 0.85],
                ],
            ]
        ]

        text, boxes, confidence = engine._parse_result(result)

        assert text == "测试\n文本"
        assert len(boxes) == 2
        assert boxes[0][0] == "测试"
        assert boxes[1][0] == "文本"
        assert confidence == pytest.approx(0.9, rel=0.1)

    def test_parse_result_empty(self):
        """测试空结果解析"""
        engine = PaddleOCREngine()

        text, boxes, confidence = engine._parse_result(None)

        assert text == ""
        assert boxes == []
        assert confidence == 0.0

    def test_get_supported_languages(self):
        """测试获取支持的语言"""
        engine = PaddleOCREngine()
        langs = engine.get_supported_languages()

        assert "ch" in langs
        assert "en" in langs
        assert "korean" in langs
        assert "japan" in langs

    def test_grayscale_image_conversion(self):
        """测试灰度图像转换"""
        gray_image = Image.new("L", (200, 100), color=128)

        mock_paddle_instance = MagicMock()
        mock_paddle_instance.ocr.return_value = [None]

        with patch.dict(
            "sys.modules",
            {"paddleocr": MagicMock(PaddleOCR=MagicMock(return_value=mock_paddle_instance))},
        ):
            engine = PaddleOCREngine()
            result = engine.recognize(gray_image)

            assert result is not None

    def test_rgba_image_conversion(self):
        """测试RGBA图像转换"""
        rgba_image = Image.new("RGBA", (200, 100), color=(255, 255, 255, 255))

        mock_paddle_instance = MagicMock()
        mock_paddle_instance.ocr.return_value = [None]

        with patch.dict(
            "sys.modules",
            {"paddleocr": MagicMock(PaddleOCR=MagicMock(return_value=mock_paddle_instance))},
        ):
            engine = PaddleOCREngine()
            result = engine.recognize(rgba_image)

            assert result is not None


class TestCNTesseractOCREngine:
    """中文Tesseract OCR引擎测试（已弃用）"""

    def test_deprecated_warning(self):
        """测试弃用警告"""
        engine = CNTesseractOCREngine()

        assert engine.is_available() is False

    def test_recognize_raises_error(self):
        """测试识别方法抛出错误"""
        engine = CNTesseractOCREngine()
        image = Image.new("RGB", (200, 100), color=(255, 255, 255))

        with pytest.raises(OCRError) as exc_info:
            engine.recognize(image)

        assert "已弃用" in str(exc_info.value)


class TestOCREngineCaching:
    """OCR引擎缓存测试"""

    def test_availability_cache(self):
        """测试可用性缓存"""
        engine = PaddleOCREngine()

        engine._available = True

        assert engine.is_available() is True

        engine._available = False

        assert engine.is_available() is False
