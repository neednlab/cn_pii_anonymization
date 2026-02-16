from paddlenlp import Taskflow

schema = ['地址','姓名','具体地址']

ie = Taskflow("information_extraction", schema=schema)

text_list = ["北京市朝阳区建国门外大街1号"]  #北京市朝阳区建国门外大街1号


for text in text_list:
    result = ie(text)
    print(result)
