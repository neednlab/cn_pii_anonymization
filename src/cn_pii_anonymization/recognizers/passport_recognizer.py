"""
中国护照号识别器

识别中国护照号码，支持新版和旧版格式。
"""

import re
from typing import Any, ClassVar

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNPassportRecognizer(CNPIIRecognizer):
    """
    中国护照号识别器

    识别中国护照号码，支持：
    - 新版护照：1位字母 + 8位数字（如：E12345678）
    - 旧版护照：14-15位字符
    - 港澳台通行证格式

    Attributes:
        PASSPORT_PATTERNS: 护照号匹配模式列表
        CONTEXT_WORDS: 上下文关键词列表

    Example:
        >>> recognizer = CNPassportRecognizer()
        >>> results = recognizer.analyze(
        ...     "护照号E12345678",
        ...     ["CN_PASSPORT"],
        ...     None
        ... )
    """

    PASSPORT_PATTERNS: ClassVar[list[Pattern]] = [
        Pattern(
            name="cn_passport_new",
            regex=r"[EG][A-Z]\d{8}",
            score=0.90,
        ),
        Pattern(
            name="cn_passport_old",
            regex=r"[A-Z]{1,2}\d{6,10}",
            score=0.65,
        ),
        Pattern(
            name="cn_passport_hk_macao",
            regex=r"[CH]\d{8,10}",
            score=0.80,
        ),
    ]

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "护照",
        "护照号",
        "通行证",
        "passport",
        "通行证号码",
        "证件号码",
        "护照号码",
        "港澳通行证",
        "台湾通行证",
    ]

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化护照识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_PASSPORT"],
            name="CN Passport Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )
        self._pattern_recognizer = PatternRecognizer(
            supported_entity="CN_PASSPORT",
            patterns=self.PASSPORT_PATTERNS,
            context=self.CONTEXT_WORDS,
        )

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的护照号

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = self._pattern_recognizer.analyze(text, entities, nlp_artifacts)
        return self._validate_results(text, results)

    def _validate_results(
        self,
        text: str,
        results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        """
        验证护照号有效性

        Args:
            text: 原始文本
            results: 识别结果列表

        Returns:
            验证后的结果列表
        """
        valid_results = []
        for result in results:
            passport = text[result.start : result.end]
            if self._is_valid_passport(passport):
                valid_results.append(result)
            else:
                logger.debug(f"无效护照号被过滤: {passport}")
        return valid_results

    @staticmethod
    def _is_valid_passport(passport: str) -> bool:
        """
        校验护照号格式

        Args:
            passport: 护照号字符串

        Returns:
            是否为有效的护照号
        """
        if not passport:
            return False

        if len(passport) < 6 or len(passport) > 15:
            return False

        new_passport_pattern = re.compile(r"^[EG][A-Z]\d{8}$")
        if new_passport_pattern.match(passport):
            return True

        old_passport_pattern = re.compile(r"^[A-Z]{1,2}\d{6,10}$")
        if old_passport_pattern.match(passport):
            return True

        hk_macao_pattern = re.compile(r"^[CH]\d{8,10}$")
        return bool(hk_macao_pattern.match(passport))
