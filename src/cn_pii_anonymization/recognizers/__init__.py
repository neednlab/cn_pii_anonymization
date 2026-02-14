"""中文PII识别器模块"""

from cn_pii_anonymization.recognizers.address_recognizer import CNAddressRecognizer
from cn_pii_anonymization.recognizers.bank_card_recognizer import CNBankCardRecognizer
from cn_pii_anonymization.recognizers.base import CNPIIRecognizer
from cn_pii_anonymization.recognizers.email_recognizer import CNEmailRecognizer
from cn_pii_anonymization.recognizers.id_card_recognizer import CNIDCardRecognizer
from cn_pii_anonymization.recognizers.name_recognizer import CNNameRecognizer
from cn_pii_anonymization.recognizers.passport_recognizer import CNPassportRecognizer
from cn_pii_anonymization.recognizers.phone_recognizer import CNPhoneRecognizer

__all__ = [
    "CNAddressRecognizer",
    "CNBankCardRecognizer",
    "CNEmailRecognizer",
    "CNIDCardRecognizer",
    "CNNameRecognizer",
    "CNPIIRecognizer",
    "CNPassportRecognizer",
    "CNPhoneRecognizer",
]
