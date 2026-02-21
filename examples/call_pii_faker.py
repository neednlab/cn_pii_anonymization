"""
使用假名替换PII的完整示例

本示例演示如何使用 Faker 生成假数据来替换文本中的个人身份信息(PII)，
包括姓名、手机号、身份证号、邮箱、地址、银行卡号等。
"""

from cn_pii_anonymization import TextProcessor
from cn_pii_anonymization.operators import CNFakeOperator
from presidio_anonymizer.entities import OperatorConfig


def create_fake_operator_config(entity_type: str) -> OperatorConfig:
    """
    创建假名替换操作符配置
    
    Args:
        entity_type: PII实体类型，如 CN_NAME, CN_PHONE_NUMBER 等
        
    Returns:
        OperatorConfig: 操作符配置对象
    """
    return OperatorConfig(
        "custom",
        {"lambda": lambda x: CNFakeOperator().operate(x, {"entity_type": entity_type})},
    )




def demo_multiple_pii_types():
    """
    示例2：多种PII类型假名替换
    演示如何同时处理多种类型的PII
    """
    print("=" * 60)
    print("示例：多种PII类型假名替换")
    print("=" * 60)
    
    processor = TextProcessor()
    
    # 为所有支持的PII类型配置假名替换
    fake_config = {
        "CN_NAME": create_fake_operator_config("CN_NAME"),
        "CN_PHONE_NUMBER": create_fake_operator_config("CN_PHONE_NUMBER"),
        "CN_ID_CARD": create_fake_operator_config("CN_ID_CARD"),
        "CN_EMAIL": create_fake_operator_config("CN_EMAIL"),
        "CN_ADDRESS": create_fake_operator_config("CN_ADDRESS"),
        "CN_BANK_CARD": create_fake_operator_config("CN_BANK_CARD"),
    }
    
    text = """
    你好 章鹏辉，
    我是公司HR于涛，请把你的简历投递至徐汇区虹桥路1号A座907室。有任何问题咨询wenti@gmail.com或拨打13912345678。
    
    另外请再次确认你的如下信息是否正确
    银行卡号:62175 1234 5678 901236
    身份证号:412728 19761114 4009
    护照号:E88329471
    """
    
    result = processor.process(text, operator_config=fake_config)
    
    print(f"原始文本:{text}")
    print(f"处理后文本:{result.anonymized_text}")
    print(f"发现的PII实体数量: {len(result.pii_entities)}")
    
    # 打印每个实体的详细信息
    for entity in result.pii_entities:
        print(f"  - {entity.entity_type}: '{entity.original_text}' -> '{entity.anonymized_text}'")
    print()


def demo_mixed_operators():
    """
    示例3：混合使用假名替换和掩码
    演示如何对不同类型的PII使用不同的处理策略
    """
    print("=" * 60)
    print("示例3：混合使用假名替换和掩码")
    print("=" * 60)
    
    from cn_pii_anonymization.operators import CNMaskOperator
    
    processor = TextProcessor()
    
    # 混合配置：手机号使用掩码，姓名和身份证使用假名替换
    mixed_config = {
        # 手机号：掩码处理，保留前3位和后4位
        "CN_PHONE_NUMBER": OperatorConfig(
            "custom",
            {
                "lambda": lambda x: CNMaskOperator().operate(
                    x, {"keep_prefix": 3, "keep_suffix": 4}
                )
            },
        ),
        # 姓名：假名替换
        "CN_NAME": create_fake_operator_config("CN_NAME"),
        # 身份证：假名替换
        "CN_ID_CARD": create_fake_operator_config("CN_ID_CARD"),
    }
    
    text = "张三的手机号是13812345678，身份证号是110101199001011234"
    result = processor.process(text, operator_config=mixed_config)
    
    print(f"原始文本: {text}")
    print(f"处理后文本: {result.anonymized_text}")
    print("说明：手机号使用掩码，姓名和身份证使用假名替换")
    print()



def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("    中文PII假名替换完整示例")
    print("=" * 60 + "\n")
    
    # 运行各个示例
    demo_multiple_pii_types()
    demo_mixed_operators()

    
    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
