"""
文本处理器

提供文本PII识别和匿名化处理的完整流程。
"""

from dataclasses import dataclass, field
from typing import Any

from presidio_anonymizer.entities import OperatorConfig

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.core.anonymizer import CNPIIAnonymizerEngine
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PIIEntity:
    """
    PII实体信息

    Attributes:
        entity_type: 实体类型
        start: 起始位置
        end: 结束位置
        score: 置信度分数
        original_text: 原始文本
        anonymized_text: 匿名化后的文本
    """

    entity_type: str
    start: int
    end: int
    score: float
    original_text: str
    anonymized_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "entity_type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "score": self.score,
            "original_text": self.original_text,
            "anonymized_text": self.anonymized_text,
        }


@dataclass
class TextProcessResult:
    """
    文本处理结果

    Attributes:
        original_text: 原始文本
        anonymized_text: 匿名化后的文本
        pii_entities: 识别出的PII实体列表
    """

    original_text: str
    anonymized_text: str
    pii_entities: list[PIIEntity] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "original_text": self.original_text,
            "anonymized_text": self.anonymized_text,
            "pii_entities": [e.to_dict() for e in self.pii_entities],
        }

    @property
    def has_pii(self) -> bool:
        """是否包含PII"""
        return len(self.pii_entities) > 0


class TextProcessor:
    """
    文本PII处理器

    整合分析器和匿名化器，提供完整的文本PII处理流程。

    Example:
        >>> processor = TextProcessor()
        >>> result = processor.process("我的手机号是13812345678")
        >>> print(result.anonymized_text)
        我的手机号是138****5678
    """

    def __init__(
        self,
        analyzer: CNPIIAnalyzerEngine | None = None,
        anonymizer: CNPIIAnonymizerEngine | None = None,
    ) -> None:
        """
        初始化文本处理器

        Args:
            analyzer: 分析器实例，None时自动创建
            anonymizer: 匿名化器实例，None时自动创建
        """
        self._analyzer = analyzer or CNPIIAnalyzerEngine()
        self._anonymizer = anonymizer or CNPIIAnonymizerEngine()

    def process(
        self,
        text: str,
        entities: list[str] | None = None,
        operator_config: dict[str, OperatorConfig] | None = None,
        language: str = "zh",
        score_threshold: float | None = None,
    ) -> TextProcessResult:
        """
        处理文本中的PII

        Args:
            text: 输入文本
            entities: 要识别的PII类型列表，None表示识别所有类型
            operator_config: 匿名化操作配置
            language: 语言类型
            score_threshold: 全局置信度阈值，None时使用配置文件中的按类型阈值

        Returns:
            TextProcessResult: 处理结果

        Example:
            >>> processor = TextProcessor()
            >>> result = processor.process(
            ...     "手机号13812345678，身份证110101199001011234",
            ...     entities=["CN_PHONE_NUMBER", "CN_ID_CARD"]
            ... )
        """
        logger.info(f"开始处理文本，长度: {len(text)}")

        analyzer_results = self._analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
            score_threshold=score_threshold,
        )

        if not analyzer_results:
            logger.info("未发现PII实体")
            return TextProcessResult(
                original_text=text,
                anonymized_text=text,
                pii_entities=[],
            )

        anonymized = self._anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operator_config,
        )

        pii_entities = self._build_pii_entities(
            text=text,
            anonymized_text=anonymized.text,
            analyzer_results=analyzer_results,
            anonymized_items=anonymized.items,
        )

        logger.info(f"处理完成，发现 {len(pii_entities)} 个PII实体")

        return TextProcessResult(
            original_text=text,
            anonymized_text=anonymized.text,
            pii_entities=pii_entities,
        )

    def analyze_only(
        self,
        text: str,
        entities: list[str] | None = None,
        language: str = "zh",
        score_threshold: float | None = None,
    ) -> list[PIIEntity]:
        """
        仅分析文本中的PII，不进行匿名化

        Args:
            text: 输入文本
            entities: 要识别的PII类型列表
            language: 语言类型
            score_threshold: 全局置信度阈值，None时使用配置文件中的按类型阈值

        Returns:
            PII实体列表
        """
        analyzer_results = self._analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
            score_threshold=score_threshold,
        )

        return [
            PIIEntity(
                entity_type=r.entity_type,
                start=r.start,
                end=r.end,
                score=r.score,
                original_text=text[r.start : r.end],
            )
            for r in analyzer_results
        ]

    def _build_pii_entities(
        self,
        text: str,
        anonymized_text: str,
        analyzer_results: list,
        anonymized_items: list,
    ) -> list[PIIEntity]:
        """
        构建PII实体列表

        Args:
            text: 原始文本
            anonymized_text: 匿名化后的文本
            analyzer_results: 分析结果（按原始位置正序排列）
            anonymized_items: 匿名化操作结果项列表（Presidio按倒序返回）

        Returns:
            PII实体列表

        Note:
            Presidio的anonymized_items是按倒序返回的（从后往前处理），
            而analyzer_results是按原始位置正序排列的。
            因此需要反转anonymized_items后再进行索引匹配。
        """
        # 反转anonymized_items使其与analyzer_results顺序一致
        reversed_items = list(reversed(anonymized_items))

        entities = []
        for idx, result in enumerate(analyzer_results):
            original = text[result.start : result.end]

            anonymized_value = self._get_anonymized_value_by_index(
                idx,
                result.entity_type,
                reversed_items,
            )

            entity = PIIEntity(
                entity_type=result.entity_type,
                start=result.start,
                end=result.end,
                score=result.score,
                original_text=original,
                anonymized_text=anonymized_value,
            )
            entities.append(entity)

        return entities

    def _get_anonymized_value_by_index(
        self,
        index: int,
        entity_type: str,
        anonymized_items: list,
    ) -> str:
        """
        根据索引获取匿名化值

        由于replace等操作会改变文本长度，原始位置不再有效。
        anonymized_items与analyzer_results一一对应，使用索引匹配。

        Args:
            index: 在analyzer_results中的索引位置
            entity_type: PII实体类型（用于验证和回退）
            anonymized_items: 匿名化操作结果项列表

        Returns:
            匿名化后的文本值，如果未找到则返回实体类型占位符
        """
        if index < len(anonymized_items):
            item = anonymized_items[index]
            return item.text

        return f"<{entity_type}>"

    def get_supported_entities(self) -> list[str]:
        """获取支持的PII实体类型列表"""
        return self._analyzer.get_supported_entities()
