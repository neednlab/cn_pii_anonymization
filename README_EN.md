# CN PII Anonymization

English | [简体中文](./README.md)

Chinese Personal Information Anonymization Library - Identify and process Personally Identifiable Information (PII) from Mainland China

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Introduction

CN PII Anonymization is a Python library focused on identifying and anonymizing Personally Identifiable Information (PII) from Mainland China. Built on the Microsoft Presidio framework, it provides both text and image processing modes, supporting the recognition and anonymization of various PII types.

## Demo

![Text Anonymization](./assets/demo_text.png)
![Image Anonymization](./assets/demo_image.png)

## Key Features

### Supported PII Types

| PII Type | Entity Identifier | Recognition Method | Priority | Description |
|----------|-------------------|-------------------|----------|-------------|
| Phone Number | `CN_PHONE_NUMBER` | Regular Expression | P0 | Supports 11-digit phone numbers, international format (+86/0086), and separator formats |
| ID Card Number | `CN_ID_CARD` | Regular Expression | P0 | Supports 18-digit ID card numbers, OCR error tolerance (19-digit fix) |
| Bank Card Number | `CN_BANK_CARD` | Regular Expression | P0 | Supports 16-19 digit bank card numbers, Luhn algorithm validation, BIN code recognition |
| Passport Number | `CN_PASSPORT` | Regular Expression | P0 | Supports Chinese passport format (E/G prefix + 8 digits) |
| Email Address | `CN_EMAIL` | Regular Expression | P1 | Standard email format recognition |
| Detailed Address | `CN_ADDRESS` | Information Extraction (IE) | P2 | Based on PaddleNLP information extraction model |
| Personal Name | `CN_NAME` | Information Extraction (IE) | P2 | Based on PaddleNLP information extraction model, supports allow_list/deny_list configuration |

### Text Anonymization Features

- **Mask Replacement**: Replace sensitive information with asterisks (*), supports keeping first N and last N characters
- **Pseudonym Replacement**: Use Faker to generate realistic fake data to replace sensitive information
- **Custom Configuration**: Configure different anonymization strategies for different PII types

### Image Anonymization Features

- **Pixel Mosaic**: Divide the recognized area into pixel blocks and apply average color
- **Gaussian Blur**: Apply Gaussian blur effect to the recognized area
- **Solid Color Fill**: Cover the recognized area with a specified color

### Technical Features

- Built on Microsoft Presidio framework, mature and stable
- Uses PaddleNLP for Chinese NLP processing
- Uses PaddleOCR for image text recognition
- Supports GPU acceleration (optional)
- Singleton pattern design for efficient resource utilization
- Complete API service support

## Installation

### Requirements

- Python >= 3.12
- Operating System: Windows / Linux / macOS

### Install with uv (Recommended)

This project uses uv for dependency management, recommended to install with uv:

```bash
# Clone the project
git clone https://github.com/neednlab/cn_pii_anonymization.git
cd cn_pii_anonymization

# Install dependencies
uv sync
```

### Verify Installation

```python
from cn_pii_anonymization import TextProcessor

processor = TextProcessor()
result = processor.process("我的手机号是13812345678")
print(result.anonymized_text)
# Output: 我的手机号是138****5678
```

## Python Library Usage Examples

### Text Processing

```python
from cn_pii_anonymization import TextProcessor

# Create processor
processor = TextProcessor()

# Process text containing PII
text = "张三的手机号是13812345678，身份证号是110101199001011234"
result = processor.process(text)

print(f"Original text: {result.original_text}")
print(f"Anonymized text: {result.anonymized_text}")
print(f"PII found: {len(result.pii_entities)}")

for entity in result.pii_entities:
    print(f"  - {entity.entity_type}: {entity.original_text} -> {entity.anonymized_text}")
```

### Image Processing

```python
from PIL import Image
from cn_pii_anonymization.processors.image_processor import ImageProcessor

# Create image processor
processor = ImageProcessor()

# Load image
image = Image.open("document.png")

# Process image
result = processor.process(
    image=image,
    mosaic_style="pixel",  # Options: pixel, blur, fill
    entities=["CN_PHONE_NUMBER", "CN_ID_CARD"]
)

# Save processed image
result.save_processed_image("redacted_document.png")

# View recognized PII
for entity in result.pii_entities:
    print(f"Type: {entity.entity_type}")
    print(f"Text: {entity.text}")
    print(f"Position: {entity.bbox}")
    print(f"Confidence: {entity.score}")
```

### Complete Examples

For more complete examples, please refer to the [examples](./examples) directory.

## API Service

### Start API Service

```bash
# Run with uv
uv run python main.py

# Or run directly
python main.py
```

After starting the service, access:
- API Service: http://localhost:8000
- API Documentation (Swagger UI): http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc
- OpenAPI Specification: http://localhost:8000/openapi.json

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API basic information |
| `/health` | GET | Health check |
| `/api/v1/text/anonymize` | POST | Text anonymization |
| `/api/v1/text/analyze` | POST | Text analysis (PII identification only) |
| `/api/v1/text/entities` | GET | Get supported entity types |
| `/api/v1/image/anonymize` | POST | Image anonymization |
| `/api/v1/image/analyze` | POST | Image analysis (PII identification only) |
| `/api/v1/image/mosaic-styles` | GET | Get supported mosaic styles |

### API Usage Examples

#### Text Anonymization

```bash
curl -X POST "http://localhost:8000/api/v1/text/anonymize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "张三的手机号是13812345678，身份证号是110101199001011234",
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
    }
  }'
```

Response Example:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "original_text": "张三的手机号是13812345678，身份证号是110101199001011234",
    "anonymized_text": "张三的手机号是138****5678，身份证号是110101********1234",
    "pii_entities": [
      {
        "entity_type": "CN_PHONE_NUMBER",
        "start": 7,
        "end": 18,
        "score": 1.0,
        "original_text": "13812345678",
        "anonymized_text": "138****5678"
      },
      {
        "entity_type": "CN_ID_CARD",
        "start": 24,
        "end": 42,
        "score": 1.0,
        "original_text": "110101199001011234",
        "anonymized_text": "110101********1234"
      }
    ]
  }
}
```

#### Text Analysis (Identification Only)

```bash
curl -X POST "http://localhost:8000/api/v1/text/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "联系方式：13812345678，邮箱：test@example.com"
  }'
```

Response Example:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "pii_entities": [
      {
        "entity_type": "CN_PHONE_NUMBER",
        "start": 5,
        "end": 16,
        "score": 1.0,
        "original_text": "13812345678",
        "anonymized_text": ""
      },
      {
        "entity_type": "CN_EMAIL",
        "start": 21,
        "end": 37,
        "score": 1.0,
        "original_text": "test@example.com",
        "anonymized_text": ""
      }
    ],
    "has_pii": true
  }
}
```

#### Image Anonymization

```bash
curl -X POST "http://localhost:8000/api/v1/image/anonymize" \
  -F "image=@document.png" \
  -F "mosaic_style=pixel" \
  -F 'entities=["CN_PHONE_NUMBER", "CN_ID_CARD"]' \
  --output redacted_document.png
```

#### Image Analysis (Return Metadata)

```bash
curl -X POST "http://localhost:8000/api/v1/image/anonymize" \
  -F "image=@document.png" \
  -F "mosaic_style=pixel" \
  -F "return_metadata=true"
```

Response Example:

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
        "score": 1.0
      }
    ],
    "ocr_text": "联系方式：13812345678",
    "ocr_confidence": 0.95
  }
}
```

#### Get Supported Entity Types

```bash
curl -X GET "http://localhost:8000/api/v1/text/entities"
```

Response Example:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "entities": [
      "CN_PHONE_NUMBER",
      "CN_ID_CARD",
      "CN_BANK_CARD",
      "CN_PASSPORT",
      "CN_EMAIL",
      "CN_ADDRESS",
      "CN_NAME"
    ]
  }
}
```

#### Get Supported Mosaic Styles

```bash
curl -X GET "http://localhost:8000/api/v1/image/mosaic-styles"
```

Response Example:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "styles": [
      {
        "name": "pixel",
        "description": "Pixel Mosaic - Divide area into pixel blocks and apply average color"
      },
      {
        "name": "blur",
        "description": "Gaussian Blur - Apply Gaussian blur effect to the area"
      },
      {
        "name": "fill",
        "description": "Solid Color Fill - Cover area with specified color"
      }
    ]
  }
}
```

### OpenAPI Documentation

Complete OpenAPI specification documentation can be accessed via:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Application Configuration
APP_NAME=CN PII Anonymization
APP_VERSION=0.1.0
DEBUG=false

# API Service Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# NLP Configuration
NLP_MODEL=lac
NLP_USE_GPU=false

# OCR Configuration
OCR_LANGUAGE=ch
OCR_USE_GPU=false
OCR_USE_ANGLE_CLS=true
OCR_DET_THRESH=0.3
OCR_DET_BOX_THRESH=0.5
OCR_DET_LIMIT_SIDE_LEN=960

# Image Processing Configuration
MAX_IMAGE_SIZE=10485760
MOSAIC_BLOCK_SIZE=10
MOSAIC_BLUR_RADIUS=15

# Recognizer Confidence Threshold Configuration
SCORE_THRESHOLD_DEFAULT=0.35
SCORE_THRESHOLD_NAME=0.3
SCORE_THRESHOLD_ADDRESS=0.3
SCORE_THRESHOLD_PHONE=0.5
SCORE_THRESHOLD_ID_CARD=0.5
SCORE_THRESHOLD_BANK_CARD=0.5
SCORE_THRESHOLD_PASSPORT=0.5
SCORE_THRESHOLD_EMAIL=0.5

# Name Recognizer Custom Lists
NAME_ALLOW_LIST=张三,李四
NAME_DENY_LIST=王五
```

### Confidence Threshold Description

Different types of recognizers have different confidence characteristics:

| Recognizer Type | Recommended Threshold | Description |
|-----------------|----------------------|-------------|
| Regex-based (Phone, ID Card, etc.) | 0.5 | Confidence fixed at 1.0, threshold has minimal impact |
| IE-based (Name, Address) | 0.3 | Information extraction model confidence typically lower (0.3-0.6) |

## Development Guide

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific tests
uv run pytest tests/unit/test_recognizers.py

# Run tests with coverage report
uv run pytest --cov=src/cn_pii_anonymization
```

### Code Quality

```bash
# Run ruff check
uv run ruff check .

# Run ruff format
uv run ruff format .

# Run mypy type check
uv run mypy src/
```

## Performance Metrics

Current NLP model recognition performance is still being optimized

| Metric | Target |
|--------|--------|
| Single image processing time | < 100 seconds (1080p image) |
| Text processing time | < 5 seconds |
| PII recognition accuracy | > 95% |

## Dependencies

### Core Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| presidio-analyzer | >=2.2 | PII recognition engine |
| presidio-anonymizer | >=2.2 | PII anonymization engine |
| presidio-image-redactor | >=0.0.50 | Image PII processing |
| PaddleNLP | >=2.8.1 | Chinese NLP processing |
| PaddleOCR | >=3.1.1 | OCR engine |
| PaddlePaddle | >=3.3.0 | Underlying framework |
| FastAPI | >=0.109 | API service framework |
| uvicorn | >=0.27 | ASGI server |

## License

This project is licensed under the MIT License. See [LICENSE](license) file for details.

## Limitations

- No API authentication implemented
- No API concurrent processing and rate limiting implemented
- The above can be considered for FaaS cloud function deployment, no need to implement in the project

## Acknowledgments

This project is built on the following excellent open source projects:

* **[Microsoft Presidio](https://github.com/microsoft/presidio)**: Overall PII recognition framework
* **[PaddleNLP](https://github.com/PaddlePaddle/PaddleNLP)**: Chinese NLP processing library
* **[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)**: Chinese OCR engine
