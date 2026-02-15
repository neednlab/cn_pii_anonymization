"""
图像处理器模块

提供图像PII识别和脱敏处理的完整流程。
"""

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from PIL import Image

from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.core.image_redactor import CNPIIImageRedactorEngine
from cn_pii_anonymization.ocr.ocr_engine import OCRResult
from cn_pii_anonymization.operators.mosaic_operator import MosaicStyle
from cn_pii_anonymization.utils.exceptions import UnsupportedImageFormatError
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ImagePIIEntity:
    """
    图像PII实体信息

    Attributes:
        entity_type: 实体类型
        text: 识别出的文本
        bbox: 边界框 (left, top, width, height)
        score: 置信度分数
    """

    entity_type: str
    text: str
    bbox: tuple[int, int, int, int]
    score: float

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "entity_type": self.entity_type,
            "text": self.text,
            "bbox": {
                "left": self.bbox[0],
                "top": self.bbox[1],
                "width": self.bbox[2],
                "height": self.bbox[3],
            },
            "score": self.score,
        }


@dataclass
class ImageProcessResult:
    """
    图像处理结果

    Attributes:
        original_image: 原始图像
        processed_image: 处理后的图像
        pii_entities: 识别出的PII实体列表
        ocr_result: OCR识别结果
    """

    original_image: Image.Image
    processed_image: Image.Image
    pii_entities: list[ImagePIIEntity] = field(default_factory=list)
    ocr_result: OCRResult | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（不包含图像数据）"""
        return {
            "pii_entities": [e.to_dict() for e in self.pii_entities],
            "ocr_text": self.ocr_result.text if self.ocr_result else "",
            "ocr_confidence": self.ocr_result.confidence if self.ocr_result else 0.0,
        }

    @property
    def has_pii(self) -> bool:
        """是否包含PII"""
        return len(self.pii_entities) > 0

    def save_processed_image(
        self,
        filepath: str,
        format: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        保存处理后的图像

        Args:
            filepath: 保存路径
            format: 图像格式，None时根据文件扩展名推断
            **kwargs: 传递给PIL.Image.save的参数
        """
        self.processed_image.save(filepath, format=format, **kwargs)
        logger.info(f"图像已保存: {filepath}")

    def get_processed_image_bytes(
        self,
        format: str = "PNG",
        **kwargs: Any,
    ) -> bytes:
        """
        获取处理后的图像字节

        Args:
            format: 图像格式
            **kwargs: 传递给PIL.Image.save的参数

        Returns:
            图像字节数据
        """
        buffer = BytesIO()
        self.processed_image.save(buffer, format=format, **kwargs)
        buffer.seek(0)
        return buffer.getvalue()


class ImageProcessor:
    """
    图像PII处理器

    整合图像脱敏引擎，提供完整的图像PII处理流程。

    Example:
        >>> processor = ImageProcessor()
        >>> image = Image.open("document.png")
        >>> result = processor.process(image)
        >>> result.save_processed_image("redacted_document.png")
    """

    def __init__(
        self,
        redactor: CNPIIImageRedactorEngine | None = None,
    ) -> None:
        """
        初始化图像处理器

        Args:
            redactor: 图像脱敏引擎实例，None时自动创建
        """
        self._redactor = redactor or CNPIIImageRedactorEngine()

    def process(
        self,
        image: Image.Image,
        mosaic_style: str | MosaicStyle = MosaicStyle.PIXEL,
        fill_color: tuple[int, int, int] = (0, 0, 0),
        entities: list[str] | None = None,
        allow_list: list[str] | None = None,
        score_threshold: float | None = None,
        **mosaic_kwargs: Any,
    ) -> ImageProcessResult:
        """
        处理图像中的PII

        Args:
            image: 输入图像
            mosaic_style: 马赛克样式 (pixel/blur/fill)
            fill_color: 纯色填充颜色 (R, G, B)
            entities: 要识别的PII类型列表，None表示识别所有类型
            allow_list: 白名单列表
            score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值
            **mosaic_kwargs: 马赛克操作符参数

        Returns:
            ImageProcessResult: 处理结果

        Example:
            >>> processor = ImageProcessor()
            >>> image = Image.open("id_card.png")
            >>> result = processor.process(
            ...     image,
            ...     mosaic_style="blur",
            ...     entities=["CN_PHONE_NUMBER", "CN_ID_CARD"]
            ... )
        """
        logger.info(f"开始处理图像，尺寸: {image.size}")

        processed_image = self._redactor.redact(
            image=image,
            mosaic_style=mosaic_style,
            fill_color=fill_color,
            entities=entities,
            allow_list=allow_list,
            score_threshold=score_threshold,
            **mosaic_kwargs,
        )

        ocr_result = self._redactor.get_ocr_result()

        pii_entities = self._build_pii_entities(ocr_result, entities, score_threshold)

        result = ImageProcessResult(
            original_image=image,
            processed_image=processed_image,
            pii_entities=pii_entities,
            ocr_result=ocr_result,
        )

        logger.info(f"图像处理完成，发现 {len(pii_entities)} 个PII实体")
        return result

    def process_file(
        self,
        filepath: str,
        mosaic_style: str | MosaicStyle = MosaicStyle.PIXEL,
        fill_color: tuple[int, int, int] = (0, 0, 0),
        entities: list[str] | None = None,
        allow_list: list[str] | None = None,
        score_threshold: float | None = None,
        **mosaic_kwargs: Any,
    ) -> ImageProcessResult:
        """
        处理图像文件中的PII

        Args:
            filepath: 图像文件路径
            mosaic_style: 马赛克样式
            fill_color: 纯色填充颜色
            entities: 要识别的PII类型列表
            allow_list: 白名单列表
            score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值
            **mosaic_kwargs: 马赛克操作符参数

        Returns:
            ImageProcessResult: 处理结果

        Raises:
            UnsupportedImageFormatError: 图像格式不支持时抛出
        """
        self._validate_image_format(filepath)

        logger.info(f"加载图像文件: {filepath}")
        image = Image.open(filepath)

        return self.process(
            image=image,
            mosaic_style=mosaic_style,
            fill_color=fill_color,
            entities=entities,
            allow_list=allow_list,
            score_threshold=score_threshold,
            **mosaic_kwargs,
        )

    def process_bytes(
        self,
        image_bytes: bytes,
        mosaic_style: str | MosaicStyle = MosaicStyle.PIXEL,
        fill_color: tuple[int, int, int] = (0, 0, 0),
        entities: list[str] | None = None,
        allow_list: list[str] | None = None,
        score_threshold: float | None = None,
        **mosaic_kwargs: Any,
    ) -> ImageProcessResult:
        """
        处理图像字节数据中的PII

        Args:
            image_bytes: 图像字节数据
            mosaic_style: 马赛克样式
            fill_color: 纯色填充颜色
            entities: 要识别的PII类型列表
            allow_list: 白名单列表
            score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值
            **mosaic_kwargs: 马赛克操作符参数

        Returns:
            ImageProcessResult: 处理结果
        """
        self._validate_image_size(image_bytes)

        image = Image.open(BytesIO(image_bytes))

        return self.process(
            image=image,
            mosaic_style=mosaic_style,
            fill_color=fill_color,
            entities=entities,
            allow_list=allow_list,
            score_threshold=score_threshold,
            **mosaic_kwargs,
        )

    def analyze_only(
        self,
        image: Image.Image,
        entities: list[str] | None = None,
        allow_list: list[str] | None = None,
        score_threshold: float | None = None,
    ) -> list[ImagePIIEntity]:
        """
        仅分析图像中的PII，不进行脱敏

        Args:
            image: 输入图像
            entities: 要识别的PII类型列表
            allow_list: 白名单列表
            score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值

        Returns:
            PII实体列表
        """
        self._redactor.redact(
            image=image,
            mosaic_style=MosaicStyle.FILL,
            fill_color=(0, 0, 0),
            entities=entities,
            allow_list=allow_list,
            score_threshold=score_threshold,
        )

        ocr_result = self._redactor.get_ocr_result()
        return self._build_pii_entities(ocr_result, entities, score_threshold)

    def _build_pii_entities(
        self,
        ocr_result: OCRResult | None,
        entities: list[str] | None,
        score_threshold: float | None,
    ) -> list[ImagePIIEntity]:
        """
        构建PII实体列表

        Args:
            ocr_result: OCR识别结果
            entities: 要识别的PII类型列表
            score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值

        Returns:
            PII实体列表
        """
        if not ocr_result:
            return []

        pii_entities: list[ImagePIIEntity] = []

        from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine

        analyzer = CNPIIAnalyzerEngine()

        for text, left, top, width, height in ocr_result.bounding_boxes:
            analyzer_results = analyzer.analyze(
                text=text,
                entities=entities,
                score_threshold=score_threshold,
            )

            for result in analyzer_results:
                entity = ImagePIIEntity(
                    entity_type=result.entity_type,
                    text=text,
                    bbox=(left, top, width, height),
                    score=result.score,
                )
                pii_entities.append(entity)

        return pii_entities

    def _validate_image_format(self, filepath: str) -> None:
        """
        验证图像格式

        Args:
            filepath: 图像文件路径

        Raises:
            UnsupportedImageFormatError: 图像格式不支持时抛出
        """
        ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""

        if ext not in settings.supported_image_formats:
            raise UnsupportedImageFormatError(
                f"不支持的图像格式: {ext}。"
                f"支持的格式: {', '.join(settings.supported_image_formats)}"
            )

    def _validate_image_size(self, image_bytes: bytes) -> None:
        """
        验证图像大小

        Args:
            image_bytes: 图像字节数据

        Raises:
            UnsupportedImageFormatError: 图像过大时抛出
        """
        size = len(image_bytes)
        if size > settings.max_image_size:
            max_size_mb = settings.max_image_size / (1024 * 1024)
            actual_size_mb = size / (1024 * 1024)
            raise UnsupportedImageFormatError(
                f"图像大小超出限制: {actual_size_mb:.2f}MB > {max_size_mb:.2f}MB"
            )

    def get_supported_entities(self) -> list[str]:
        """获取支持的PII实体类型列表"""
        return self._redactor.get_supported_entities()
