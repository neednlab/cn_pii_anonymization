"""
中文PII匿名化引擎

封装Presidio AnonymizerEngine，提供中文PII匿名化处理能力。
"""

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, OperatorResult

from cn_pii_anonymization.operators import CNFakeOperator, CNMaskOperator
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNPIIAnonymizerEngine:
    """
    中文PII匿名化引擎

    封装Presidio AnonymizerEngine，提供中文PII匿名化处理能力。
    支持多种匿名化操作：掩码、假名替换等。

    Attributes:
        _anonymizer: Presidio匿名化引擎实例
        _operators: 自定义操作符配置字典

    Example:
        >>> engine = CNPIIAnonymizerEngine()
        >>> result = engine.anonymize(
        ...     text="手机号13812345678",
        ...     analyzer_results=analyzer_results,
        ...     operators={"CN_PHONE_NUMBER": OperatorConfig("mask", {"masking_char": "*"})}
        ... )
        >>> print(result.text)
    """

    _instance: "CNPIIAnonymizerEngine | None" = None
    _initialized: bool = False

    def __new__(cls) -> "CNPIIAnonymizerEngine":
        """单例模式，确保全局只有一个匿名化器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化匿名化引擎"""
        if CNPIIAnonymizerEngine._initialized:
            return

        logger.info("初始化中文PII匿名化引擎...")
        self._setup_anonymizer()
        self._setup_operators()
        CNPIIAnonymizerEngine._initialized = True
        logger.info("中文PII匿名化引擎初始化完成")

    def _setup_anonymizer(self) -> None:
        """设置匿名化引擎"""
        self._anonymizer = AnonymizerEngine()

    def _setup_operators(self) -> None:
        """设置自定义操作符"""
        self._operators: dict[str, OperatorConfig] = {
            "CN_PHONE_NUMBER": OperatorConfig(
                "custom",
                {
                    "lambda": lambda x: CNMaskOperator().operate(
                        x, {"keep_prefix": 3, "keep_suffix": 4}
                    )
                },
            ),
            "CN_ID_CARD": OperatorConfig(
                "custom",
                {
                    "lambda": lambda x: CNMaskOperator().operate(
                        x, {"keep_prefix": 6, "keep_suffix": 4}
                    )
                },
            ),
            "CN_BANK_CARD": OperatorConfig(
                "custom",
                {
                    "lambda": lambda x: CNMaskOperator().operate(
                        x, {"keep_prefix": 4, "keep_suffix": 4}
                    )
                },
            ),
            "CN_PASSPORT": OperatorConfig(
                "custom",
                {
                    "lambda": lambda x: CNMaskOperator().operate(
                        x, {"keep_prefix": 2, "keep_suffix": 2}
                    )
                },
            ),
            "CN_EMAIL": OperatorConfig(
                "custom",
                {
                    "lambda": lambda x: CNMaskOperator().operate(
                        x, {"keep_prefix": 2, "keep_suffix": 0, "mask_email_domain": True}
                    )
                },
            ),
        }

    def anonymize(
        self,
        text: str,
        analyzer_results: list,
        operators: dict[str, OperatorConfig] | None = None,
    ) -> OperatorResult:
        """
        对识别出的PII进行匿名化处理

        Args:
            text: 原始文本
            analyzer_results: 分析器返回的识别结果列表
            operators: 自定义操作符配置，用于指定不同PII类型的处理方式

        Returns:
            匿名化处理结果，包含处理后的文本和操作详情

        Example:
            >>> engine = CNPIIAnonymizerEngine()
            >>> result = engine.anonymize(
            ...     text="手机号13812345678",
            ...     analyzer_results=results,
            ...     operators={
            ...         "CN_PHONE_NUMBER": OperatorConfig(
            ...             "mask",
            ...             {"masking_char": "*", "chars_to_mask": 4, "from_end": True}
            ...         )
            ...     }
            ... )
        """
        logger.debug(f"开始匿名化处理，文本长度: {len(text)}")

        merged_operators = self._operators.copy()
        if operators:
            merged_operators.update(operators)

        result = self._anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=merged_operators,
        )

        logger.debug(f"匿名化完成，处理了 {len(result.items)} 个PII实体")
        return result

    def set_operator(
        self,
        entity_type: str,
        operator_config: OperatorConfig,
    ) -> None:
        """
        设置特定实体类型的匿名化操作

        Args:
            entity_type: PII实体类型
            operator_config: 操作符配置

        Example:
            >>> engine = CNPIIAnonymizerEngine()
            >>> engine.set_operator(
            ...     "CN_PHONE_NUMBER",
            ...     OperatorConfig("fake", {"entity_type": "CN_PHONE_NUMBER"})
            ... )
        """
        self._operators[entity_type] = operator_config
        logger.info(f"已设置 {entity_type} 的匿名化操作: {operator_config.operator_name}")

    def get_mask_operator(
        self,
        masking_char: str = "*",
        keep_prefix: int = 0,
        keep_suffix: int = 0,
    ) -> OperatorConfig:
        """
        获取掩码操作符配置

        Args:
            masking_char: 掩码字符
            keep_prefix: 保留前N位
            keep_suffix: 保留后N位

        Returns:
            操作符配置
        """
        return OperatorConfig(
            "custom",
            {
                "lambda": lambda x: CNMaskOperator().operate(
                    x,
                    {
                        "masking_char": masking_char,
                        "keep_prefix": keep_prefix,
                        "keep_suffix": keep_suffix,
                    },
                )
            },
        )

    def get_fake_operator(self, entity_type: str) -> OperatorConfig:
        """
        获取假名替换操作符配置

        Args:
            entity_type: PII实体类型

        Returns:
            操作符配置
        """
        return OperatorConfig(
            "custom",
            {"lambda": lambda x: CNFakeOperator().operate(x, {"entity_type": entity_type})},
        )

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
