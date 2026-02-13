# CN PII Anonymization 技术设计文档 (TDD)

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| **文档名称** | CN PII Anonymization 技术设计文档 |
| **版本** | v1.0 |
| **日期** | 2026-02-13 |
| **状态** | 初稿 |
| **关联文档** | PRD.md |

---

## 2. 技术选型

### 2.1 核心框架选择

本项目选择 **Microsoft Presidio** 作为核心框架，原因如下：

| 特性 | 说明 |
|------|------|
| **开源免费** | MIT许可证，可商用 |
| **模块化设计** | Analyzer、Anonymizer、Image Redactor三大模块独立且协同 |
| **可扩展性强** | 支持自定义识别器、自定义匿名化操作 |
| **多语言支持** | 支持中文NLP模型（spaCy、Stanza） |
| **多模态处理** | 同时支持文本和图像PII处理 |
| **成熟稳定** | 微软官方维护，社区活跃 |

### 2.2 技术栈总览

```
┌─────────────────────────────────────────────────────────────┐
│                    CN PII Anonymization                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   API层     │  │  CLI工具    │  │    SDK/库接口       │  │
│  │  (FastAPI)  │  │  (Click)    │  │   (Python Package)  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
├─────────┴────────────────┴────────────────────┴─────────────┤
│                      核心处理层                               │
│  ┌──────────────────┐         ┌──────────────────────────┐  │
│  │   文本处理器      │         │      图像处理器           │  │
│  │ TextProcessor    │         │    ImageProcessor        │  │
│  └────────┬─────────┘         └────────────┬─────────────┘  │
├───────────┴────────────────────────────────┴────────────────┤
│                    Presidio 核心层                            │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────┐  │
│  │ AnalyzerEngine│ │AnonymizerEngine│ │ImageRedactorEngine│  │
│  └───────┬───────┘ └───────┬───────┘ └─────────┬─────────┘  │
├──────────┴─────────────────┴─────────────────┴──────────────┤
│                      中文PII识别器层                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ 手机号识别器 │ │ 身份证识别器 │ │ 银行卡识别器 │ ...        │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├──────────────────────────────────────────────────────────────┤
│                      基础设施层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  spaCy CN   │ │  Tesseract  │ │   Loguru    │            │
│  │  NLP模型    │ │    OCR      │ │   日志      │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 依赖组件

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.12 | 运行环境 |
| presidio-analyzer | ^2.2 | PII识别引擎 |
| presidio-anonymizer | ^2.2 | PII匿名化引擎 |
| presidio-image-redactor | ^1.0 | 图像PII处理 |
| spaCy | ^3.7 | 中文NLP处理 |
| zh-core-web-lg | 3.7.0 | 中文语言模型 |
| pytesseract | ^0.3.10 | OCR引擎接口 |
| Tesseract-OCR | 5.3+ | OCR引擎 |
| FastAPI | ^0.109 | API服务框架 |
| Loguru | ^0.7 | 日志管理 |
| Pillow | ^10.0 | 图像处理 |
| Faker | ^22.0 | 假名生成 |

---

## 3. 系统架构设计

### 3.1 目录结构

```
cn_pii_anonymization/
├── src/
│   └── cn_pii_anonymization/
│       ├── __init__.py
│       ├── core/                      # 核心模块
│       │   ├── __init__.py
│       │   ├── analyzer.py            # 分析器引擎封装
│       │   ├── anonymizer.py          # 匿名化引擎封装
│       │   └── image_redactor.py      # 图像脱敏引擎封装
│       │
│       ├── recognizers/               # 中文PII识别器
│       │   ├── __init__.py
│       │   ├── base.py                # 识别器基类
│       │   ├── phone_recognizer.py    # 手机号识别器
│       │   ├── id_card_recognizer.py  # 身份证识别器
│       │   ├── bank_card_recognizer.py# 银行卡识别器
│       │   ├── passport_recognizer.py # 护照号识别器
│       │   ├── email_recognizer.py    # 邮箱识别器
│       │   ├── address_recognizer.py  # 地址识别器
│       │   └── name_recognizer.py     # 姓名识别器
│       │
│       ├── operators/                 # 自定义匿名化操作
│       │   ├── __init__.py
│       │   ├── mask_operator.py       # 掩码操作
│       │   ├── fake_operator.py       # 假名替换操作
│       │   └── mosaic_operator.py     # 马赛克操作(图像)
│       │
│       ├── processors/                # 处理器模块
│       │   ├── __init__.py
│       │   ├── text_processor.py      # 文本处理器
│       │   └── image_processor.py     # 图像处理器
│       │
│       ├── api/                       # API模块
│       │   ├── __init__.py
│       │   ├── app.py                 # FastAPI应用
│       │   ├── routes/                # 路由
│       │   │   ├── __init__.py
│       │   │   ├── text.py            # 文本处理路由
│       │   │   └── image.py           # 图像处理路由
│       │   ├── schemas/               # 数据模型
│       │   │   ├── __init__.py
│       │   │   ├── request.py         # 请求模型
│       │   │   └── response.py        # 响应模型
│       │   └── middleware/            # 中间件
│       │       ├── __init__.py
│       │       └── logging.py         # 日志中间件
│       │
│       ├── config/                    # 配置模块
│       │   ├── __init__.py
│       │   ├── settings.py            # 配置管理
│       │   └── recognizer_config.yaml # 识别器配置
│       │
│       └── utils/                     # 工具模块
│           ├── __init__.py
│           ├── validators.py          # 校验工具
│           └── helpers.py             # 辅助函数
│
├── tests/                             # 测试目录
│   ├── __init__.py
│   ├── conftest.py                    # pytest配置
│   ├── unit/                          # 单元测试
│   │   ├── test_recognizers.py
│   │   ├── test_operators.py
│   │   └── test_processors.py
│   └── integration/                   # 集成测试
│       ├── test_text_pipeline.py
│       └── test_image_pipeline.py
│
├── docs/                              # 文档目录
├── SPEC/                              # 规格文档
│   ├── PRD.md
│   └── TDD.md
├── pyproject.toml                     # 项目配置
├── README.md
└── main.py                            # 入口文件
```

### 3.2 核心模块设计

#### 3.2.1 分析器引擎 (AnalyzerEngine)

```python
class CNPIIAnalyzerEngine:
    """中文PII分析器引擎"""
    
    def __init__(
        self,
        nlp_engine: NlpEngine,
        registry: RecognizerRegistry,
        context_aware_enhancer: Optional[ContextAwareEnhancer] = None,
    ):
        self._nlp_engine = nlp_engine
        self._registry = registry
        self._context_aware_enhancer = context_aware_enhancer
    
    def analyze(
        self,
        text: str,
        language: str = "zh",
        entities: Optional[List[str]] = None,
        score_threshold: float = 0.5,
        allow_list: Optional[List[str]] = None,
    ) -> List[RecognizerResult]:
        """分析文本中的PII实体"""
        pass
    
    def add_recognizer(self, recognizer: EntityRecognizer) -> None:
        """添加自定义识别器"""
        pass
```

#### 3.2.2 匿名化引擎 (AnonymizerEngine)

```python
class CNPIIAnonymizerEngine:
    """中文PII匿名化引擎"""
    
    def __init__(self):
        self._operators: Dict[str, OperatorConfig] = {}
    
    def anonymize(
        self,
        text: str,
        analyzer_results: List[RecognizerResult],
        operators: Optional[Dict[str, OperatorConfig]] = None,
    ) -> EngineResult:
        """对识别出的PII进行匿名化处理"""
        pass
    
    def set_operator(
        self,
        entity_type: str,
        operator_config: OperatorConfig,
    ) -> None:
        """设置特定实体类型的匿名化操作"""
        pass
```

#### 3.2.3 图像脱敏引擎 (ImageRedactorEngine)

```python
class CNPIIImageRedactorEngine:
    """中文PII图像脱敏引擎"""
    
    def __init__(
        self,
        image_analyzer_engine: ImageAnalyzerEngine,
        ocr_engine: Optional[OCREngine] = None,
    ):
        self._image_analyzer = image_analyzer_engine
        self._ocr_engine = ocr_engine or TesseractOCREngine()
    
    def redact(
        self,
        image: Image,
        fill: Union[Tuple[int, int, int], str] = (0, 0, 0),
        mosaic_style: str = "pixel",
        allow_list: Optional[List[str]] = None,
    ) -> Image:
        """对图像中的PII进行脱敏处理"""
        pass
```

---

## 4. 中文PII识别器设计

### 4.1 识别器基类

```python
from abc import abstractmethod
from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

class CNPIIRecognizer(EntityRecognizer):
    """中文PII识别器基类"""
    
    def __init__(
        self,
        supported_entities: List[str],
        supported_language: str = "zh",
        **kwargs,
    ):
        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            **kwargs,
        )
    
    @abstractmethod
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        """分析文本，返回识别结果"""
        pass
    
    def load(self) -> None:
        """加载资源"""
        pass
```

### 4.2 手机号识别器

**识别规则：**
- 中国大陆手机号：11位数字，以1开头，第二位为3-9
- 支持带国际区号格式：+86、0086
- 支持带分隔符格式：空格、横线

**正则表达式：**
```
(?:(?:\+|00)86)?1[3-9]\d{9}
```

**实现设计：**

```python
class CNPhoneRecognizer(CNPIIRecognizer):
    """中国大陆手机号识别器"""
    
    PATTERNS = [
        Pattern(
            name="cn_phone",
            regex=r"(?:(?:\+|00)86)?1[3-9]\d{9}",
            score=0.85,
        ),
        Pattern(
            name="cn_phone_with_separator",
            regex=r"(?:(?:\+|00)86)?1[3-9]\d[\s-]?\d{4}[\s-]?\d{4}",
            score=0.75,
        ),
    ]
    
    CONTEXT_WORDS = [
        "手机", "电话", "联系方式", "联系电话",
        "mobile", "phone", "tel", "联系电话",
    ]
    
    def __init__(self):
        super().__init__(supported_entities=["CN_PHONE_NUMBER"])
        self._pattern_recognizer = PatternRecognizer(
            supported_entity="CN_PHONE_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT_WORDS,
        )
    
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        results = self._pattern_recognizer.analyze(text, entities, nlp_artifacts)
        return self._validate_results(text, results)
    
    def _validate_results(
        self,
        text: str,
        results: List[RecognizerResult],
    ) -> List[RecognizerResult]:
        """验证手机号有效性"""
        valid_results = []
        for result in results:
            phone = text[result.start:result.end]
            if self._is_valid_phone(phone):
                valid_results.append(result)
        return valid_results
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """校验手机号格式"""
        phone = re.sub(r"[\s\-\+]", "", phone)
        phone = phone.removeprefix("86").removeprefix("0086")
        if len(phone) != 11:
            return False
        return phone[0] == "1" and phone[1] in "3456789"
```

### 4.3 身份证识别器

**识别规则：**
- 18位身份证号：6位地区码 + 8位出生日期 + 3位顺序码 + 1位校验码
- 15位身份证号（旧版）：6位地区码 + 6位出生日期 + 3位顺序码
- 支持校验码验证

**正则表达式：**
```
[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]
```

**实现设计：**

```python
class CNIDCardRecognizer(CNPIIRecognizer):
    """中国大陆身份证识别器"""
    
    ID_CARD_PATTERN = Pattern(
        name="cn_id_card",
        regex=r"[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]",
        score=0.5,
    )
    
    CONTEXT_WORDS = [
        "身份证", "身份证号", "证件号", "身份号码",
        "ID", "身份证件", "公民身份",
    ]
    
    PROVINCE_CODES = {
        11: "北京", 12: "天津", 13: "河北", 14: "山西", 15: "内蒙古",
        21: "辽宁", 22: "吉林", 23: "黑龙江",
        31: "上海", 32: "江苏", 33: "浙江", 34: "安徽", 35: "福建",
        36: "江西", 37: "山东",
        41: "河南", 42: "湖北", 43: "湖南", 44: "广东", 45: "广西",
        46: "海南",
        50: "重庆", 51: "四川", 52: "贵州", 53: "云南", 54: "西藏",
        61: "陕西", 62: "甘肃", 63: "青海", 64: "宁夏", 65: "新疆",
        71: "台湾", 81: "香港", 82: "澳门",
    }
    
    def __init__(self):
        super().__init__(supported_entities=["CN_ID_CARD"])
    
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        results = []
        pattern = re.compile(self.ID_CARD_PATTERN.regex)
        
        for match in pattern.finditer(text):
            id_card = match.group()
            if self._validate_id_card(id_card):
                result = RecognizerResult(
                    entity_type="CN_ID_CARD",
                    start=match.start(),
                    end=match.end(),
                    score=0.95,
                )
                results.append(result)
        
        return results
    
    def _validate_id_card(self, id_card: str) -> bool:
        """验证身份证号有效性"""
        if len(id_card) != 18:
            return False
        
        province_code = int(id_card[:2])
        if province_code not in self.PROVINCE_CODES:
            return False
        
        if not self._validate_birth_date(id_card[6:14]):
            return False
        
        if not self._validate_check_digit(id_card):
            return False
        
        return True
    
    @staticmethod
    def _validate_birth_date(date_str: str) -> bool:
        """验证出生日期"""
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            birth_date = datetime(year, month, day)
            return birth_date <= datetime.now()
        except ValueError:
            return False
    
    @staticmethod
    def _validate_check_digit(id_card: str) -> bool:
        """验证校验码"""
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = "10X98765432"
        
        total = sum(
            int(id_card[i]) * weights[i]
            for i in range(17)
        )
        
        expected_check = check_codes[total % 11]
        return id_card[17].upper() == expected_check
```

### 4.4 银行卡识别器

**识别规则：**
- 16-19位数字
- 支持Luhn算法校验
- 支持常见银行BIN码识别

**实现设计：**

```python
class CNBankCardRecognizer(CNPIIRecognizer):
    """中国大陆银行卡识别器"""
    
    BANK_CARD_PATTERN = Pattern(
        name="cn_bank_card",
        regex=r"\b\d{16,19}\b",
        score=0.3,
    )
    
    CONTEXT_WORDS = [
        "银行卡", "卡号", "账号", "银行账号",
        "信用卡", "借记卡", "储蓄卡",
        "bank", "card", "account",
    ]
    
    BANK_BIN_CODES = {
        "工商银行": ["622202", "622203", "622208", "621225"],
        "农业银行": ["622848", "622849", "622845"],
        "中国银行": ["621660", "621661", "621663"],
        "建设银行": ["621700", "436742", "436745"],
        "交通银行": ["622260", "622261"],
        "招商银行": ["622580", "622588", "621286"],
        "浦发银行": ["622518", "622520", "622521"],
        "民生银行": ["622615", "622617", "622618"],
        "兴业银行": ["622909", "622910"],
        "平安银行": ["622155", "622156"],
    }
    
    def __init__(self):
        super().__init__(supported_entities=["CN_BANK_CARD"])
    
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        results = []
        pattern = re.compile(self.BANK_CARD_PATTERN.regex)
        
        for match in pattern.finditer(text):
            card_number = match.group()
            if self._validate_bank_card(card_number):
                score = self._calculate_score(card_number)
                result = RecognizerResult(
                    entity_type="CN_BANK_CARD",
                    start=match.start(),
                    end=match.end(),
                    score=score,
                )
                results.append(result)
        
        return results
    
    def _validate_bank_card(self, card_number: str) -> bool:
        """使用Luhn算法验证银行卡号"""
        if not card_number.isdigit():
            return False
        
        if len(card_number) < 16 or len(card_number) > 19:
            return False
        
        return self._luhn_check(card_number)
    
    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        """Luhn算法校验"""
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        total = sum(odd_digits)
        for d in even_digits:
            doubled = d * 2
            total += doubled if doubled < 10 else doubled - 9
        
        return total % 10 == 0
    
    def _calculate_score(self, card_number: str) -> float:
        """根据BIN码计算置信度"""
        for bank, bin_codes in self.BANK_BIN_CODES.items():
            if any(card_number.startswith(code) for code in bin_codes):
                return 0.95
        return 0.7
```

### 4.5 护照号识别器

**识别规则：**
- 中国护照：1位字母 + 8位数字（新版）或 14-15位字符（旧版）
- 支持港澳台护照格式

**实现设计：**

```python
class CNPassportRecognizer(CNPIIRecognizer):
    """中国护照号识别器"""
    
    PASSPORT_PATTERNS = [
        Pattern(
            name="cn_passport_new",
            regex=r"[EG][A-Z]\d{8}",
            score=0.85,
        ),
        Pattern(
            name="cn_passport_old",
            regex=r"[A-Z]{1,2}\d{6,10}",
            score=0.6,
        ),
    ]
    
    CONTEXT_WORDS = [
        "护照", "护照号", "通行证",
        "passport", "通行证号码",
    ]
    
    def __init__(self):
        super().__init__(supported_entities=["CN_PASSPORT"])
```

### 4.6 邮箱识别器

**识别规则：**
- 标准邮箱格式：用户名@域名
- 支持中文邮箱格式检测
- 支持常见邮箱服务商识别

**实现设计：**

```python
class CNEmailRecognizer(CNPIIRecognizer):
    """邮箱地址识别器"""
    
    EMAIL_PATTERN = Pattern(
        name="email",
        regex=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        score=0.85,
    )
    
    CONTEXT_WORDS = [
        "邮箱", "电子邮件", "email", "邮件地址",
        "联系方式", "电子邮箱",
    ]
```

### 4.7 地址识别器 (P2 - NER)

**识别规则：**
- 使用spaCy中文NER模型
- 结合中国行政区划数据
- 支持省、市、区、街道、门牌号等多级地址

**实现设计：**

```python
class CNAddressRecognizer(CNPIIRecognizer):
    """中国地址识别器"""
    
    PROVINCES = [
        "北京市", "上海市", "天津市", "重庆市",
        "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
        "江苏省", "浙江省", "安徽省", "福建省", "江西省",
        "山东省", "河南省", "湖北省", "湖南省", "广东省",
        "海南省", "四川省", "贵州省", "云南省", "陕西省",
        "甘肃省", "青海省", "台湾省", "内蒙古自治区",
        "广西壮族自治区", "西藏自治区", "宁夏回族自治区",
        "新疆维吾尔自治区", "香港特别行政区", "澳门特别行政区",
    ]
    
    ADDRESS_KEYWORDS = [
        "路", "街", "道", "巷", "弄", "号", "栋", "单元", "室",
        "小区", "花园", "大厦", "公寓", "村", "镇", "乡", "县", "市",
    ]
    
    def __init__(self):
        super().__init__(supported_entities=["CN_ADDRESS"])
    
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        results = []
        
        for province in self.PROVINCES:
            if province in text:
                start = text.find(province)
                end = self._find_address_end(text, start)
                result = RecognizerResult(
                    entity_type="CN_ADDRESS",
                    start=start,
                    end=end,
                    score=0.85,
                )
                results.append(result)
        
        return results
    
    def _find_address_end(self, text: str, start: int) -> int:
        """查找地址结束位置"""
        pass
```

### 4.8 姓名识别器 (P2 - NER)

**识别规则：**
- 使用spaCy中文NER模型识别PERSON实体
- 结合中国姓氏库进行验证
- 支持中文姓名常见格式（2-4字）

**实现设计：**

```python
class CNNameRecognizer(CNPIIRecognizer):
    """中国姓名识别器"""
    
    COMMON_SURNAMES = [
        "王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
        "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
    ]
    
    NAME_PATTERNS = [
        Pattern(name="cn_name", regex=r"[\u4e00-\u9fa5]{2,4}", score=0.3),
    ]
    
    def __init__(self):
        super().__init__(supported_entities=["CN_NAME"])
    
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        results = []
        
        if nlp_artifacts and nlp_artifacts.entities:
            for ent in nlp_artifacts.entities:
                if ent.label_ == "PERSON":
                    if self._validate_chinese_name(ent.text):
                        result = RecognizerResult(
                            entity_type="CN_NAME",
                            start=ent.start_char,
                            end=ent.end_char,
                            score=0.85,
                        )
                        results.append(result)
        
        return results
    
    def _validate_chinese_name(self, name: str) -> bool:
        """验证中文姓名"""
        if not name or len(name) < 2 or len(name) > 4:
            return False
        
        if not all('\u4e00' <= c <= '\u9fa5' for c in name):
            return False
        
        return name[0] in self.COMMON_SURNAMES
```

---

## 5. 匿名化操作设计

### 5.1 文本匿名化操作

#### 5.1.1 掩码操作 (Mask)

```python
class CNMaskOperator(Operator):
    """中文掩码操作"""
    
    def operate(
        self,
        text: str,
        params: Dict[str, Any],
    ) -> str:
        """
        掩码处理
        
        参数:
            chars_to_mask: 掩码字符数
            masking_char: 掩码字符，默认为"*"
            from_end: 是否从末尾开始，默认为False
            keep_prefix: 保留前N位
            keep_suffix: 保留后N位
        """
        masking_char = params.get("masking_char", "*")
        keep_prefix = params.get("keep_prefix", 0)
        keep_suffix = params.get("keep_suffix", 0)
        
        if keep_prefix + keep_suffix >= len(text):
            return text
        
        prefix = text[:keep_prefix]
        suffix = text[-keep_suffix:] if keep_suffix > 0 else ""
        middle_len = len(text) - keep_prefix - keep_suffix
        middle = masking_char * middle_len
        
        return prefix + middle + suffix
```

#### 5.1.2 假名替换操作 (Fake)

```python
from faker import Faker

class CNFakeOperator(Operator):
    """中文假名替换操作"""
    
    def __init__(self):
        self._faker = Faker("zh_CN")
        self._fake_generators = {
            "CN_NAME": self._faker.name,
            "CN_PHONE_NUMBER": self._faker.phone_number,
            "CN_ID_CARD": self._faker.ssn,
            "CN_ADDRESS": self._faker.address,
            "CN_EMAIL": self._faker.email,
            "CN_BANK_CARD": self._faker.credit_card_number,
        }
    
    def operate(
        self,
        text: str,
        params: Dict[str, Any],
    ) -> str:
        """生成假数据替换"""
        entity_type = params.get("entity_type")
        generator = self._fake_generators.get(entity_type)
        
        if generator:
            return generator()
        return text
```

### 5.2 图像匿名化操作

#### 5.2.1 像素块马赛克

```python
class PixelMosaicOperator:
    """像素块马赛克操作"""
    
    def __init__(self, block_size: int = 10):
        self._block_size = block_size
    
    def apply(
        self,
        image: Image,
        bbox: Tuple[int, int, int, int],
    ) -> Image:
        """应用像素块马赛克"""
        x1, y1, x2, y2 = bbox
        region = image.crop((x1, y1, x2, y2))
        
        small = region.resize(
            ((x2 - x1) // self._block_size, (y2 - y1) // self._block_size),
            resample=Image.Resampling.NEAREST,
        )
        mosaic = small.resize(
            (x2 - x1, y2 - y1),
            resample=Image.Resampling.NEAREST,
        )
        
        image.paste(mosaic, (x1, y1))
        return image
```

#### 5.2.2 高斯模糊

```python
from PIL import ImageFilter

class GaussianBlurOperator:
    """高斯模糊操作"""
    
    def __init__(self, radius: int = 10):
        self._radius = radius
    
    def apply(
        self,
        image: Image,
        bbox: Tuple[int, int, int, int],
    ) -> Image:
        """应用高斯模糊"""
        x1, y1, x2, y2 = bbox
        region = image.crop((x1, y1, x2, y2))
        blurred = region.filter(ImageFilter.GaussianBlur(self._radius))
        image.paste(blurred, (x1, y1))
        return image
```

#### 5.2.3 纯色覆盖

```python
class SolidFillOperator:
    """纯色覆盖操作"""
    
    def __init__(self, fill_color: Tuple[int, int, int] = (0, 0, 0)):
        self._fill_color = fill_color
    
    def apply(
        self,
        image: Image,
        bbox: Tuple[int, int, int, int],
    ) -> Image:
        """应用纯色覆盖"""
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        draw.rectangle(bbox, fill=self._fill_color)
        return image
```

---

## 6. 处理器设计

### 6.1 文本处理器

```python
class TextProcessor:
    """文本PII处理器"""
    
    def __init__(
        self,
        analyzer: CNPIIAnalyzerEngine,
        anonymizer: CNPIIAnonymizerEngine,
    ):
        self._analyzer = analyzer
        self._anonymizer = anonymizer
    
    def process(
        self,
        text: str,
        entities: Optional[List[str]] = None,
        operator_config: Optional[Dict[str, OperatorConfig]] = None,
        language: str = "zh",
    ) -> TextProcessResult:
        """
        处理文本中的PII
        
        Args:
            text: 输入文本
            entities: 要识别的PII类型列表
            operator_config: 匿名化操作配置
            language: 语言类型
        
        Returns:
            TextProcessResult: 处理结果
        """
        analyzer_results = self._analyzer.analyze(
            text=text,
            language=language,
            entities=entities,
        )
        
        anonymized = self._anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operator_config,
        )
        
        return TextProcessResult(
            original_text=text,
            anonymized_text=anonymized.text,
            pii_entities=[
                PIIEntity(
                    entity_type=r.entity_type,
                    start=r.start,
                    end=r.end,
                    score=r.score,
                    original_text=text[r.start:r.end],
                )
                for r in analyzer_results
            ],
        )
```

### 6.2 图像处理器

```python
class ImageProcessor:
    """图像PII处理器"""
    
    def __init__(
        self,
        image_analyzer: ImageAnalyzerEngine,
        ocr_engine: OCREngine,
        mosaic_operator: Optional[MosaicOperator] = None,
    ):
        self._image_analyzer = image_analyzer
        self._ocr_engine = ocr_engine
        self._mosaic_operator = mosaic_operator or PixelMosaicOperator()
    
    def process(
        self,
        image: Image,
        mosaic_style: str = "pixel",
        fill_color: Tuple[int, int, int] = (0, 0, 0),
        entities: Optional[List[str]] = None,
        allow_list: Optional[List[str]] = None,
    ) -> ImageProcessResult:
        """
        处理图像中的PII
        
        Args:
            image: 输入图像
            mosaic_style: 马赛克样式 (pixel/blur/fill)
            fill_color: 纯色覆盖颜色
            entities: 要识别的PII类型列表
            allow_list: 白名单列表
        
        Returns:
            ImageProcessResult: 处理结果
        """
        ocr_result = self._ocr_engine.recognize(image)
        
        analyzer_results = self._image_analyzer.analyze(
            image=image,
            ocr_result=ocr_result,
            entities=entities,
            allow_list=allow_list,
        )
        
        processed_image = image.copy()
        bboxes = self._get_bboxes(ocr_result, analyzer_results)
        
        for bbox in bboxes:
            processed_image = self._apply_mosaic(
                processed_image,
                bbox,
                mosaic_style,
                fill_color,
            )
        
        return ImageProcessResult(
            original_image=image,
            processed_image=processed_image,
            pii_entities=self._extract_entities(ocr_result, analyzer_results),
        )
```

---

## 7. API设计

### 7.1 RESTful API接口

#### 7.1.1 文本处理接口

```
POST /api/v1/text/anonymize
```

**请求体：**
```json
{
    "text": "我的手机号是13812345678，身份证号是110101199001011234",
    "entities": ["CN_PHONE_NUMBER", "CN_ID_CARD"],
    "operators": {
        "CN_PHONE_NUMBER": {
            "type": "mask",
            "masking_char": "*",
            "keep_prefix": 3,
            "keep_suffix": 4
        },
        "CN_ID_CARD": {
            "type": "mask",
            "masking_char": "*",
            "keep_prefix": 6,
            "keep_suffix": 4
        }
    },
    "language": "zh"
}
```

**响应体：**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "original_text": "我的手机号是13812345678，身份证号是110101199001011234",
        "anonymized_text": "我的手机号是138****5678，身份证号是110101********1234",
        "pii_entities": [
            {
                "entity_type": "CN_PHONE_NUMBER",
                "start": 6,
                "end": 17,
                "score": 0.95,
                "original_text": "13812345678",
                "anonymized_text": "138****5678"
            },
            {
                "entity_type": "CN_ID_CARD",
                "start": 22,
                "end": 40,
                "score": 0.95,
                "original_text": "110101199001011234",
                "anonymized_text": "110101********1234"
            }
        ]
    }
}
```

#### 7.1.2 图像处理接口

```
POST /api/v1/image/anonymize
```

**请求：** multipart/form-data
- `image`: 图像文件
- `mosaic_style`: 马赛克样式 (pixel/blur/fill)
- `fill_color`: 填充颜色（JSON格式）
- `entities`: 要识别的PII类型（JSON数组）

**响应体：**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "pii_entities": [
            {
                "entity_type": "CN_PHONE_NUMBER",
                "bbox": [100, 200, 250, 230],
                "score": 0.85,
                "original_text": "13812345678"
            }
        ],
        "image_url": "/api/v1/image/download/processed_image_id"
    }
}
```

### 7.2 FastAPI实现

```python
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="CN PII Anonymization API",
    description="中国个人信息脱敏API",
    version="1.0.0",
)

@app.post("/api/v1/text/anonymize")
async def anonymize_text(request: TextAnonymizeRequest):
    """文本PII匿名化"""
    processor = get_text_processor()
    result = processor.process(
        text=request.text,
        entities=request.entities,
        operator_config=request.operators,
        language=request.language,
    )
    return APIResponse(data=result)

@app.post("/api/v1/image/anonymize")
async def anonymize_image(
    image: UploadFile = File(...),
    mosaic_style: str = Form("pixel"),
    entities: Optional[str] = Form(None),
):
    """图像PII匿名化"""
    processor = get_image_processor()
    img = Image.open(image.file)
    
    result = processor.process(
        image=img,
        mosaic_style=mosaic_style,
        entities=json.loads(entities) if entities else None,
    )
    
    img_bytes = io.BytesIO()
    result.processed_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return StreamingResponse(
        img_bytes,
        media_type="image/png",
    )
```

---

## 8. 配置设计

### 8.1 识别器配置 (recognizer_config.yaml)

```yaml
recognizers:
  cn_phone:
    enabled: true
    entity_type: CN_PHONE_NUMBER
    score_threshold: 0.85
    context_words:
      - 手机
      - 电话
      - 联系方式
  
  cn_id_card:
    enabled: true
    entity_type: CN_ID_CARD
    score_threshold: 0.95
    validate_check_digit: true
  
  cn_bank_card:
    enabled: true
    entity_type: CN_BANK_CARD
    score_threshold: 0.7
    validate_luhn: true
  
  cn_passport:
    enabled: true
    entity_type: CN_PASSPORT
    score_threshold: 0.85
  
  cn_email:
    enabled: true
    entity_type: CN_EMAIL
    score_threshold: 0.85
  
  cn_address:
    enabled: false
    entity_type: CN_ADDRESS
    score_threshold: 0.7
  
  cn_name:
    enabled: false
    entity_type: CN_NAME
    score_threshold: 0.7

nlp_engine:
  type: spacy
  models:
    - lang_code: zh
      model_name: zh_core_web_lg

ocr_engine:
  type: tesseract
  language: chi_sim+eng
  config: --psm 6
```

### 8.2 应用配置 (settings.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    
    app_name: str = "CN PII Anonymization"
    app_version: str = "1.0.0"
    debug: bool = False
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    spacy_model: str = "zh_core_web_lg"
    tesseract_path: Optional[str] = None
    
    max_image_size: int = 10 * 1024 * 1024
    supported_image_formats: List[str] = ["png", "jpg", "jpeg", "bmp"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 9. 错误处理设计

### 9.1 异常类定义

```python
class CNPIIError(Exception):
    """基础异常类"""
    pass

class OCRError(CNPIIError):
    """OCR识别异常"""
    pass

class UnsupportedImageFormatError(CNPIIError):
    """不支持的图像格式异常"""
    pass

class PIIRecognitionError(CNPIIError):
    """PII识别异常"""
    pass

class AnonymizationError(CNPIIError):
    """匿名化处理异常"""
    pass
```

### 9.2 错误响应格式

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(CNPIIError)
async def pii_exception_handler(request: Request, exc: CNPIIError):
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": str(exc),
            "error_type": type(exc).__name__,
        },
    )
```

---

## 10. 性能优化设计

### 10.1 性能指标

| 指标 | 目标值 | 优化策略 |
|------|--------|----------|
| 单张图片处理时间 | < 10秒 | OCR并行处理、图像压缩 |
| 文本处理时间 | < 100ms | 正则预编译、识别器缓存 |
| PII识别准确率 | > 99% | 多重验证、上下文增强 |
| 内存占用 | < 500MB | 模型懒加载、图像流式处理 |

### 10.2 优化策略

1. **NLP模型优化**
   - 使用spaCy的`exclude`参数排除不需要的管道组件
   - 预加载模型，避免重复加载

2. **OCR优化**
   - 设置合理的DPI（300）
   - 使用多线程处理大图分块

3. **识别器优化**
   - 正则表达式预编译
   - 识别器结果缓存

4. **图像处理优化**
   - 大图自动缩放
   - 使用Pillow的惰性加载

---

## 11. 测试策略

### 11.1 单元测试

```python
class TestCNPhoneRecognizer:
    """手机号识别器测试"""
    
    @pytest.fixture
    def recognizer(self):
        return CNPhoneRecognizer()
    
    @pytest.mark.parametrize("text,expected_count", [
        ("我的手机号是13812345678", 1),
        ("联系电话：+86 138-1234-5678", 1),
        ("这是普通文本没有手机号", 0),
    ])
    def test_recognize_phone(
        self,
        recognizer,
        text: str,
        expected_count: int,
    ):
        results = recognizer.analyze(text, ["CN_PHONE_NUMBER"], None)
        assert len(results) == expected_count
```

### 11.2 集成测试

```python
class TestTextPipeline:
    """文本处理管道集成测试"""
    
    @pytest.fixture
    def processor(self):
        return TextProcessor(
            analyzer=CNPIIAnalyzerEngine(),
            anonymizer=CNPIIAnonymizerEngine(),
        )
    
    def test_full_pipeline(self, processor):
        text = "张三的手机号是13812345678，身份证号是110101199001011234"
        result = processor.process(text)
        
        assert "138****5678" in result.anonymized_text
        assert len(result.pii_entities) >= 2
```

---

## 12. 部署方案

### 12.1 Docker部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install uv && uv sync

COPY . .

RUN python -m spacy download zh_core_web_lg

EXPOSE 8000

CMD ["uvicorn", "cn_pii_anonymization.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 12.2 Docker Compose

```yaml
version: '3.8'

services:
  pii-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 13. 开发计划

### 13.1 迭代计划

| 阶段 | 内容 | 周期 |
|------|------|------|
| **Phase 1** | 基础框架搭建、核心识别器实现 | 2周 |
| **Phase 2** | 文本处理管道、API接口开发 | 2周 |
| **Phase 3** | 图像处理管道、OCR集成 | 2周 |
| **Phase 4** | 测试完善、文档编写 | 1周 |
| **Phase 5** | 性能优化、部署上线 | 1周 |

### 13.2 里程碑

- **M1**: 完成P0级别PII识别器（手机号、身份证、银行卡、护照）
- **M2**: 完成文本处理管道和API接口
- **M3**: 完成图像处理管道
- **M4**: 完成P1级别PII识别器（邮箱）
- **M5**: 完成P2级别PII识别器（地址、姓名）
- **M6**: 完成性能优化和部署

---

## 14. 附录

### 14.1 PII实体类型对照表

| 实体类型 | 描述 | 优先级 |
|----------|------|--------|
| CN_PHONE_NUMBER | 中国大陆手机号 | P0 |
| CN_ID_CARD | 中国大陆身份证号 | P0 |
| CN_BANK_CARD | 中国大陆银行卡号 | P0 |
| CN_PASSPORT | 中国护照号 | P0 |
| CN_EMAIL | 邮箱地址 | P1 |
| CN_ADDRESS | 中国地址 | P2 |
| CN_NAME | 中文姓名 | P2 |

### 14.2 参考资源

- [Microsoft Presidio GitHub](https://github.com/microsoft/presidio)
- [Presidio 官方文档](https://microsoft.github.io/presidio/)
- [spaCy 中文模型](https://spacy.io/models/zh)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [中国行政区划代码](http://www.mca.gov.cn/article/sj/xzqh/)
