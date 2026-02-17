"""
核心引擎单元测试

测试分析器和匿名化引擎的功能。
"""

import pytest
from presidio_analyzer.recognizer_result import RecognizerResult

from cn_pii_anonymization.config.settings import PIIPrioritySettings, settings
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


class TestPIIPriorityFilter:
    """PII识别器优先级过滤测试类"""

    @pytest.fixture(scope="class")
    def analyzer(self):
        """创建分析器实例"""
        engine = CNPIIAnalyzerEngine()
        yield engine
        CNPIIAnalyzerEngine.reset()

    def test_priority_id_card_over_phone(self, analyzer):
        """测试身份证优先级高于手机号

        身份证号110101199001011237中包含手机号格式的子串，
        但应该只被识别为身份证号。
        """
        # 使用一个有效的身份证号
        text = "身份证号110101199001011237"
        results = analyzer.analyze(text)

        # 应该只识别出身份证，不应该识别出手机号
        entity_types = [r.entity_type for r in results]
        assert "CN_ID_CARD" in entity_types
        # 手机号不应该被识别（因为它是身份证的一部分）
        assert "CN_PHONE_NUMBER" not in entity_types

    def test_priority_id_card_over_bank_card(self, analyzer):
        """测试身份证优先级高于银行卡

        身份证号是18位数字，银行卡号是16-19位数字，
        当一个数字串同时满足两种格式时，应优先识别为身份证。
        """
        # 使用一个有效的身份证号（18位数字）
        text = "证件号110101199001011237"
        results = analyzer.analyze(text)

        entity_types = [r.entity_type for r in results]
        # 应该只识别出身份证
        assert "CN_ID_CARD" in entity_types
        # 不应该识别出银行卡
        assert "CN_BANK_CARD" not in entity_types

    def test_priority_bank_card_over_phone(self, analyzer):
        """测试银行卡优先级高于手机号

        当银行卡号和手机号识别结果重叠时，银行卡优先级更高。
        注意：手机号识别器内部已有_is_part_of_bank_card方法过滤银行卡中的手机号，
        这个测试主要验证分析器层面的优先级过滤机制。
        """
        # 使用一个有效的银行卡号（16位，通过Luhn校验）
        # 4111111111111111 是一个有效的银行卡号格式（Visa测试卡号）
        text = "银行卡号4111111111111111"
        results = analyzer.analyze(text)

        entity_types = [r.entity_type for r in results]
        # 应该识别出银行卡
        assert "CN_BANK_CARD" in entity_types
        # 不应该识别出手机号
        assert "CN_PHONE_NUMBER" not in entity_types

    def test_separate_entities_not_filtered(self, analyzer):
        """测试不重叠的实体不会被过滤

        当身份证和手机号在文本中不重叠时，两者都应该被识别。
        """
        text = "手机号13812345678，身份证110101199001011237"
        results = analyzer.analyze(text)

        entity_types = [r.entity_type for r in results]
        # 两者都应该被识别
        assert "CN_PHONE_NUMBER" in entity_types
        assert "CN_ID_CARD" in entity_types

    def test_results_overlap_method(self):
        """测试重叠检测方法"""
        # 完全重叠
        r1 = RecognizerResult(entity_type="CN_ID_CARD", start=0, end=18, score=0.95)
        r2 = RecognizerResult(entity_type="CN_PHONE_NUMBER", start=0, end=11, score=0.85)
        assert CNPIIAnalyzerEngine._results_overlap(r1, r2)

        # 部分重叠
        r3 = RecognizerResult(entity_type="CN_ID_CARD", start=0, end=18, score=0.95)
        r4 = RecognizerResult(entity_type="CN_PHONE_NUMBER", start=10, end=21, score=0.85)
        assert CNPIIAnalyzerEngine._results_overlap(r3, r4)

        # 不重叠
        r5 = RecognizerResult(entity_type="CN_PHONE_NUMBER", start=0, end=11, score=0.85)
        r6 = RecognizerResult(entity_type="CN_ID_CARD", start=20, end=38, score=0.95)
        assert not CNPIIAnalyzerEngine._results_overlap(r5, r6)

        # 相邻不重叠
        r7 = RecognizerResult(entity_type="CN_PHONE_NUMBER", start=0, end=11, score=0.85)
        r8 = RecognizerResult(entity_type="CN_ID_CARD", start=11, end=29, score=0.95)
        assert not CNPIIAnalyzerEngine._results_overlap(r7, r8)

    def test_priority_settings(self):
        """测试优先级配置"""
        priority_settings = PIIPrioritySettings()

        # 身份证优先级最高
        assert priority_settings.get_priority("CN_ID_CARD") == 1
        # 银行卡次之
        assert priority_settings.get_priority("CN_BANK_CARD") == 2
        # 手机号再次
        assert priority_settings.get_priority("CN_PHONE_NUMBER") == 3
        # 未配置的类型返回默认值
        assert priority_settings.get_priority("UNKNOWN_TYPE") == 99

    def test_priority_order(self):
        """测试优先级顺序：身份证 > 银行卡 > 手机号"""
        priority_settings = settings.pii_priorities

        id_priority = priority_settings.get_priority("CN_ID_CARD")
        bank_priority = priority_settings.get_priority("CN_BANK_CARD")
        phone_priority = priority_settings.get_priority("CN_PHONE_NUMBER")

        assert id_priority < bank_priority < phone_priority

    def test_apply_priority_filter_method(self):
        """测试优先级过滤方法"""
        # 创建模拟的识别结果
        results = [
            RecognizerResult(entity_type="CN_PHONE_NUMBER", start=0, end=11, score=0.85),
            RecognizerResult(entity_type="CN_ID_CARD", start=0, end=18, score=0.95),
        ]

        # 创建一个临时分析器实例来测试方法
        CNPIIAnalyzerEngine.reset()
        analyzer = CNPIIAnalyzerEngine()
        filtered = analyzer._apply_priority_filter(results)

        # 应该只保留身份证（优先级更高）
        assert len(filtered) == 1
        assert filtered[0].entity_type == "CN_ID_CARD"

        CNPIIAnalyzerEngine.reset()

    def test_apply_priority_filter_multiple_overlaps(self):
        """测试多个重叠结果的优先级过滤"""
        # 创建多个重叠的结果：身份证、银行卡、手机号都重叠
        results = [
            RecognizerResult(entity_type="CN_PHONE_NUMBER", start=5, end=16, score=0.85),
            RecognizerResult(entity_type="CN_BANK_CARD", start=0, end=16, score=0.90),
            RecognizerResult(entity_type="CN_ID_CARD", start=0, end=18, score=0.95),
        ]

        CNPIIAnalyzerEngine.reset()
        analyzer = CNPIIAnalyzerEngine()
        filtered = analyzer._apply_priority_filter(results)

        # 应该只保留身份证（优先级最高）
        assert len(filtered) == 1
        assert filtered[0].entity_type == "CN_ID_CARD"

        CNPIIAnalyzerEngine.reset()

    def test_apply_priority_filter_no_overlap(self):
        """测试不重叠的结果不会被过滤"""
        results = [
            RecognizerResult(entity_type="CN_PHONE_NUMBER", start=0, end=11, score=0.85),
            RecognizerResult(entity_type="CN_ID_CARD", start=20, end=38, score=0.95),
            RecognizerResult(entity_type="CN_BANK_CARD", start=50, end=66, score=0.90),
        ]

        CNPIIAnalyzerEngine.reset()
        analyzer = CNPIIAnalyzerEngine()
        filtered = analyzer._apply_priority_filter(results)

        # 所有结果都应该保留（不重叠）
        assert len(filtered) == 3

        CNPIIAnalyzerEngine.reset()

    def test_apply_priority_filter_empty_results(self):
        """测试空结果列表"""
        CNPIIAnalyzerEngine.reset()
        analyzer = CNPIIAnalyzerEngine()
        filtered = analyzer._apply_priority_filter([])
        assert len(filtered) == 0

        CNPIIAnalyzerEngine.reset()

    def test_apply_priority_filter_single_result(self):
        """测试单个结果"""
        results = [
            RecognizerResult(entity_type="CN_PHONE_NUMBER", start=0, end=11, score=0.85),
        ]

        CNPIIAnalyzerEngine.reset()
        analyzer = CNPIIAnalyzerEngine()
        filtered = analyzer._apply_priority_filter(results)

        assert len(filtered) == 1
        assert filtered[0].entity_type == "CN_PHONE_NUMBER"

        CNPIIAnalyzerEngine.reset()
