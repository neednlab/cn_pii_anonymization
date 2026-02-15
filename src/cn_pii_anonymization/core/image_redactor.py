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
        CNPIIImageRedactorEngine._initialized = True
        logger.info("中文PII图像脱敏引擎初始化完成")

    def redact(
        self,
        image: Image.Image,
        mosaic_style: str | MosaicStyle = MosaicStyle.PIXEL,
        fill_color: tuple[int, int, int] = (0, 0, 0),
        entities: list[str] | None = None,
        allow_list: list[str] | None = None,
        score_threshold: float = 0.5,
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
            score_threshold: 置信度阈值
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

    def _analyze_ocr_result(
        self,
        ocr_result: OCRResult,
        entities: list[str] | None,
        allow_list: list[str] | None,
        score_threshold: float,
    ) -> list[tuple[str, int, int, int, int, float]]:
        """
        分析OCR结果，识别PII实体

        对于每个OCR文本框，不仅分析其自身文本，还会尝试与相邻行合并后分析，
        以识别跨行的PII实体（如多行地址）。

        对于已识别为地址(CN_ADDRESS)的PII，会自动扩展边界框覆盖上下相邻行，
        因为地址通常会跨越多行OCR识别。

        Args:
            ocr_result: OCR识别结果
            entities: 要识别的PII类型列表
            allow_list: 白名单列表
            score_threshold: 置信度阈值

        Returns:
            PII边界框列表，每个元素为 (text, left, top, width, height, score)

        Raises:
            PIIRecognitionError: PII识别失败时抛出
        """
        pii_bboxes: list[tuple[str, int, int, int, int, float]] = []

        try:
            boxes = ocr_result.bounding_boxes
            n = len(boxes)

            analyzed_indices: set[int] = set()

            for i in range(n):
                if i in analyzed_indices:
                    continue

                text, left, top, width, height = boxes[i]
                if allow_list and text in allow_list:
                    continue

                analyzer_results = self._analyzer.analyze(
                    text=text,
                    entities=entities,
                    score_threshold=score_threshold,
                )

                for result in analyzer_results:
                    final_left, final_top = left, top
                    final_width, final_height = width, height
                    final_text = text

                    if result.entity_type == "CN_ADDRESS":
                        expanded_bbox = self._expand_address_bbox(
                            boxes, i, analyzed_indices
                        )
                        if expanded_bbox:
                            final_left, final_top, final_width, final_height, final_text, merged_indices = expanded_bbox
                            for idx in merged_indices:
                                if idx != i:
                                    analyzed_indices.add(idx)

                    pii_bboxes.append((final_text, final_left, final_top, final_width, final_height, result.score))
                    logger.debug(
                        f"发现PII: {final_text[:20]}... (类型: {result.entity_type}, 置信度: {result.score:.2f})"
                    )

            return pii_bboxes

        except Exception as e:
            logger.error(f"PII识别失败: {e}")
            raise PIIRecognitionError(f"PII识别失败: {e}") from e

    def _expand_address_bbox(
        self,
        boxes: list[tuple[str, int, int, int, int]],
        center_idx: int,
        analyzed_indices: set[int],
        max_expand_lines: int = 2,
    ) -> tuple[int, int, int, int, str, list[int]] | None:
        """
        扩展地址边界框，覆盖下方相邻的行

        地址通常会跨越多行OCR识别，当一行被识别为地址时，
        其下方相邻行很可能也是地址的一部分。
        只向下扩展，避免误合并上方的非地址内容。

        Args:
            boxes: 所有OCR边界框列表
            center_idx: 中心框索引
            analyzed_indices: 已分析的框索引集合
            max_expand_lines: 最大扩展行数

        Returns:
            扩展后的边界框 (left, top, width, height, merged_text, merged_indices)，
            如果没有扩展则返回 None
        """
        text, left, top, width, height = boxes[center_idx]
        merged_left, merged_top = left, top
        merged_width, merged_height = width, height
        merged_text = text
        merged_indices = [center_idx]

        adjacent_indices = self._find_adjacent_boxes_below(
            boxes, center_idx, y_threshold=height * 2.0
        )

        for adj_idx in adjacent_indices:
            if adj_idx in analyzed_indices:
                continue
            if len(merged_indices) > max_expand_lines:
                break

            adj_text, adj_left, adj_top, adj_width, adj_height = boxes[adj_idx]

            if adj_height > height * 3:
                logger.debug(f"跳过高度异常的框: '{adj_text}' (高度: {adj_height} > {height * 3})")
                continue

            adj_results = self._analyzer.analyze(
                text=adj_text,
                entities=["CN_ADDRESS"],
                score_threshold=0.5,
            )

            if len(adj_results) == 0:
                merged_text = merged_text + adj_text
                merged_left = min(merged_left, adj_left)
                merged_width = max(merged_left + merged_width, adj_left + adj_width) - merged_left
                merged_height = max(merged_top + merged_height, adj_top + adj_height) - merged_top
                merged_indices.append(adj_idx)
                logger.debug(f"扩展地址边界框: 添加 '{adj_text}'")

        if len(merged_indices) > 1:
            return (merged_left, merged_top, merged_width, merged_height, merged_text, merged_indices)
        return None

    def _find_adjacent_boxes_below(
        self,
        boxes: list[tuple[str, int, int, int, int]],
        center_idx: int,
        y_threshold: float = 50.0,
    ) -> list[int]:
        """
        查找在指定框下方的相邻框

        用于地址扩展，只查找下方的框，且放宽X轴条件，
        因为地址可能跨行且X轴位置不同。

        Args:
            boxes: 所有OCR边界框列表
            center_idx: 中心框索引
            y_threshold: Y坐标差距阈值，超过此值认为不相邻

        Returns:
            下方相邻框的索引列表
        """
        adjacent: list[int] = []
        _text, _left, top, _width, height = boxes[center_idx]
        center_bottom = top + height

        for i, (_adj_text, _adj_left, adj_top, _adj_width, _adj_height) in enumerate(boxes):
            if i == center_idx:
                continue

            if adj_top < center_bottom:
                continue

            y_gap = adj_top - center_bottom

            if y_gap > y_threshold:
                continue

            adjacent.append(i)

        adjacent.sort(key=lambda idx: boxes[idx][2])

        return adjacent

    def _merge_overlapping_bboxes(
        self,
        bboxes: list[tuple[str, int, int, int, int, float]],
        padding: int = 5,
    ) -> list[tuple[int, int, int, int]]:
        """
        合并重叠的边界框

        使用连通分量算法，将所有重叠或相邻的框归为一组，然后每组生成一个合并后的框。
        这确保了所有应该合并的框都会被正确合并。

        Args:
            bboxes: 边界框列表
            padding: 边界框扩展像素

        Returns:
            合并后的边界框列表 (left, top, right, bottom)
        """
        if not bboxes:
            return []

        expanded_boxes = []
        for _text, left, top, width, height, _score in bboxes:
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

        def merge_two_boxes(box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
            """合并两个框"""
            return (
                min(box1[0], box2[0]),
                min(box1[1], box2[1]),
                max(box1[2], box2[2]),
                max(box1[3], box2[3]),
            )

        n = len(expanded_boxes)
        parent = list(range(n))

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for i in range(n):
            for j in range(i + 1, n):
                if boxes_overlap(expanded_boxes[i], expanded_boxes[j]):
                    union(i, j)

        groups: dict[int, list[int]] = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)

        merged = []
        for indices in groups.values():
            group_boxes = [expanded_boxes[i] for i in indices]
            merged_box = group_boxes[0]
            for box in group_boxes[1:]:
                merged_box = merge_two_boxes(merged_box, box)
            merged.append(merged_box)

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

    def get_supported_entities(self) -> list[str]:
        """获取支持的PII实体类型列表"""
        return self._analyzer.get_supported_entities()

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
