"""
中国大陆银行卡识别器

识别中国大陆银行卡号码，支持Luhn算法校验。
"""

import re
from typing import Any, ClassVar

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNBankCardRecognizer(CNPIIRecognizer):
    """
    中国大陆银行卡识别器

    识别中国大陆银行卡号码，支持：
    - 16-19位数字格式
    - Luhn算法校验
    - 常见银行BIN码识别

    Attributes:
        BANK_CARD_PATTERN: 银行卡匹配正则
        CONTEXT_WORDS: 上下文关键词列表
        BANK_BIN_CODES: 常见银行BIN码映射

    Example:
        >>> recognizer = CNBankCardRecognizer()
        >>> results = recognizer.analyze(
        ...     "银行卡号6222021234567890123",
        ...     ["CN_BANK_CARD"],
        ...     None
        ... )
    """

    BANK_CARD_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?<![a-zA-Z\d])\d(?:\s*\d){15,18}(?![a-zA-Z\d])"
    )

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "银行卡",
        "卡号",
        "账号",
        "银行账号",
        "信用卡",
        "借记卡",
        "储蓄卡",
        "bank",
        "card",
        "account",
        "银行卡号",
        "信用卡号",
    ]

    BANK_BIN_CODES: ClassVar[dict[str, list[str]]] = {
        "工商银行": ["622202", "622203", "622208", "621225", "621226"],
        "农业银行": ["622848", "622849", "622845", "622846"],
        "中国银行": ["621660", "621661", "621663", "621665"],
        "建设银行": ["621700", "436742", "436745", "622280"],
        "交通银行": ["622260", "622261", "622262"],
        "招商银行": ["622580", "622588", "621286", "621483"],
        "浦发银行": ["622518", "622520", "622521", "622522"],
        "民生银行": ["622615", "622617", "622618", "622622"],
        "兴业银行": ["622909", "622910", "622911", "622912"],
        "平安银行": ["622155", "622156", "622157", "622158"],
        "光大银行": ["622660", "622661", "622662", "622663"],
        "华夏银行": ["622630", "622631", "622632"],
        "广发银行": ["622568", "622569", "622570"],
        "中信银行": ["622690", "622691", "622692"],
        "邮储银行": ["622188", "622199", "622810"],
    }

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化银行卡识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_BANK_CARD"],
            name="CN Bank Card Recognizer",
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
        分析文本中的银行卡号

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = []

        for match in self.BANK_CARD_PATTERN.finditer(text):
            card_number = match.group()
            if self._validate_bank_card(card_number):
                score = self._calculate_score(card_number)
                result = self._create_result(
                    entity_type="CN_BANK_CARD",
                    start=match.start(),
                    end=match.end(),
                    score=score,
                )
                results.append(result)
            else:
                logger.debug(f"无效银行卡号被过滤: {card_number}")

        return results

    def _validate_bank_card(self, card_number: str) -> bool:
        """
        使用Luhn算法验证银行卡号

        Args:
            card_number: 银行卡号字符串（可能包含空格）

        Returns:
            是否为有效的银行卡号
        """
        # 去除空格后再验证
        card_number = card_number.replace(" ", "")

        if not card_number.isdigit():
            return False

        if len(card_number) < 16 or len(card_number) > 19:
            return False

        return self._luhn_check(card_number)

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """
        Luhn算法校验

        Args:
            card_number: 银行卡号字符串

        Returns:
            是否通过Luhn校验
        """
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        total = sum(odd_digits)
        for d in even_digits:
            doubled = d * 2
            total += doubled if doubled < 10 else doubled - 9

        return total % 10 == 0

    def _calculate_score(self, card_number: str) -> float:
        """
        根据BIN码计算置信度

        Args:
            card_number: 银行卡号字符串（可能包含空格）

        Returns:
            置信度分数
        """
        # 去除空格后再计算
        card_number = card_number.replace(" ", "")

        for _bank, bin_codes in self.BANK_BIN_CODES.items():
            if any(card_number.startswith(code) for code in bin_codes):
                return 0.95
        return 0.7
