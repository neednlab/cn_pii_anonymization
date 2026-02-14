"""
OCR引擎单元测试

测试OCR引擎的功能。
"""

from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from cn_pii_anonymization.ocr.ocr_engine import CNTesseractOCREngine, OCRResult


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


class TestCNTesseractOCREngine:
    """中文Tesseract OCR引擎测试"""

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """创建测试图像"""
        return Image.new("RGB", (200, 100), color=(255, 255, 255))

    @pytest.fixture
    def mock_ocr_data(self) -> dict:
        """创建模拟OCR数据"""
        return {
            "text": ["测试", "文本", "", "13812345678"],
            "left": [10, 60, 0, 110],
            "top": [10, 10, 0, 10],
            "width": [40, 40, 0, 80],
            "height": [20, 20, 0, 20],
            "conf": [90, 85, -1, 95],
        }

    def test_init(self):
        """测试初始化"""
        engine = CNTesseractOCREngine()

        assert engine._language == "chi_sim+eng"
        assert engine._config == "--psm 6 --oem 3"

    def test_init_with_custom_params(self):
        """测试自定义参数初始化"""
        engine = CNTesseractOCREngine(
            language="eng",
            config="--psm 3",
        )

        assert engine._language == "eng"
        assert engine._config == "--psm 3"

    def test_is_available_true(self):
        """测试OCR引擎可用"""
        with patch.dict(
            "sys.modules",
            {"pytesseract": MagicMock(get_tesseract_version=MagicMock(return_value="5.3.0"))},
        ):
            engine = CNTesseractOCREngine()
            engine._tesseract_available = None
            result = engine.is_available()

            assert result is True

    def test_is_available_false(self):
        """测试OCR引擎不可用"""
        with patch.dict(
            "sys.modules",
            {"pytesseract": MagicMock(get_tesseract_version=MagicMock(side_effect=Exception("Not found")))},
        ):
            engine = CNTesseractOCREngine()
            engine._tesseract_available = None
            result = engine.is_available()

            assert result is False

    def test_recognize(self, sample_image, mock_ocr_data):
        """测试OCR识别"""
        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_data.return_value = mock_ocr_data
        mock_pytesseract.image_to_string.return_value = "测试文本 13812345678"
        mock_pytesseract.Output.DICT = "dict"

        with patch.dict("sys.modules", {"pytesseract": mock_pytesseract}):
            engine = CNTesseractOCREngine()
            result = engine.recognize(sample_image)

            assert result.text == "测试文本 13812345678"
            assert len(result.bounding_boxes) == 3
            assert result.bounding_boxes[0] == ("测试", 10, 10, 40, 20)

    def test_recognize_with_error(self, sample_image):
        """测试OCR识别错误"""
        from cn_pii_anonymization.utils.exceptions import OCRError

        mock_pytesseract = MagicMock()
        mock_pytesseract.TesseractError = Exception
        mock_pytesseract.image_to_data.side_effect = Exception("OCR Error")

        with patch.dict("sys.modules", {"pytesseract": mock_pytesseract}):
            engine = CNTesseractOCREngine()

            with pytest.raises(OCRError):
                engine.recognize(sample_image)

    def test_extract_bounding_boxes(self):
        """测试边界框提取"""
        engine = CNTesseractOCREngine()

        data = {
            "text": ["测试", "", "文本"],
            "left": [10, 0, 60],
            "top": [10, 0, 10],
            "width": [40, 0, 40],
            "height": [20, 0, 20],
            "conf": [90, -1, 85],
        }

        boxes = engine._extract_bounding_boxes(data)

        assert len(boxes) == 2
        assert boxes[0] == ("测试", 10, 10, 40, 20)
        assert boxes[1] == ("文本", 60, 10, 40, 20)

    def test_calculate_confidence(self):
        """测试置信度计算"""
        engine = CNTesseractOCREngine()

        data = {
            "text": ["测试", "文本"],
            "conf": [90, 80],
        }

        confidence = engine._calculate_confidence(data)

        assert confidence == 0.85

    def test_calculate_confidence_empty(self):
        """测试空数据置信度计算"""
        engine = CNTesseractOCREngine()

        data = {
            "text": [],
            "conf": [],
        }

        confidence = engine._calculate_confidence(data)

        assert confidence == 0.0

    def test_get_supported_languages(self):
        """测试获取支持的语言"""
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_languages.return_value = ["chi_sim", "eng", "chi_tra"]

        with patch.dict("sys.modules", {"pytesseract": mock_pytesseract}):
            engine = CNTesseractOCREngine()
            langs = engine.get_supported_languages()

            assert "chi_sim" in langs
            assert "eng" in langs

    def test_get_supported_languages_error(self):
        """测试获取语言列表错误"""
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_languages.side_effect = Exception("Error")

        with patch.dict("sys.modules", {"pytesseract": mock_pytesseract}):
            engine = CNTesseractOCREngine()
            langs = engine.get_supported_languages()

            assert langs == []


class TestOCREngineCaching:
    """OCR引擎缓存测试"""

    def test_availability_cache(self):
        """测试可用性缓存"""
        engine = CNTesseractOCREngine()

        engine._tesseract_available = True

        assert engine.is_available() is True

        engine._tesseract_available = False

        assert engine.is_available() is False
