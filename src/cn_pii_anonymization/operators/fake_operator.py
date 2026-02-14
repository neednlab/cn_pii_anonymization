"""
假名替换操作符

提供假数据生成和替换功能。
"""

from typing import Any, ClassVar

from faker import Faker

from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class CNFakeOperator:
    """
    中文假名替换操作符

    使用Faker库生成中文假数据，支持：
    - 姓名
    - 手机号
    - 身份证号
    - 地址
    - 邮箱
    - 银行卡号

    Example:
        >>> operator = CNFakeOperator()
        >>> result = operator.operate("张三", {"entity_type": "CN_NAME"})
        >>> print(result)  # 输出假名，如：李四
    """

    def __init__(self) -> None:
        """初始化假名生成器"""
        self._faker = Faker("zh_CN")
        self._fake_generators: dict[str, Any] = {
            "CN_NAME": self._generate_name,
            "CN_PHONE_NUMBER": self._generate_phone,
            "CN_ID_CARD": self._generate_id_card,
            "CN_ADDRESS": self._generate_address,
            "CN_EMAIL": self._generate_email,
            "CN_BANK_CARD": self._generate_bank_card,
            "CN_PASSPORT": self._generate_passport,
        }

    def operate(
        self,
        text: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """
        生成假数据替换

        Args:
            text: 原始文本（用于确定长度等）
            params: 处理参数
                - entity_type: PII实体类型

        Returns:
            生成的假数据

        Example:
            >>> operator = CNFakeOperator()
            >>> operator.operate("张三", {"entity_type": "CN_NAME"})
            '李四'
        """
        params = params or {}
        entity_type = params.get("entity_type")

        if not entity_type:
            logger.warning("未指定entity_type，返回原始文本")
            return text

        generator = self._fake_generators.get(entity_type)
        if generator:
            return generator()

        logger.warning(f"不支持的实体类型: {entity_type}")
        return text

    def _generate_name(self) -> str:
        """生成中文姓名"""
        return self._faker.name()

    def _generate_phone(self) -> str:
        """生成手机号"""
        phone = self._faker.phone_number()
        if phone.startswith("+86"):
            phone = phone[3:]
        phone = phone.replace(" ", "").replace("-", "")
        return phone

    def _generate_id_card(self) -> str:
        """生成身份证号"""
        ssn = self._faker.ssn()
        return ssn

    def _generate_address(self) -> str:
        """生成地址"""
        return self._faker.address()

    def _generate_email(self) -> str:
        """生成邮箱"""
        return self._faker.email()

    def _generate_bank_card(self) -> str:
        """生成银行卡号"""
        return self._faker.credit_card_number()

    def _generate_passport(self) -> str:
        """生成护照号"""
        import random
        import string

        prefix = random.choice(["E", "G"])
        letter = random.choice(string.ascii_uppercase)
        digits = "".join(random.choices(string.digits, k=8))
        return f"{prefix}{letter}{digits}"


class FakeConfig:
    """假名配置类"""

    ENTITY_TYPE_MAPPING: ClassVar[dict[str, str]] = {
        "CN_NAME": "姓名",
        "CN_PHONE_NUMBER": "手机号",
        "CN_ID_CARD": "身份证号",
        "CN_ADDRESS": "地址",
        "CN_EMAIL": "邮箱",
        "CN_BANK_CARD": "银行卡号",
        "CN_PASSPORT": "护照号",
    }

    def __init__(self, entity_type: str) -> None:
        """
        初始化假名配置

        Args:
            entity_type: PII实体类型
        """
        self.entity_type = entity_type

    def to_params(self) -> dict[str, Any]:
        """转换为参数字典"""
        return {"entity_type": self.entity_type}

    @property
    def description(self) -> str:
        """获取实体类型描述"""
        return self.ENTITY_TYPE_MAPPING.get(self.entity_type, self.entity_type)
