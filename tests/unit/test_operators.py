"""
操作符单元测试
"""

import pytest

from cn_pii_anonymization.operators.fake_operator import CNFakeOperator
from cn_pii_anonymization.operators.mask_operator import CNMaskOperator


class TestCNMaskOperator:
    """掩码操作符测试类"""

    @pytest.fixture
    def operator(self):
        """创建操作符实例"""
        return CNMaskOperator()

    @pytest.mark.parametrize(
        "text,params,expected",
        [
            ("13812345678", {"keep_prefix": 3, "keep_suffix": 4}, "138****5678"),
            ("13812345678", {"keep_prefix": 0, "keep_suffix": 4}, "*******5678"),
            ("13812345678", {"keep_prefix": 3, "keep_suffix": 0}, "138********"),
            ("13812345678", {"keep_prefix": 0, "keep_suffix": 0}, "***********"),
            (
                "13812345678",
                {"masking_char": "#", "keep_prefix": 3, "keep_suffix": 4},
                "138####5678",
            ),
            ("ab", {"keep_prefix": 1, "keep_suffix": 1}, "ab"),
            ("", {"keep_prefix": 3, "keep_suffix": 4}, ""),
        ],
    )
    def test_mask_operation(self, operator, text, params, expected):
        """测试掩码操作"""
        result = operator.operate(text, params)
        assert result == expected

    def test_email_mask(self, operator):
        """测试邮箱掩码"""
        email = "test@example.com"
        result = operator.operate(email, {"mask_email_domain": True, "keep_prefix": 2})
        assert "@" in result
        assert result.startswith("te")
        assert result.endswith(".com")


class TestCNFakeOperator:
    """假名操作符测试类"""

    @pytest.fixture
    def operator(self):
        """创建操作符实例"""
        return CNFakeOperator()

    @pytest.mark.parametrize(
        "entity_type",
        [
            "CN_NAME",
            "CN_PHONE_NUMBER",
            "CN_ID_CARD",
            "CN_ADDRESS",
            "CN_EMAIL",
            "CN_BANK_CARD",
            "CN_PASSPORT",
        ],
    )
    def test_fake_generation(self, operator, entity_type):
        """测试假数据生成"""
        result = operator.operate("original", {"entity_type": entity_type})
        assert result != "original"
        assert len(result) > 0

    def test_unknown_entity_type(self, operator):
        """测试未知实体类型"""
        result = operator.operate("original", {"entity_type": "UNKNOWN"})
        assert result == "original"

    def test_no_entity_type(self, operator):
        """测试未指定实体类型"""
        result = operator.operate("original", {})
        assert result == "original"

    def test_phone_format(self, operator):
        """测试手机号格式"""
        phone = operator.operate("13812345678", {"entity_type": "CN_PHONE_NUMBER"})
        assert len(phone) == 11
        assert phone.startswith("1")

    def test_id_card_format(self, operator):
        """测试身份证格式"""
        id_card = operator.operate("110101199001011234", {"entity_type": "CN_ID_CARD"})
        assert len(id_card) == 18
