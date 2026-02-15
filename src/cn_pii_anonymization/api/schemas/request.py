"""
API请求模型

定义所有API端点的请求数据模型。
"""

from pydantic import BaseModel, Field


class OperatorConfigRequest(BaseModel):
    """
    匿名化操作配置请求模型

    Attributes:
        type: 操作类型 (mask, fake)
        masking_char: 掩码字符，默认为*
        keep_prefix: 保留前N位
        keep_suffix: 保留后N位
        mask_email_domain: 是否掩码邮箱域名
    """

    type: str = Field(default="mask", description="操作类型: mask 或 fake")
    masking_char: str = Field(default="*", description="掩码字符")
    keep_prefix: int = Field(default=0, ge=0, description="保留前N位")
    keep_suffix: int = Field(default=0, ge=0, description="保留后N位")
    mask_email_domain: bool = Field(default=False, description="是否掩码邮箱域名")


class TextAnonymizeRequest(BaseModel):
    """
    文本匿名化请求模型

    Attributes:
        text: 待处理的文本
        entities: 要识别的PII类型列表，None表示识别所有类型
        operators: 各PII类型的匿名化操作配置
        language: 语言类型，默认为zh
        score_threshold: 全局置信度阈值，None时使用配置文件中的按类型阈值
    """

    text: str = Field(..., min_length=1, max_length=100000, description="待处理的文本")
    entities: list[str] | None = Field(
        default=None,
        description="要识别的PII类型列表，None表示识别所有类型",
    )
    operators: dict[str, OperatorConfigRequest] | None = Field(
        default=None,
        description="各PII类型的匿名化操作配置",
    )
    language: str = Field(default="zh", description="语言类型")
    score_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="全局置信度阈值，None时使用配置文件中的按类型阈值",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "我的手机号是13812345678，身份证号是110101199001011234",
                    "entities": ["CN_PHONE_NUMBER", "CN_ID_CARD"],
                    "operators": {
                        "CN_PHONE_NUMBER": {
                            "type": "mask",
                            "masking_char": "*",
                            "keep_prefix": 3,
                            "keep_suffix": 4,
                        },
                        "CN_ID_CARD": {
                            "type": "mask",
                            "masking_char": "*",
                            "keep_prefix": 6,
                            "keep_suffix": 4,
                        },
                    },
                    "language": "zh",
                    "score_threshold": None,
                }
            ]
        }
    }


class TextAnalyzeRequest(BaseModel):
    """
    文本分析请求模型（仅分析不匿名化）

    Attributes:
        text: 待分析的文本
        entities: 要识别的PII类型列表
        language: 语言类型
        score_threshold: 全局置信度阈值，None时使用配置文件中的按类型阈值
    """

    text: str = Field(..., min_length=1, max_length=100000, description="待分析的文本")
    entities: list[str] | None = Field(
        default=None,
        description="要识别的PII类型列表",
    )
    language: str = Field(default="zh", description="语言类型")
    score_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="全局置信度阈值，None时使用配置文件中的按类型阈值",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "我的手机号是13812345678",
                    "entities": ["CN_PHONE_NUMBER"],
                    "language": "zh",
                    "score_threshold": None,
                }
            ]
        }
    }


class HealthCheckRequest(BaseModel):
    """健康检查请求模型"""

    pass
