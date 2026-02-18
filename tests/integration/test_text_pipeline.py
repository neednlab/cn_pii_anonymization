"""
文本处理管道集成测试
"""

import pytest

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.core.anonymizer import CNPIIAnonymizerEngine
from cn_pii_anonymization.processors.text_processor import TextProcessor


class TestTextPipeline:
    """文本处理管道集成测试"""

    @pytest.fixture(scope="class")
    def processor(self):
        """创建处理器实例"""
        analyzer = CNPIIAnalyzerEngine()
        anonymizer = CNPIIAnonymizerEngine()
        return TextProcessor(analyzer=analyzer, anonymizer=anonymizer)

    def test_full_pipeline_phone(self, processor):
        """测试完整管道 - 手机号"""
        text = "我的手机号是13812345678"
        result = processor.process(text)

        assert result.anonymized_text != text
        assert "138****5678" in result.anonymized_text
        assert len(result.pii_entities) == 1

    def test_full_pipeline_id_card(self, processor):
        """测试完整管道 - 身份证"""
        # 使用有效的身份证号（校验位正确）
        # 110101199001011237 是经过校验位计算的有效身份证号
        text = "身份证号110101199001011237"
        result = processor.process(text)

        assert result.anonymized_text != text
        assert len(result.pii_entities) == 1

    def test_full_pipeline_multiple_pii(self, processor):
        """测试完整管道 - 多个PII"""
        text = "张三的手机号是13812345678，身份证号是110101199001011237"
        result = processor.process(text)

        assert result.has_pii
        entity_types = {e.entity_type for e in result.pii_entities}
        assert "CN_PHONE_NUMBER" in entity_types
        assert "CN_ID_CARD" in entity_types

    def test_full_pipeline_with_context(self, processor):
        """测试完整管道 - 带上下文"""
        text_with_context = "联系电话：13812345678"
        text_without_context = "随机数字13812345678"

        result_with = processor.process(text_with_context)
        result_without = processor.process(text_without_context)

        assert result_with.has_pii
        assert result_without.has_pii

    def test_pipeline_preserves_structure(self, processor):
        """测试管道保持文本结构"""
        text = "姓名：张三\n手机号：13812345678\n邮箱：test@example.com"
        result = processor.process(text)

        lines = result.anonymized_text.split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("姓名：")
        assert lines[1].startswith("手机号：")
        assert lines[2].startswith("邮箱：")

    def test_pipeline_empty_text(self, processor):
        """测试管道 - 空文本"""
        result = processor.process("")

        assert not result.has_pii
        assert result.anonymized_text == ""

    def test_pipeline_long_text(self, processor):
        """测试管道 - 长文本"""
        text = "这是一段很长的文本。" * 100 + "手机号13812345678" + "继续更多文本。" * 100
        result = processor.process(text)

        assert result.has_pii
        assert len(result.pii_entities) == 1
