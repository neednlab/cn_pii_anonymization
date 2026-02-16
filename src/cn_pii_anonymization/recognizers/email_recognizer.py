"""
邮箱地址识别器

识别邮箱地址。
"""

from typing import Any, ClassVar

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNEmailRecognizer(CNPIIRecognizer):
    """
    邮箱地址识别器

    识别标准邮箱地址格式，支持：
    - 标准邮箱格式：用户名@域名
    - 常见邮箱服务商识别

    Attributes:
        EMAIL_PATTERN: 邮箱匹配正则
        CONTEXT_WORDS: 上下文关键词列表
        COMMON_DOMAINS: 常见邮箱域名列表

    Example:
        >>> recognizer = CNEmailRecognizer()
        >>> results = recognizer.analyze(
        ...     "邮箱test@example.com",
        ...     ["CN_EMAIL"],
        ...     None
        ... )
    """

    EMAIL_PATTERN: ClassVar[Pattern] = Pattern(
        name="email",
        regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        score=0.85,
    )

    CONTEXT_WORDS: ClassVar[list[str]] = [
        "邮箱",
        "电子邮件",
        "email",
        "邮件地址",
        "联系方式",
        "电子邮箱",
        "邮箱地址",
        "E-mail",
        "Email",
        "MAIL",
    ]

    COMMON_DOMAINS: ClassVar[list[str]] = [
        "qq.com",
        "163.com",
        "126.com",
        "sina.com",
        "sohu.com",
        "aliyun.com",
        "foxmail.com",
        "outlook.com",
        "hotmail.com",
        "gmail.com",
        "yahoo.com",
        "icloud.com",
        "live.com",
        "yeah.net",
        "139.com",
    ]

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化邮箱识别器

        Args:
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=["CN_EMAIL"],
            name="CN Email Recognizer",
            context=self.CONTEXT_WORDS,
            **kwargs,
        )
        self._pattern_recognizer = PatternRecognizer(
            supported_entity="CN_EMAIL",
            patterns=[self.EMAIL_PATTERN],
            context=self.CONTEXT_WORDS,
        )

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本中的邮箱地址

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
        验证邮箱有效性并调整置信度

        Args:
            text: 原始文本
            results: 识别结果列表

        Returns:
            验证后的结果列表
        """
        valid_results = []
        for result in results:
            email = text[result.start : result.end]
            if self._is_valid_email(email):
                score = self._calculate_score(email)
                result.score = score
                result.recognition_metadata[RecognizerResult.RECOGNIZER_NAME_KEY] = self.name
                result.recognition_metadata[RecognizerResult.RECOGNIZER_IDENTIFIER_KEY] = self.id
                valid_results.append(result)
            else:
                logger.debug(f"无效邮箱被过滤: {email}")
        return valid_results

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        校验邮箱格式

        Args:
            email: 邮箱字符串

        Returns:
            是否为有效的邮箱
        """
        if not email or "@" not in email:
            return False

        local_part, domain = email.rsplit("@", 1)

        if len(local_part) < 1 or len(local_part) > 64:
            return False

        if len(domain) < 1 or len(domain) > 255:
            return False

        if domain.startswith(".") or domain.endswith("."):
            return False

        return ".." not in domain

    def _calculate_score(self, email: str) -> float:
        """
        根据域名计算置信度

        Args:
            email: 邮箱字符串

        Returns:
            置信度分数
        """
        domain = email.rsplit("@", 1)[1].lower()

        if domain in self.COMMON_DOMAINS:
            return 0.95

        return 0.85
