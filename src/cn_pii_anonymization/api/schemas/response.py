"""
API响应模型

定义所有API端点的响应数据模型。
"""

from typing import Any

from pydantic import BaseModel, Field


class PIIEntityResponse(BaseModel):
    """
    PII实体响应模型

    Attributes:
        entity_type: 实体类型
        start: 起始位置
        end: 结束位置
        score: 置信度分数
        original_text: 原始文本
        anonymized_text: 匿名化后的文本
    """

    entity_type: str = Field(..., description="实体类型")
    start: int = Field(..., ge=0, description="起始位置")
    end: int = Field(..., ge=0, description="结束位置")
    score: float = Field(..., ge=0.0, le=1.0, description="置信度分数")
    original_text: str = Field(..., description="原始文本")
    anonymized_text: str = Field(default="", description="匿名化后的文本")


class TextAnonymizeData(BaseModel):
    """
    文本匿名化响应数据模型

    Attributes:
        original_text: 原始文本
        anonymized_text: 匿名化后的文本
        pii_entities: 识别出的PII实体列表
    """

    original_text: str = Field(..., description="原始文本")
    anonymized_text: str = Field(..., description="匿名化后的文本")
    pii_entities: list[PIIEntityResponse] = Field(
        default_factory=list,
        description="识别出的PII实体列表",
    )


class TextAnalyzeData(BaseModel):
    """
    文本分析响应数据模型

    Attributes:
        pii_entities: 识别出的PII实体列表
        has_pii: 是否包含PII
    """

    pii_entities: list[PIIEntityResponse] = Field(
        default_factory=list,
        description="识别出的PII实体列表",
    )
    has_pii: bool = Field(..., description="是否包含PII")


class SupportedEntitiesData(BaseModel):
    """
    支持的实体类型响应数据模型

    Attributes:
        entities: 支持的PII实体类型列表
    """

    entities: list[str] = Field(..., description="支持的PII实体类型列表")


class APIResponse(BaseModel):
    """
    统一API响应模型

    Attributes:
        code: 响应状态码
        message: 响应消息
        data: 响应数据
    """

    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: Any = Field(default=None, description="响应数据")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": 200,
                    "message": "success",
                    "data": {
                        "original_text": "我的手机号是13812345678",
                        "anonymized_text": "我的手机号是138****5678",
                        "pii_entities": [
                            {
                                "entity_type": "CN_PHONE_NUMBER",
                                "start": 6,
                                "end": 17,
                                "score": 0.95,
                                "original_text": "13812345678",
                                "anonymized_text": "138****5678",
                            }
                        ],
                    },
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """
    错误响应模型

    Attributes:
        code: 错误状态码
        message: 错误消息
        error_type: 错误类型
        details: 错误详情
    """

    code: int = Field(default=400, description="错误状态码")
    message: str = Field(..., description="错误消息")
    error_type: str = Field(default="CNPIIError", description="错误类型")
    details: dict[str, Any] | None = Field(default=None, description="错误详情")


class HealthCheckData(BaseModel):
    """
    健康检查响应数据模型

    Attributes:
        status: 服务状态
        version: 应用版本
        nlp_engine: NLP引擎状态
    """

    status: str = Field(default="healthy", description="服务状态")
    version: str = Field(..., description="应用版本")
    nlp_engine: str = Field(default="loaded", description="NLP引擎状态")


class ImagePIIEntityResponse(BaseModel):
    """
    图像PII实体响应模型

    Attributes:
        entity_type: 实体类型
        text: 识别出的文本
        bbox: 边界框信息
        score: 置信度分数
    """

    entity_type: str = Field(..., description="实体类型")
    text: str = Field(..., description="识别出的文本")
    bbox: dict[str, int] = Field(..., description="边界框信息")
    score: float = Field(..., ge=0.0, le=1.0, description="置信度分数")


class ImageAnonymizeData(BaseModel):
    """
    图像匿名化响应数据模型

    Attributes:
        pii_entities: 识别出的PII实体列表
        ocr_text: OCR识别的完整文本
        ocr_confidence: OCR识别置信度
    """

    pii_entities: list[ImagePIIEntityResponse] = Field(
        default_factory=list,
        description="识别出的PII实体列表",
    )
    ocr_text: str = Field(default="", description="OCR识别的完整文本")
    ocr_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="OCR识别置信度",
    )


class ImageAnalyzeData(BaseModel):
    """
    图像分析响应数据模型

    Attributes:
        pii_entities: 识别出的PII实体列表
        ocr_text: OCR识别的完整文本
        has_pii: 是否包含PII
    """

    pii_entities: list[ImagePIIEntityResponse] = Field(
        default_factory=list,
        description="识别出的PII实体列表",
    )
    ocr_text: str = Field(default="", description="OCR识别的完整文本")
    has_pii: bool = Field(..., description="是否包含PII")
