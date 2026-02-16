"""测试IE引擎批量处理修复"""
import sys
sys.path.insert(0, 'src')

from cn_pii_anonymization.nlp.ie_engine import PaddleNLPInfoExtractionEngine

ie = PaddleNLPInfoExtractionEngine(schema=['地址', '姓名'])

text1 = "甲25号写字楼230室"
text2 = "刘先生住在广东省深圳市南山区粤海街道科兴科学园B栋。"

print("=== 单个调用测试 ===")
result1 = ie.extract(text1)
print(f"text1 结果: {result1}")

result2 = ie.extract(text2)
print(f"text2 结果: {result2}")

print("\n=== 批量调用测试 ===")
batch_results = ie.extract_batch([text1, text2])
print(f"批量结果: {batch_results}")

print("\n=== 验证缓存格式 ===")
# 模拟识别器使用缓存的方式
for text in [text1, text2]:
    ie_result = batch_results.get(text, [])
    print(f"\n文本: {text}")
    print(f"缓存结果: {ie_result}")
    
    # 从缓存结果中提取地址（模拟识别器的逻辑）
    addresses = []
    for item in ie_result:
        if isinstance(item, dict) and "地址" in item:
            for addr in item["地址"]:
                addresses.append({
                    "text": addr.get("text", ""),
                    "probability": addr.get("probability", 0.85),
                })
    print(f"提取的地址: {addresses}")
