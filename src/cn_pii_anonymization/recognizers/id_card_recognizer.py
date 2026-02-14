"""
中国大陆身份证识别器

识别中国大陆身份证号码，支持校验码验证。
"""

import re
from datetime import datetime
from typing import Any, ClassVar

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNIDCardRecognizer(CNPIIRecognizer):
    """
    中国大陆身份证识别器

    识别中国大陆18位身份证号码，支持：
    - 地区码验证
    - 出生日期验证
    - 校验码验证

    Attributes:
        ID_CARD_PATTERN: 身份证匹配正则
        CONTEXT_WORDS: 上下文关键词列表
        PROVINCE_CODES: 省份代码映射

    Example:
        >>> recognizer = CNIDCardRecognizer()
        >>> results = recognizer.analyze(
        ...     "身份证号110101199001011234",
        ...     ["CN_ID_CARD"],
        ...     None
        ... )
    """

    ID_CARD_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]"
    )

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "身份证",
        "身份证号",
        "证件号",
        "身份号码",
        "ID",
        "身份证件",
        "公民身份",
        "身份证号码",
        "身份证明",
        "居民身份证",
    ]

    PROVINCE_CODES: ClassVar[dict[int, str]] = {
        11: "北京",
        12: "天津",
        13: "河北",
        14: "山西",
        15: "内蒙古",
        21: "辽宁",
        22: "吉林",
        23: "黑龙江",
        31: "上海",
        32: "江苏",
        33: "浙江",
        34: "安徽",
        35: "福建",
        36: "江西",
        37: "山东",
        41: "河南",
        42: "湖北",
        43: "湖南",
        44: "广东",
        45: "广西",
        46: "海南",
        50: "重庆",
        51: "四川",
        52: "贵州",
        53: "云南",
        54: "西藏",
        61: "陕西",
        62: "甘肃",
        63: "青海",
        64: "宁夏",
        65: "新疆",
        71: "台湾",
        81: "香港",
        82: "澳门",
    }

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化身份证识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_ID_CARD"],
            name="CN ID Card Recognizer",
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
        分析文本中的身份证号

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = []

        for match in self.ID_CARD_PATTERN.finditer(text):
            id_card = match.group()
            if self._validate_id_card(id_card):
                result = self._create_result(
                    entity_type="CN_ID_CARD",
                    start=match.start(),
                    end=match.end(),
                    score=0.95,
                )
                results.append(result)
            else:
                logger.debug(f"无效身份证号被过滤: {id_card}")

        return results

    def _validate_id_card(self, id_card: str) -> bool:
        """
        验证身份证号有效性

        Args:
            id_card: 身份证号字符串

        Returns:
            是否为有效的身份证号
        """
        if len(id_card) != 18:
            return False

        province_code = int(id_card[:2])
        if province_code not in self.PROVINCE_CODES:
            return False

        if not self._validate_birth_date(id_card[6:14]):
            return False

        return self._validate_check_digit(id_card)

    @staticmethod
    def _validate_birth_date(date_str: str) -> bool:
        """
        验证出生日期

        Args:
            date_str: 8位日期字符串 (YYYYMMDD)

        Returns:
            是否为有效的日期
        """
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            if year < 1900 or year > datetime.now().year:
                return False

            birth_date = datetime(year, month, day)

            return birth_date <= datetime.now()
        except ValueError:
            return False

    @staticmethod
    def _validate_check_digit(id_card: str) -> bool:
        """
        验证校验码

        使用GB 11643-1999标准计算校验码。

        Args:
            id_card: 身份证号字符串

        Returns:
            校验码是否正确
        """
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = "10X98765432"

        total = sum(int(id_card[i]) * weights[i] for i in range(17))

        expected_check = check_codes[total % 11]
        return id_card[17].upper() == expected_check
