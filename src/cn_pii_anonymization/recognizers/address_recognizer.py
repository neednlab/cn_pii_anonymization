"""
中国地址识别器

完全依赖PaddleNLP LAC模型的NER结果识别中国大陆地址。
"""

import re
from typing import Any, ClassVar

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNAddressRecognizer(CNPIIRecognizer):
    """
    中国大陆地址识别器

    完全依赖PaddleNLP LAC NER结果识别中国大陆地址。
    如果NER未识别到LOCATION实体，将输出WARNING日志并返回空结果。

    Attributes:
        CONTEXT_WORDS: 上下文关键词列表

    Example:
        >>> recognizer = CNAddressRecognizer()
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

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化地址识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_ADDRESS"],
            name="CN Address Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的地址

        完全依赖NER结果。如果NER不可用或未识别到LOCATION实体，
        将输出WARNING日志并返回空结果。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        if not nlp_artifacts:
            logger.warning(f"地址识别器: NLP结果为空，无法识别地址。文本: '{text[:50]}...'")
            return []

        if not hasattr(nlp_artifacts, "entities") or not nlp_artifacts.entities:
            logger.warning(f"地址识别器: NER结果为空，无法识别地址。文本: '{text[:50]}...'")
            return []

        results = self._analyze_with_ner(text, nlp_artifacts)

        if not results:
            logger.warning(
                f"地址识别器: NER未识别到任何LOCATION实体，无法识别地址。文本: '{text[:50]}...'"
            )

        return results

    def _analyze_with_ner(
        self,
        text: str,
        nlp_artifacts: NlpArtifacts,
    ) -> list[RecognizerResult]:
        """
        使用NER结果分析地址

        支持两种格式：
        1. spaCy格式：nlp_artifacts.entities是spacy.tokens.Span列表
        2. PaddleNLP格式：nlp_artifacts.entities是字典列表

        Args:
            text: 原始文本
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = []
        ner_addresses_found = []

        for ent in nlp_artifacts.entities:
            if isinstance(ent, dict):
                if ent.get("label") in ("LOCATION", "LOC"):
                    address_text = ent.get("text", "")
                    start = ent.get("start", 0)
                    end = ent.get("end", len(address_text))
                    ner_addresses_found.append(address_text)

                    if self._validate_address(address_text):
                        score = self._calculate_score(address_text)
                        result = self._create_result(
                            entity_type="CN_ADDRESS",
                            start=start,
                            end=end,
                            score=score,
                        )
                        results.append(result)
                        logger.debug(
                            f"地址识别器(NER): 识别到有效地址 '{address_text}', "
                            f"位置=[{start}:{end}], 置信度={score:.2f}"
                        )
                    else:
                        logger.debug(
                            f"地址识别器(NER): NER识别的 '{address_text}' 未通过地址格式验证"
                        )
            elif hasattr(ent, "label_") and ent.label_ in ("LOCATION", "LOC", "GPE"):
                address_text = text[ent.start_char : ent.end_char]
                ner_addresses_found.append(address_text)

                if self._validate_address(address_text):
                    score = self._calculate_score(address_text)
                    result = self._create_result(
                        entity_type="CN_ADDRESS",
                        start=ent.start_char,
                        end=ent.end_char,
                        score=score,
                    )
                    results.append(result)
                    logger.debug(
                        f"地址识别器(NER): 识别到有效地址 '{address_text}', "
                        f"位置=[{ent.start_char}:{ent.end_char}], 置信度={score:.2f}"
                    )
                else:
                    logger.debug(f"地址识别器(NER): NER识别的 '{address_text}' 未通过地址格式验证")

        if ner_addresses_found:
            logger.debug(
                f"地址识别器: NER识别到 {len(ner_addresses_found)} 个LOCATION实体: {ner_addresses_found}"
            )
        else:
            logger.debug("地址识别器: NER未识别到任何LOCATION实体")

        return results

    def _validate_address(self, address: str) -> bool:
        """
        验证地址格式有效性

        仅检查基本格式：长度至少2个字符，不超过100个字符。

        Args:
            address: 地址字符串

        Returns:
            是否为有效地址格式
        """
        if not address:
            return False

        if len(address) < 2:
            return False

        return len(address) <= 100

    def _calculate_score(self, address: str) -> float:
        """
        计算地址识别置信度

        基于NER结果，给予基础置信度。

        Args:
            address: 地址字符串

        Returns:
            置信度分数
        """
        score = 0.75

        if re.search(r"[省市县区]", address):
            score += 0.05

        if re.search(r"[路街道巷]", address):
            score += 0.05

        return min(score, 0.85)
