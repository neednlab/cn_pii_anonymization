"""验证安装脚本"""

from paddlenlp import Taskflow

from cn_pii_anonymization import TextProcessor

schema = ["地址", "姓名", "具体地址", "人名"]

# 初始化静态模型
ie = Taskflow("information_extraction", schema=schema)
lac = Taskflow("lexical_analysis")

text = """你好 章鹏辉，
    我是公司HR于涛，请把你的简历投递至徐汇区虹桥路1号A座907室。有任何问题咨询wenti@gmail.com或拨打13912345678。
    另外请再次确认你的如下信息是否正确
    银行卡号:62175 1234 5678 901236
    身份证号:412728 19761114 4009
    护照号:E88329471"""

ie_result = ie(text)
print(ie_result)
lac_result = lac(text)
print(lac_result)

processor = TextProcessor()
result = processor.process(text)
print(f"脱敏结果: {result.anonymized_text}")
