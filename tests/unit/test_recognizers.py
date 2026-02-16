"""
PII识别器单元测试

测试所有中文PII识别器的功能。
"""

import pytest

from cn_pii_anonymization.recognizers.address_recognizer import CNAddressRecognizer
from cn_pii_anonymization.recognizers.bank_card_recognizer import CNBankCardRecognizer
from cn_pii_anonymization.recognizers.email_recognizer import CNEmailRecognizer
from cn_pii_anonymization.recognizers.id_card_recognizer import CNIDCardRecognizer
from cn_pii_anonymization.recognizers.name_recognizer import CNNameRecognizer
from cn_pii_anonymization.recognizers.passport_recognizer import CNPassportRecognizer
from cn_pii_anonymization.recognizers.phone_recognizer import CNPhoneRecognizer


class TestCNPhoneRecognizer:
    """手机号识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return CNPhoneRecognizer()

    @pytest.mark.parametrize(
        "text,expected_count",
        [
            ("我的手机号是13812345678", 1),
            ("联系电话：+8613812345678", 1),
            ("电话：138-1234-5678", 1),
            ("手机号是+86 138-1234-5678", 1),
            ("这是普通文本没有手机号", 0),
            ("数字12345678901不是手机号", 0),
            ("两个手机号13812345678和13987654321", 2),
        ],
    )
    def test_recognize_phone(self, recognizer, text, expected_count):
        """测试手机号识别"""
        results = recognizer.analyze(text, ["CN_PHONE_NUMBER"], None)
        assert len(results) == expected_count

    def test_phone_format_validation(self, recognizer):
        """测试手机号格式验证"""
        valid_phones = [
            "13812345678",
            "15912345678",
            "18612345678",
            "+8613812345678",
            "008613812345678",
            "138-1234-5678",
        ]

        for phone in valid_phones:
            assert CNPhoneRecognizer._is_valid_phone(phone), f"{phone} 应该是有效的"

        invalid_phones = [
            "12812345678",
            "1381234567",
            "138123456789",
            "23812345678",
            "abcdefghijk",
        ]

        for phone in invalid_phones:
            assert not CNPhoneRecognizer._is_valid_phone(phone), f"{phone} 应该是无效的"

    def test_recognizer_supported_entities(self, recognizer):
        """测试支持的实体类型"""
        assert "CN_PHONE_NUMBER" in recognizer.supported_entities

    def test_recognizer_context_words(self, recognizer):
        """测试上下文关键词"""
        text_with_context = "手机号码：13812345678"
        text_without_context = "随机数字13812345678"

        results_with_context = recognizer.analyze(text_with_context, ["CN_PHONE_NUMBER"], None)
        results_without_context = recognizer.analyze(
            text_without_context, ["CN_PHONE_NUMBER"], None
        )

        assert len(results_with_context) == 1
        assert len(results_without_context) == 1


class TestCNIDCardRecognizer:
    """身份证识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return CNIDCardRecognizer()

    @pytest.mark.parametrize(
        "text,expected_count",
        [
            ("身份证号110101199001011237", 1),
            ("证件号码：110101199003077475", 1),
            ("身份号码110101198512150031", 1),
            ("这是普通文本没有身份证", 0),
            ("两个身份证110101199001011237和110101199003077475", 2),
            # 测试带空格的身份证号
            ("身份证号 1101 0119 9001 0112 37", 1),
            ("证件号码：1101 0119 9003 0774 75", 1),
            ("身份号码 1101 0119 8512 1500 31", 1),
            # 测试不同空格格式
            ("身份证 1101  0119  9001  0112  37", 1),  # 多个空格
            ("带空格的身份证 1101 0119 9001 0112 37 和不带空格的 110101199003077475", 2),
        ],
    )
    def test_recognize_id_card(self, recognizer, text, expected_count):
        """测试身份证识别"""
        results = recognizer.analyze(text, ["CN_ID_CARD"], None)
        assert len(results) == expected_count

    def test_id_card_validation(self, recognizer):
        """测试身份证验证"""
        valid_id_cards = [
            "110101199001011237",
            "110101199003077475",
            "110101198512150031",
            "310101198001010018",
        ]

        for id_card in valid_id_cards:
            assert recognizer._validate_id_card(id_card), f"{id_card} 应该是有效的"

        invalid_id_cards = [
            "110101199001011234",
            "123456789012345678",
            "110101199013011234",
            "110101199001321234",
            "000101199001011234",
        ]

        for id_card in invalid_id_cards:
            assert not recognizer._validate_id_card(id_card), f"{id_card} 应该是无效的"

    def test_province_code_validation(self, recognizer):
        """测试省份代码验证"""
        assert 11 in recognizer.PROVINCE_CODES
        assert 31 in recognizer.PROVINCE_CODES
        assert 44 in recognizer.PROVINCE_CODES
        assert 99 not in recognizer.PROVINCE_CODES

    def test_birth_date_validation(self, recognizer):
        """测试出生日期验证"""
        assert recognizer._validate_birth_date("19900101")
        assert recognizer._validate_birth_date("20001231")
        assert not recognizer._validate_birth_date("18991231")
        assert not recognizer._validate_birth_date("20251301")
        assert not recognizer._validate_birth_date("19900132")

    def test_check_digit_validation(self, recognizer):
        """测试校验码验证"""
        assert recognizer._validate_check_digit("110101199001011237")
        assert recognizer._validate_check_digit("110101199003077475")
        assert not recognizer._validate_check_digit("110101199001011234")

    def test_id_card_with_spaces(self, recognizer):
        """测试带空格的身份证号验证"""
        # 带空格的有效身份证号
        valid_id_cards_with_spaces = [
            "1101 0119 9001 0112 37",
            "1101 0119 9003 0774 75",
            "1101 0119 8512 1500 31",
            "1101  0119  9001  0112  37",  # 多个空格
        ]

        for id_card in valid_id_cards_with_spaces:
            assert recognizer._validate_id_card(id_card), f"{id_card} 应该是有效的"

        # 带空格的无效身份证号
        invalid_id_cards_with_spaces = [
            "1101 0119 9001 0112 34",  # 校验码错误
            "1101 0119 9003 0774 76",  # 校验码错误
        ]

        for id_card in invalid_id_cards_with_spaces:
            assert not recognizer._validate_id_card(id_card), f"{id_card} 应该是无效的"

    def test_recognizer_supported_entities(self, recognizer):
        """测试支持的实体类型"""
        assert "CN_ID_CARD" in recognizer.supported_entities


class TestCNBankCardRecognizer:
    """银行卡识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return CNBankCardRecognizer()

    @pytest.mark.parametrize(
        "text,expected_count",
        [
            ("银行卡号 4111111111111111", 1),
            ("信用卡 5500000000000004", 1),
            ("账号 6011000000000004", 1),
            ("这是普通文本没有银行卡", 0),
            ("两个银行卡 4111111111111111 和 5500000000000004", 2),
            # 测试带空格的银行卡号
            ("银行卡号 4111 1111 1111 1111", 1),
            ("信用卡 5500 0000 0000 0004", 1),
            ("账号 6011 0000 0000 0004", 1),
            ("带空格的卡号 4111 1111 1111 1111 和不带空格的 5500000000000004", 2),
            # 测试不同空格格式
            ("卡号 4111 1111 1111 1111", 1),
            ("卡号 4111  1111  1111  1111", 1),  # 多个空格
            # 测试不应识别为银行卡的情况（前后有字母）
            ("统一社会信用代码91310000552936878J", 0),  # 字母结尾
            ("编号A4111111111111111", 0),  # 字母开头
            ("订单号ORDER12345678901234", 0),  # 前后有字母
            ("产品编号ABC4111111111111111XYZ", 0),  # 前后有字母
        ],
    )
    def test_recognize_bank_card(self, recognizer, text, expected_count):
        """测试银行卡识别"""
        results = recognizer.analyze(text, ["CN_BANK_CARD"], None)
        assert len(results) == expected_count

    def test_luhn_check(self, recognizer):
        """测试Luhn算法校验"""
        valid_cards = [
            "4111111111111111",
            "5500000000000004",
            "6011000000000004",
            "3566002020360505",
        ]

        for card in valid_cards:
            assert recognizer._luhn_check(card), f"{card} 应该通过Luhn校验"

        invalid_cards = [
            "4111111111111112",
            "5500000000000005",
            "1234567890123456",
        ]

        for card in invalid_cards:
            assert not recognizer._luhn_check(card), f"{card} 不应该通过Luhn校验"

    def test_bank_card_with_spaces(self, recognizer):
        """测试带空格的银行卡号验证"""
        # 带空格的有效银行卡号
        valid_cards_with_spaces = [
            "4111 1111 1111 1111",
            "5500 0000 0000 0004",
            "6011 0000 0000 0004",
            "4111  1111  1111  1111",  # 多个空格
        ]

        for card in valid_cards_with_spaces:
            assert recognizer._validate_bank_card(card), f"{card} 应该是有效的"

        # 带空格的无效银行卡号
        invalid_cards_with_spaces = [
            "4111 1111 1111 1112",
            "5500 0000 0000 0005",
        ]

        for card in invalid_cards_with_spaces:
            assert not recognizer._validate_bank_card(card), f"{card} 应该是无效的"

    def test_score_calculation(self, recognizer):
        """测试置信度计算"""
        known_bin_card = "6222021234567890"
        unknown_bin_card = "4111111111111111"

        known_score = recognizer._calculate_score(known_bin_card)
        unknown_score = recognizer._calculate_score(unknown_bin_card)

        assert known_score == 0.95
        assert unknown_score == 0.7

    def test_bank_bin_codes(self, recognizer):
        """测试银行BIN码"""
        assert "工商银行" in recognizer.BANK_BIN_CODES
        assert "招商银行" in recognizer.BANK_BIN_CODES
        assert "622202" in recognizer.BANK_BIN_CODES["工商银行"]

    def test_recognizer_supported_entities(self, recognizer):
        """测试支持的实体类型"""
        assert "CN_BANK_CARD" in recognizer.supported_entities


class TestCNPassportRecognizer:
    """护照识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return CNPassportRecognizer()

    @pytest.mark.parametrize(
        "text,expected_count",
        [
            ("护照号E12345678", 1),
            ("通行证C12345678", 1),
            ("护照G12345678", 1),
            ("这是普通文本没有护照号", 0),
        ],
    )
    def test_recognize_passport(self, recognizer, text, expected_count):
        """测试护照识别"""
        results = recognizer.analyze(text, ["CN_PASSPORT"], None)
        assert len(results) == expected_count

    def test_passport_validation(self, recognizer):
        """测试护照验证"""
        valid_passports = [
            "E12345678",
            "G12345678",
            "C12345678",
            "H12345678",
            "AB123456",
        ]

        for passport in valid_passports:
            assert recognizer._is_valid_passport(passport), f"{passport} 应该是有效的"

        invalid_passports = [
            "12345678",
            "",
            "ABC",
        ]

        for passport in invalid_passports:
            assert not recognizer._is_valid_passport(passport), f"{passport} 应该是无效的"

    def test_passport_formats(self, recognizer):
        """测试不同护照格式"""
        new_format = "E12345678"
        old_format = "AB123456"
        hk_macao_format = "C12345678"

        assert recognizer._is_valid_passport(new_format)
        assert recognizer._is_valid_passport(old_format)
        assert recognizer._is_valid_passport(hk_macao_format)

    def test_recognizer_supported_entities(self, recognizer):
        """测试支持的实体类型"""
        assert "CN_PASSPORT" in recognizer.supported_entities


class TestCNEmailRecognizer:
    """邮箱识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return CNEmailRecognizer()

    @pytest.mark.parametrize(
        "text,expected_count",
        [
            ("邮箱test@example.com", 1),
            ("电子邮件test@qq.com", 1),
            ("联系方式test@163.com", 1),
            ("这是普通文本没有邮箱", 0),
            ("两个邮箱test@qq.com和test@163.com", 2),
        ],
    )
    def test_recognize_email(self, recognizer, text, expected_count):
        """测试邮箱识别"""
        results = recognizer.analyze(text, ["CN_EMAIL"], None)
        assert len(results) == expected_count

    def test_email_validation(self, recognizer):
        """测试邮箱验证"""
        valid_emails = [
            "test@example.com",
            "test.qq@163.com",
            "test_email@qq.com",
            "test123@gmail.com",
        ]

        for email in valid_emails:
            assert recognizer._is_valid_email(email), f"{email} 应该是有效的"

        invalid_emails = [
            "",
            "test",
            "@example.com",
            "test@",
            "test@.com",
            "test@example..com",
        ]

        for email in invalid_emails:
            assert not recognizer._is_valid_email(email), f"{email} 应该是无效的"

    def test_score_calculation(self, recognizer):
        """测试置信度计算"""
        common_email = "test@qq.com"
        uncommon_email = "test@unknown.com"

        common_score = recognizer._calculate_score(common_email)
        uncommon_score = recognizer._calculate_score(uncommon_email)

        assert common_score == 0.95
        assert uncommon_score == 0.85

    def test_common_domains(self, recognizer):
        """测试常见域名"""
        assert "qq.com" in recognizer.COMMON_DOMAINS
        assert "163.com" in recognizer.COMMON_DOMAINS
        assert "gmail.com" in recognizer.COMMON_DOMAINS

    def test_recognizer_supported_entities(self, recognizer):
        """测试支持的实体类型"""
        assert "CN_EMAIL" in recognizer.supported_entities


class TestRecognizerIntegration:
    """识别器集成测试"""

    @pytest.fixture
    def phone_recognizer(self):
        return CNPhoneRecognizer()

    @pytest.fixture
    def id_card_recognizer(self):
        return CNIDCardRecognizer()

    @pytest.fixture
    def bank_card_recognizer(self):
        return CNBankCardRecognizer()

    @pytest.fixture
    def passport_recognizer(self):
        return CNPassportRecognizer()

    @pytest.fixture
    def email_recognizer(self):
        return CNEmailRecognizer()

    def test_multiple_recognizers(
        self,
        phone_recognizer,
        id_card_recognizer,
        bank_card_recognizer,
        passport_recognizer,
        email_recognizer,
    ):
        """测试多个识别器同时工作"""
        text = "手机号13812345678，邮箱test@qq.com"

        phone_results = phone_recognizer.analyze(text, ["CN_PHONE_NUMBER"], None)
        email_results = email_recognizer.analyze(text, ["CN_EMAIL"], None)

        assert len(phone_results) == 1
        assert len(email_results) == 1

    def test_no_false_positives(
        self,
        phone_recognizer,
        id_card_recognizer,
        bank_card_recognizer,
        passport_recognizer,
        email_recognizer,
    ):
        """测试无误报"""
        text = "这是一段普通的中文文本，没有任何PII信息。包含一些数字12345和字母abcdef。"

        phone_results = phone_recognizer.analyze(text, ["CN_PHONE_NUMBER"], None)
        id_card_results = id_card_recognizer.analyze(text, ["CN_ID_CARD"], None)
        bank_card_results = bank_card_recognizer.analyze(text, ["CN_BANK_CARD"], None)
        passport_results = passport_recognizer.analyze(text, ["CN_PASSPORT"], None)
        email_results = email_recognizer.analyze(text, ["CN_EMAIL"], None)

        assert len(phone_results) == 0
        assert len(id_card_results) == 0
        assert len(bank_card_results) == 0
        assert len(passport_results) == 0
        assert len(email_results) == 0


class TestCNAddressRecognizer:
    """地址识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return CNAddressRecognizer()

    @pytest.mark.parametrize(
        "text,expected_count",
        [
            ("地址：北京市朝阳区建国路88号", 1),
            ("居住地：上海市浦东新区张江高科技园区", 1),
            ("收货地址：广东省深圳市南山区科技园路1号", 1),
            ("通讯地址：浙江省杭州市西湖区文三路100号", 1),
            ("这是普通文本没有地址信息", 0),
        ],
    )
    def test_recognize_address(self, recognizer, text, expected_count):
        """测试地址识别"""
        results = recognizer.analyze(text, ["CN_ADDRESS"], None)
        assert len(results) == expected_count

    def test_address_validation(self, recognizer):
        """测试地址验证"""
        valid_addresses = [
            "北京市朝阳区建国路88号",
            "上海市浦东新区张江高科技园区",
            "广东省深圳市南山区科技园路1号",
            "四川省成都市武侯区人民南路四段1号",
        ]

        for address in valid_addresses:
            assert recognizer._validate_address(address), f"{address} 应该是有效的"

        invalid_addresses = [
            "北京",
            "上海市",
            "普通文本",
            "a" * 101,
        ]

        for address in invalid_addresses:
            assert not recognizer._validate_address(address), f"{address} 应该是无效的"

    def test_province_recognition(self, recognizer):
        """测试省份识别"""
        assert "北京市" in recognizer.PROVINCES
        assert "上海市" in recognizer.PROVINCES
        assert "广东省" in recognizer.PROVINCES
        assert "新疆维吾尔自治区" in recognizer.PROVINCES

    def test_score_calculation(self, recognizer):
        """测试置信度计算"""
        detailed_address = "北京市朝阳区建国路88号院1号楼101室"
        simple_address = "北京市朝阳区"

        detailed_score = recognizer._calculate_score(detailed_address)
        simple_score = recognizer._calculate_score(simple_address)

        assert detailed_score > simple_score
        assert detailed_score >= 0.7

    def test_address_keywords(self, recognizer):
        """测试地址关键词"""
        assert "路" in recognizer.ADDRESS_KEYWORDS
        assert "街" in recognizer.ADDRESS_KEYWORDS
        assert "号" in recognizer.ADDRESS_KEYWORDS
        assert "小区" in recognizer.ADDRESS_KEYWORDS

    def test_recognizer_supported_entities(self, recognizer):
        """测试支持的实体类型"""
        assert "CN_ADDRESS" in recognizer.supported_entities


class TestCNNameRecognizer:
    """姓名识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建识别器实例"""
        return CNNameRecognizer()

    @pytest.mark.parametrize(
        "text,expected_count",
        [
            ("联系人：张三", 1),
            ("姓名：李四", 1),
            ("经办人：王五", 1),
            ("申请人欧阳明华", 1),
            ("产品编号ABC123测试", 0),
        ],
    )
    def test_recognize_name(self, recognizer, text, expected_count):
        """测试姓名识别"""
        results = recognizer.analyze(text, ["CN_NAME"], None)
        assert len(results) == expected_count

    def test_name_validation(self, recognizer):
        """测试姓名验证"""
        valid_names = [
            "张三",
            "李四",
            "王五",
            "欧阳明华",
            "司马相如",
            "诸葛孔明",
        ]

        for name in valid_names:
            assert recognizer._validate_chinese_name(name), f"{name} 应该是有效的"

        invalid_names = [
            "",
            "a",
            "张",
            "张三李四王五",
            "123",
            "北京市",
            "有限公司",
        ]

        for name in invalid_names:
            assert not recognizer._validate_chinese_name(name), f"{name} 应该是无效的"

    def test_surname_recognition(self, recognizer):
        """测试姓氏识别"""
        assert "王" in recognizer.COMMON_SURNAMES
        assert "李" in recognizer.COMMON_SURNAMES
        assert "张" in recognizer.COMMON_SURNAMES
        assert "欧阳" in recognizer.COMPOUND_SURNAMES
        assert "司马" in recognizer.COMPOUND_SURNAMES
        assert "诸葛" in recognizer.COMPOUND_SURNAMES

    def test_score_calculation(self, recognizer):
        """测试置信度计算"""
        compound_surname_name = "欧阳明华"
        common_name = "张三"

        compound_score = recognizer._calculate_score(compound_surname_name)
        common_score = recognizer._calculate_score(common_name)

        assert compound_score > common_score

    def test_name_blacklist(self, recognizer):
        """测试姓名黑名单"""
        assert "北京市" in recognizer.NAME_BLACKLIST
        assert "有限公司" in recognizer.NAME_BLACKLIST
        assert "大学" in recognizer.NAME_BLACKLIST

    def test_recognizer_supported_entities(self, recognizer):
        """测试支持的实体类型"""
        assert "CN_NAME" in recognizer.supported_entities


class TestP2RecognizerIntegration:
    """P2级别识别器集成测试"""

    @pytest.fixture
    def address_recognizer(self):
        return CNAddressRecognizer()

    @pytest.fixture
    def name_recognizer(self):
        return CNNameRecognizer()

    def test_address_and_name_together(self, address_recognizer, name_recognizer):
        """测试地址和姓名识别器同时工作"""
        text = "联系人：张三，地址：北京市朝阳区建国路88号"

        address_results = address_recognizer.analyze(text, ["CN_ADDRESS"], None)
        name_results = name_recognizer.analyze(text, ["CN_NAME"], None)

        assert len(address_results) == 1
        assert len(name_results) >= 1

    def test_no_false_positives_for_address(self, address_recognizer):
        """测试地址识别器无误报"""
        text = "这是一段普通的中文文本，没有任何PII信息。"

        address_results = address_recognizer.analyze(text, ["CN_ADDRESS"], None)

        assert len(address_results) == 0
