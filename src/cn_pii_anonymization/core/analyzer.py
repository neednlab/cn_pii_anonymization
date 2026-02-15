"""
中文PII分析器引擎

封装Presidio AnalyzerEngine，提供中文PII识别能力。
使用PaddleNLP作为NLP引擎，使用信息抽取引擎识别姓名和地址。
"""

from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry

from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.nlp.ie_engine import PaddleNLPInfoExtractionEngine
from cn_pii_anonymization.nlp.nlp_engine import PaddleNlpEngineProvider
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
    使用PaddleNLP信息抽取引擎识别姓名和地址。

    Attributes:
        _analyzer: Presidio分析器引擎实例
        _registry: 识别器注册表
        _nlp_engine: PaddleNLP引擎（分词与词性标注）
        _ie_engine: PaddleNLP信息抽取引擎（姓名和地址识别）

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
        self._setup_ie_engine()
        self._setup_registry()
        self._setup_analyzer()
        CNPIIAnalyzerEngine._initialized = True
        logger.info("中文PII分析器引擎初始化完成")

    def _setup_nlp_engine(self) -> None:
        """设置NLP引擎（使用PaddleNLP LAC，用于分词和词性标注）"""
        nlp_configuration = {
            "nlp_engine_name": "paddlenlp",
            "models": [
                {"lang_code": "zh", "model_name": settings.nlp_model},
            ],
        }
        provider = PaddleNlpEngineProvider(nlp_configuration=nlp_configuration)
        self._nlp_engine = provider.create_engine()
        logger.debug(f"NLP引擎已加载: PaddleNLP LAC ({settings.nlp_model})")

    def _setup_ie_engine(self) -> None:
        """设置信息抽取引擎（用于姓名和地址识别）"""
        self._ie_engine = PaddleNLPInfoExtractionEngine(
            schema=["地址", "姓名"],
            use_gpu=False,
        )
        logger.debug("信息抽取引擎已创建: schema=['地址', '姓名']")

    def _setup_registry(self) -> None:
        """设置识别器注册表并注册中文PII识别器"""
        self._registry = RecognizerRegistry(supported_languages=["zh"])

        # 正则表达式识别器（不需要IE引擎）
        regex_recognizers = [
            CNPhoneRecognizer(),
            CNIDCardRecognizer(),
            CNBankCardRecognizer(),
            CNPassportRecognizer(),
            CNEmailRecognizer(),
        ]

        for recognizer in regex_recognizers:
            self._registry.add_recognizer(recognizer)
            logger.debug(f"已注册识别器: {recognizer.supported_entities}")

        # 信息抽取识别器（需要IE引擎）
        ie_recognizers = [
            CNAddressRecognizer(ie_engine=self._ie_engine),
            CNNameRecognizer(ie_engine=self._ie_engine),
        ]

        for recognizer in ie_recognizers:
            self._registry.add_recognizer(recognizer)
            logger.debug(f"已注册识别器(IE): {recognizer.supported_entities}")

    def _setup_analyzer(self) -> None:
        """设置分析器"""
        self._analyzer = AnalyzerEngine(
            registry=self._registry,
            supported_languages=["zh"],
            nlp_engine=self._nlp_engine,
        )

    def analyze(
        self,
        text: str,
        language: str = "zh",
        entities: list[str] | None = None,
        score_threshold: float | None = None,
        allow_list: list[str] | None = None,
        **kwargs: Any,
    ) -> list:
        """
        分析文本中的PII实体

        Args:
            text: 待分析的文本
            language: 语言代码，默认为"zh"
            entities: 要识别的PII类型列表，None表示识别所有类型
            score_threshold: 全局置信度阈值，None时使用配置文件中的按类型阈值
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

        nlp_artifacts = self._nlp_engine.process_text(text, language)

        threshold_settings = settings.score_thresholds
        min_threshold = threshold_settings.default

        results = self._analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
            score_threshold=min_threshold,
            allow_list=allow_list,
            nlp_artifacts=nlp_artifacts,
            **kwargs,
        )

        if score_threshold is not None:
            filtered_results = [r for r in results if r.score >= score_threshold]
        else:
            filtered_results = [
                r for r in results
                if r.score >= threshold_settings.get_threshold(r.entity_type)
            ]

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

    def get_ie_engine(self) -> PaddleNLPInfoExtractionEngine | None:
        """
        获取信息抽取引擎实例

        Returns:
            信息抽取引擎实例
        """
        return self._ie_engine

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
