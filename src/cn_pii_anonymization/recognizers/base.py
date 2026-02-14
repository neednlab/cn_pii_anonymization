"""
中文PII识别器基类

提供中文PII识别器的基类和公共功能。
"""

from abc import abstractmethod
from typing import Any, ClassVar

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts


class CNPIIRecognizer(EntityRecognizer):
    """
    中文PII识别器基类

    继承自Presidio的EntityRecognizer，为中文PII识别器提供公共功能。

    所有中文PII识别器都应继承此类并实现analyze方法。

    Attributes:
        CONTEXT_WORDS: 上下文关键词列表，用于提高识别准确率

    Example:
        >>> class MyRecognizer(CNPIIRecognizer):
        ...     def analyze(self, text, entities, nlp_artifacts):
        ...         # 实现识别逻辑
        ...         pass
    """

    CONTEXT_WORDS: ClassVar[list[str]] = []

    def __init__(
        self,
        supported_entities: list[str],
        supported_language: str = "zh",
        name: str | None = None,
        context: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化识别器

        Args:
            supported_entities: 支持的实体类型列表
            supported_language: 支持的语言，默认为"zh"
            name: 识别器名称
            context: 上下文关键词列表
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            name=name,
            context=context or self.CONTEXT_WORDS,
            **kwargs,
        )

    @abstractmethod
    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts,
    ) -> list[RecognizerResult]:
        """
        分析文本，返回识别结果

        子类必须实现此方法。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        pass

    def load(self) -> None:
        """加载资源（可选实现）"""
        pass

    def _validate_result(
        self,
        text: str,
        result: RecognizerResult,
    ) -> bool:
        """
        验证识别结果的有效性

        子类可重写此方法实现自定义验证逻辑。

        Args:
            text: 原始文本
            result: 识别结果

        Returns:
            结果是否有效
        """
        return True

    def _filter_results(
        self,
        text: str,
        results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        """
        过滤无效的识别结果

        Args:
            text: 原始文本
            results: 识别结果列表

        Returns:
            过滤后的结果列表
        """
        return [r for r in results if self._validate_result(text, r)]
