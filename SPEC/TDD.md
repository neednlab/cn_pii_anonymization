# CN PII Anonymization 技术设计文档 (TDD)

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| **文档名称** | CN PII Anonymization 技术设计文档 |
| **版本** | v2.1 |
| **日期** | 2026-02-17 |
| **关联文档** | PRD.md |

### 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v2.1 | 2026-02-17 | 姓名识别IE schema扩展，支持"姓名"和"人名"两种类型 |
| v2.0 | 2026-02-17 | 添加PII识别器优先级机制，确保重叠结果只保留高优先级类型 |
| v1.9 | 2026-02-16 | 身份证识别器添加OCR错误容错机制，支持19位数字修复 |
| v1.8 | 2026-02-16 | 姓名识别器添加allow_list和deny_list自定义配置功能 |
| v1.7 | 2026-02-16 | 修复银行卡/身份证识别器边界匹配，排除前后有字母的情况 |
| v1.6 | 2026-02-16 | 身份证识别器支持带空格格式的身份证号；统一使用数字边界匹配 |
| v1.5 | 2026-02-16 | 银行卡识别器支持带空格格式的银行卡号 |
| v1.4 | 2026-02-15 | 将姓名和地址识别方案从LAC NER改为信息抽取(information_extraction)方法 |
| v1.3 | 2026-02-15 | 与实际代码同步更新 |
| v1.2 | 2026-02-14 | 添加PaddleOCR引擎设计 |
| v1.1 | 2026-02-13 | 初始版本 |

---

## 2. 技术选型

### 2.1 核心框架选择

本项目选择 **Microsoft Presidio** 作为核心框架，原因如下：

| 特性 | 说明 |
|------|------|
| **开源免费** | MIT许可证，可商用 |
| **模块化设计** | Analyzer、Anonymizer、Image Redactor三大模块独立且协同 |
| **可扩展性强** | 支持自定义识别器、自定义匿名化操作 |
| **多语言支持** | 支持中文NLP模型 |
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
│  │ (正则匹配)   │ │ (正则匹配)   │ │ (正则匹配)   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐ ┌─────────────┐                            │
│  │ 姓名识别器   │ │ 地址识别器   │                            │
│  │(信息抽取IE)  │ │(信息抽取IE)  │                            │
│  └─────────────┘ └─────────────┘                            │
├──────────────────────────────────────────────────────────────┤
│                      基础设施层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ PaddleNLP   │ │  PaddleOCR  │ │   Loguru    │            │
│  │ LAC + IE    │ │    OCR      │ │   日志      │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

**说明：**
- LAC (lexical_analysis): 用于分词和词性标注
- IE (information_extraction): 用于姓名和地址的精确识别

### 2.3 依赖组件

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.12 | 运行环境 |
| presidio-analyzer | >=2.2 | PII识别引擎 |
| presidio-anonymizer | >=2.2 | PII匿名化引擎 |
| presidio-image-redactor | >=0.0.50 | 图像PII处理 |
| PaddleNLP | >=2.8.1 | 中文NLP处理（LAC模型） |
| PaddleOCR | >=3.1.1 | OCR引擎（中文识别优化，支持PP-OCRv4/PP-OCRv5） |
| PaddlePaddle | >=3.3.0 | PaddleNLP/PaddleOCR底层框架 |
| aistudio-sdk | >=0.2.5,<0.3.0 | PaddleNLP模型下载支持 |
| FastAPI | >=0.109 | API服务框架 |
| uvicorn | >=0.27 | ASGI服务器 |
| Loguru | >=0.7 | 日志管理 |
| Pillow | >=10.0 | 图像处理 |
| Faker | >=22.0 | 假名生成 |
| pydantic | >=2.0 | 数据验证 |
| pydantic-settings | >=2.0 | 配置管理 |
| PyYAML | >=6.0 | YAML解析 |
| Click | >=8.0 | CLI工具 |

---

## 2.5 PII识别器优先级机制

### 2.5.1 设计背景

在实际应用中，同一文本片段可能同时满足多种PII类型的识别规则。例如：
- 身份证号（18位数字）可能被银行卡识别器识别为银行卡号
- 身份证号中的部分数字可能被手机号识别器识别为手机号
- 银行卡号（16-19位数字）中的部分数字可能被手机号识别器识别为手机号

为确保一段文本只被识别为一种PII类型，需要引入优先级机制。

### 2.5.2 优先级规则

| 优先级 | PII类型 | 说明 |
|--------|---------|------|
| 1（最高） | CN_ID_CARD | 身份证号具有最严格的校验规则（省份码、出生日期、校验码） |
| 2 | CN_BANK_CARD | 银行卡号具有Luhn校验 |
| 3 | CN_PHONE_NUMBER | 手机号格式相对简单 |
| 4 | CN_PASSPORT | 护照号格式特殊 |
| 5 | CN_EMAIL | 邮箱格式特殊 |
| 6 | CN_NAME | 姓名识别依赖IE模型 |
| 7（最低） | CN_ADDRESS | 地址识别依赖IE模型 |

### 2.5.3 实现设计

**优先级配置类：**

```python
class PIIPrioritySettings:
    """
    PII识别器优先级配置

    当多个识别器的识别结果重叠时，优先级高的结果将被保留。
    优先级数值越小，优先级越高。
    """

    cn_id_card: int = 1
    cn_bank_card: int = 2
    cn_phone_number: int = 3
    cn_passport: int = 4
    cn_email: int = 5
    cn_name: int = 6
    cn_address: int = 7

    def get_priority(self, entity_type: str) -> int:
        """获取指定实体类型的优先级"""
        priority_map = {
            "CN_ID_CARD": self.cn_id_card,
            "CN_BANK_CARD": self.cn_bank_card,
            "CN_PHONE_NUMBER": self.cn_phone_number,
            "CN_PASSPORT": self.cn_passport,
            "CN_EMAIL": self.cn_email,
            "CN_NAME": self.cn_name,
            "CN_ADDRESS": self.cn_address,
        }
        return priority_map.get(entity_type, 99)
```

**优先级过滤方法：**

```python
def _apply_priority_filter(self, results: list[RecognizerResult]) -> list[RecognizerResult]:
    """
    应用优先级过滤

    当多个识别结果重叠时，保留高优先级的结果。
    """
    if not results or len(results) <= 1:
        return results

    priority_settings = settings.pii_priorities
    filtered: list[RecognizerResult] = []

    # 按起始位置排序
    sorted_results = sorted(results, key=lambda r: (r.start, r.end))

    for result in sorted_results:
        should_add = True
        result_priority = priority_settings.get_priority(result.entity_type)

        # 检查与已保留结果的重叠情况
        to_remove: list[int] = []
        for i, existing in enumerate(filtered):
            existing_priority = priority_settings.get_priority(existing.entity_type)

            if self._results_overlap(result, existing):
                if result_priority < existing_priority:
                    # 新结果优先级更高，标记移除旧结果
                    to_remove.append(i)
                else:
                    # 已有结果优先级更高或相等，不添加新结果
                    should_add = False
                    break

        # 移除被覆盖的低优先级结果
        for i in reversed(to_remove):
            filtered.pop(i)

        if should_add:
            filtered.append(result)

    return filtered

@staticmethod
def _results_overlap(r1: RecognizerResult, r2: RecognizerResult) -> bool:
    """检查两个识别结果是否重叠"""
    return r1.start < r2.end and r2.start < r1.end
```

### 2.5.4 处理流程

```
文本输入
    ↓
各识别器并行识别
    ↓
置信度阈值过滤
    ↓
优先级过滤（新增）
    ├── 检测重叠结果
    ├── 比较优先级
    └── 保留高优先级结果
    ↓
返回最终识别结果
```

### 2.5.5 示例

**输入文本：** `身份证号110101199001011237`

**识别结果（过滤前）：**
- CN_ID_CARD: 位置[4:22]，优先级1
- CN_BANK_CARD: 位置[4:22]，优先级2（身份证号也符合银行卡号格式）
- CN_PHONE_NUMBER: 位置[8:19]，优先级3（身份证号中包含手机号格式的子串）

**识别结果（过滤后）：**
- CN_ID_CARD: 位置[4:22]（保留优先级最高的身份证识别结果）

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
│       ├── nlp/                       # NLP引擎模块
│       │   ├── __init__.py
│       │   └── nlp_engine.py          # PaddleNLP引擎封装
│       │
│       ├── ocr/                       # OCR引擎模块
│       │   ├── __init__.py
│       │   └── ocr_engine.py          # PaddleOCR引擎封装
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
│       │   ├── settings.py            # 配置管理(pydantic-settings)
│       │   └── recognizer_config.yaml # 识别器配置(遗留文件，暂未使用)
│       │
│       └── utils/                     # 工具模块
│           ├── __init__.py
│           ├── exceptions.py          # 异常类定义
│           └── logger.py              # 日志工具(Loguru)
│
├── tests/                             # 测试目录
│   ├── __init__.py
│   ├── conftest.py                    # pytest配置
│   ├── unit/                          # 单元测试
│   │   ├── test_recognizers.py
│   │   ├── test_operators.py
│   │   ├── test_processors.py
│   │   ├── test_engines.py
│   │   ├── test_ocr_engine.py
│   │   └── test_image_operators.py
│   ├── integration/                   # 集成测试
│   │   ├── test_text_pipeline.py
│   │   ├── test_api.py
│   │   └── test_image_api.py
│   └── performance/                   # 性能测试
│       └── test_performance.py
│
├── scripts/                           # 脚本目录
│   ├── check_device.py                # 设备检查脚本
│   ├── download_models.py             # 模型下载脚本
│   └── test_ocr_mkldnn.py             # OCR MKLDNN测试脚本
│
├── docs/                              # 文档目录
├── SPEC/                              # 规格文档
│   ├── PRD.md
│   ├── TDD.md
│   └── process.md                     # 开发进度文档
├── pyproject.toml                     # 项目配置
├── README.md
├── main.py                            # 入口文件
├── Dockerfile                         # Docker构建文件
└── docker-compose.yml                 # Docker Compose配置
```

### 3.2 核心模块设计

#### 3.2.1 分析器引擎 (AnalyzerEngine)

```python
from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry

from cn_pii_anonymization.nlp.nlp_engine import PaddleNlpEngineProvider


class CNPIIAnalyzerEngine:
    """
    中文PII分析器引擎

    封装Presidio AnalyzerEngine，注册中文PII识别器，提供中文PII识别能力。
    使用PaddleNLP作为NLP引擎，替代spaCy。

    采用单例模式，确保全局只有一个分析器实例。

    Attributes:
        _analyzer: Presidio分析器引擎实例
        _registry: 识别器注册表
        _nlp_engine: PaddleNLP引擎

    Example:
        >>> engine = CNPIIAnalyzerEngine()
        >>> results = engine.analyze("我的手机号是13812345678")
        >>> for r in results:
        ...     print(f"发现{r.entity_type}: {r.score}")
    """

    _instance: "CNPIIAnalyzerEngine | None" = None
    _initialized: bool = False

    def __new__(cls) -> "CNPIIAnalyzerEngine":
        """单例模式，确保全局只有一个分析器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化分析器引擎"""
        if CNPIIAnalyzerEngine._initialized:
            return

        self._setup_nlp_engine()
        self._setup_registry()
        self._setup_analyzer()
        CNPIIAnalyzerEngine._initialized = True

    def _setup_nlp_engine(self) -> None:
        """设置NLP引擎（使用PaddleNLP）"""
        pass

    def _setup_registry(self) -> None:
        """设置识别器注册表并注册中文PII识别器"""
        pass

    def _setup_analyzer(self) -> None:
        """设置分析器"""
        pass

    def analyze(
        self,
        text: str,
        language: str = "zh",
        entities: list[str] | None = None,
        score_threshold: float = 0.5,
        allow_list: list[str] | None = None,
        **kwargs: Any,
    ) -> list:
        """
        分析文本中的PII实体

        Args:
            text: 待分析的文本
            language: 语言代码，默认为"zh"
            entities: 要识别的PII类型列表，None表示识别所有类型
            score_threshold: 置信度阈值，低于此值的结果将被过滤
            allow_list: 白名单列表，匹配的内容将被排除
            **kwargs: 其他参数传递给Presidio分析器

        Returns:
            识别结果列表
        """
        pass

    def add_recognizer(self, recognizer: Any) -> None:
        """
        添加自定义识别器

        Args:
            recognizer: 自定义识别器实例
        """
        pass

    def get_supported_entities(self, language: str = "zh") -> list[str]:
        """
        获取支持的PII实体类型列表

        Args:
            language: 语言代码

        Returns:
            支持的实体类型列表
        """
        pass

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
```

#### 3.2.2 匿名化引擎 (AnonymizerEngine)

```python
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, OperatorResult


class CNPIIAnonymizerEngine:
    """
    中文PII匿名化引擎

    封装Presidio AnonymizerEngine，提供中文PII匿名化处理能力。
    支持多种匿名化操作：掩码、假名替换等。

    采用单例模式，确保全局只有一个匿名化器实例。

    Attributes:
        _anonymizer: Presidio匿名化引擎实例
        _operators: 自定义操作符配置字典

    Example:
        >>> engine = CNPIIAnonymizerEngine()
        >>> result = engine.anonymize(
        ...     text="手机号13812345678",
        ...     analyzer_results=analyzer_results,
        ...     operators={"CN_PHONE_NUMBER": OperatorConfig("mask", {"masking_char": "*"})}
        ... )
        >>> print(result.text)
    """

    _instance: "CNPIIAnonymizerEngine | None" = None
    _initialized: bool = False

    def __new__(cls) -> "CNPIIAnonymizerEngine":
        """单例模式，确保全局只有一个匿名化器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化匿名化引擎"""
        if CNPIIAnonymizerEngine._initialized:
            return

        self._setup_anonymizer()
        self._setup_operators()
        CNPIIAnonymizerEngine._initialized = True

    def _setup_anonymizer(self) -> None:
        """设置匿名化引擎"""
        pass

    def _setup_operators(self) -> None:
        """设置自定义操作符"""
        pass

    def anonymize(
        self,
        text: str,
        analyzer_results: list,
        operators: dict[str, OperatorConfig] | None = None,
    ) -> OperatorResult:
        """
        对识别出的PII进行匿名化处理

        Args:
            text: 原始文本
            analyzer_results: 分析器返回的识别结果列表
            operators: 自定义操作符配置，用于指定不同PII类型的处理方式

        Returns:
            匿名化处理结果，包含处理后的文本和操作详情
        """
        pass

    def set_operator(
        self,
        entity_type: str,
        operator_config: OperatorConfig,
    ) -> None:
        """
        设置特定实体类型的匿名化操作

        Args:
            entity_type: PII实体类型
            operator_config: 操作符配置
        """
        pass

    def get_mask_operator(
        self,
        masking_char: str = "*",
        keep_prefix: int = 0,
        keep_suffix: int = 0,
    ) -> OperatorConfig:
        """
        获取掩码操作符配置

        Args:
            masking_char: 掩码字符
            keep_prefix: 保留前N位
            keep_suffix: 保留后N位

        Returns:
            操作符配置
        """
        pass

    def get_fake_operator(self, entity_type: str) -> OperatorConfig:
        """
        获取假名替换操作符配置

        Args:
            entity_type: PII实体类型

        Returns:
            操作符配置
        """
        pass

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
```

#### 3.2.3 图像脱敏引擎 (ImageRedactorEngine)

```python
from PIL import Image

from cn_pii_anonymization.core.analyzer import CNPIIAnalyzerEngine
from cn_pii_anonymization.ocr.ocr_engine import OCRResult, PaddleOCREngine
from cn_pii_anonymization.operators.mosaic_operator import MosaicStyle


class CNPIIImageRedactorEngine:
    """
    中文PII图像脱敏引擎

    整合OCR识别、PII分析和图像脱敏功能，提供完整的图像PII处理能力。

    采用单例模式，确保全局只有一个图像脱敏实例。

    Attributes:
        _analyzer: PII分析器引擎
        _ocr_engine: OCR引擎
        _ocr_result_cache: OCR结果缓存

    Example:
        >>> engine = CNPIIImageRedactorEngine()
        >>> image = Image.open("document.png")
        >>> result = engine.redact(image)
        >>> result.save("redacted_document.png")
    """

    _instance: "CNPIIImageRedactorEngine | None" = None
    _initialized: bool = False

    def __new__(cls) -> "CNPIIImageRedactorEngine":
        """单例模式，确保全局只有一个图像脱敏实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化图像脱敏引擎"""
        if CNPIIImageRedactorEngine._initialized:
            return

        self._analyzer = CNPIIAnalyzerEngine()
        self._ocr_engine = PaddleOCREngine()
        self._ocr_result_cache: OCRResult | None = None
        CNPIIImageRedactorEngine._initialized = True

    def redact(
        self,
        image: Image.Image,
        mosaic_style: str | MosaicStyle = MosaicStyle.PIXEL,
        fill_color: tuple[int, int, int] = (0, 0, 0),
        entities: list[str] | None = None,
        allow_list: list[str] | None = None,
        score_threshold: float = 0.5,
        **mosaic_kwargs: Any,
    ) -> Image.Image:
        """
        对图像中的PII进行脱敏处理

        Args:
            image: PIL图像对象
            mosaic_style: 马赛克样式 (pixel/blur/fill)
            fill_color: 纯色填充颜色 (R, G, B)
            entities: 要识别的PII类型列表，None表示识别所有类型
            allow_list: 白名单列表，匹配的内容将被排除
            score_threshold: 置信度阈值
            **mosaic_kwargs: 马赛克操作符参数

        Returns:
            处理后的图像

        Raises:
            OCRError: OCR识别失败时抛出
            PIIRecognitionError: PII识别失败时抛出
        """
        pass

    def get_ocr_result(self) -> OCRResult | None:
        """
        获取最近一次OCR识别结果

        Returns:
            OCRResult: OCR识别结果，如果尚未执行OCR则返回None
        """
        pass

    def get_supported_entities(self) -> list[str]:
        """获取支持的PII实体类型列表"""
        pass

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False
```

---

## 4. NLP引擎模块设计

### 4.1 PaddleNLP处理结果

```python
from presidio_analyzer.nlp_engine import NlpArtifacts


class PaddleNlpArtifacts(NlpArtifacts):
    """
    PaddleNLP处理结果

    继承Presidio的NlpArtifacts，兼容其接口。

    Attributes:
        entities: NER识别的实体列表
        tokens: 分词结果列表
        tokens_indices: 分词索引列表
        lemmas: 词形还原列表
        nlp_engine: NLP引擎
        language: 语言代码
        scores: 实体置信度列表
        keywords: 关键词列表
    """

    def __init__(
        self,
        entities: list[Any] | None = None,
        tokens: list[str] | None = None,
        tokens_indices: list[int] | None = None,
        lemmas: list[str] | None = None,
        nlp_engine: Any = None,
        language: str = "zh",
        scores: list[float] | None = None,
    ) -> None:
        self.entities = entities or []
        self.tokens = tokens or []
        self.tokens_indices = tokens_indices or []
        self.lemmas = lemmas or []
        self.nlp_engine = nlp_engine
        self.language = language
        self.scores = scores or [0.85] * len(self.entities)
        self.keywords = self._extract_keywords(lemmas or [])

    def _extract_keywords(self, lemmas: list[str]) -> list[str]:
        """从词形列表中提取关键词"""
        pass

    def to_json(self) -> str:
        """转换为JSON字符串"""
        pass
```

### 4.2 PaddleNLP引擎（分词与词性标注）

```python
from typing import ClassVar


class PaddleNLPEngine:
    """
    PaddleNLP引擎

    封装PaddleNLP Taskflow，提供中文NLP处理能力，包括：
    - 分词 (lexical_analysis)
    - 词性标注

    兼容Presidio框架的NlpEngine接口。

    Example:
        >>> engine = PaddleNLPEngine()
        >>> artifacts = engine.process_text("张三的手机号是13812345678")
        >>> print(artifacts.tokens)
    """

    STOPWORDS: ClassVar[set[str]] = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
    }

    PUNCTUATION: ClassVar[set[str]] = {
        "，", "。", "！", "？", "；", "：", """, """, "'",
        "（", "）", "【", "】", "《", "》", "、", "…", "—",
    }

    NER_TAG_MAP: ClassVar[dict[str, str]] = {
        "PER": "PERSON",
        "PERSON": "PERSON",
        "nr": "PERSON",
        "LOC": "LOCATION",
        "LOCATION": "LOCATION",
        "ns": "LOCATION",
        "ORG": "ORG",
        "ORGANIZATION": "ORG",
        "nt": "ORG",
        "TIME": "DATE",
        "t": "DATE",
    }

    def __init__(self, use_gpu: bool = False) -> None:
        """
        初始化PaddleNLP引擎

        Args:
            use_gpu: 是否使用GPU加速
        """
        self._use_gpu = use_gpu
        self._lac: Any = None
        self._initialized = False
        self._init_error: str | None = None

    def is_loaded(self) -> bool:
        """检查引擎是否已加载"""
        return self._initialized

    def load(self) -> None:
        """加载引擎（兼容Presidio接口）"""
        pass

    def _init_lac(self) -> None:
        """延迟初始化PaddleNLP LAC模型"""
        pass

    def _simple_tokenize(self, text: str) -> list[str]:
        """
        简单分词（当PaddleNLP不可用时的后备方案）

        Args:
            text: 待分词文本

        Returns:
            分词结果列表
        """
        pass

    def process_text(self, text: str, language: str = "zh") -> PaddleNlpArtifacts:
        """
        处理文本，返回NLP处理结果

        Args:
            text: 待处理的文本
            language: 语言代码

        Returns:
            PaddleNlpArtifacts: NLP处理结果
        """
        pass

    def _extract_entities(
        self,
        tokens: list,
        tags: list,
        text: str,
    ) -> list:
        """
        从LAC结果中提取实体

        Args:
            tokens: 分词结果
            tags: 词性/实体标签
            text: 原始文本

        Returns:
            实体列表，每个元素包含实体文本、类型和位置
        """
        pass

    def is_stopword(self, word: str, language: str = "zh") -> bool:
        """检查是否为停用词"""
        pass

    def is_punct(self, word: str, language: str = "zh") -> bool:
        """检查是否为标点符号"""
        pass

    def is_supported_language(self, language: str) -> bool:
        """检查是否支持指定语言"""
        return language in ("zh", "chinese", "zh-cn")

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return ["zh", "chinese", "zh-cn"]
```

### 4.3 PaddleNLP信息抽取引擎

```python
class PaddleNLPInfoExtractionEngine:
    """
    PaddleNLP信息抽取引擎

    封装PaddleNLP Taskflow的information_extraction方法，
    用于姓名和地址的精确识别。


    Attributes:
        _ie_engine: 信息抽取Taskflow实例
        _schema: 抽取schema，定义要识别的实体类型
        ADDRESS_SCHEMA_KEYS: 地址schema类型集合，支持"地址"和"具体地址"
        NAME_SCHEMA_KEYS: 姓名schema类型集合，支持"姓名"和"人名"

    Example:
        >>> engine = PaddleNLPInfoExtractionEngine()
        >>> result = engine.extract("刘先生住在广东省深圳市南山区粤海街道科兴科学园B栋。")
        >>> print(result)
        [{'地址': [{'text': '广东省深圳市南山区粤海街道科兴科学园B栋', 'probability': 0.95}]}]
    """

    DEFAULT_SCHEMA: ClassVar[list[str]] = ["地址", "具体地址", "姓名", "人名"]
    ADDRESS_SCHEMA_KEYS: ClassVar[set[str]] = {"地址", "具体地址"}
    NAME_SCHEMA_KEYS: ClassVar[set[str]] = {"姓名", "人名"}

    def __init__(
        self,
        schema: list[str] | None = None,
        use_gpu: bool = False,
    ) -> None:
        """
        初始化信息抽取引擎

        Args:
            schema: 要抽取的实体类型列表，默认为['地址', '具体地址', '姓名']
            use_gpu: 是否使用GPU加速
        """
        self._schema = schema or self.DEFAULT_SCHEMA.copy()
        self._use_gpu = use_gpu
        self._ie_engine: Any = None
        self._initialized = False
        self._init_error: str | None = None

    def load(self) -> None:
        """加载引擎"""
        pass

    def _init_ie_engine(self) -> None:
        """延迟初始化信息抽取模型"""
        pass

    def extract(self, text: str) -> list[dict]:
        """
        从文本中抽取信息

        Args:
            text: 待抽取的文本

        Returns:
            抽取结果列表，每个元素是一个字典，包含实体类型和对应的文本

        Example:
            >>> result = engine.extract("张三住在北京市朝阳区")
            >>> # 返回: [{'姓名': [{'text': '张三', 'probability': 0.9}],
            >>> #         '地址': [{'text': '北京市朝阳区', 'probability': 0.85}]}]
        """
        pass

    def extract_addresses(self, text: str) -> list[dict]:
        """
        仅抽取地址信息

        支持识别"地址"和"具体地址"两种schema类型的地址信息。
        动态检测当前schema中包含的地址类型key，遍历所有地址类型key提取地址信息。

        Args:
            text: 待抽取的文本

        Returns:
            地址列表，每个元素包含text和probability
        """
        pass

    def extract_names(self, text: str) -> list[dict]:
        """
        仅抽取姓名信息

        支持识别"姓名"和"人名"两种schema类型的姓名信息。

        Args:
            text: 待抽取的文本

        Returns:
            姓名列表，每个元素包含text和probability
        """
        pass

    def is_loaded(self) -> bool:
        """检查引擎是否已加载"""
        return self._initialized

    def get_schema(self) -> list[str]:
        """获取当前schema"""
        return self._schema.copy()

    def set_schema(self, schema: list[str]) -> None:
        """
        设置新的schema（需要重新初始化引擎）

        Args:
            schema: 新的实体类型列表
        """
        pass
```

### 4.4 PaddleNLP引擎提供者

```python
class PaddleNlpEngineProvider:
    """
    PaddleNLP引擎提供者

    兼容Presidio的NlpEngineProvider接口。

    Example:
        >>> provider = PaddleNlpEngineProvider()
        >>> engine = provider.create_engine()
        >>> artifacts = engine.process_text("测试文本")
    """

    def __init__(self, nlp_configuration: dict | None = None) -> None:
        """
        初始化引擎提供者

        Args:
            nlp_configuration: NLP配置字典
        """
        self._configuration = nlp_configuration or {}

    def create_engine(self) -> PaddleNLPEngine:
        """
        创建PaddleNLP引擎实例

        Returns:
            PaddleNLPEngine实例
        """
        pass
```

---

## 5. OCR引擎模块设计

### 5.1 OCR识别结果

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class OCRResult:
    """
    OCR识别结果

    Attributes:
        text: 识别出的文本
        bounding_boxes: 文本边界框列表，每个元素为 (text, left, top, width, height)
        confidence: 整体置信度
    """

    text: str
    bounding_boxes: list[tuple[str, int, int, int, int]]
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        pass
```

### 5.2 OCR引擎基类

```python
from abc import ABC, abstractmethod


class BaseOCREngine(ABC):
    """
    OCR引擎基类

    定义OCR引擎的接口规范。
    """

    @abstractmethod
    def recognize(self, image: Image.Image) -> OCRResult:
        """
        识别图像中的文本

        Args:
            image: PIL图像对象

        Returns:
            OCRResult: OCR识别结果
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查OCR引擎是否可用

        Returns:
            bool: 是否可用
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """
        获取支持的语言列表

        Returns:
            支持的语言代码列表
        """
        pass
```

### 5.3 PaddleOCR引擎

```python
class PaddleOCREngine(BaseOCREngine):
    """
    PaddleOCR引擎

    封装PaddleOCR，提供中文OCR识别能力。
    支持PP-OCRv4模型，识别准确率高。

    Example:
        >>> engine = PaddleOCREngine()
        >>> if engine.is_available():
        ...     result = engine.recognize(image)
        ...     print(result.text)
    """

    def __init__(
        self,
        language: str = "ch",
        use_gpu: bool = False,
        use_angle_cls: bool = True,
        det_thresh: float | None = None,
        det_box_thresh: float | None = None,
        det_limit_side_len: int | None = None,
        model_dir: str | None = None,
        ocr_version: str | None = None,
    ) -> None:
        """
        初始化PaddleOCR引擎

        Args:
            language: OCR语言，默认中文(ch)
                - ch: 中文+英文
                - en: 英文
                - korean: 韩文
                - japan: 日文
            use_gpu: 是否使用GPU加速
            use_angle_cls: 是否使用方向分类器（识别文字方向）
            det_thresh: 文本检测像素阈值，值越小检测越敏感
            det_box_thresh: 文本检测框阈值，值越小检测越敏感
            det_limit_side_len: 图像边长限制
            model_dir: 本地模型目录路径
            ocr_version: OCR版本，默认PP-OCRv4
        """
        pass

    def _init_ocr(self) -> Any:
        """延迟初始化PaddleOCR实例"""
        pass

    def recognize(self, image: Image.Image) -> OCRResult:
        """
        识别图像中的文本

        Args:
            image: PIL图像对象

        Returns:
            OCRResult: OCR识别结果

        Raises:
            OCRError: OCR识别失败时抛出
        """
        pass

    def _parse_result(
        self,
        result: list | None,
    ) -> tuple[str, list[tuple[str, int, int, int, int]], float]:
        """
        解析PaddleOCR结果

        Args:
            result: PaddleOCR返回的结果

        Returns:
            tuple: (文本, 边界框列表, 平均置信度)
        """
        pass

    def is_available(self) -> bool:
        """检查PaddleOCR是否可用"""
        pass

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return ["ch", "en", "korean", "japan", "chinese_cht", "ta", "te", "ka", "latin", "arabic", "cyrillic", "devanagari"]
```

---

## 6. 中文PII识别器设计

### 6.1 识别器基类

```python
from abc import abstractmethod
from typing import Any, ClassVar

from presidio_analyzer import AnalysisExplanation, EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts


class CNPIIRecognizer(EntityRecognizer):
    """
    中文PII识别器基类

    继承自Presidio的EntityRecognizer，为中文PII识别器提供公共功能。

    所有中文PII识别器都应继承此类并实现analyze方法。

    Attributes:
        CONTEXT_WORDS: 上下文关键词列表，用于提高识别准确率

    Example:
        >>> class MyRecognizer(CNPIIRecognizer):
        ...     def analyze(self, text, entities, nlp_artifacts):
        ...         # 实现识别逻辑
        ...         pass
    """

    CONTEXT_WORDS: ClassVar[list[str]] = []

    def __init__(
        self,
        supported_entities: list[str],
        supported_language: str = "zh",
        name: str | None = None,
        context: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化识别器

        Args:
            supported_entities: 支持的实体类型列表
            supported_language: 支持的语言，默认为"zh"
            name: 识别器名称
            context: 上下文关键词列表
            **kwargs: 其他参数传递给父类
        """
        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            name=name,
            context=context or self.CONTEXT_WORDS,
            **kwargs,
        )

    @abstractmethod
    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None,
    ) -> list[RecognizerResult]:
        """
        分析文本，返回识别结果

        子类必须实现此方法。

        Args:
            text: 待分析的文本
            entities: 要识别的实体类型列表
            nlp_artifacts: NLP处理结果

        Returns:
            识别结果列表
        """
        pass

    def load(self) -> None:
        """加载资源（可选实现）"""
        pass

    def _create_result(
        self,
        entity_type: str,
        start: int,
        end: int,
        score: float,
    ) -> RecognizerResult:
        """
        创建识别结果

        Args:
            entity_type: 实体类型
            start: 起始位置
            end: 结束位置
            score: 置信度分数

        Returns:
            RecognizerResult实例
        """
        analysis_explanation = AnalysisExplanation(
            recognizer=self.name,
            original_score=score,
            pattern_name=self.name,
            pattern="regex" if hasattr(self, "_compiled_patterns") else "rule",
        )

        return RecognizerResult(
            entity_type=entity_type,
            start=start,
            end=end,
            score=score,
            analysis_explanation=analysis_explanation,
            recognition_metadata={
                RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
            },
        )

    def _validate_result(
        self,
        text: str,
        result: RecognizerResult,
    ) -> bool:
        """
        验证识别结果的有效性

        子类可重写此方法实现自定义验证逻辑。

        Args:
            text: 原始文本
            result: 识别结果

        Returns:
            结果是否有效
        """
        return True

    def _filter_results(
        self,
        text: str,
        results: list[RecognizerResult],
    ) -> list[RecognizerResult]:
        """
        过滤无效的识别结果

        Args:
            text: 原始文本
            results: 识别结果列表

        Returns:
            过滤后的结果列表
        """
        return [r for r in results if self._validate_result(text, r)]
```

### 6.2 手机号识别器

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

### 6.3 身份证识别器

**识别规则：**
- 18位身份证号：6位地区码 + 8位出生日期 + 3位顺序码 + 1位校验码
- 15位身份证号（旧版）：6位地区码 + 6位出生日期 + 3位顺序码
- 支持数字间包含空格（如 `1101 0119 9001 0112 37`）
- 支持校验码验证
- **OCR错误容错**：当匹配到19位数字时，尝试移除一位数字得到有效的18位身份证号

**正则表达式：**
```
# 18位身份证号
(?<![a-zA-Z\d])[1-9](?:\s*\d){17}(?![a-zA-Z\d])

# OCR错误容错（19位数字）
(?<![a-zA-Z\d])[1-9](?:\s*\d){18}(?![a-zA-Z\d])
```

**正则说明：**
- `(?<![a-zA-Z\d])` - 前面不能是字母或数字（负向后行断言）
- `[1-9]` - 以1-9开头
- `(?:\s*\d){17}` - 后面跟着17组（空格+数字），总共18位数字
- `(?:\s*\d){18}` - 后面跟着18组（空格+数字），总共19位数字（OCR错误情况）
- `\s*` - 允许零个或多个空格
- `(?![a-zA-Z\d])` - 后面不能是字母或数字（负向先行断言）

**OCR错误容错机制：**
当OCR识别将身份证号识别为19位数字时（多了一位），尝试移除每一位数字，检查是否能得到有效的18位身份证号。优先检查常见错误位置（如第6位，即出生年份开头）。

**实现设计：**

```python
class CNIDCardRecognizer(CNPIIRecognizer):
    """中国大陆身份证识别器
    
    支持：
    - 18位身份证号识别
    - OCR错误容错（19位数字时尝试修复）
    """
    
    ID_CARD_PATTERN = re.compile(
        r"(?<![a-zA-Z\d])[1-9](?:\s*\d){17}(?![a-zA-Z\d])"
    )
    
    # OCR错误容错正则：匹配19位数字
    ID_CARD_OCR_ERROR_PATTERN = re.compile(
        r"(?<![a-zA-Z\d])[1-9](?:\s*\d){18}(?![a-zA-Z\d])"
    )
    
    CONTEXT_WORDS = [
        "身份证", "身份证号", "证件号", "身份号码",
        "ID", "身份证件", "公民身份",
        "身份证号码", "身份证明", "居民身份证",
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
        
        # 正常匹配18位身份证号
        for match in self.ID_CARD_PATTERN.finditer(text):
            id_card = match.group()
            if self._validate_id_card(id_card):
                result = RecognizerResult(
                    entity_type="CN_ID_CARD",
                    start=match.start(),
                    end=match.end(),
                    score=0.95,
                )
                results.append(result)
        
        # OCR错误容错：处理19位数字情况
        ocr_error_results = self._handle_ocr_errors(text)
        results.extend(ocr_error_results)
        
        return results
    
    def _handle_ocr_errors(self, text: str) -> List[RecognizerResult]:
        """处理OCR识别错误的情况
        
        当OCR将身份证号识别为19位数字时（多了一位），
        尝试移除每一位数字，检查是否能得到有效的18位身份证号。
        """
        results = []
        
        for match in self.ID_CARD_OCR_ERROR_PATTERN.finditer(text):
            ocr_text = match.group()
            ocr_text_clean = ocr_text.replace(" ", "")
            
            if len(ocr_text_clean) != 19:
                continue
            
            valid_id_card = self._try_fix_ocr_error(ocr_text_clean)
            if valid_id_card:
                logger.info(
                    f"OCR错误容错: 从 '{ocr_text_clean}' 修复为 '{valid_id_card}'"
                )
                result = RecognizerResult(
                    entity_type="CN_ID_CARD",
                    start=match.start(),
                    end=match.end(),
                    score=0.90,  # 容错识别置信度略低
                )
                results.append(result)
        
        return results
    
    def _try_fix_ocr_error(self, ocr_text: str) -> str | None:
        """尝试修复OCR错误
        
        移除19位数字中的每一位，检查是否能得到有效的18位身份证号。
        优先检查常见错误位置（如第6位，即出生年份开头）。
        """
        if len(ocr_text) != 19:
            return None
        
        # 优先检查出生年份开头位置（第6、7、8位）
        priority_positions = [6, 7, 8, 0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        
        for pos in priority_positions:
            if pos >= len(ocr_text):
                continue
            candidate = ocr_text[:pos] + ocr_text[pos + 1:]
            if self._validate_id_card(candidate):
                return candidate
        
        return None
    
    def _validate_id_card(self, id_card: str) -> bool:
        """验证身份证号有效性"""
        # 去除空格后再验证
        id_card = id_card.replace(" ", "")
        
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

### 6.4 银行卡识别器

**识别规则：**
- 16-19位数字
- 支持数字间包含空格（如 `4111 1111 1111 1111`）
- 支持Luhn算法校验
- 支持常见银行BIN码识别

**正则表达式：**
```
(?<![a-zA-Z\d])\d(?:\s*\d){15,18}(?![a-zA-Z\d])
```

**正则说明：**
- `(?<![a-zA-Z\d])` - 前面不能是字母或数字（负向后行断言）
- `\d` - 以数字开头
- `(?:\s*\d){15,18}` - 后面跟着15到18组（空格+数字），总共16-19位数字
- `\s*` - 允许零个或多个空格
- `(?![a-zA-Z\d])` - 后面不能是字母或数字（负向先行断言）

**实现设计：**

```python
class CNBankCardRecognizer(CNPIIRecognizer):
    """中国大陆银行卡识别器"""
    
    BANK_CARD_PATTERN = re.compile(
        r"(?<![a-zA-Z\d])\d(?:\s*\d){15,18}(?![a-zA-Z\d])"
    )
    
    CONTEXT_WORDS = [
        "银行卡", "卡号", "账号", "银行账号",
        "信用卡", "借记卡", "储蓄卡",
        "bank", "card", "account",
        "银行卡号", "信用卡号",
    ]
    
    BANK_BIN_CODES = {
        "工商银行": ["622202", "622203", "622208", "621225", "621226"],
        "农业银行": ["622848", "622849", "622845", "622846"],
        "中国银行": ["621660", "621661", "621663", "621665"],
        "建设银行": ["621700", "436742", "436745", "622280"],
        "交通银行": ["622260", "622261", "622262"],
        "招商银行": ["622580", "622588", "621286", "621483"],
        "浦发银行": ["622518", "622520", "622521", "622522"],
        "民生银行": ["622615", "622617", "622618", "622622"],
        "兴业银行": ["622909", "622910", "622911", "622912"],
        "平安银行": ["622155", "622156", "622157", "622158"],
        "光大银行": ["622660", "622661", "622662", "622663"],
        "华夏银行": ["622630", "622631", "622632"],
        "广发银行": ["622568", "622569", "622570"],
        "中信银行": ["622690", "622691", "622692"],
        "邮储银行": ["622188", "622199", "622810"],
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
        
        for match in self.BANK_CARD_PATTERN.finditer(text):
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
        # 去除空格后再验证
        card_number = card_number.replace(" ", "")
        
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
        # 去除空格后再计算
        card_number = card_number.replace(" ", "")
        
        for bank, bin_codes in self.BANK_BIN_CODES.items():
            if any(card_number.startswith(code) for code in bin_codes):
                return 0.95
        return 0.7
```

### 6.5 护照号识别器

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

### 6.6 邮箱识别器

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

### 6.7 地址识别器 (P2 - 信息抽取)

**识别规则：**
- 使用PaddleNLP Taskflow的`information_extraction`方法进行地址识别
- Schema定义：`['地址', '具体地址']`，支持两种地址类型
- 支持省、市、区、街道、门牌号等多级地址识别
- **过滤规则**：识别到的地址字符数<6时，不作为PII返回（过滤掉过短的地址片段）
- **置信度**：直接采用information_extraction返回的probability结果

**实现设计：**

```python
class CNAddressRecognizer(CNPIIRecognizer):
    """中国大陆地址识别器"""
    
    # 地址最小长度阈值，小于此长度的地址将被过滤
    MIN_ADDRESS_LENGTH = 6
    
    # 地址schema类型集合，支持"地址"和"具体地址"两种类型
    ADDRESS_SCHEMA_KEYS = {"地址", "具体地址"}
    
    def __init__(self, ie_engine: Any = None):
        """
        初始化地址识别器
        
        Args:
            ie_engine: 信息抽取引擎实例（PaddleNLP Taskflow information_extraction）
        """
        super().__init__(supported_entities=["CN_ADDRESS"])
        self._ie_engine = ie_engine
    
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        """使用信息抽取模型识别地址"""
        results = []
        
        if self._ie_engine is None:
            return results
        
        ie_result = self._ie_engine(text)
        
        for item in ie_result:
            # 支持"地址"和"具体地址"两种schema类型
            for key in self.ADDRESS_SCHEMA_KEYS:
                if key in item:
                    for addr in item[key]:
                        addr_text = addr["text"]
                        # 过滤长度小于6的地址
                        if len(addr_text) < self.MIN_ADDRESS_LENGTH:
                            continue
                        
                        start = text.find(addr_text)
                        if start != -1:
                            # 直接使用IE返回的probability作为置信度
                            score = addr.get("probability", 0.85)
                            result = RecognizerResult(
                                entity_type="CN_ADDRESS",
                                start=start,
                                end=start + len(addr_text),
                                score=score,
                            )
                            results.append(result)
        
        return results
```

### 6.8 姓名识别器 (P2 - 信息抽取)

**识别规则：**
- 使用PaddleNLP Taskflow的`information_extraction`方法进行姓名识别
- Schema定义：`['姓名', '人名']`，支持两种姓名类型
- 支持中文姓名常见格式（2-5字）
- **置信度**：直接采用information_extraction返回的probability结果
- **allow_list**：允许通过的姓名列表，这些姓名不会被识别为PII
- **deny_list**：必须被脱敏的姓名列表，无论IE是否识别都会强制标记为PII

**实现设计：**

```python
class CNNameRecognizer(CNPIIRecognizer):
    """中文姓名识别器
    
    支持自定义allow_list和deny_list配置：
    - allow_list: 允许通过的姓名列表，这些姓名不会被识别为PII
    - deny_list: 必须被脱敏的姓名列表，无论IE是否识别都会强制标记为PII
    
    NAME_SCHEMA_KEYS: 姓名schema类型集合，支持"姓名"和"人名"
    """
    
    NAME_SCHEMA_KEYS: ClassVar[set[str]] = {"姓名", "人名"}
    
    def __init__(
        self,
        ie_engine: Any = None,
        allow_list: list[str] | None = None,
        deny_list: list[str] | None = None,
    ):
        """
        初始化姓名识别器
        
        Args:
            ie_engine: 信息抽取引擎实例（PaddleNLP Taskflow information_extraction）
            allow_list: 允许通过的姓名列表，这些姓名不会被识别为PII
            deny_list: 必须被脱敏的姓名列表，无论IE是否识别都会强制标记为PII
        """
        super().__init__(supported_entities=["CN_NAME"])
        self._ie_engine = ie_engine
        self._allow_list: set[str] = (
            {name for name in allow_list if name and name.strip()} if allow_list else set()
        )
        self._deny_list: set[str] = (
            {name for name in deny_list if name and name.strip()} if deny_list else set()
        )
    
    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: NlpArtifacts,
    ) -> List[RecognizerResult]:
        """使用信息抽取模型识别姓名
        
        处理逻辑：
        1. 先处理deny_list：强制标记为PII（置信度1.0）
        2. 处理IE识别结果，过滤allow_list中的姓名
        3. 合并结果，避免重复
        """
        results = []
        
        # 1. 处理deny_list
        for name in self._deny_list:
            start = 0
            while True:
                pos = text.find(name, start)
                if pos == -1:
                    break
                result = RecognizerResult(
                    entity_type="CN_NAME",
                    start=pos,
                    end=pos + len(name),
                    score=1.0,  # 用户明确要求脱敏，使用最高置信度
                )
                results.append(result)
                start = pos + len(name)
        
        # 2. 处理IE识别结果
        if self._ie_engine is not None:
            ie_result = self._ie_engine(text)
            
            for item in ie_result:
                if "姓名" in item:
                    for name in item["姓名"]:
                        name_text = name["text"]
                        # 过滤allow_list中的姓名
                        if name_text in self._allow_list:
                            continue
                        
                        start = text.find(name_text)
                        if start != -1:
                            # 直接使用IE返回的probability作为置信度
                            score = name.get("probability", 0.85)
                            result = RecognizerResult(
                                entity_type="CN_NAME",
                                start=start,
                                end=start + len(name_text),
                                score=score,
                            )
                            results.append(result)
        
        return results
    
    def set_allow_list(self, allow_list: list[str] | None) -> None:
        """动态设置允许列表"""
        pass
    
    def set_deny_list(self, deny_list: list[str] | None) -> None:
        """动态设置拒绝列表"""
        pass
    
    def get_allow_list(self) -> list[str]:
        """获取当前的允许列表"""
        pass
    
    def get_deny_list(self) -> list[str]:
        """获取当前的拒绝列表"""
        pass
```

**配置方式：**

在`.env`文件中配置：
```
# 允许通过的姓名列表（不需要被脱敏），使用逗号分隔
NAME_ALLOW_LIST=张三,李四,王五

# 必须被脱敏的姓名列表（无论IE是否识别），使用逗号分隔
NAME_DENY_LIST=赵六,钱七
```

---

## 7. 匿名化操作设计

### 7.1 文本匿名化操作

#### 7.1.1 掩码操作 (Mask)

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

#### 7.1.2 假名替换操作 (Fake)

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

### 7.2 图像匿名化操作

#### 7.2.1 马赛克样式枚举

```python
from enum import StrEnum


class MosaicStyle(StrEnum):
    """
    马赛克样式枚举

    Attributes:
        PIXEL: 像素块马赛克
        BLUR: 高斯模糊
        FILL: 纯色填充
    """

    PIXEL = "pixel"
    BLUR = "blur"
    FILL = "fill"
```

#### 7.2.2 马赛克操作符基类

```python
from abc import ABC, abstractmethod


class MosaicOperator(ABC):
    """
    马赛克操作符抽象基类

    定义马赛克操作的接口规范。
    """

    @abstractmethod
    def apply(
        self,
        image: Image.Image,
        bbox: tuple[int, int, int, int],
    ) -> Image.Image:
        """
        对图像指定区域应用马赛克效果

        Args:
            image: PIL图像对象
            bbox: 边界框 (left, top, right, bottom)

        Returns:
            处理后的图像
        """
        pass
```

#### 7.2.3 像素块马赛克

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

#### 7.2.4 高斯模糊

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

#### 7.2.5 纯色覆盖

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

#### 7.2.6 马赛克操作符工厂

```python
def create_mosaic_operator(
    style: MosaicStyle | str,
    **kwargs: Any,
) -> MosaicOperator:
    """
    创建马赛克操作符工厂函数

    Args:
        style: 马赛克样式
        **kwargs: 操作符参数

    Returns:
        MosaicOperator: 马赛克操作符实例

    Example:
        >>> operator = create_mosaic_operator("pixel", block_size=10)
        >>> operator = create_mosaic_operator("blur", radius=15)
        >>> operator = create_mosaic_operator("fill", fill_color=(128, 128, 128))
    """
    if isinstance(style, str):
        style = MosaicStyle(style)

    operators = {
        MosaicStyle.PIXEL: PixelMosaicOperator,
        MosaicStyle.BLUR: GaussianBlurOperator,
        MosaicStyle.FILL: SolidFillOperator,
    }

    operator_class = operators.get(style)
    if operator_class is None:
        raise ValueError(f"不支持的马赛克样式: {style}")

    return operator_class(**kwargs)
```

---

## 8. 处理器设计

### 8.1 文本处理器

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

### 8.2 图像处理器

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

## 9. API设计

### 9.1 RESTful API接口

#### 9.1.1 文本处理接口

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

#### 9.1.2 图像处理接口

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

### 9.2 API端点列表

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/` | GET | API基本信息 |
| `/api/v1/text/anonymize` | POST | 文本匿名化 |
| `/api/v1/text/analyze` | POST | 文本分析（仅识别PII） |
| `/api/v1/text/entities` | GET | 获取支持的实体类型 |
| `/api/v1/image/anonymize` | POST | 图像脱敏 |
| `/api/v1/image/analyze` | POST | 图像分析（仅识别PII） |
| `/api/v1/image/mosaic-styles` | GET | 获取支持的马赛克样式 |

### 9.3 FastAPI实现

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

## 10. 配置设计

### 10.1 应用配置 (settings.py)

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类

    支持从环境变量和.env文件加载配置。

    Attributes:
        app_name: 应用名称
        app_version: 应用版本
        debug: 调试模式
        api_host: API服务主机
        api_port: API服务端口
        log_level: 日志级别
        log_file: 日志文件路径
        nlp_model: PaddleNLP模型名称
        nlp_use_gpu: NLP是否使用GPU
        ocr_language: OCR语言设置
        ocr_use_gpu: OCR是否使用GPU
        ocr_use_angle_cls: OCR是否使用方向分类器
        ocr_det_thresh: OCR文本检测像素阈值
        ocr_det_box_thresh: OCR文本检测框阈值
        ocr_det_limit_side_len: OCR图像边长限制
        ocr_model_dir: OCR本地模型目录
        ocr_version: OCR版本
        max_image_size: 最大图像大小(字节)
        supported_image_formats: 支持的图像格式列表
        mosaic_block_size: 默认马赛克块大小
        mosaic_blur_radius: 默认模糊半径
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "CN PII Anonymization"
    app_version: str = "0.1.0"
    debug: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    nlp_model: str = "lac"
    nlp_use_gpu: bool = False

    ocr_language: str = "ch"
    ocr_use_gpu: bool = False
    ocr_use_angle_cls: bool = True
    ocr_det_thresh: float = 0.3
    ocr_det_box_thresh: float = 0.5
    ocr_det_limit_side_len: int = 960
    ocr_model_dir: str | None = None
    ocr_version: str = "PP-OCRv4"

    max_image_size: int = 10 * 1024 * 1024
    supported_image_formats: list[str] = Field(
        default_factory=lambda: ["png", "jpg", "jpeg", "bmp", "gif", "webp"]
    )

    mosaic_block_size: int = 10
    mosaic_blur_radius: int = 15

    @property
    def log_file_path(self) -> Path:
        """获取日志文件的完整路径"""
        return Path(self.log_file)


settings = Settings()
```

---

## 11. 错误处理设计

### 11.1 异常类定义

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

### 11.2 错误响应格式

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

## 12. 性能优化设计

### 12.1 性能指标

| 指标 | 目标值 | 优化策略 |
|------|--------|----------|
| 单张图片处理时间 | < 100s | OCR并行处理、图像压缩 |
| 文本处理时间 | < 5s| 正则预编译、识别器缓存 |
| PII识别准确率 | > 95% | 多重验证、上下文增强 |
| 内存占用 | < 500MB | 模型懒加载、图像流式处理 |

### 12.2 优化策略

1. **NLP模型优化**
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

## 13. 测试策略

### 13.1 单元测试

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
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install uv && uv sync

COPY . .

EXPOSE 8000

CMD ["uvicorn", "cn_pii_anonymization.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 14.2 Docker Compose

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


## 13. 附录

### 13.1 PII实体类型对照表

| 实体类型 | 描述 | 识别方式 | 优先级 |
|----------|------|----------|--------|
| CN_PHONE_NUMBER | 中国大陆手机号 | 正则表达式 | P0 |
| CN_ID_CARD | 中国大陆身份证号 | 正则表达式 | P0 |
| CN_BANK_CARD | 中国大陆银行卡号 | 正则表达式 | P0 |
| CN_PASSPORT | 中国护照号 | 正则表达式 | P0 |
| CN_EMAIL | 邮箱地址 | 正则表达式 | P1 |
| CN_ADDRESS | 中国地址 | 信息抽取(IE) | P2 |
| CN_NAME | 中文姓名 | 信息抽取(IE) | P2 |

**识别方式说明：**
- **正则表达式**：使用预定义的正则模式进行匹配，适用于格式固定的PII类型
- **信息抽取(IE)**：使用PaddleNLP Taskflow的information_extraction方法，适用于语义复杂的PII类型

### 15.2 参考资源

- [Microsoft Presidio GitHub](https://github.com/microsoft/presidio)
- [Presidio 官方文档](https://microsoft.github.io/presidio/)
- [中国行政区划代码](http://www.mca.gov.cn/article/sj/xzqh/)
