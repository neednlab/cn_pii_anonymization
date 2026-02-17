from paddlenlp import Taskflow

schema = ['地址','姓名','具体地址','人名']

ie = Taskflow("information_extraction", schema=schema)

text_list = ["你好 章鹏辉，\n我是公司HR于涛，请把你的简历投递至徐汇区虹桥路1号A座907室。有任何问题咨询wenti@gmail.com或拨打13912345678。\n另外请再次确认你的如下信息是否正确\n银行卡号:62175 1234 5678 901236\n身份证号:412728 19761114 4009\n护照号:E88329471"]  #北京市朝阳区建国门外大街1号


for text in text_list:
    result = ie(text)
    print(result)
