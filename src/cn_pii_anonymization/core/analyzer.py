"""
中文PII分析器引擎

封装Presidio AnalyzerEngine，提供中文PII识别能力。
使用PaddleNLP作为NLP引擎，使用信息抽取引擎识别姓名和地址。
支持PII识别器优先级机制，当多个识别结果重叠时，保留高优先级的结果。
"""

from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.recognizer_result import RecognizerResult

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
            schema=["地址", "具体地址", "姓名", "人名"],
            use_gpu=False,
        )
        logger.debug("信息抽取引擎已创建: schema=['地址', '具体地址', '姓名', '人名']")

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
            CNNameRecognizer(
                ie_engine=self._ie_engine,
                allow_list=settings.parsed_name_allow_list,
                deny_list=settings.parsed_name_deny_list,
            ),
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
                r for r in results if r.score >= threshold_settings.get_threshold(r.entity_type)
            ]

        # 应用优先级过滤：当结果重叠时，保留高优先级的结果
        filtered_results = self._apply_priority_filter(filtered_results)

        logger.debug(f"分析完成，发现 {len(filtered_results)} 个PII实体")
        return filtered_results

    def analyze_batch(
        self,
        texts: list[str],
        language: str = "zh",
        entities: list[str] | None = None,
        score_threshold: float | None = None,
        allow_list: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, list]:
        """
        批量分析多个文本中的PII实体（性能优化版本）

        相比逐个调用analyze，批量处理会：
        1. 预先批量调用IE引擎处理所有文本
        2. 将IE结果缓存供识别器使用
        3. 减少模型加载和初始化开销

        Args:
            texts: 待分析的文本列表
            language: 语言代码，默认为"zh"
            entities: 要识别的PII类型列表，None表示识别所有类型
            score_threshold: 全局置信度阈值，None时使用配置文件中的按类型阈值
            allow_list: 白名单列表，匹配的内容将被排除
            **kwargs: 其他参数传递给Presidio分析器

        Returns:
            字典，key为原始文本，value为该文本的识别结果列表

        Example:
            >>> engine = CNPIIAnalyzerEngine()
            >>> texts = ["手机号13812345678", "身份证110101199001011234"]
            >>> results = engine.analyze_batch(texts)
        """
        if not texts:
            return {}

        logger.debug(f"开始批量分析 {len(texts)} 个文本")

        # 预先批量调用IE引擎，缓存结果
        self._precompute_ie_results(texts)

        threshold_settings = settings.score_thresholds
        min_threshold = threshold_settings.default

        results_map: dict[str, list] = {}

        for text in texts:
            if not text:
                results_map[text] = []
                continue

            nlp_artifacts = self._nlp_engine.process_text(text, language)

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
                    r for r in results if r.score >= threshold_settings.get_threshold(r.entity_type)
                ]

            # 应用优先级过滤：当结果重叠时，保留高优先级的结果
            filtered_results = self._apply_priority_filter(filtered_results)

            results_map[text] = filtered_results

        logger.debug("批量分析完成")
        return results_map

    def _apply_priority_filter(self, results: list[RecognizerResult]) -> list[RecognizerResult]:
        """
        应用优先级过滤

        当多个识别结果重叠时，保留高优先级的结果。
        优先级规则：身份证 > 银行卡 > 手机号 > 护照 > 邮箱 > 姓名 > 地址

        Args:
            results: 原始识别结果列表

        Returns:
            过滤后的识别结果列表
        """
        if not results or len(results) <= 1:
            return results

        priority_settings = settings.pii_priorities
        filtered: list[RecognizerResult] = []

        # 按起始位置排序
        sorted_results = sorted(results, key=lambda r: (r.start, r.end))

        for result in sorted_results:
            # 检查是否与已保留的结果重叠
            should_add = True
            result_priority = priority_settings.get_priority(result.entity_type)

            # 检查与已保留结果的重叠情况
            to_remove: list[int] = []
            for i, existing in enumerate(filtered):
                existing_priority = priority_settings.get_priority(existing.entity_type)

                # 检查是否重叠
                if self._results_overlap(result, existing):
                    if result_priority < existing_priority:
                        # 新结果优先级更高，标记移除旧结果
                        to_remove.append(i)
                        logger.debug(
                            f"优先级过滤: {result.entity_type}(优先级{result_priority}) "
                            f"覆盖 {existing.entity_type}(优先级{existing_priority}) "
                            f"位置[{result.start}:{result.end}] vs [{existing.start}:{existing.end}]"
                        )
                    else:
                        # 已有结果优先级更高或相等，不添加新结果
                        should_add = False
                        logger.debug(
                            f"优先级过滤: {existing.entity_type}(优先级{existing_priority}) "
                            f"保留，忽略 {result.entity_type}(优先级{result_priority}) "
                            f"位置[{existing.start}:{existing.end}] vs [{result.start}:{result.end}]"
                        )
                        break

            # 移除被覆盖的低优先级结果
            for i in reversed(to_remove):
                filtered.pop(i)

            if should_add:
                filtered.append(result)

        return filtered

    @staticmethod
    def _results_overlap(r1: RecognizerResult, r2: RecognizerResult) -> bool:
        """
        检查两个识别结果是否重叠

        两个结果重叠的定义：它们的文本范围有交集

        Args:
            r1: 第一个识别结果
            r2: 第二个识别结果

        Returns:
            是否重叠
        """
        return r1.start < r2.end and r2.start < r1.end

    def _precompute_ie_results(self, texts: list[str]) -> None:
        """
        预先计算IE结果并缓存到识别器

        批量调用IE引擎处理所有文本，将结果缓存到识别器中，
        避免识别器逐个调用IE引擎。

        Args:
            texts: 待处理的文本列表
        """
        if not self._ie_engine:
            return

        # 去重文本
        unique_texts = list({text for text in texts if text and text.strip()})
        if not unique_texts:
            return

        # 批量调用IE引擎
        ie_results = self._ie_engine.extract_batch(unique_texts)

        # 将结果缓存到识别器
        for recognizer in self._registry.recognizers:
            if hasattr(recognizer, "set_ie_cache"):
                recognizer.set_ie_cache(ie_results)

        logger.debug(f"IE结果预计算完成，处理 {len(unique_texts)} 个唯一文本")

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

    def update_name_lists(
        self,
        allow_list: list[str] | None = None,
        deny_list: list[str] | None = None,
    ) -> None:
        """
        动态更新姓名识别器的allow_list和deny_list

        允许在运行时更新姓名识别器的配置，无需重启服务。

        Args:
            allow_list: 新的允许列表，None表示不更新
            deny_list: 新的拒绝列表，None表示不更新

        Example:
            >>> engine = CNPIIAnalyzerEngine()
            >>> engine.update_name_lists(
            ...     allow_list=["张三", "李四"],
            ...     deny_list=["王五"]
            ... )
        """
        for recognizer in self._registry.recognizers:
            if isinstance(recognizer, CNNameRecognizer):
                if allow_list is not None:
                    recognizer.set_allow_list(allow_list)
                if deny_list is not None:
                    recognizer.set_deny_list(deny_list)
                logger.info(
                    f"姓名识别器列表已更新: "
                    f"allow_list={recognizer.get_allow_list()}, "
                    f"deny_list={recognizer.get_deny_list()}"
                )
                break

    def get_name_recognizer_lists(self) -> dict[str, list[str]]:
        """
        获取当前姓名识别器的allow_list和deny_list

        Returns:
            包含allow_list和deny_list的字典

        Example:
            >>> engine = CNPIIAnalyzerEngine()
            >>> lists = engine.get_name_recognizer_lists()
            >>> print(lists["allow_list"])
            ['张三', '李四']
        """
        for recognizer in self._registry.recognizers:
            if isinstance(recognizer, CNNameRecognizer):
                return {
                    "allow_list": recognizer.get_allow_list(),
                    "deny_list": recognizer.get_deny_list(),
                }
        return {"allow_list": [], "deny_list": []}

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
