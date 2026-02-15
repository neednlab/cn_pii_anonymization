"""
中国姓名识别器
使用PaddleNLP Taskflow的information_extraction方法进行姓名识别。
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
    使用PaddleNLP Taskflow的information_extraction方法进行姓名识别。

    Attributes:
        CONTEXT_WORDS: 上下文关键词列表
        _ie_engine: 信息抽取引擎实例

    Example:
        >>> recognizer = CNNameRecognizer(ie_engine=ie_engine)
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

    def __init__(self, ie_engine: Any = None, **kwargs: Any) -> None:
        """
        初始化姓名识别器

        Args:
            ie_engine: 信息抽取引擎实例（PaddleNLP Taskflow information_extraction）
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_NAME"],
            name="CN Name Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )
        self._ie_engine = ie_engine
        logger.debug("姓名识别器初始化完成（使用信息抽取引擎）")

    def set_ie_engine(self, ie_engine: Any) -> None:
        """
        设置信息抽取引擎

        Args:
            ie_engine: 信息抽取引擎实例
        """
        self._ie_engine = ie_engine
        logger.debug("姓名识别器已设置新的信息抽取引擎")

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的姓名

        使用信息抽取模型识别姓名，置信度直接采用IE返回的probability结果。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果（此识别器不使用）

        Returns:
            识别结果列表
        """
        if not text:
            return []

        if self._ie_engine is None:
            logger.debug("姓名识别器: 信息抽取引擎未设置，跳过识别")
            return []

        results = self._analyze_with_ie(text)

        if not results:
            logger.debug(f"姓名识别器: 未识别到任何姓名。文本: '{text[:50]}...'")

        return results

    def _analyze_with_ie(self, text: str) -> list[RecognizerResult]:
        """
        使用信息抽取模型分析姓名

        Args:
            text: 原始文本

        Returns:
            识别结果列表
        """
        results = []
        names_found = []

        try:
            ie_result = self._ie_engine.extract_names(text)

            for name_info in ie_result:
                name_text = name_info.get("text", "")
                probability = name_info.get("probability", 0.85)

                if not name_text:
                    continue

                names_found.append(name_text)

                start = text.find(name_text)
                if start == -1:
                    logger.warning(
                        f"姓名识别器: 无法在原文中定位姓名 '{name_text}'"
                    )
                    continue

                end = start + len(name_text)

                # 直接使用IE返回的probability作为置信度
                result = self._create_result(
                    entity_type="CN_NAME",
                    start=start,
                    end=end,
                    score=probability,
                )
                results.append(result)
                logger.debug(
                    f"姓名识别器(IE): 识别到姓名 '{name_text}', "
                    f"位置=[{start}:{end}], 置信度={probability:.4f}"
                )

        except Exception as e:
            logger.error(f"姓名识别器: 信息抽取失败 - {e}")

        if names_found:
            logger.debug(
                f"姓名识别器: 信息抽取识别到 {len(names_found)} 个姓名: {names_found}"
            )
        else:
            logger.debug("姓名识别器: 信息抽取未识别到任何姓名")

        return results
