"""
图像处理集成测试

测试图像处理API端点。
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from cn_pii_anonymization.api.app import app
from cn_pii_anonymization.ocr.ocr_engine import OCRResult


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_image_bytes() -> bytes:
    """创建测试图像字节"""
    image = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def mock_ocr_result() -> OCRResult:
    """创建模拟OCR结果"""
    return OCRResult(
        text="测试文本 13812345678 测试完成",
        bounding_boxes=[
            ("测试文本", 10, 10, 80, 20),
            ("13812345678", 100, 10, 110, 20),
            ("测试完成", 220, 10, 80, 20),
        ],
        confidence=0.9,
    )


class TestImageMosaicStylesEndpoint:
    """马赛克样式端点测试"""

    def test_get_mosaic_styles(self, client: TestClient) -> None:
        """测试获取马赛克样式"""
        response = client.get("/api/v1/image/mosaic-styles")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "styles" in data["data"]
        assert len(data["data"]["styles"]) == 3


class TestImageAnalyzeEndpoint:
    """图像分析端点测试"""

    @patch("cn_pii_anonymization.core.image_redactor.CNTesseractOCREngine")
    def test_analyze_image(
        self,
        mock_ocr_class: MagicMock,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_result: OCRResult,
    ) -> None:
        """测试图像分析"""
        mock_ocr_instance = mock_ocr_class.return_value
        mock_ocr_instance.is_available.return_value = True
        mock_ocr_instance.recognize.return_value = mock_ocr_result

        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/analyze",
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "pii_entities" in data["data"]
        assert "has_pii" in data["data"]

    @patch("cn_pii_anonymization.core.image_redactor.CNTesseractOCREngine")
    def test_analyze_image_with_entities(
        self,
        mock_ocr_class: MagicMock,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_result: OCRResult,
    ) -> None:
        """测试带实体类型的图像分析"""
        mock_ocr_instance = mock_ocr_class.return_value
        mock_ocr_instance.is_available.return_value = True
        mock_ocr_instance.recognize.return_value = mock_ocr_result

        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/analyze",
            files=files,
            data={"entities": '["CN_PHONE_NUMBER"]'},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    def test_analyze_image_invalid_format(self, client: TestClient) -> None:
        """测试无效图像格式"""
        files = {"image": ("test.txt", b"not an image", "text/plain")}
        response = client.post(
            "/api/v1/image/analyze",
            files=files,
        )

        assert response.status_code == 400

    def test_analyze_image_invalid_entities(
        self,
        client: TestClient,
        sample_image_bytes: bytes,
    ) -> None:
        """测试无效实体类型格式"""
        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/analyze",
            files=files,
            data={"entities": "invalid json"},
        )

        assert response.status_code == 400


class TestImageAnonymizeEndpoint:
    """图像脱敏端点测试"""

    @patch("cn_pii_anonymization.core.image_redactor.CNTesseractOCREngine")
    def test_anonymize_image(
        self,
        mock_ocr_class: MagicMock,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_result: OCRResult,
    ) -> None:
        """测试图像脱敏"""
        mock_ocr_instance = mock_ocr_class.return_value
        mock_ocr_instance.is_available.return_value = True
        mock_ocr_instance.recognize.return_value = mock_ocr_result

        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/anonymize",
            files=files,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    @patch("cn_pii_anonymization.core.image_redactor.CNTesseractOCREngine")
    def test_anonymize_image_with_metadata(
        self,
        mock_ocr_class: MagicMock,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_result: OCRResult,
    ) -> None:
        """测试带元数据的图像脱敏"""
        mock_ocr_instance = mock_ocr_class.return_value
        mock_ocr_instance.is_available.return_value = True
        mock_ocr_instance.recognize.return_value = mock_ocr_result

        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/anonymize",
            files=files,
            data={"return_metadata": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "pii_entities" in data["data"]

    @patch("cn_pii_anonymization.core.image_redactor.CNTesseractOCREngine")
    def test_anonymize_image_with_blur(
        self,
        mock_ocr_class: MagicMock,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_result: OCRResult,
    ) -> None:
        """测试模糊马赛克"""
        mock_ocr_instance = mock_ocr_class.return_value
        mock_ocr_instance.is_available.return_value = True
        mock_ocr_instance.recognize.return_value = mock_ocr_result

        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/anonymize",
            files=files,
            data={"mosaic_style": "blur"},
        )

        assert response.status_code == 200

    @patch("cn_pii_anonymization.core.image_redactor.CNTesseractOCREngine")
    def test_anonymize_image_with_fill(
        self,
        mock_ocr_class: MagicMock,
        client: TestClient,
        sample_image_bytes: bytes,
        mock_ocr_result: OCRResult,
    ) -> None:
        """测试纯色填充"""
        mock_ocr_instance = mock_ocr_class.return_value
        mock_ocr_instance.is_available.return_value = True
        mock_ocr_instance.recognize.return_value = mock_ocr_result

        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/anonymize",
            files=files,
            data={
                "mosaic_style": "fill",
                "fill_color": "128,128,128",
            },
        )

        assert response.status_code == 200

    def test_anonymize_image_invalid_fill_color(
        self,
        client: TestClient,
        sample_image_bytes: bytes,
    ) -> None:
        """测试无效填充颜色"""
        files = {"image": ("test.png", sample_image_bytes, "image/png")}
        response = client.post(
            "/api/v1/image/anonymize",
            files=files,
            data={
                "mosaic_style": "fill",
                "fill_color": "invalid",
            },
        )

        assert response.status_code == 400

    def test_anonymize_image_invalid_format(self, client: TestClient) -> None:
        """测试无效图像格式"""
        files = {"image": ("test.txt", b"not an image", "text/plain")}
        response = client.post(
            "/api/v1/image/anonymize",
            files=files,
        )

        assert response.status_code == 400
