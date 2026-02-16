"""测试IE引擎批量处理"""
from paddlenlp import Taskflow

schema = ['地址', '姓名']

ie = Taskflow("information_extraction", schema=schema)

text1 = "甲25号写字楼230室"
text2 = "刘先生住在广东省深圳市南山区粤海街道科兴科学园B栋。"

# 单个调用
print("=== 单个调用 ===")
result1 = ie(text1)
print(f"text1 结果: {result1}")

result2 = ie(text2)
print(f"text2 结果: {result2}")

# 批量调用
print("\n=== 批量调用 ===")
batch_results = ie([text1, text2])
print(f"批量结果类型: {type(batch_results)}")
print(f"批量结果: {batch_results}")

# 检查批量结果的格式
print("\n=== 批量结果解析 ===")
for i, result in enumerate(batch_results):
    print(f"结果 {i}: {result}")
    if isinstance(result, dict) and "地址" in result:
        for addr in result["地址"]:
            print(f"  地址: {addr}")
