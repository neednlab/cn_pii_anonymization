"""
中国大陆手机号识别器

识别中国大陆手机号码，支持多种格式。
"""

import re
from typing import Any, ClassVar

from presidio_analyzer import Pattern, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNPhoneRecognizer(CNPIIRecognizer):
    """
    中国大陆手机号识别器

    识别中国大陆手机号码，支持以下格式：
    - 11位手机号：13812345678
    - 带国际区号：+8613812345678, 008613812345678
    - 带分隔符：138-1234-5678, 138 1234 5678

    Attributes:
        PATTERNS: 手机号匹配模式列表
        CONTEXT_WORDS: 上下文关键词列表

    Example:
        >>> recognizer = CNPhoneRecognizer()
        >>> results = recognizer.analyze("我的手机号是13812345678", ["CN_PHONE_NUMBER"], None)
        >>> print(results[0].entity_type)
        CN_PHONE_NUMBER
    """

    PATTERNS: ClassVar[list[Pattern]] = [
        Pattern(
            name="cn_phone_bare",
            regex=r"1[3-9]\d{9}",
            score=0.85,
        ),
        Pattern(
            name="cn_phone_with_country_code",
            regex=r"(?:\+86|0086)1[3-9]\d{9}",
            score=0.90,
        ),
        Pattern(
            name="cn_phone_with_separator",
            regex=r"(?:\+86|0086)?1[3-9]\d[\s\-]?\d{4}[\s\-]?\d{4}",
            score=0.75,
        ),
    ]

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "手机",
        "电话",
        "联系方式",
        "联系电话",
        "手机号",
        "手机号码",
        "移动电话",
        "mobile",
        "phone",
        "tel",
        "联系电话",
        "电话号码",
    ]

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化手机号识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_PHONE_NUMBER"],
            name="CN Phone Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )
        self._compiled_patterns = [
            (pattern.name, re.compile(pattern.regex), pattern.score) for pattern in self.PATTERNS
        ]

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的手机号

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        all_results = []

        for _pattern_name, compiled_pattern, score in self._compiled_patterns:
            for match in compiled_pattern.finditer(text):
                phone = match.group()
                if self._is_valid_phone(phone):
                    # 检查是否是身份证号的一部分
                    if self._is_part_of_id_card(text, match.start(), match.end()):
                        logger.debug(f"手机号匹配被过滤（身份证号的一部分）: {phone}")
                        continue

                    # 检查是否是银行卡号的一部分
                    if self._is_part_of_bank_card(text, match.start(), match.end()):
                        logger.debug(f"手机号匹配被过滤（银行卡号的一部分）: {phone}")
                        continue

                    result = self._create_result(
                        entity_type="CN_PHONE_NUMBER",
                        start=match.start(),
                        end=match.end(),
                        score=score,
                    )
                    all_results.append(result)

        return self._merge_overlapping_results(all_results)

    def _merge_overlapping_results(
        self,
        results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        """
        合并重叠的结果，保留最高分数的结果

        Args:
            results: 识别结果列表

        Returns:
            合并后的结果列表
        """
        if not results:
            return []

        sorted_results = sorted(results, key=lambda r: (r.start, -r.score))

        merged = []
        for result in sorted_results:
            is_overlapping = False
            for existing in merged:
                if result.start >= existing.start and result.end <= existing.end:
                    is_overlapping = True
                    break
                if result.start < existing.end and result.end > existing.start:
                    is_overlapping = True
                    break

            if not is_overlapping:
                merged.append(result)

        return merged

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """
        校验手机号格式

        Args:
            phone: 手机号字符串

        Returns:
            是否为有效的手机号
        """
        clean_phone = re.sub(r"[\s\-\+]", "", phone)
        clean_phone = re.sub(r"^86", "", clean_phone)
        clean_phone = re.sub(r"^0086", "", clean_phone)

        if len(clean_phone) != 11:
            return False

        if not clean_phone.isdigit():
            return False

        return clean_phone[0] == "1" and clean_phone[1] in "3456789"

    def _is_part_of_id_card(self, text: str, start: int, end: int) -> bool:
        """
        检查匹配位置是否是身份证号的一部分

        身份证号格式：18位，前17位数字，最后一位数字或X
        如果匹配的手机号前后有足够的数字，可能是身份证号的一部分

        Args:
            text: 原始文本
            start: 匹配起始位置
            end: 匹配结束位置

        Returns:
            是否是身份证号的一部分
        """
        # 检查前面是否有足够的数字
        prefix_digits = 0
        for i in range(start - 1, -1, -1):
            if text[i].isdigit():
                prefix_digits += 1
            else:
                break

        # 检查后面是否有足够的数字或X
        suffix_chars = 0
        for i in range(end, len(text)):
            if text[i].isdigit() or text[i].upper() == "X":
                suffix_chars += 1
            else:
                break

        # 如果前面有6位以上数字，且后面有1位以上数字/X，则可能是身份证号
        if prefix_digits >= 6 and suffix_chars >= 1:
            id_start = start - prefix_digits
            id_end = end + suffix_chars
            potential_id = text[id_start:id_end]
            if len(potential_id) == 18 and potential_id[:17].isdigit():
                if potential_id[17].isdigit() or potential_id[17].upper() == "X":
                    return True

        return False

    def _is_part_of_bank_card(self, text: str, start: int, end: int) -> bool:
        """
        检查匹配位置是否是银行卡号的一部分

        银行卡号格式：16-19位数字
        如果匹配的手机号前后有足够的数字，可能是银行卡号的一部分

        Args:
            text: 原始文本
            start: 匹配起始位置
            end: 匹配结束位置

        Returns:
            是否是银行卡号的一部分
        """
        # 检查前面是否有数字
        prefix_digits = 0
        for i in range(start - 1, -1, -1):
            if text[i].isdigit():
                prefix_digits += 1
            else:
                break

        # 检查后面是否有数字
        suffix_digits = 0
        for i in range(end, len(text)):
            if text[i].isdigit():
                suffix_digits += 1
            else:
                break

        # 如果前后数字加起来超过5位，则可能是银行卡号的一部分
        # 银行卡号16-19位，手机号11位，所以如果前后有超过5位数字，说明是更长数字串的一部分
        total_extra = prefix_digits + suffix_digits
        if total_extra >= 5:
            return True

        return False
