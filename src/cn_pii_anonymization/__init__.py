"""
CN PII Anonymization - 中国个人信息脱敏库

本库提供中国大陆个人身份信息(PII)的识别与脱敏处理功能。

支持的PII类型:
- 手机号 (CN_PHONE_NUMBER)
- 身份证号 (CN_ID_CARD)
- 银行卡号 (CN_BANK_CARD)
- 护照号 (CN_PASSPORT)
- 邮箱地址 (CN_EMAIL)
- 地址 (CN_ADDRESS) - P2
- 姓名 (CN_NAME) - P2

Example:
    >>> from cn_pii_anonymization import TextProcessor
    >>> processor = TextProcessor()
    >>> result = processor.process("我的手机号是13812345678")
    >>> print(result.anonymized_text)
    我的手机号是138****5678
"""

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.core.anonymizer import CNPIIAnonymizerEngine
from cn_pii_anonymization.processors.text_processor import TextProcessor

__version__ = "0.1.0"
__author__ = "CN PII Team"

__all__ = [
    "CNPIIAnalyzerEngine",
    "CNPIIAnonymizerEngine",
    "TextProcessor",
]
