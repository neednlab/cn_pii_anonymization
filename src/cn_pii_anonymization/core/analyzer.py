"""
中文PII分析器引擎

封装Presidio AnalyzerEngine，提供中文PII识别能力。
"""

from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.recognizers import (
    CNAddressRecognizer,
    CNBankCardRecognizer,
    CNEmailRecognizer,
    CNIDCardRecognizer,
    CNNameRecognizer,
    CNPassportRecognizer,
    CNPhoneRecognizer,
)
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNPIIAnalyzerEngine:
    """
    中文PII分析器引擎

    封装Presidio AnalyzerEngine，注册中文PII识别器，提供中文PII识别能力。

    Attributes:
        _analyzer: Presidio分析器引擎实例
        _registry: 识别器注册表
        _nlp_engine: NLP引擎

    Example:
        >>> engine = CNPIIAnalyzerEngine()
        >>> results = engine.analyze("我的手机号是13812345678")
        >>> for r in results:
        ...     print(f"发现{r.entity_type}: {r.score}")
    """

    _instance: "CNPIIAnalyzerEngine | None" = None
    _initialized: bool = False

    def __new__(cls) -> "CNPIIAnalyzerEngine":
        """单例模式，确保全局只有一个分析器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化分析器引擎"""
        if CNPIIAnalyzerEngine._initialized:
            return

        logger.info("初始化中文PII分析器引擎...")
        self._setup_nlp_engine()
        self._setup_registry()
        self._setup_analyzer()
        CNPIIAnalyzerEngine._initialized = True
        logger.info("中文PII分析器引擎初始化完成")

    def _setup_nlp_engine(self) -> None:
        """设置NLP引擎"""
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "zh", "model_name": settings.spacy_model},
            ],
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        self._nlp_engine = provider.create_engine()
        logger.debug(f"NLP引擎已加载: {settings.spacy_model}")

    def _setup_registry(self) -> None:
        """设置识别器注册表并注册中文PII识别器"""
        self._registry = RecognizerRegistry(supported_languages=["zh"])
        self._registry.load_predefined_recognizers(nlp_engine=self._nlp_engine)

        cn_recognizers = [
            CNPhoneRecognizer(),
            CNIDCardRecognizer(),
            CNBankCardRecognizer(),
            CNPassportRecognizer(),
            CNEmailRecognizer(),
            CNAddressRecognizer(),
            CNNameRecognizer(),
        ]

        for recognizer in cn_recognizers:
            self._registry.add_recognizer(recognizer)
            logger.debug(f"已注册识别器: {recognizer.supported_entities}")

    def _setup_analyzer(self) -> None:
        """设置分析器"""
        self._analyzer = AnalyzerEngine(
            nlp_engine=self._nlp_engine,
            registry=self._registry,
            supported_languages=["zh"],
        )

    def analyze(
        self,
        text: str,
        language: str = "zh",
        entities: list[str] | None = None,
        score_threshold: float = 0.5,
        allow_list: list[str] | None = None,
        **kwargs: Any,
    ) -> list:
        """
        分析文本中的PII实体

        Args:
            text: 待分析的文本
            language: 语言代码，默认为"zh"
            entities: 要识别的PII类型列表，None表示识别所有类型
            score_threshold: 置信度阈值，低于此值的结果将被过滤
            allow_list: 白名单列表，匹配的内容将被排除
            **kwargs: 其他参数传递给Presidio分析器

        Returns:
            识别结果列表

        Example:
            >>> engine = CNPIIAnalyzerEngine()
            >>> results = engine.analyze(
            ...     "手机号13812345678，身份证110101199001011234",
            ...     entities=["CN_PHONE_NUMBER", "CN_ID_CARD"]
            ... )
        """
        logger.debug(f"开始分析文本，长度: {len(text)}")

        results = self._analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
            score_threshold=score_threshold,
            allow_list=allow_list,
            **kwargs,
        )

        filtered_results = [r for r in results if r.score >= score_threshold]

        logger.debug(f"分析完成，发现 {len(filtered_results)} 个PII实体")
        return filtered_results

    def add_recognizer(self, recognizer: Any) -> None:
        """
        添加自定义识别器

        Args:
            recognizer: 自定义识别器实例
        """
        self._registry.add_recognizer(recognizer)
        logger.info(f"已添加自定义识别器: {recognizer.supported_entities}")

    def get_supported_entities(self, language: str = "zh") -> list[str]:
        """
        获取支持的PII实体类型列表

        Args:
            language: 语言代码

        Returns:
            支持的实体类型列表
        """
        return self._analyzer.get_supported_entities(language=language)

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
