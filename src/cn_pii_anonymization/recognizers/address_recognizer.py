"""
中国地址识别器

识别中国大陆地址信息，支持多级地址格式。
支持PaddleNLP LAC模型的NER结果。
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

    识别中国大陆地址，支持以下格式：
    - 省级：北京市、上海市、广东省等
    - 市级：广州市、深圳市等
    - 区县级：朝阳区、海淀区等
    - 详细地址：街道、门牌号、小区等

    支持PaddleNLP LAC模型的LOC/LOCATION实体。

    Attributes:
        PROVINCES: 省级行政区划列表
        PROVINCE_ABBREVS: 省级简称映射
        ADDRESS_KEYWORDS: 地址关键词列表
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

    PROVINCES: ClassVar[list[str]] = [
        "北京市",
        "上海市",
        "天津市",
        "重庆市",
        "河北省",
        "山西省",
        "辽宁省",
        "吉林省",
        "黑龙江省",
        "江苏省",
        "浙江省",
        "安徽省",
        "福建省",
        "江西省",
        "山东省",
        "河南省",
        "湖北省",
        "湖南省",
        "广东省",
        "海南省",
        "四川省",
        "贵州省",
        "云南省",
        "陕西省",
        "甘肃省",
        "青海省",
        "台湾省",
        "内蒙古自治区",
        "广西壮族自治区",
        "西藏自治区",
        "宁夏回族自治区",
        "新疆维吾尔自治区",
        "香港特别行政区",
        "澳门特别行政区",
    ]

    PROVINCE_ABBREVS: ClassVar[dict[str, str]] = {
        "北京": "北京市",
        "上海": "上海市",
        "天津": "天津市",
        "重庆": "重庆市",
        "河北": "河北省",
        "山西": "山西省",
        "辽宁": "辽宁省",
        "吉林": "吉林省",
        "黑龙江": "黑龙江省",
        "江苏": "江苏省",
        "浙江": "浙江省",
        "安徽": "安徽省",
        "福建": "福建省",
        "江西": "江西省",
        "山东": "山东省",
        "河南": "河南省",
        "湖北": "湖北省",
        "湖南": "湖南省",
        "广东": "广东省",
        "海南": "海南省",
        "四川": "四川省",
        "贵州": "贵州省",
        "云南": "云南省",
        "陕西": "陕西省",
        "甘肃": "甘肃省",
        "青海": "青海省",
        "台湾": "台湾省",
        "内蒙古": "内蒙古自治区",
        "广西": "广西壮族自治区",
        "西藏": "西藏自治区",
        "宁夏": "宁夏回族自治区",
        "新疆": "新疆维吾尔自治区",
        "香港": "香港特别行政区",
        "澳门": "澳门特别行政区",
    }

    ADDRESS_KEYWORDS: ClassVar[list[str]] = [
        "路",
        "街",
        "道",
        "巷",
        "弄",
        "号",
        "栋",
        "幢",
        "单元",
        "室",
        "层",
        "楼",
        "小区",
        "花园",
        "大厦",
        "公寓",
        "广场",
        "城",
        "村",
        "镇",
        "乡",
        "县",
        "市",
        "区",
        "旗",
        "盟",
        "州",
        "开发区",
        "高新区",
        "工业园",
        "科技园",
        "产业园",
    ]

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

    ADDRESS_END_PATTERNS: ClassVar[list[str]] = [
        r"\d+号",
        r"\d+栋",
        r"\d+幢",
        r"\d+单元",
        r"\d+室",
        r"\d+层",
        r"\d+楼",
        r"\d+号院",
        r".*小区",
        r".*花园",
        r".*大厦",
        r".*公寓",
        r".*广场",
        r".*城",
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
        self._province_pattern = self._build_province_pattern()
        self._address_end_regex = re.compile("|".join(self.ADDRESS_END_PATTERNS), re.UNICODE)

    def _build_province_pattern(self) -> re.Pattern:
        """
        构建省份匹配正则表达式

        Returns:
            编译后的正则表达式
        """
        province_names = sorted(self.PROVINCES, key=len, reverse=True)
        province_abbrevs = sorted(self.PROVINCE_ABBREVS.keys(), key=len, reverse=True)
        pattern = "|".join(province_names + province_abbrevs)
        return re.compile(pattern, re.UNICODE)

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的地址

        支持PaddleNLP LAC模型的NER结果格式。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = []

        if nlp_artifacts:
            ner_results = self._analyze_with_ner(text, nlp_artifacts)
            results.extend(ner_results)

        rule_results = self._analyze_with_rules(text)
        results.extend(rule_results)

        results = self._merge_overlapping_results(results)
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

        if not hasattr(nlp_artifacts, "entities") or not nlp_artifacts.entities:
            return results

        for ent in nlp_artifacts.entities:
            if isinstance(ent, dict):
                if ent.get("label") in ("LOCATION", "LOC"):
                    address_text = ent.get("text", "")
                    start = ent.get("start", 0)
                    end = ent.get("end", len(address_text))
                    if self._validate_address(address_text):
                        score = self._calculate_score(address_text)
                        result = self._create_result(
                            entity_type="CN_ADDRESS",
                            start=start,
                            end=end,
                            score=score,
                        )
                        results.append(result)
            elif hasattr(ent, "label_") and ent.label_ in ("LOCATION", "LOC", "GPE"):
                address_text = text[ent.start_char : ent.end_char]
                if self._validate_address(address_text):
                    score = self._calculate_score(address_text)
                    result = self._create_result(
                        entity_type="CN_ADDRESS",
                        start=ent.start_char,
                        end=ent.end_char,
                        score=score,
                    )
                    results.append(result)

        return results

    def _analyze_with_rules(self, text: str) -> list[RecognizerResult]:
        """
        使用规则匹配分析地址

        Args:
            text: 待分析的文本

        Returns:
            识别结果列表
        """
        results = []

        for match in self._province_pattern.finditer(text):
            start = match.start()
            end = self._find_address_end(text, start)
            address_text = text[start:end]

            if self._validate_address(address_text):
                score = self._calculate_score(address_text)
                result = self._create_result(
                    entity_type="CN_ADDRESS",
                    start=start,
                    end=end,
                    score=score,
                )
                results.append(result)

        return results

    def _find_address_end(self, text: str, start: int) -> int:
        """
        查找地址结束位置

        Args:
            text: 原始文本
            start: 地址开始位置

        Returns:
            地址结束位置
        """
        end = start
        max_end = min(start + 100, len(text))

        while end < max_end:
            char = text[end]
            if self._is_address_char(char, text, end):
                end += 1
            else:
                break

        while end > start and text[end - 1] in "，。、；：！？,.;:!?":
            end -= 1

        return end

    def _is_address_char(self, char: str, text: str, pos: int) -> bool:
        """
        判断字符是否属于地址

        Args:
            char: 当前字符
            text: 原始文本
            pos: 当前位置

        Returns:
            是否为地址字符
        """
        if char.isalnum():
            return True

        if char in self.ADDRESS_KEYWORDS:
            return True

        if char in "（）()":
            return True

        if char in "-—_·．.":
            return True

        return char in "号栋幢单元室层楼院"

    def _validate_address(self, address: str) -> bool:
        """
        验证地址有效性

        Args:
            address: 地址字符串

        Returns:
            是否为有效地址
        """
        if len(address) < 4:
            return False

        if len(address) > 100:
            return False

        has_province = any(p in address for p in self.PROVINCES) or any(
            abbrev in address and address.find(abbrev) == 0 for abbrev in self.PROVINCE_ABBREVS
        )
        if not has_province:
            return False

        return any(kw in address for kw in self.ADDRESS_KEYWORDS)

    def _calculate_score(self, address: str) -> float:
        """
        计算地址识别置信度

        Args:
            address: 地址字符串

        Returns:
            置信度分数
        """
        score = 0.5

        if any(p in address for p in self.PROVINCES):
            score += 0.15

        if any(kw in address for kw in ["市", "区", "县"]):
            score += 0.1

        if any(kw in address for kw in ["路", "街", "道"]):
            score += 0.1

        if self._address_end_regex.search(address):
            score += 0.15

        if any(kw in address for kw in ["小区", "花园", "大厦", "公寓"]):
            score += 0.05

        if re.search(r"\d+号", address):
            score += 0.05

        return min(score, 0.95)

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
                    if result.score > existing.score:
                        merged.remove(existing)
                    else:
                        is_overlapping = True
                    break

            if not is_overlapping:
                merged.append(result)

        return merged
