"""
中国姓名识别器

完全依赖PaddleNLP LAC模型的NER结果识别中文姓名。
"""

from typing import Any, ClassVar

from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNNameRecognizer(CNPIIRecognizer):
    """
    中文姓名识别器

    完全依赖PaddleNLP LAC NER结果识别中文姓名。
    如果NER未识别到PERSON实体，将输出WARNING日志并返回空结果。

    Attributes:
        CONTEXT_WORDS: 上下文关键词列表

    Example:
        >>> recognizer = CNNameRecognizer()
        >>> results = recognizer.analyze(
        ...     "联系人：张三",
        ...     ["CN_NAME"],
        ...     nlp_artifacts
        ... )
        >>> print(results[0].entity_type)
        CN_NAME
    """

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "姓名",
        "名字",
        "叫",
        "是",
        "联系人",
        "负责人",
        "经办人",
        "收件人",
        "寄件人",
        "申请人",
        "被申请人",
        "原告",
        "被告",
        "证人",
        "受害人",
        "嫌疑人",
        "当事人",
        "业主",
        "租户",
        "房东",
        "买家",
        "卖家",
        "客户",
        "用户",
        "会员",
        "员工",
        "经理",
        "总监",
        "董事长",
        "总经理",
        "先生",
        "女士",
        "小姐",
        "name",
    ]

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化姓名识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_NAME"],
            name="CN Name Recognizer",
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
        分析文本中的姓名

        完全依赖NER结果。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        if not nlp_artifacts:
            return []

        if not hasattr(nlp_artifacts, "entities") or not nlp_artifacts.entities:
            return []

        results = self._analyze_with_ner(text, nlp_artifacts)

        if not results:
            logger.debug(
                f"姓名识别器: NER未识别到任何PERSON实体，无法识别姓名。文本: '{text[:50]}...'"
            )

        return results

    def _analyze_with_ner(
        self,
        text: str,
        nlp_artifacts: NlpArtifacts,
    ) -> list[RecognizerResult]:
        """
        使用NER结果分析姓名

        支持格式：
        1. PaddleNLP格式：nlp_artifacts.entities是字典列表

        Args:
            text: 原始文本
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        results = []
        ner_names_found = []

        for ent in nlp_artifacts.entities:
            if isinstance(ent, dict):
                if ent.get("label") in ("PERSON", "PER"):
                    name_text = ent.get("text", "")
                    start = ent.get("start", 0)
                    end = ent.get("end", len(name_text))
                    ner_names_found.append(name_text)

                    if self._validate_chinese_name(name_text):
                        score = self._calculate_score(name_text)
                        result = self._create_result(
                            entity_type="CN_NAME",
                            start=start,
                            end=end,
                            score=score,
                        )
                        results.append(result)
                        logger.debug(
                            f"姓名识别器(NER): 识别到有效姓名 '{name_text}', "
                            f"位置=[{start}:{end}], 置信度={score:.2f}"
                        )
                    else:
                        logger.debug(f"姓名识别器(NER): NER识别的 '{name_text}' 未通过姓名格式验证")
            elif hasattr(ent, "label_") and ent.label_ == "PERSON":
                name_text = text[ent.start_char : ent.end_char]
                ner_names_found.append(name_text)

                if self._validate_chinese_name(name_text):
                    score = self._calculate_score(name_text)
                    result = self._create_result(
                        entity_type="CN_NAME",
                        start=ent.start_char,
                        end=ent.end_char,
                        score=score,
                    )
                    results.append(result)
                    logger.debug(
                        f"姓名识别器(NER): 识别到有效姓名 '{name_text}', "
                        f"位置=[{ent.start_char}:{ent.end_char}], 置信度={score:.2f}"
                    )
                else:
                    logger.debug(f"姓名识别器(NER): NER识别的 '{name_text}' 未通过姓名格式验证")

        if ner_names_found:
            logger.debug(
                f"姓名识别器: NER识别到 {len(ner_names_found)} 个PERSON实体: {ner_names_found}"
            )
        else:
            logger.debug("姓名识别器: NER未识别到任何PERSON实体")

        return results

    def _validate_chinese_name(self, name: str) -> bool:
        """
        验证中文姓名格式有效性

        仅检查基本格式：长度2-5个中文字符。

        Args:
            name: 姓名字符串

        Returns:
            是否为有效姓名格式
        """
        if not name:
            return False

        if len(name) < 2 or len(name) > 5:
            return False

        # 判断姓名中的每个字符都在常用汉字 Unicode 范围内（\u4e00-\u9fa5）
        return all("\u4e00" <= c <= "\u9fa5" for c in name)

    def _calculate_score(self, name: str) -> float:
        """
        计算姓名识别置信度

        基于NER结果，给予基础置信度。

        Args:
            name: 姓名字符串

        Returns:
            置信度分数
        """
        score = 0.75

        if len(name) in (2, 3):
            score += 0.05

        return min(score, 0.85)
