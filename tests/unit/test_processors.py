"""
处理器单元测试
"""


class TestTextProcessor:
    """文本处理器测试类"""

    def test_process_phone(self, text_processor, sample_texts):
        """测试手机号处理"""
        result = text_processor.process(sample_texts["phone"])

        assert result.has_pii
        assert len(result.pii_entities) == 1
        assert result.pii_entities[0].entity_type == "CN_PHONE_NUMBER"
        assert "****" in result.anonymized_text

    def test_process_id_card(self, text_processor, sample_texts):
        """测试身份证处理"""
        result = text_processor.process(sample_texts["id_card"])

        assert result.has_pii
        id_card_entities = [e for e in result.pii_entities if e.entity_type == "CN_ID_CARD"]
        assert len(id_card_entities) == 1

    def test_process_mixed(self, text_processor, sample_texts):
        """测试混合PII处理"""
        result = text_processor.process(sample_texts["mixed"])

        assert result.has_pii
        assert len(result.pii_entities) >= 2

    def test_process_no_pii(self, text_processor, sample_texts):
        """测试无PII文本"""
        result = text_processor.process(sample_texts["no_pii"])

        assert not result.has_pii
        assert result.anonymized_text == sample_texts["no_pii"]

    def test_analyze_only(self, text_processor, sample_texts):
        """测试仅分析不匿名化"""
        entities = text_processor.analyze_only(sample_texts["phone"])

        assert len(entities) == 1
        assert entities[0].entity_type == "CN_PHONE_NUMBER"
        assert entities[0].original_text == "13812345678"

    def test_specific_entities(self, text_processor):
        """测试指定实体类型"""
        text = "手机号13812345678，邮箱test@example.com"
        result = text_processor.process(text, entities=["CN_PHONE_NUMBER"])

        phone_entities = [e for e in result.pii_entities if e.entity_type == "CN_PHONE_NUMBER"]
        email_entities = [e for e in result.pii_entities if e.entity_type == "CN_EMAIL"]

        assert len(phone_entities) == 1
        assert len(email_entities) == 0

    def test_result_to_dict(self, text_processor, sample_texts):
        """测试结果转换为字典"""
        result = text_processor.process(sample_texts["phone"])
        result_dict = result.to_dict()

        assert "original_text" in result_dict
        assert "anonymized_text" in result_dict
        assert "pii_entities" in result_dict
        assert isinstance(result_dict["pii_entities"], list)

    def test_get_supported_entities(self, text_processor):
        """测试获取支持的实体类型"""
        entities = text_processor.get_supported_entities()

        assert "CN_PHONE_NUMBER" in entities
        assert "CN_ID_CARD" in entities
        assert "CN_BANK_CARD" in entities
        assert "CN_PASSPORT" in entities
        assert "CN_EMAIL" in entities
