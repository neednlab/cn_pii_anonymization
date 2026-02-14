"""
文本处理路由

提供文本PII识别和匿名化的API端点。
"""

from fastapi import APIRouter, HTTPException
from presidio_anonymizer.entities import OperatorConfig

from cn_pii_anonymization.api.schemas import (
    APIResponse,
    OperatorConfigRequest,
    PIIEntityResponse,
    SupportedEntitiesData,
    TextAnalyzeData,
    TextAnonymizeData,
    TextAnonymizeRequest,
)
from cn_pii_anonymization.operators import CNMaskOperator
from cn_pii_anonymization.processors.text_processor import TextProcessor
from cn_pii_anonymization.utils.exceptions import CNPIIError
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/text", tags=["文本处理"])

_text_processor: TextProcessor | None = None


def get_text_processor() -> TextProcessor:
    """获取文本处理器单例"""
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor


def build_operator_config(
    operators: dict[str, OperatorConfigRequest] | None,
) -> dict[str, OperatorConfig] | None:
    """
    构建操作符配置

    Args:
        operators: 请求中的操作符配置

    Returns:
        Presidio操作符配置字典
    """
    if not operators:
        return None

    config: dict[str, OperatorConfig] = {}
    for entity_type, op_config in operators.items():
        op_type = op_config.type
        params = {
            "masking_char": op_config.masking_char,
            "keep_prefix": op_config.keep_prefix,
            "keep_suffix": op_config.keep_suffix,
            "mask_email_domain": op_config.mask_email_domain,
        }

        if op_type == "mask":
            config[entity_type] = OperatorConfig(
                "custom",
                {"lambda": lambda x, p=params: CNMaskOperator().operate(x, p)},
            )
        elif op_type == "fake":
            from cn_pii_anonymization.operators import CNFakeOperator

            config[entity_type] = OperatorConfig(
                "custom",
                {"lambda": lambda x, et=entity_type: CNFakeOperator().operate(et, {})},
            )

    return config


@router.post(
    "/anonymize",
    response_model=APIResponse,
    summary="文本匿名化",
    description="识别文本中的PII并进行匿名化处理",
)
async def anonymize_text(request: TextAnonymizeRequest) -> APIResponse:
    """
    文本匿名化接口

    识别文本中的PII实体并进行匿名化处理。

    Args:
        request: 匿名化请求

    Returns:
        APIResponse: 包含匿名化结果的响应
    """
    try:
        logger.info(f"收到文本匿名化请求，文本长度: {len(request.text)}")

        processor = get_text_processor()
        operator_config = build_operator_config(request.operators)

        result = processor.process(
            text=request.text,
            entities=request.entities,
            operator_config=operator_config,
            language=request.language,
            score_threshold=request.score_threshold,
        )

        pii_entities = [
            PIIEntityResponse(
                entity_type=e.entity_type,
                start=e.start,
                end=e.end,
                score=e.score,
                original_text=e.original_text,
                anonymized_text=e.anonymized_text,
            )
            for e in result.pii_entities
        ]

        data = TextAnonymizeData(
            original_text=result.original_text,
            anonymized_text=result.anonymized_text,
            pii_entities=pii_entities,
        )

        logger.info(f"匿名化完成，发现 {len(pii_entities)} 个PII实体")

        return APIResponse(code=200, message="success", data=data)

    except CNPIIError as e:
        logger.error(f"PII处理错误: {e.message}")
        raise HTTPException(status_code=400, detail=e.message) from None
    except Exception as e:
        logger.exception(f"处理请求时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post(
    "/analyze",
    response_model=APIResponse,
    summary="文本分析",
    description="仅分析文本中的PII，不进行匿名化",
)
async def analyze_text(request: TextAnonymizeRequest) -> APIResponse:
    """
    文本分析接口

    仅分析文本中的PII实体，不进行匿名化处理。

    Args:
        request: 分析请求

    Returns:
        APIResponse: 包含分析结果的响应
    """
    try:
        logger.info(f"收到文本分析请求，文本长度: {len(request.text)}")

        processor = get_text_processor()
        entities = processor.analyze_only(
            text=request.text,
            entities=request.entities,
            language=request.language,
            score_threshold=request.score_threshold,
        )

        pii_entities = [
            PIIEntityResponse(
                entity_type=e.entity_type,
                start=e.start,
                end=e.end,
                score=e.score,
                original_text=e.original_text,
                anonymized_text="",
            )
            for e in entities
        ]

        data = TextAnalyzeData(
            pii_entities=pii_entities,
            has_pii=len(entities) > 0,
        )

        logger.info(f"分析完成，发现 {len(pii_entities)} 个PII实体")

        return APIResponse(code=200, message="success", data=data)

    except CNPIIError as e:
        logger.error(f"PII处理错误: {e.message}")
        raise HTTPException(status_code=400, detail=e.message) from None
    except Exception as e:
        logger.exception(f"处理请求时发生未知错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get(
    "/entities",
    response_model=APIResponse,
    summary="获取支持的实体类型",
    description="返回系统支持的所有PII实体类型",
)
async def get_supported_entities() -> APIResponse:
    """
    获取支持的PII实体类型

    Returns:
        APIResponse: 包含支持的实体类型列表
    """
    try:
        processor = get_text_processor()
        entities = processor.get_supported_entities()

        data = SupportedEntitiesData(entities=entities)

        return APIResponse(code=200, message="success", data=data)

    except Exception as e:
        logger.exception(f"获取实体类型时发生错误: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None
