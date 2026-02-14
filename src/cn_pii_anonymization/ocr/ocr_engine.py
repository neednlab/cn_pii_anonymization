"""
OCR引擎模块

封装Tesseract OCR引擎，提供中文OCR识别能力。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from PIL import Image

from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.utils.exceptions import OCRError
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OCRResult:
    """
    OCR识别结果

    Attributes:
        text: 识别出的文本
        bounding_boxes: 文本边界框列表，每个元素为 (text, left, top, width, height)
        confidence: 整体置信度
    """

    text: str
    bounding_boxes: list[tuple[str, int, int, int, int]]
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "text": self.text,
            "bounding_boxes": [
                {
                    "text": bb[0],
                    "left": bb[1],
                    "top": bb[2],
                    "width": bb[3],
                    "height": bb[4],
                }
                for bb in self.bounding_boxes
            ],
            "confidence": self.confidence,
        }


class OCREngine(ABC):
    """
    OCR引擎抽象基类

    定义OCR引擎的接口规范。
    """

    @abstractmethod
    def recognize(self, image: Image.Image) -> OCRResult:
        """
        识别图像中的文本

        Args:
            image: PIL图像对象

        Returns:
            OCRResult: OCR识别结果

        Raises:
            OCRError: OCR识别失败时抛出
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查OCR引擎是否可用

        Returns:
            bool: 是否可用
        """
        pass


class CNTesseractOCREngine(OCREngine):
    """
    中文Tesseract OCR引擎

    封装pytesseract，提供中文OCR识别能力。

    Attributes:
        language: OCR语言设置
        config: Tesseract配置参数

    Example:
        >>> engine = CNTesseractOCREngine()
        >>> if engine.is_available():
        ...     result = engine.recognize(image)
        ...     print(result.text)
    """

    def __init__(
        self,
        language: str = "chi_sim+eng",
        config: str = "--psm 6 --oem 3",
    ) -> None:
        """
        初始化OCR引擎

        Args:
            language: OCR语言，默认中文简体+英文
            config: Tesseract配置参数
        """
        self._language = language
        self._config = config
        self._tesseract_available: bool | None = None

        if settings.tesseract_path:
            self._setup_tesseract_path()

        logger.debug(f"OCR引擎初始化: language={language}, config={config}")

    def _setup_tesseract_path(self) -> None:
        """设置Tesseract可执行文件路径"""
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
        logger.info(f"Tesseract路径已设置: {settings.tesseract_path}")

    def recognize(self, image: Image.Image) -> OCRResult:
        """
        识别图像中的文本

        Args:
            image: PIL图像对象

        Returns:
            OCRResult: OCR识别结果

        Raises:
            OCRError: OCR识别失败时抛出
        """
        import pytesseract
        from pytesseract import TesseractError

        try:
            logger.debug(f"开始OCR识别，图像尺寸: {image.size}")

            data = pytesseract.image_to_data(
                image,
                lang=self._language,
                config=self._config,
                output_type=pytesseract.Output.DICT,
            )

            text = pytesseract.image_to_string(
                image,
                lang=self._language,
                config=self._config,
            ).strip()

            bounding_boxes = self._extract_bounding_boxes(data)

            confidence = self._calculate_confidence(data)

            result = OCRResult(
                text=text,
                bounding_boxes=bounding_boxes,
                confidence=confidence,
            )

            logger.debug(f"OCR识别完成，文本长度: {len(text)}，边界框数量: {len(bounding_boxes)}")

            return result

        except TesseractError as e:
            logger.error(f"OCR识别失败: {e}")
            raise OCRError(f"OCR识别失败: {e}") from e
        except Exception as e:
            logger.error(f"OCR处理异常: {e}")
            raise OCRError(f"OCR处理异常: {e}") from e

    def _extract_bounding_boxes(
        self,
        data: dict[str, Any],
    ) -> list[tuple[str, int, int, int, int]]:
        """
        从OCR数据中提取边界框

        Args:
            data: pytesseract返回的数据字典

        Returns:
            边界框列表，每个元素为 (text, left, top, width, height)
        """
        bounding_boxes = []

        n_boxes = len(data.get("text", []))
        for i in range(n_boxes):
            text = data["text"][i].strip()
            if not text:
                continue

            conf = data.get("conf", [0] * n_boxes)[i]
            if conf < 0:
                continue

            left = data["left"][i]
            top = data["top"][i]
            width = data["width"][i]
            height = data["height"][i]

            bounding_boxes.append((text, left, top, width, height))

        return bounding_boxes

    def _calculate_confidence(self, data: dict[str, Any]) -> float:
        """
        计算整体置信度

        Args:
            data: pytesseract返回的数据字典

        Returns:
            平均置信度 (0-1)
        """
        confidences = []
        n_boxes = len(data.get("text", []))

        for i in range(n_boxes):
            conf = data.get("conf", [0] * n_boxes)[i]
            if conf > 0:
                confidences.append(conf)

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences) / 100.0

    def is_available(self) -> bool:
        """
        检查Tesseract是否可用

        Returns:
            bool: 是否可用
        """
        if self._tesseract_available is not None:
            return self._tesseract_available

        try:
            import pytesseract

            version = pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info(f"Tesseract版本: {version}")
            return True
        except Exception as e:
            self._tesseract_available = False
            logger.warning(f"Tesseract不可用: {e}")
            return False

    def get_supported_languages(self) -> list[str]:
        """
        获取支持的语言列表

        Returns:
            支持的语言代码列表
        """
        import pytesseract

        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.error(f"获取语言列表失败: {e}")
            return []
