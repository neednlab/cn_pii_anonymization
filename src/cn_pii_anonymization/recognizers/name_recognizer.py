"""
中国姓名识别器
使用PaddleNLP Taskflow的information_extraction方法进行姓名识别。
支持自定义allow_list和deny_list配置。
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

    支持自定义allow_list和deny_list配置：
    - allow_list: 允许通过的姓名列表，这些姓名不会被识别为PII
    - deny_list: 必须被脱敏的姓名列表，无论IE是否识别都会强制标记为PII

    Attributes:
        CONTEXT_WORDS: 上下文关键词列表
        _ie_engine: 信息抽取引擎实例
        _ie_cache: IE结果缓存，用于批量处理优化
        _allow_list: 允许通过的姓名列表
        _deny_list: 必须被脱敏的姓名列表

    Example:
        >>> recognizer = CNNameRecognizer(
        ...     ie_engine=ie_engine,
        ...     allow_list=["张三", "李四"],
        ...     deny_list=["王五"]
        ... )
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

    NAME_SCHEMA_KEYS: ClassVar[set[str]] = {"姓名", "人名"}

    def __init__(
        self,
        ie_engine: Any = None,
        allow_list: list[str] | None = None,
        deny_list: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化姓名识别器

        Args:
            ie_engine: 信息抽取引擎实例（PaddleNLP Taskflow information_extraction）
            allow_list: 允许通过的姓名列表，这些姓名不会被识别为PII
            deny_list: 必须被脱敏的姓名列表，无论IE是否识别都会强制标记为PII
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_NAME"],
            name="CN Name Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )
        self._ie_engine = ie_engine
        self._ie_cache: dict[str, list[dict]] | None = None
        # 过滤空字符串
        self._allow_list: set[str] = (
            {name for name in allow_list if name and name.strip()} if allow_list else set()
        )
        self._deny_list: set[str] = (
            {name for name in deny_list if name and name.strip()} if deny_list else set()
        )
        logger.debug(
            f"姓名识别器初始化完成（使用信息抽取引擎），"
            f"allow_list={self._allow_list}, deny_list={self._deny_list}"
        )

    def set_ie_engine(self, ie_engine: Any) -> None:
        """
        设置信息抽取引擎

        Args:
            ie_engine: 信息抽取引擎实例
        """
        self._ie_engine = ie_engine
        logger.debug("姓名识别器已设置新的信息抽取引擎")

    def set_allow_list(self, allow_list: list[str] | None) -> None:
        """
        设置允许通过的姓名列表

        Args:
            allow_list: 允许通过的姓名列表，这些姓名不会被识别为PII
        """
        if allow_list:
            self._allow_list = {name for name in allow_list if name and name.strip()}
        else:
            self._allow_list = set()
        logger.debug(f"姓名识别器已设置allow_list: {self._allow_list}")

    def set_deny_list(self, deny_list: list[str] | None) -> None:
        """
        设置必须被脱敏的姓名列表

        Args:
            deny_list: 必须被脱敏的姓名列表，无论IE是否识别都会强制标记为PII
        """
        if deny_list:
            self._deny_list = {name for name in deny_list if name and name.strip()}
        else:
            self._deny_list = set()
        logger.debug(f"姓名识别器已设置deny_list: {self._deny_list}")

    def get_allow_list(self) -> list[str]:
        """
        获取当前的允许列表

        Returns:
            允许通过的姓名列表
        """
        return list(self._allow_list)

    def get_deny_list(self) -> list[str]:
        """
        获取当前的拒绝列表

        Returns:
            必须被脱敏的姓名列表
        """
        return list(self._deny_list)

    def set_ie_cache(self, cache: dict[str, list[dict]] | None) -> None:
        """
        设置IE结果缓存

        用于批量处理优化，避免重复调用IE引擎。

        Args:
            cache: IE结果缓存字典，key为文本，value为抽取结果
        """
        self._ie_cache = cache
        logger.debug(f"姓名识别器已设置IE缓存，包含 {len(cache) if cache else 0} 个条目")

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
        分析文本中的姓名

        使用信息抽取模型识别姓名，置信度直接采用IE返回的probability结果。
        同时处理allow_list和deny_list：
        - allow_list中的姓名不会被识别为PII（从IE结果中过滤）
        - deny_list中的姓名无论IE是否识别，都会强制标记为PII

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果（此识别器不使用）

        Returns:
            识别结果列表
        """
        if not text:
            return []

        results = []

        # 1. 先处理deny_list：强制标记为PII
        deny_results = self._process_deny_list(text)
        results.extend(deny_results)

        # 2. 处理IE识别结果，过滤allow_list中的姓名
        if self._ie_engine is not None:
            ie_results = self._analyze_with_ie(text)
            # 过滤掉在allow_list中的姓名
            filtered_ie_results = [
                r for r in ie_results if text[r.start : r.end] not in self._allow_list
            ]
            # 过滤掉已被deny_list覆盖的结果（避免重复）
            deny_positions = {(r.start, r.end) for r in deny_results}
            filtered_ie_results = [
                r for r in filtered_ie_results if (r.start, r.end) not in deny_positions
            ]
            results.extend(filtered_ie_results)

        if not results:
            logger.debug(f"姓名识别器: 未识别到任何姓名。文本: '{text[:50]}...'")

        return results

    def _process_deny_list(self, text: str) -> list[RecognizerResult]:
        """
        处理deny_list，强制标记为PII

        在文本中搜索deny_list中的姓名，找到后强制标记为PII。
        使用高置信度（1.0）表示这是用户明确要求脱敏的姓名。

        Args:
            text: 原始文本

        Returns:
            识别结果列表
        """
        results = []

        if not self._deny_list:
            return results

        for name in self._deny_list:
            # 在文本中查找所有出现的位置
            start = 0
            while True:
                pos = text.find(name, start)
                if pos == -1:
                    break

                end = pos + len(name)
                result = self._create_result(
                    entity_type="CN_NAME",
                    start=pos,
                    end=end,
                    score=1.0,  # 使用最高置信度，表示用户明确要求脱敏
                )
                results.append(result)
                logger.debug(
                    f"姓名识别器(deny_list): 强制标记姓名 '{name}', 位置=[{pos}:{end}], 置信度=1.0"
                )
                start = end

        if results:
            logger.debug(f"姓名识别器: deny_list强制标记了 {len(results)} 个姓名")

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
        # 用于合并相同位置的重复结果，key为(start, end)，value为(result, probability)
        position_map: dict[tuple[int, int], tuple[RecognizerResult, float]] = {}

        try:
            # 优先使用缓存
            if self._ie_cache is not None and text in self._ie_cache:
                ie_result = self._ie_cache[text]
                # 从缓存结果中提取姓名（支持"姓名"和"人名"两种key）
                names = []
                for item in ie_result:
                    if isinstance(item, dict):
                        for key in self.NAME_SCHEMA_KEYS:
                            if key in item:
                                for name in item[key]:
                                    names.append(
                                        {
                                            "text": name.get("text", ""),
                                            "probability": name.get("probability", 0.85),
                                        }
                                    )
            else:
                # 缓存未命中，直接调用IE引擎
                ie_result = self._ie_engine.extract_names(text)
                names = ie_result

            for name_info in names:
                name_text = name_info.get("text", "")
                probability = name_info.get("probability", 0.85)

                if not name_text:
                    continue

                names_found.append(name_text)

                start = text.find(name_text)
                if start == -1:
                    logger.warning(f"姓名识别器: 无法在原文中定位姓名 '{name_text}'")
                    continue

                end = start + len(name_text)
                position = (start, end)

                # 合并相同位置的结果，只保留置信度最高的
                if position in position_map:
                    existing_result, existing_prob = position_map[position]
                    if probability > existing_prob:
                        # 新结果置信度更高，替换旧结果
                        result = self._create_result(
                            entity_type="CN_NAME",
                            start=start,
                            end=end,
                            score=probability,
                        )
                        position_map[position] = (result, probability)
                        logger.debug(
                            f"姓名识别器(IE): 合并重复结果 '{name_text}', "
                            f"位置=[{start}:{end}], 更高置信度={probability:.4f} (原={existing_prob:.4f})"
                        )
                    else:
                        logger.debug(
                            f"姓名识别器(IE): 忽略重复结果 '{name_text}', "
                            f"位置=[{start}:{end}], 较低置信度={probability:.4f} (保留={existing_prob:.4f})"
                        )
                else:
                    # 新位置，直接添加
                    result = self._create_result(
                        entity_type="CN_NAME",
                        start=start,
                        end=end,
                        score=probability,
                    )
                    position_map[position] = (result, probability)
                    logger.debug(
                        f"姓名识别器(IE): 识别到姓名 '{name_text}', "
                        f"位置=[{start}:{end}], 置信度={probability:.4f}"
                    )

            # 从position_map中提取最终结果
            results = [item[0] for item in position_map.values()]

        except Exception as e:
            logger.error(f"姓名识别器: 信息抽取失败 - {e}")

        if names_found:
            logger.debug(f"姓名识别器: 信息抽取识别到 {len(names_found)} 个姓名(含重复), 合并后 {len(results)} 个")
        else:
            logger.debug("姓名识别器: 信息抽取未识别到任何姓名")

        return results
