"""
PaddleNLP NLP引擎模块

封装PaddleNLP Taskflow，提供中文NLP处理能力。
"""

import os

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_onednn_backend"] = "0"
os.environ["FLAGS_disable_onednn_backend"] = "1"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_json_format_model"] = "0"
os.environ["PADDLE_PDX_USE_PIR_TRT"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["PADDLE_PDX_MODEL_SOURCE"] = "bos"

from typing import Any, ClassVar

from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class PaddleNlpArtifacts(NlpArtifacts):
    """
    PaddleNLP处理结果

    继承Presidio的NlpArtifacts，兼容其接口。

    Attributes:
        entities: NER识别的实体列表
        tokens: 分词结果列表
        tokens_indices: 分词索引列表
        lemmas: 词形还原列表
        nlp_engine: NLP引擎
        language: 语言代码
        scores: 实体置信度列表
        keywords: 关键词列表
    """

    def __init__(
        self,
        entities: list[Any] | None = None,
        tokens: list[str] | None = None,
        tokens_indices: list[int] | None = None,
        lemmas: list[str] | None = None,
        nlp_engine: Any = None,
        language: str = "zh",
        scores: list[float] | None = None,
    ) -> None:
        self.entities = entities or []
        self.tokens = tokens or []
        self.tokens_indices = tokens_indices or []
        self.lemmas = lemmas or []
        self.nlp_engine = nlp_engine
        self.language = language
        self.scores = scores or [0.85] * len(self.entities)
        self.keywords = self._extract_keywords(lemmas or [])

    def _extract_keywords(self, lemmas: list[str]) -> list[str]:
        """从词形列表中提取关键词"""
        keywords = []
        for lemma in lemmas:
            if lemma and lemma not in ("-", "，", "。", "！", "？"):
                keywords.append(lemma.lower())
        return keywords

    def to_json(self) -> str:
        """转换为JSON字符串"""
        import json

        return json.dumps(
            {
                "entities": [str(e) for e in self.entities],
                "tokens": self.tokens,
                "tokens_indices": self.tokens_indices,
                "lemmas": self.lemmas,
                "language": self.language,
                "scores": self.scores,
                "keywords": self.keywords,
            }
        )


class PaddleNLPEngine:
    """
    PaddleNLP引擎

    封装PaddleNLP Taskflow，提供中文NLP处理能力，包括：
    - 分词 (lexical_analysis)
    - 词性标注
    - 命名实体识别

    兼容Presidio框架的NlpEngine接口。

    Example:
        >>> engine = PaddleNLPEngine()
        >>> artifacts = engine.process_text("张三的手机号是13812345678")
        >>> print(artifacts.tokens)
    """

    STOPWORDS: ClassVar[set[str]] = {
        "的",
        "了",
        "是",
        "在",
        "我",
        "有",
        "和",
        "就",
        "不",
        "人",
        "都",
        "一",
        "一个",
        "上",
        "也",
        "很",
        "到",
        "说",
        "要",
        "去",
        "你",
        "会",
        "着",
        "没有",
        "看",
        "好",
        "自己",
        "这",
        "那",
        "她",
        "他",
        "它",
        "们",
        "这个",
        "那个",
        "什么",
        "怎么",
        "吗",
        "呢",
        "啊",
        "吧",
        "哦",
        "嗯",
        "呀",
        "哈",
        "嘿",
        "喂",
        "哎",
        "唉",
    }

    PUNCTUATION: ClassVar[set[str]] = {
        "，",
        "。",
        "！",
        "？",
        "；",
        "：",
        """, """,
        "'",
        "（",
        "）",
        "【",
        "】",
        "《",
        "》",
        "、",
        "…",
        "—",
        "～",
        "·",
        ".",
        ",",
        "!",
        "?",
        ";",
        ":",
        "(",
        ")",
        "[",
        "]",
        "<",
        ">",
        "-",
        "_",
        "/",
        "\\",
    }

    NER_TAG_MAP: ClassVar[dict[str, str]] = {
        "PER": "PERSON",
        "PERSON": "PERSON",
        "nr": "PERSON",
        "LOC": "LOCATION",
        "LOCATION": "LOCATION",
        "ns": "LOCATION",
        "ORG": "ORG",
        "ORGANIZATION": "ORG",
        "nt": "ORG",
        "TIME": "DATE",
        "t": "DATE",
    }

    def __init__(self, use_gpu: bool = False) -> None:
        """
        初始化PaddleNLP引擎

        Args:
            use_gpu: 是否使用GPU加速
        """
        self._use_gpu = use_gpu
        self._lac: Any = None
        self._initialized = False
        self._init_error: str | None = None
        logger.debug(f"PaddleNLP引擎初始化: use_gpu={use_gpu}")

    def is_loaded(self) -> bool:
        """检查引擎是否已加载"""
        return self._initialized

    def load(self) -> None:
        """加载引擎（兼容Presidio接口）"""
        self._init_lac()

    def _init_lac(self) -> None:
        """延迟初始化PaddleNLP LAC模型"""
        if self._initialized or self._init_error:
            return

        try:
            from paddlenlp import Taskflow

            self._lac = Taskflow(
                "lexical_analysis",
                device="gpu" if self._use_gpu else "cpu",
            )
            self._initialized = True
            logger.info(f"PaddleNLP LAC模型初始化成功: use_gpu={self._use_gpu}")
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"PaddleNLP初始化失败: {e}")
            self._initialized = True

    def _simple_tokenize(self, text: str) -> list[str]:
        """
        简单分词（当PaddleNLP不可用时的后备方案）

        Args:
            text: 待分词文本

        Returns:
            分词结果列表
        """
        import re

        pattern = r"[\u4e00-\u9fa5]+|[a-zA-Z]+|[0-9]+|[^\s]"
        tokens = re.findall(pattern, text)
        return tokens

    def process_text(self, text: str, language: str = "zh") -> PaddleNlpArtifacts:
        """
        处理文本，返回NLP处理结果

        Args:
            text: 待处理的文本
            language: 语言代码

        Returns:
            PaddleNlpArtifacts: NLP处理结果
        """
        if not text:
            return PaddleNlpArtifacts(
                entities=[],
                tokens=[],
                tokens_indices=[],
                lemmas=[],
                nlp_engine=self,
                language=language,
            )

        try:
            self._init_lac()

            if self._lac is not None:
                result = self._lac(text)

                if isinstance(result, list) and len(result) > 0:
                    result = result[0]

                tokens = result.get("segs", result.get("word", []))
                tags = result.get("tags", result.get("tag", []))

                tokens_indices = []
                current_pos = 0
                for token in tokens:
                    tokens_indices.append(current_pos)
                    current_pos += len(token)

                entities = self._extract_entities(tokens, tags, text)

                return PaddleNlpArtifacts(
                    entities=entities,
                    tokens=list(tokens) if tokens else [],
                    tokens_indices=tokens_indices,
                    lemmas=list(tokens) if tokens else [],
                    nlp_engine=self,
                    language=language,
                )
            else:
                tokens = self._simple_tokenize(text)
                tokens_indices = []
                current_pos = 0
                for token in tokens:
                    tokens_indices.append(current_pos)
                    current_pos += len(token)

                return PaddleNlpArtifacts(
                    entities=[],
                    tokens=tokens,
                    tokens_indices=tokens_indices,
                    lemmas=tokens,
                    nlp_engine=self,
                    language=language,
                )

        except Exception as e:
            logger.error(f"NLP处理失败: {e}")
            tokens = self._simple_tokenize(text)
            tokens_indices = []
            current_pos = 0
            for token in tokens:
                tokens_indices.append(current_pos)
                current_pos += len(token)

            return PaddleNlpArtifacts(
                entities=[],
                tokens=tokens,
                tokens_indices=tokens_indices,
                lemmas=tokens,
                nlp_engine=self,
                language=language,
            )

    def _extract_entities(
        self,
        tokens: list,
        tags: list,
        text: str,
    ) -> list:
        """
        从LAC结果中提取实体

        Args:
            tokens: 分词结果
            tags: 词性/实体标签
            text: 原始文本

        Returns:
            实体列表，每个元素包含实体文本、类型和位置
        """
        entities = []

        if not tokens or not tags:
            return entities

        current_pos = 0
        for token, tag in zip(tokens, tags, strict=False):
            start = text.find(token, current_pos)
            if start == -1:
                current_pos += len(token)
                continue

            end = start + len(token)

            mapped_label = self.NER_TAG_MAP.get(tag)
            if mapped_label:
                entity_info = {
                    "text": token,
                    "label": mapped_label,
                    "start": start,
                    "end": end,
                }
                entities.append(entity_info)
                logger.debug(
                    f"NER识别到实体: 类型={mapped_label}, 文本='{token}', 位置=[{start}:{end}]"
                )

            current_pos = end

        if entities:
            logger.debug(f"NER共识别到 {len(entities)} 个实体")
        else:
            logger.debug("NER未识别到任何实体")

        return entities

    def is_stopword(self, word: str, language: str = "zh") -> bool:
        """
        检查是否为停用词

        Args:
            word: 待检查的词
            language: 语言代码

        Returns:
            是否为停用词
        """
        return word.lower() in self.STOPWORDS

    def is_punct(self, word: str, language: str = "zh") -> bool:
        """
        检查是否为标点符号

        Args:
            word: 待检查的词
            language: 语言代码

        Returns:
            是否为标点符号
        """
        return word in self.PUNCTUATION

    def is_supported_language(self, language: str) -> bool:
        """
        检查是否支持指定语言

        Args:
            language: 语言代码

        Returns:
            是否支持该语言
        """
        return language in ("zh", "chinese", "zh-cn")

    def get_supported_languages(self) -> list[str]:
        """
        获取支持的语言列表

        Returns:
            支持的语言代码列表
        """
        return ["zh", "chinese", "zh-cn"]


class PaddleNlpEngineProvider:
    """
    PaddleNLP引擎提供者

    兼容Presidio的NlpEngineProvider接口。

    Example:
        >>> provider = PaddleNlpEngineProvider()
        >>> engine = provider.create_engine()
        >>> artifacts = engine.process_text("测试文本")
    """

    def __init__(self, nlp_configuration: dict | None = None) -> None:
        """
        初始化引擎提供者

        Args:
            nlp_configuration: NLP配置字典
        """
        self._configuration = nlp_configuration or {}

    def create_engine(self) -> PaddleNLPEngine:
        """
        创建PaddleNLP引擎实例

        Returns:
            PaddleNLPEngine实例
        """
        use_gpu = False

        models = self._configuration.get("models", [])
        for model_config in models:
            if model_config.get("lang_code") == "zh":
                use_gpu = model_config.get("use_gpu", False)
                break

        return PaddleNLPEngine(use_gpu=use_gpu)
