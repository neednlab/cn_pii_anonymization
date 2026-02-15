from paddlenlp import Taskflow

# 关键点：不要只写 '地点'，而是把你想区分的层级写在 schema 里
schema = ['地址','姓名','住址','住所']

ie = Taskflow("information_extraction", schema=schema)

text = "刘先生住在广东省深圳市南山区粤海街道科兴科学园B栋。"
text2 = "喻张超在上海市"
text3 = "任侠, 黄浦区人"
text4 = "北京市北京市朝阳区花园路甲220号花园路"

for text in [text4]:
    result = ie(text)
    print(result)
