"""
pytest配置文件

定义测试fixtures和公共配置。
"""

import pytest

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.core.anonymizer import CNPIIAnonymizerEngine
from cn_pii_anonymization.processors.text_processor import TextProcessor


@pytest.fixture(scope="session")
def analyzer_engine():
    """创建分析器引擎实例（会话级别）"""
    engine = CNPIIAnalyzerEngine()
    yield engine
    CNPIIAnalyzerEngine.reset()


@pytest.fixture(scope="session")
def anonymizer_engine():
    """创建匿名化引擎实例（会话级别）"""
    engine = CNPIIAnonymizerEngine()
    yield engine
    CNPIIAnonymizerEngine.reset()


@pytest.fixture
def text_processor(analyzer_engine, anonymizer_engine):
    """创建文本处理器实例"""
    return TextProcessor(
        analyzer=analyzer_engine,
        anonymizer=anonymizer_engine,
    )


@pytest.fixture
def sample_texts():
    """测试样本文本"""
    return {
        "phone": "我的手机号是13812345678",
        "phone_with_country_code": "联系电话：+8613812345678",
        "phone_with_separator": "电话：138-1234-5678",
        "id_card": "身份证号110101199001011237",
        "bank_card": "银行卡号6222021234567890123",
        "passport": "护照号E12345678",
        "email": "邮箱test@example.com",
        "mixed": "张三的手机号是13812345678，身份证号是110101199001011237，邮箱是test@example.com",
        "no_pii": "这是一段普通的中文文本，没有任何PII信息。",
    }
