"""
测试信息抽取引擎集成到分析器

验证姓名和地址识别使用information_extraction方法。
"""

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine


def test_ie_integration():
    """测试信息抽取引擎集成"""
    print("=" * 60)
    print("测试信息抽取引擎集成到分析器")
    print("=" * 60)

    # 重置单例以确保重新初始化
    CNPIIAnalyzerEngine.reset()

    # 创建分析器引擎
    engine = CNPIIAnalyzerEngine()

    # 测试用例
    test_cases = [
        "刘先生住在广东省深圳市南山区粤海街道科兴科学园B栋。",
        "喻张超在上海市工作",
        "任侠, 黄浦区人",
        "徐汇区虹桥路183号",
        "张三的手机号是13812345678，身份证号是110101199001011234",
    ]

    for text in test_cases:
        print(f"\n文本: {text}")
        results = engine.analyze(text, score_threshold=0.3)

        if results:
            for r in results:
                pii_text = text[r.start : r.end]
                print(
                    f"  - 类型: {r.entity_type}, 内容: '{pii_text}', "
                    f"位置: [{r.start}:{r.end}], 置信度: {r.score:.4f}"
                )
        else:
            print("  未识别到PII")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_address_length_filter():
    """测试地址长度过滤（<6字符的地址应被过滤）"""
    print("\n" + "=" * 60)
    print("测试地址长度过滤（<6字符的地址应被过滤）")
    print("=" * 60)

    CNPIIAnalyzerEngine.reset()
    engine = CNPIIAnalyzerEngine()

    # 测试短地址（应被过滤）
    test_cases = [
        ("北京市", "短地址，应被过滤"),
        ("上海市", "短地址，应被过滤"),
        ("广东省深圳市南山区粤海街道科兴科学园B栋", "长地址，应被识别"),
    ]

    for text, desc in test_cases:
        print(f"\n文本: {text} ({desc})")
        results = engine.analyze(text, entities=["CN_ADDRESS"], score_threshold=0.3)

        if results:
            for r in results:
                pii_text = text[r.start : r.end]
                print(
                    f"  - 类型: {r.entity_type}, 内容: '{pii_text}', "
                    f"长度: {len(pii_text)}, 置信度: {r.score:.4f}"
                )
        else:
            print("  未识别到地址PII（可能被过滤）")


if __name__ == "__main__":
    test_ie_integration()
    test_address_length_filter()
