"""
图像脱敏引擎模块

封装Presidio ImageRedactorEngine，提供图像PII识别和脱敏能力。
"""

from typing import Any

from PIL import Image

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.ocr.ocr_engine import OCRResult, PaddleOCREngine
from cn_pii_anonymization.operators.mosaic_operator import (
    MosaicStyle,
    create_mosaic_operator,
)
from cn_pii_anonymization.utils.exceptions import OCRError, PIIRecognitionError
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNPIIImageRedactorEngine:
    """
    中文PII图像脱敏引擎

    整合OCR识别、PII分析和图像脱敏功能，提供完整的图像PII处理能力。

    Attributes:
        _analyzer: PII分析器引擎
        _ocr_engine: OCR引擎
        _ocr_result_cache: OCR结果缓存

    Example:
        >>> engine = CNPIIImageRedactorEngine()
        >>> image = Image.open("document.png")
        >>> result = engine.redact(image)
        >>> result.save("redacted_document.png")
    """

    _instance: "CNPIIImageRedactorEngine | None" = None
    _initialized: bool = False

    def __new__(cls) -> "CNPIIImageRedactorEngine":
        """单例模式，确保全局只有一个图像脱敏实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化图像脱敏引擎"""
        if CNPIIImageRedactorEngine._initialized:
            return

        logger.info("初始化中文PII图像脱敏引擎...")
        self._analyzer = CNPIIAnalyzerEngine()
        self._ocr_engine = PaddleOCREngine()
        self._ocr_result_cache: OCRResult | None = None
        self._pii_bboxes_cache: list[tuple[str, str, int, int, int, int, float]] = []
        CNPIIImageRedactorEngine._initialized = True
        logger.info("中文PII图像脱敏引擎初始化完成")

    def redact(
        self,
        image: Image.Image,
        mosaic_style: str | MosaicStyle = MosaicStyle.PIXEL,
        fill_color: tuple[int, int, int] = (0, 0, 0),
        entities: list[str] | None = None,
        allow_list: list[str] | None = None,
        score_threshold: float | None = None,
        **mosaic_kwargs: Any,
    ) -> Image.Image:
        """
        对图像中的PII进行脱敏处理

        Args:
            image: PIL图像对象
            mosaic_style: 马赛克样式 (pixel/blur/fill)
            fill_color: 纯色填充颜色 (R, G, B)
            entities: 要识别的PII类型列表，None表示识别所有类型
            allow_list: 白名单列表，匹配的内容将被排除
            score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值
            **mosaic_kwargs: 马赛克操作符参数

        Returns:
            处理后的图像

        Raises:
            OCRError: OCR识别失败时抛出
            PIIRecognitionError: PII识别失败时抛出

        Example:
            >>> engine = CNPIIImageRedactorEngine()
            >>> image = Image.open("id_card.png")
            >>> redacted = engine.redact(image, mosaic_style="blur")
        """
        logger.info(f"开始图像脱敏处理，图像尺寸: {image.size}")

        if not self._ocr_engine.is_available():
            raise OCRError("OCR引擎不可用，请确保已正确安装PaddleOCR")

        ocr_result = self._perform_ocr(image)
        self._ocr_result_cache = ocr_result

        pii_bboxes = self._analyze_ocr_result(
            ocr_result=ocr_result,
            entities=entities,
            allow_list=allow_list,
            score_threshold=score_threshold,
        )

        if not pii_bboxes:
            logger.info("未发现PII实体，返回原图")
            return image.copy()

        merged_bboxes = self._merge_overlapping_bboxes(pii_bboxes)
        logger.debug(f"合并后边界框数量: {len(merged_bboxes)}")

        processed_image = self._apply_mosaic(
            image=image,
            bboxes=merged_bboxes,
            mosaic_style=mosaic_style,
            fill_color=fill_color,
            **mosaic_kwargs,
        )

        logger.info(f"图像脱敏完成，处理了 {len(merged_bboxes)} 个PII区域")
        return processed_image

    def _perform_ocr(self, image: Image.Image) -> OCRResult:
        """
        执行OCR识别

        Args:
            image: PIL图像对象

        Returns:
            OCRResult: OCR识别结果

        Raises:
            OCRError: OCR识别失败时抛出
        """
        try:
            logger.debug("开始OCR识别...")
            result = self._ocr_engine.recognize(image)
            logger.debug(f"OCR识别完成，识别到 {len(result.bounding_boxes)} 个文本区域")
            return result
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            raise OCRError(f"OCR识别失败: {e}") from e

    def _merge_adjacent_text_boxes(
        self,
        boxes: list[tuple[str, int, int, int, int]],
        max_horizontal_gap: int = 20,
        max_vertical_diff: int = 5,
    ) -> list[tuple[str, int, int, int, int]]:
        """
        合并相邻的文本框

        将同一行中水平相邻的文本框合并，解决OCR将连续文本分割成多个框的问题。

        Args:
            boxes: OCR文本框列表 (text, left, top, width, height)
            max_horizontal_gap: 最大水平间距阈值，小于此值则合并（默认20像素）
            max_vertical_diff: 最大垂直位置差异阈值，用于判断是否同一行

        Returns:
            合并后的文本框列表
        """
        if not boxes:
            return []

        # 按垂直位置分组（同一行的文本框）
        lines: list[list[tuple[str, int, int, int, int]]] = []

        for box in boxes:
            text, left, top, width, height = box
            placed = False

            for line in lines:
                if line:
                    _, _, ref_top, _, ref_height = line[0]
                    if abs(top - ref_top) <= max_vertical_diff:
                        line.append(box)
                        placed = True
                        break

            if not placed:
                lines.append([box])

        merged_boxes: list[tuple[str, int, int, int, int]] = []

        for line in lines:
            line.sort(key=lambda b: b[1])

            current_text, current_left, current_top, current_width, current_height = line[0]

            for i in range(1, len(line)):
                text, left, top, width, height = line[i]
                gap = left - (current_left + current_width)

                if gap <= max_horizontal_gap:
                    current_text += text
                    current_width = (left + width) - current_left
                    current_height = max(current_height, height)
                else:
                    merged_boxes.append(
                        (current_text, current_left, current_top, current_width, current_height)
                    )
                    current_text = text
                    current_left = left
                    current_top = top
                    current_width = width
                    current_height = height

            merged_boxes.append(
                (current_text, current_left, current_top, current_width, current_height)
            )

        logger.debug(f"相邻文本框合并: {len(boxes)} -> {len(merged_boxes)} 个")
        return merged_boxes

    def _analyze_ocr_result(
        self,
        ocr_result: OCRResult,
        entities: list[str] | None,
        allow_list: list[str] | None,
        score_threshold: float | None,
    ) -> list[tuple[str, str, int, int, int, int, float]]:
        """
        分析OCR结果，识别PII实体（并行优化版本）

        对每个OCR文本框进行并行分析，识别其中的PII实体，
        返回PII边界框列表用于后续脱敏处理。

        使用批量分析优化IE引擎调用，并使用缓存避免重复分析相同文本。

        Args:
            ocr_result: OCR识别结果
            entities: 要识别的PII类型列表
            allow_list: 白名单列表
            score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值

        Returns:
            PII边界框列表，每个元素为 (entity_type, text, left, top, width, height, score)

        Raises:
            PIIRecognitionError: PII识别失败时抛出
        """
        pii_bboxes: list[tuple[str, str, int, int, int, int, float]] = []

        try:
            boxes = ocr_result.bounding_boxes

            if not boxes:
                return pii_bboxes

            # 合并相邻文本框，解决OCR分割问题
            boxes = self._merge_adjacent_text_boxes(boxes)

            # 预过滤白名单和去重
            unique_texts: dict[str, list[tuple[int, int, int, int]]] = {}
            for text, left, top, width, height in boxes:
                if allow_list and text in allow_list:
                    continue
                if text not in unique_texts:
                    unique_texts[text] = []
                unique_texts[text].append((left, top, width, height))

            if not unique_texts:
                return pii_bboxes

            # 使用批量分析方法（会预先调用IE引擎并缓存结果）
            texts_to_analyze = list(unique_texts.keys())
            analysis_results = self._analyzer.analyze_batch(
                texts=texts_to_analyze,
                entities=entities,
                score_threshold=score_threshold,
            )

            # 根据分析结果构建PII边界框
            for text, bbox_list in unique_texts.items():
                analyzer_results = analysis_results.get(text, [])
                for result in analyzer_results:
                    # 对于每个识别到的PII，为所有相同文本的位置创建边界框
                    for left, top, width, height in bbox_list:
                        pii_bboxes.append(
                            (result.entity_type, text, left, top, width, height, result.score)
                        )
                        logger.debug(
                            f"发现PII: {text[:20]}... (类型: {result.entity_type}, 置信度: {result.score:.2f})"
                        )

            # 缓存PII边界框结果
            self._pii_bboxes_cache = pii_bboxes

            return pii_bboxes

        except Exception as e:
            logger.error(f"PII识别失败: {e}")
            raise PIIRecognitionError(f"PII识别失败: {e}") from e

    def _merge_overlapping_bboxes(
        self,
        bboxes: list[tuple[str, str, int, int, int, int, float]],
        padding: int = 5,
    ) -> list[tuple[int, int, int, int]]:
        """
        合并重叠的边界框

        使用迭代合并算法，每次合并后重新检查是否有新的重叠，
        直到没有更多合并为止。这确保了所有应该合并的框都会被正确合并。

        Args:
            bboxes: 边界框列表，格式为 (entity_type, text, left, top, width, height, score)
            padding: 边界框扩展像素

        Returns:
            合并后的边界框列表 (left, top, right, bottom)
        """
        if not bboxes:
            return []

        expanded_boxes = []
        for _entity_type, _text, left, top, width, height, _score in bboxes:
            expanded_boxes.append(
                (
                    left - padding,
                    top - padding,
                    left + width + padding,
                    top + height + padding,
                )
            )

        def boxes_overlap(box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]) -> bool:
            """检查两个框是否重叠或相邻"""
            return (
                box1[0] <= box2[2]
                and box2[0] <= box1[2]
                and box1[1] <= box2[3]
                and box2[1] <= box1[3]
            )

        def merge_two_boxes(
            box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]
        ) -> tuple[int, int, int, int]:
            """合并两个框"""
            return (
                min(box1[0], box2[0]),
                min(box1[1], box2[1]),
                max(box1[2], box2[2]),
                max(box1[3], box2[3]),
            )

        merged = list(expanded_boxes)

        changed = True
        while changed:
            changed = False
            new_merged = []
            used = [False] * len(merged)

            for i in range(len(merged)):
                if used[i]:
                    continue

                current_box = merged[i]
                used[i] = True

                for j in range(i + 1, len(merged)):
                    if used[j]:
                        continue

                    if boxes_overlap(current_box, merged[j]):
                        current_box = merge_two_boxes(current_box, merged[j])
                        used[j] = True
                        changed = True

                new_merged.append(current_box)

            merged = new_merged

        merged.sort(key=lambda x: (x[1], x[0]))

        logger.debug(f"边界框合并: {len(expanded_boxes)} -> {len(merged)} 个")

        return merged

    def _apply_mosaic(
        self,
        image: Image.Image,
        bboxes: list[tuple[int, int, int, int]],
        mosaic_style: str | MosaicStyle,
        fill_color: tuple[int, int, int],
        **kwargs: Any,
    ) -> Image.Image:
        """
        应用马赛克效果

        Args:
            image: PIL图像对象
            bboxes: 边界框列表
            mosaic_style: 马赛克样式
            fill_color: 填充颜色
            **kwargs: 马赛克操作符参数

        Returns:
            处理后的图像
        """
        if isinstance(mosaic_style, str):
            mosaic_style = MosaicStyle(mosaic_style)

        if mosaic_style == MosaicStyle.FILL:
            kwargs["fill_color"] = fill_color

        operator = create_mosaic_operator(mosaic_style, **kwargs)

        result = image.copy()
        for bbox in bboxes:
            result = operator.apply(result, bbox)

        return result

    def get_ocr_result(self) -> OCRResult | None:
        """
        获取最近一次OCR识别结果

        Returns:
            OCRResult: OCR识别结果，如果尚未执行OCR则返回None
        """
        return self._ocr_result_cache

    def get_pii_bboxes(
        self,
    ) -> list[tuple[str, str, int, int, int, int, float]]:
        """
        获取最近一次PII边界框结果

        Returns:
            PII边界框列表，每个元素为 (entity_type, text, left, top, width, height, score)
        """
        return self._pii_bboxes_cache

    def get_supported_entities(self) -> list[str]:
        """获取支持的PII实体类型列表"""
        return self._analyzer.get_supported_entities()

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
