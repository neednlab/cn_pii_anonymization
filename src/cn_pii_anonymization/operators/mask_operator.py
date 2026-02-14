"""
掩码操作符

提供文本掩码处理功能。
"""

from typing import Any


class CNMaskOperator:
    """
    中文掩码操作符

    提供灵活的文本掩码处理功能，支持：
    - 指定掩码字符
    - 保留前N位和后N位
    - 邮箱域名特殊处理

    Example:
        >>> operator = CNMaskOperator()
        >>> result = operator.operate("13812345678", {"keep_prefix": 3, "keep_suffix": 4})
        >>> print(result)
        138****5678
    """

    def operate(
        self,
        text: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """
        掩码处理

        Args:
            text: 待处理的文本
            params: 处理参数
                - masking_char: 掩码字符，默认为"*"
                - keep_prefix: 保留前N位，默认为0
                - keep_suffix: 保留后N位，默认为0
                - mask_email_domain: 是否掩码邮箱域名，默认为False

        Returns:
            掩码处理后的文本

        Example:
            >>> operator = CNMaskOperator()
            >>> operator.operate("13812345678", {"keep_prefix": 3, "keep_suffix": 4})
            '138****5678'
        """
        if not text:
            return text

        params = params or {}
        masking_char = params.get("masking_char", "*")
        keep_prefix = params.get("keep_prefix", 0)
        keep_suffix = params.get("keep_suffix", 0)
        mask_email_domain = params.get("mask_email_domain", False)

        if mask_email_domain and "@" in text:
            return self._mask_email(text, masking_char, keep_prefix)

        if keep_prefix + keep_suffix >= len(text):
            return text

        prefix = text[:keep_prefix] if keep_prefix > 0 else ""
        suffix = text[-keep_suffix:] if keep_suffix > 0 else ""
        middle_len = len(text) - keep_prefix - keep_suffix
        middle = masking_char * middle_len

        return prefix + middle + suffix

    @staticmethod
    def _mask_email(email: str, masking_char: str, keep_prefix: int) -> str:
        """
        掩码邮箱地址

        Args:
            email: 邮箱地址
            masking_char: 掩码字符
            keep_prefix: 用户名保留前N位

        Returns:
            掩码后的邮箱地址
        """
        if "@" not in email:
            return email

        local_part, domain = email.rsplit("@", 1)

        if keep_prefix > 0 and len(local_part) > keep_prefix:
            masked_local = local_part[:keep_prefix] + masking_char * (len(local_part) - keep_prefix)
        else:
            masked_local = masking_char * len(local_part)

        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            tld = domain_parts[-1]
            masked_domain = masking_char * (len(domain) - len(tld) - 1) + "." + tld
        else:
            masked_domain = masking_char * len(domain)

        return f"{masked_local}@{masked_domain}"


class MaskConfig:
    """掩码配置类"""

    def __init__(
        self,
        masking_char: str = "*",
        keep_prefix: int = 0,
        keep_suffix: int = 0,
    ) -> None:
        """
        初始化掩码配置

        Args:
            masking_char: 掩码字符
            keep_prefix: 保留前N位
            keep_suffix: 保留后N位
        """
        self.masking_char = masking_char
        self.keep_prefix = keep_prefix
        self.keep_suffix = keep_suffix

    def to_params(self) -> dict[str, Any]:
        """转换为参数字典"""
        return {
            "masking_char": self.masking_char,
            "keep_prefix": self.keep_prefix,
            "keep_suffix": self.keep_suffix,
        }
