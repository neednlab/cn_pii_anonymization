"""
性能测试

测试PII识别和匿名化的性能。
"""

import time

import pytest

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.core.anonymizer import CNPIIAnonymizerEngine
from cn_pii_anonymization.processors.text_processor import TextProcessor


class TestPerformance:
    """性能测试类"""

    @pytest.fixture(scope="class")
    def processor(self):
        """创建处理器实例"""
        return TextProcessor()

    @pytest.fixture(scope="class")
    def analyzer(self):
        """创建分析器实例"""
        return CNPIIAnalyzerEngine()

    @pytest.fixture(scope="class")
    def anonymizer(self):
        """创建匿名化实例"""
        return CNPIIAnonymizerEngine()

    @pytest.fixture
    def sample_text(self):
        """创建测试文本"""
        return "手机号13812345678，身份证110101199001011237"

    @pytest.fixture
    def long_text(self):
        """创建长文本"""
        base_text = "这是一段测试文本，手机号13812345678，身份证110101199001011237。"
        return base_text * 100

    def test_analyze_performance_short(self, analyzer, sample_text, benchmark):
        """测试短文本分析性能"""
        result = benchmark(analyzer.analyze, sample_text)

        assert len(result) >= 2

    def test_analyze_performance_long(self, analyzer, long_text, benchmark):
        """测试长文本分析性能"""
        result = benchmark(analyzer.analyze, long_text)

        assert len(result) >= 200

    def test_anonymize_performance_short(self, analyzer, anonymizer, sample_text, benchmark):
        """测试短文本匿名化性能"""
        analyzer_results = analyzer.analyze(sample_text)

        result = benchmark(anonymizer.anonymize, sample_text, analyzer_results)

        assert result.text != sample_text

    def test_anonymize_performance_long(self, analyzer, anonymizer, long_text, benchmark):
        """测试长文本匿名化性能"""
        analyzer_results = analyzer.analyze(long_text)

        result = benchmark(anonymizer.anonymize, long_text, analyzer_results)

        assert result.text != long_text

    def test_full_pipeline_performance(self, processor, sample_text, benchmark):
        """测试完整管道性能"""
        result = benchmark(processor.process, sample_text)

        assert result.anonymized_text != sample_text

    def test_multiple_iterations(self, analyzer, sample_text):
        """测试多次迭代性能"""
        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            analyzer.analyze(sample_text)

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        print(f"\n总时间: {total_time:.3f}s")
        print(f"平均时间: {avg_time * 1000:.2f}ms")
        print(f"每秒处理: {iterations / total_time:.1f}次")

        assert avg_time < 0.1

    def test_memory_usage(self, analyzer, sample_text):
        """测试内存使用"""
        import tracemalloc

        tracemalloc.start()

        for _ in range(1000):
            analyzer.analyze(sample_text)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n当前内存: {current / 1024 / 1024:.2f}MB")
        print(f"峰值内存: {peak / 1024 / 1024:.2f}MB")

        assert peak < 100 * 1024 * 1024


class TestRecognizerPerformance:
    """识别器性能测试"""

    @pytest.fixture(scope="class")
    def analyzer(self):
        """创建分析器实例"""
        return CNPIIAnalyzerEngine()

    def test_phone_recognition_speed(self, analyzer, benchmark):
        """测试手机号识别速度"""
        text = "手机号13812345678"

        result = benchmark(analyzer.analyze, text, entities=["CN_PHONE_NUMBER"])

        assert len(result) == 1

    def test_id_card_recognition_speed(self, analyzer, benchmark):
        """测试身份证识别速度"""
        text = "身份证110101199001011237"

        result = benchmark(analyzer.analyze, text, entities=["CN_ID_CARD"])

        assert len(result) == 1

    def test_mixed_recognition_speed(self, analyzer, benchmark):
        """测试混合识别速度"""
        text = "手机号13812345678，身份证110101199001011237"

        result = benchmark(analyzer.analyze, text)

        assert len(result) >= 2


class TestConcurrency:
    """并发测试"""

    @pytest.fixture(scope="class")
    def processor(self):
        """创建处理器实例"""
        return TextProcessor()

    def test_concurrent_processing(self, processor):
        """测试并发处理"""
        import concurrent.futures

        texts = [
            "手机号13812345678",
            "身份证110101199001011237",
        ] * 10

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(processor.process, texts))

        assert len(results) == 20
        for result in results:
            assert result.anonymized_text != texts[0]
