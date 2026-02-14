# CN PII Anonymization

中国个人信息脱敏库 - 识别和处理中国大陆个人身份信息（PII）

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## 项目简介

CN PII Anonymization 是一个专注于中国大陆个人身份信息（PII）识别与脱敏处理的 Python 库。基于 Microsoft Presidio 框架构建，提供文本和图像两种处理模式，支持多种 PII 类型的识别与匿名化处理。

### 核心功能

- **文本 PII 识别与脱敏**：自动识别文本中的敏感信息并进行掩码或假名替换
- **图像 PII 识别与马赛克**：通过 OCR 识别图像中的文字，对 PII 区域进行马赛克处理
- **RESTful API 服务**：提供标准化的 HTTP 接口，方便集成到现有系统
- **可扩展架构**：支持自定义识别器和匿名化操作

### 支持的 PII 类型

| PII 类型 | 实体名称 | 优先级 | 说明 |
|----------|----------|--------|------|
| 手机号 | `CN_PHONE_NUMBER` | P0 | 中国大陆 11 位手机号，支持国际区号格式 |
| 身份证号 | `CN_ID_CARD` | P0 | 18 位身份证号，支持校验码验证 |
| 银行卡号 | `CN_BANK_CARD` | P0 | 16-19 位银行卡号，支持 Luhn 算法校验 |
| 护照号 | `CN_PASSPORT` | P0 | 中国护照号，支持新版/旧版/港澳台格式 |
| 邮箱地址 | `CN_EMAIL` | P1 | 标准邮箱格式 |
| 详细地址 | `CN_ADDRESS` | P2 | 中国大陆地址，支持省市区县多级识别 |
| 个人姓名 | `CN_NAME` | P2 | 中文姓名，支持常见姓氏和复姓 |

## 安装指南

### 环境要求

- Python 3.12+
- Tesseract OCR 5.3+（图像处理需要）

### 使用 uv 安装（推荐）

```bash
# 克隆项目
git clone https://github.com/your-repo/cn-pii-anonymization.git
cd cn-pii-anonymization

# 安装依赖
uv sync

# 下载 spaCy 中文模型
uv run python -m spacy download zh_core_web_lg
```

### 安装 Tesseract OCR

**Windows:**

```powershell
# 使用 Chocolatey 安装
choco install tesseract

# 或下载安装包
# https://github.com/UB-Mannheim/tesseract/wiki
```

**macOS:**

```bash
brew install tesseract
brew install tesseract-lang
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim
```

## 快速开始

### 文本处理

```python
from cn_pii_anonymization import TextProcessor

# 创建处理器
processor = TextProcessor()

# 处理文本
text = "我的手机号是13812345678，身份证号是110101199001011234"
result = processor.process(text)

print(result.anonymized_text)
# 输出: 我的手机号是138****5678，身份证号是110101********1234

# 查看识别到的 PII 实体
for entity in result.pii_entities:
    print(f"类型: {entity.entity_type}, 原文: {entity.original_text}, 置信度: {entity.score}")
```

### 图像处理

```python
from PIL import Image
from cn_pii_anonymization import ImageProcessor

# 创建处理器
processor = ImageProcessor()

# 加载图像
image = Image.open("document.png")

# 处理图像
result = processor.process(image, mosaic_style="pixel")

# 保存处理后的图像
result.processed_image.save("document_anonymized.png")

# 查看识别到的 PII 实体
for entity in result.pii_entities:
    print(f"类型: {entity.entity_type}, 位置: {entity.bbox}, 原文: {entity.original_text}")
```

### 启动 API 服务

```bash
# 使用 uvicorn 启动
uv run uvicorn main:app --host 0.0.0.0 --port 8000

# 或直接运行
uv run python main.py
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 文档

### 文本匿名化接口

**POST** `/api/v1/text/anonymize`

请求体：

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

响应体：

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
                "original_text": "13812345678"
            },
            {
                "entity_type": "CN_ID_CARD",
                "start": 22,
                "end": 40,
                "score": 0.95,
                "original_text": "110101199001011234"
            }
        ]
    }
}
```

### 文本分析接口

**POST** `/api/v1/text/analyze`

仅分析文本中的 PII，不进行脱敏处理。

请求体：

```json
{
    "text": "我的手机号是13812345678",
    "entities": ["CN_PHONE_NUMBER"],
    "language": "zh"
}
```

### 图像匿名化接口

**POST** `/api/v1/image/anonymize`

请求格式：`multipart/form-data`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image | file | 是 | - | 图像文件（PNG/JPG/JPEG/BMP） |
| mosaic_style | string | 否 | `pixel` | 马赛克样式：`pixel`（像素块）、`blur`（高斯模糊）、`fill`（纯色填充） |
| fill_color | string | 否 | `0,0,0` | 填充颜色（R,G,B 格式，如 `255,0,0` 表示红色） |
| entities | string | 否 | 全部 | 要识别的 PII 类型（JSON 数组） |
| allow_list | string | 否 | - | 白名单列表（JSON 数组） |
| score_threshold | float | 否 | `0.5` | 置信度阈值（0-1 之间） |
| return_metadata | bool | 否 | `false` | 是否返回元数据（PII 实体信息） |

**请求示例（使用 curl）：**

```bash
# 基本用法：返回处理后的图像
curl -X POST "http://localhost:8000/api/v1/image/anonymize" \
  -F "image=@document.png" \
  -F "mosaic_style=pixel" \
  --output redacted_document.png

# 高级用法：指定 PII 类型和马赛克样式
curl -X POST "http://localhost:8000/api/v1/image/anonymize" \
  -F "image=@document.png" \
  -F "mosaic_style=blur" \
  -F 'entities=["CN_PHONE_NUMBER", "CN_ID_CARD"]' \
  -F "score_threshold=0.7" \
  --output redacted_document.png

# 返回元数据模式：获取 PII 实体信息
curl -X POST "http://localhost:8000/api/v1/image/anonymize" \
  -F "image=@document.png" \
  -F "mosaic_style=pixel" \
  -F "return_metadata=true"
```

**响应示例（默认模式 - 返回图像）：**

成功时返回处理后的图像文件（PNG 格式），响应头包含：

```
Content-Type: image/png
X-PII-Count: 2
Content-Disposition: attachment; filename=redacted_document.png
```

**响应示例（元数据模式 - return_metadata=true）：**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "pii_entities": [
            {
                "entity_type": "CN_PHONE_NUMBER",
                "text": "13812345678",
                "bbox": {
                    "left": 100,
                    "top": 200,
                    "width": 150,
                    "height": 30
                },
                "score": 0.95
            },
            {
                "entity_type": "CN_ID_CARD",
                "text": "110101199001011234",
                "bbox": {
                    "left": 100,
                    "top": 250,
                    "width": 200,
                    "height": 30
                },
                "score": 0.92
            }
        ],
        "ocr_text": "姓名: 张三\n手机号: 13812345678\n身份证号: 110101199001011234",
        "ocr_confidence": 0.88
    }
}
```

### 图像分析接口

**POST** `/api/v1/image/analyze`

仅分析图像中的 PII，返回识别结果，不进行脱敏处理。

请求格式：`multipart/form-data`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| image | file | 是 | - | 图像文件（PNG/JPG/JPEG/BMP） |
| entities | string | 否 | 全部 | 要识别的 PII 类型（JSON 数组） |
| allow_list | string | 否 | - | 白名单列表（JSON 数组） |
| score_threshold | float | 否 | `0.5` | 置信度阈值（0-1 之间） |

**请求示例（使用 curl）：**

```bash
curl -X POST "http://localhost:8000/api/v1/image/analyze" \
  -F "image=@document.png" \
  -F 'entities=["CN_PHONE_NUMBER", "CN_ID_CARD"]'
```

**响应示例：**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "pii_entities": [
            {
                "entity_type": "CN_PHONE_NUMBER",
                "text": "13812345678",
                "bbox": {
                    "left": 100,
                    "top": 200,
                    "width": 150,
                    "height": 30
                },
                "score": 0.95
            }
        ],
        "ocr_text": "姓名: 张三\n手机号: 13812345678",
        "has_pii": true
    }
}
```

### 其他接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/text/entities` | GET | 获取支持的文本 PII 实体类型 |
| `/api/v1/image/mosaic-styles` | GET | 获取支持的马赛克样式 |
| `/health` | GET | 健康检查 |

## 匿名化操作

### 掩码操作（Mask）

将指定位置的字符替换为掩码字符。

```python
from cn_pii_anonymization.operators import CNMaskOperator

operator = CNMaskOperator()

# 掩码手机号：保留前3位和后4位
result = operator.operate("13812345678", {
    "masking_char": "*",
    "keep_prefix": 3,
    "keep_suffix": 4
})
# 结果: 138****5678

# 掩码身份证：保留前6位和后4位
result = operator.operate("110101199001011234", {
    "masking_char": "*",
    "keep_prefix": 6,
    "keep_suffix": 4
})
# 结果: 110101********1234
```

### 假名替换操作（Fake）

使用 Faker 生成假数据替换原始 PII。

```python
from cn_pii_anonymization.operators import CNFakeOperator

operator = CNFakeOperator()

# 生成假手机号
result = operator.operate("13812345678", {"entity_type": "CN_PHONE_NUMBER"})
# 结果: 13987654321（随机生成的有效手机号）

# 生成假姓名
result = operator.operate("张三", {"entity_type": "CN_NAME"})
# 结果: 李明（随机生成的中文姓名）
```

## 马赛克样式

### 像素块马赛克（Pixel）

将识别区域划分为像素块并取平均色。

```python
from cn_pii_anonymization.operators import PixelMosaicOperator

operator = PixelMosaicOperator(block_size=10)
processed_image = operator.apply(image, bbox=(100, 200, 300, 250))
```

### 高斯模糊（Blur）

对识别区域应用高斯模糊。

```python
from cn_pii_anonymization.operators import GaussianBlurOperator

operator = GaussianBlurOperator(radius=10)
processed_image = operator.apply(image, bbox=(100, 200, 300, 250))
```

### 纯色填充（Fill）

用指定颜色覆盖识别区域。

```python
from cn_pii_anonymization.operators import SolidFillOperator

operator = SolidFillOperator(fill_color=(0, 0, 0))  # 黑色
processed_image = operator.apply(image, bbox=(100, 200, 300, 250))
```

## 配置说明

### 环境变量配置

创建 `.env` 文件：

```env
# 应用配置
APP_NAME=CN PII Anonymization
APP_VERSION=1.0.0
DEBUG=false

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# NLP 配置
SPACY_MODEL=zh_core_web_lg

# OCR 配置
TESSERACT_PATH=/usr/bin/tesseract
OCR_LANGUAGE=chi_sim+eng
OCR_CONFIG=--psm 6

# 图像处理配置
MAX_IMAGE_SIZE=10485760
MOSAIC_BLOCK_SIZE=10
MOSAIC_BLUR_RADIUS=10
```

### 识别器配置

编辑 `config/recognizer_config.yaml`：

```yaml
recognizers:
  cn_phone:
    enabled: true
    entity_type: CN_PHONE_NUMBER
    score_threshold: 0.85

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
    enabled: true
    entity_type: CN_ADDRESS
    score_threshold: 0.7

  cn_name:
    enabled: true
    entity_type: CN_NAME
    score_threshold: 0.7
```

## 开发指南

### 项目结构

```
cn_pii_anonymization/
├── src/cn_pii_anonymization/
│   ├── api/                    # API 模块
│   │   ├── routes/             # 路由定义
│   │   ├── schemas/            # 数据模型
│   │   └── middleware/         # 中间件
│   ├── config/                 # 配置模块
│   ├── core/                   # 核心引擎
│   │   ├── analyzer.py         # 分析器引擎
│   │   ├── anonymizer.py       # 匿名化引擎
│   │   └── image_redactor.py   # 图像脱敏引擎
│   ├── ocr/                    # OCR 模块
│   ├── operators/              # 匿名化操作符
│   ├── processors/             # 处理器
│   ├── recognizers/            # PII 识别器
│   └── utils/                  # 工具函数
├── tests/                      # 测试目录
├── SPEC/                       # 规格文档
├── pyproject.toml              # 项目配置
├── Dockerfile                  # Docker 镜像
└── docker-compose.yml          # Docker 编排
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行带覆盖率的测试
uv run pytest --cov=src/cn_pii_anonymization --cov-report=html

# 运行特定测试
uv run pytest tests/unit/test_recognizers.py -v

# 运行性能测试
uv run pytest tests/performance/ -v
```

### 代码规范

```bash
# 代码检查
uv run ruff check src/

# 代码格式化
uv run ruff format src/

# 类型检查
uv run mypy src/
```

## 部署指南

### Docker 部署

```bash
# 构建镜像
docker build -t cn-pii-anonymization:latest .

# 运行容器
docker run -d -p 8000:8000 --name pii-api cn-pii-anonymization:latest
```

### Docker Compose 部署

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 生产环境建议

1. **资源限制**：配置合理的 CPU 和内存限制
2. **日志管理**：配置日志轮转和持久化存储
3. **健康检查**：配置健康检查端点监控
4. **负载均衡**：使用 Nginx 或云负载均衡器
5. **HTTPS**：配置 SSL 证书启用 HTTPS

## 性能指标

| 指标 | 目标值 | 实测值 |
|------|--------|--------|
| 短文本分析时间 | < 100ms | ~3ms |
| 短文本匿名化时间 | < 100ms | ~65μs |
| 单张图片处理时间 | < 10s | 取决于 OCR |
| PII 识别准确率 | > 99% | 99.2% |
| 测试覆盖率 | > 80% | 85% |

## 常见问题

### Q: 图像处理时 OCR 识别不准确？

A: 确保 Tesseract OCR 已正确安装中文语言包。可以通过以下命令检查：

```bash
tesseract --list-langs
```

如果缺少 `chi_sim`，请安装中文语言包。

### Q: 如何添加自定义识别器？

A: 继承 `CNPIIRecognizer` 基类并实现 `analyze` 方法：

```python
from cn_pii_anonymization.recognizers import CNPIIRecognizer

class MyCustomRecognizer(CNPIIRecognizer):
    def __init__(self):
        super().__init__(supported_entities=["MY_CUSTOM_TYPE"])

    def analyze(self, text, entities, nlp_artifacts):
        # 实现识别逻辑
        pass
```

### Q: 如何禁用特定识别器？

A: 在 `recognizer_config.yaml` 中将对应识别器的 `enabled` 设置为 `false`。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [Microsoft Presidio](https://github.com/microsoft/presidio) - 核心 PII 处理框架
- [spaCy](https://spacy.io/) - NLP 处理
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR 引擎
- [Faker](https://faker.readthedocs.io/) - 假数据生成

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request
