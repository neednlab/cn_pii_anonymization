"""
核心引擎单元测试

测试分析器和匿名化引擎的功能。
"""

import pytest

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.core.anonymizer import CNPIIAnonymizerEngine


class TestCNPIIAnalyzerEngine:
    """分析器引擎测试类"""

    @pytest.fixture(scope="class")
    def analyzer(self):
        """创建分析器实例"""
        engine = CNPIIAnalyzerEngine()
        yield engine
        CNPIIAnalyzerEngine.reset()

    def test_analyze_phone(self, analyzer):
        """测试手机号分析"""
        text = "我的手机号是13812345678"
        results = analyzer.analyze(text, entities=["CN_PHONE_NUMBER"])

        assert len(results) == 1
        assert results[0].entity_type == "CN_PHONE_NUMBER"

    def test_analyze_id_card(self, analyzer):
        """测试身份证分析"""
        text = "身份证号110101199001011237"
        results = analyzer.analyze(text, entities=["CN_ID_CARD"])

        assert len(results) == 1
        assert results[0].entity_type == "CN_ID_CARD"

    def test_analyze_multiple_entities(self, analyzer):
        """测试多实体分析"""
        text = "手机号13812345678，身份证110101199001011237"
        results = analyzer.analyze(text)

        entity_types = {r.entity_type for r in results}
        assert "CN_PHONE_NUMBER" in entity_types
        assert "CN_ID_CARD" in entity_types

    def test_analyze_with_score_threshold(self, analyzer):
        """测试分数阈值过滤"""
        text = "手机号13812345678"
        results = analyzer.analyze(text, score_threshold=1.01)

        assert len(results) == 0

    def test_analyze_with_allow_list(self, analyzer):
        """测试白名单过滤"""
        text = "手机号13812345678"
        results = analyzer.analyze(text, allow_list=["13812345678"])

        assert len(results) == 0

    def test_analyze_empty_text(self, analyzer):
        """测试空文本分析"""
        results = analyzer.analyze("")

        assert len(results) == 0

    def test_analyze_no_pii(self, analyzer):
        """测试无PII文本"""
        text = "这是一段普通的中文文本"
        results = analyzer.analyze(text)

        assert len(results) == 0

    def test_singleton_pattern(self, analyzer):
        """测试单例模式"""
        analyzer2 = CNPIIAnalyzerEngine()
        assert analyzer is analyzer2

    def test_reset_singleton(self, analyzer):
        """测试重置单例"""
        CNPIIAnalyzerEngine.reset()
        new_analyzer = CNPIIAnalyzerEngine()
        assert new_analyzer is not analyzer
        CNPIIAnalyzerEngine.reset()


class TestCNPIIAnonymizerEngine:
    """匿名化引擎测试类"""

    @pytest.fixture(scope="class")
    def anonymizer(self):
        """创建匿名化实例"""
        engine = CNPIIAnonymizerEngine()
        yield engine
        CNPIIAnonymizerEngine.reset()

    @pytest.fixture(scope="class")
    def analyzer(self):
        """创建分析器实例"""
        engine = CNPIIAnalyzerEngine()
        yield engine
        CNPIIAnalyzerEngine.reset()

    def test_anonymize_phone(self, anonymizer, analyzer):
        """测试手机号匿名化"""
        text = "我的手机号是13812345678"
        analyzer_results = analyzer.analyze(text, entities=["CN_PHONE_NUMBER"])
        result = anonymizer.anonymize(text, analyzer_results)

        assert "138****5678" in result.text
        assert len(result.items) == 1

    def test_anonymize_id_card(self, anonymizer, analyzer):
        """测试身份证匿名化"""
        text = "身份证号110101199001011237"
        analyzer_results = analyzer.analyze(text, entities=["CN_ID_CARD"])
        result = anonymizer.anonymize(text, analyzer_results)

        assert len(result.items) == 1

    def test_anonymize_multiple_entities(self, anonymizer, analyzer):
        """测试多实体匿名化"""
        text = "手机号13812345678，邮箱test@qq.com"
        analyzer_results = analyzer.analyze(text)
        result = anonymizer.anonymize(text, analyzer_results)

        assert result.text != text

    def test_anonymize_empty_text(self, anonymizer):
        """测试空文本匿名化"""
        result = anonymizer.anonymize("", [])

        assert result.text == ""

    def test_anonymize_no_pii(self, anonymizer):
        """测试无PII文本匿名化"""
        text = "这是一段普通的中文文本"
        result = anonymizer.anonymize(text, [])

        assert result.text == text

    def test_singleton_pattern(self, anonymizer):
        """测试单例模式"""
        anonymizer2 = CNPIIAnonymizerEngine()
        assert anonymizer is anonymizer2

    def test_reset_singleton(self, anonymizer):
        """测试重置单例"""
        CNPIIAnonymizerEngine.reset()
        new_anonymizer = CNPIIAnonymizerEngine()
        assert new_anonymizer is not anonymizer
        CNPIIAnonymizerEngine.reset()


class TestEngineIntegration:
    """引擎集成测试"""

    @pytest.fixture(scope="class")
    def analyzer(self):
        """创建分析器实例"""
        engine = CNPIIAnalyzerEngine()
        yield engine
        CNPIIAnalyzerEngine.reset()

    @pytest.fixture(scope="class")
    def anonymizer(self):
        """创建匿名化实例"""
        engine = CNPIIAnonymizerEngine()
        yield engine
        CNPIIAnonymizerEngine.reset()

    def test_full_pipeline(self, analyzer, anonymizer):
        """测试完整管道"""
        text = "手机号13812345678，身份证110101199001011237"

        analyzer_results = analyzer.analyze(text)
        anonymized = anonymizer.anonymize(text, analyzer_results)

        assert anonymized.text != text
        assert len(anonymized.items) >= 2

    def test_preserve_structure(self, analyzer, anonymizer):
        """测试保持文本结构"""
        text = "姓名：张三\n手机号：13812345678\n邮箱：test@qq.com"

        analyzer_results = analyzer.analyze(text)
        anonymized = anonymizer.anonymize(text, analyzer_results)

        lines = anonymized.text.split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("姓名：")
        assert lines[1].startswith("手机号：")
        assert lines[2].startswith("邮箱：")

    def test_entities_parameter(self, analyzer, anonymizer):
        """测试指定实体类型"""
        text = "手机号13812345678，邮箱test@qq.com"

        analyzer_results = analyzer.analyze(text, entities=["CN_PHONE_NUMBER"])
        anonymized = anonymizer.anonymize(text, analyzer_results)

        assert "138****5678" in anonymized.text
        assert "test@qq.com" in anonymized.text
