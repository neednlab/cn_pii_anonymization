"""
中国地址识别器
使用PaddleNLP information_extraction方法进行地址识别。
"""

from typing import Any, ClassVar

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNAddressRecognizer(CNPIIRecognizer):
    """
    中国大陆地址识别器

    使用PaddleNLP Taskflow的information_extraction方法进行地址识别。

    Attributes:
        CONTEXT_WORDS: 上下文关键词列表
        _ie_engine: 信息抽取引擎实例
        MIN_ADDRESS_LENGTH: 地址最小长度阈值
        _ie_cache: IE结果缓存，用于批量处理优化

    Example:
        >>> recognizer = CNAddressRecognizer(ie_engine=ie_engine)
        >>> results = recognizer.analyze(
        ...     "地址：北京市朝阳区建国路88号",
        ...     ["CN_ADDRESS"],
        ...     nlp_artifacts
        ... )
        >>> print(results[0].entity_type)
        CN_ADDRESS
    """

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "地址",
        "住址",
        "居住地",
        "家庭住址",
        "通讯地址",
        "联系地址",
        "邮寄地址",
        "收货地址",
        "发货地址",
        "办公地址",
        "公司地址",
        "户籍地址",
        "注册地址",
        "所在地",
        "address",
        "addr",
    ]

    # 地址最小长度阈值，小于此长度的地址可认为非详细地址，将被直接过滤(如"上海市")
    MIN_ADDRESS_LENGTH: ClassVar[int] = 6

    def __init__(self, ie_engine: Any = None, **kwargs: Any) -> None:
        """
        初始化地址识别器

        Args:
            ie_engine: 信息抽取引擎实例（PaddleNLP Taskflow information_extraction）
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_ADDRESS"],
            name="CN Address Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )
        self._ie_engine = ie_engine
        self._ie_cache: dict[str, list[dict]] | None = None
        logger.debug("地址识别器初始化完成（使用信息抽取引擎）")

    def set_ie_engine(self, ie_engine: Any) -> None:
        """
        设置信息抽取引擎

        Args:
            ie_engine: 信息抽取引擎实例
        """
        self._ie_engine = ie_engine
        logger.debug("地址识别器已设置新的信息抽取引擎")

    def set_ie_cache(self, cache: dict[str, list[dict]] | None) -> None:
        """
        设置IE结果缓存

        用于批量处理优化，避免重复调用IE引擎。

        Args:
            cache: IE结果缓存字典，key为文本，value为抽取结果
        """
        self._ie_cache = cache
        logger.debug(f"地址识别器已设置IE缓存，包含 {len(cache) if cache else 0} 个条目")

    def clear_ie_cache(self) -> None:
        """清除IE结果缓存"""
        self._ie_cache = None

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的地址

        使用信息抽取模型识别地址，置信度直接采用IE返回的probability结果。
        过滤长度小于6的地址。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果（兼容Presidio的EntityRecognizer，但此识别器不实际使用）

        Returns:
            识别结果列表
        """
        if not text:
            return []

        if self._ie_engine is None:
            logger.debug("地址识别器: 信息抽取引擎未设置，跳过识别")
            return []

        results = self._analyze_with_ie(text)

        if not results:
            logger.debug(f"地址识别器: 未识别到任何地址。文本: '{text[:50]}...'")

        return results

    def _analyze_with_ie(self, text: str) -> list[RecognizerResult]:
        """
        使用信息抽取模型分析地址

        Args:
            text: 原始文本

        Returns:
            识别结果列表
        """
        results = []
        addresses_found = []

        try:
            # 优先使用缓存
            if self._ie_cache is not None and text in self._ie_cache:
                ie_result = self._ie_cache[text]
                # 从缓存结果中提取地址
                addresses = []
                for item in ie_result:
                    if isinstance(item, dict) and "地址" in item:
                        for addr in item["地址"]:
                            addresses.append({
                                "text": addr.get("text", ""),
                                "probability": addr.get("probability", 0.85),
                            })
            else:
                # 缓存未命中，直接调用IE引擎
                ie_result = self._ie_engine.extract_addresses(text)
                addresses = ie_result

            for addr_info in addresses:
                addr_text = addr_info.get("text", "")
                probability = addr_info.get("probability", 0.85)

                if not addr_text:
                    continue

                # 过滤长度小于MIN_ADDRESS_LENGTH的地址
                if len(addr_text) < self.MIN_ADDRESS_LENGTH:
                    logger.debug(
                        f"地址识别器: 地址 '{addr_text}' 长度 {len(addr_text)} < {self.MIN_ADDRESS_LENGTH}，已过滤"
                    )
                    continue

                addresses_found.append(addr_text)

                start = text.find(addr_text)
                if start == -1:
                    logger.warning(
                        f"地址识别器: 无法在原文中定位地址 '{addr_text}'"
                    )
                    continue

                end = start + len(addr_text)

                # 直接使用IE返回的probability作为置信度
                result = self._create_result(
                    entity_type="CN_ADDRESS",
                    start=start,
                    end=end,
                    score=probability,
                )
                results.append(result)
                logger.debug(
                    f"地址识别器(IE): 识别到地址 '{addr_text}', "
                    f"位置=[{start}:{end}], 置信度={probability:.4f}"
                )

        except Exception as e:
            logger.error(f"地址识别器: 信息抽取失败 - {e}")

        if addresses_found:
            logger.debug(
                f"地址识别器: 信息抽取识别到 {len(addresses_found)} 个地址: {addresses_found}"
            )
        else:
            logger.debug("地址识别器: 信息抽取未识别到任何地址")

        return results
