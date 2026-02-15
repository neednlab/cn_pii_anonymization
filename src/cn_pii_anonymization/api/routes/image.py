"""
图像处理API路由

提供图像PII识别和脱敏的API端点。
"""

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image

from cn_pii_anonymization.api.schemas import (
    APIResponse,
    ImageAnalyzeData,
    ImageAnonymizeData,
    ImagePIIEntityResponse,
)
from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.operators.mosaic_operator import MosaicStyle
from cn_pii_anonymization.processors.image_processor import ImageProcessor
from cn_pii_anonymization.utils.exceptions import (
    OCRError,
    UnsupportedImageFormatError,
)
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/image", tags=["图像处理"])

_image_processor: ImageProcessor | None = None


def get_image_processor() -> ImageProcessor:
    """获取图像处理器单例"""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor


def validate_image_file(file: UploadFile) -> None:
    """验证上传的图像文件"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.supported_image_formats:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图像格式: {ext}。支持的格式: {', '.join(settings.supported_image_formats)}",
        )


@router.post(
    "/anonymize",
    summary="图像PII脱敏",
    description="识别图像中的PII信息并进行脱敏处理，返回处理后的图像。",
    response_description="处理后的图像文件",
    response_model=None,
)
async def anonymize_image(
    image: Annotated[UploadFile, File(..., description="要处理的图像文件")],
    mosaic_style: Annotated[
        str,
        Form(description="马赛克样式: pixel(像素块), blur(模糊), fill(纯色填充)"),
    ] = "pixel",
    fill_color: Annotated[
        str,
        Form(description="纯色填充颜色，格式: R,G,B，如: 0,0,0"),
    ] = "0,0,0",
    entities: Annotated[
        str | None,
        Form(description='要识别的PII类型，JSON数组格式，如: ["CN_PHONE_NUMBER"]'),
    ] = None,
    allow_list: Annotated[
        str | None,
        Form(description="白名单，JSON数组格式"),
    ] = None,
    score_threshold: Annotated[
        float | None,
        Form(description="置信度阈值，0-1之间，不指定时使用配置文件中的按类型阈值"),
    ] = None,
    return_metadata: Annotated[
        bool,
        Form(description="是否返回元数据（PII实体信息）"),
    ] = False,
) -> StreamingResponse | APIResponse:
    """
    图像PII脱敏

    Args:
        image: 上传的图像文件
        mosaic_style: 马赛克样式 (pixel/blur/fill)
        fill_color: 纯色填充颜色 (R,G,B)
        entities: 要识别的PII类型列表
        allow_list: 白名单列表
        score_threshold: 置信度阈值
        return_metadata: 是否返回元数据

    Returns:
        处理后的图像文件或包含元数据的响应
    """
    import json

    logger.info(f"收到图像脱敏请求: filename={image.filename}, mosaic_style={mosaic_style}")

    validate_image_file(image)

    try:
        image_bytes = await image.read()

        if len(image_bytes) > settings.max_image_size:
            raise HTTPException(
                status_code=400,
                detail=f"图像大小超出限制: {len(image_bytes) / (1024 * 1024):.2f}MB > {settings.max_image_size / (1024 * 1024):.2f}MB",
            )

        pil_image = Image.open(BytesIO(image_bytes))

        entities_list: list[str] | None = None
        if entities:
            try:
                entities_list = json.loads(entities)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="entities格式错误，应为JSON数组"
                ) from None

        allow_list_data: list[str] | None = None
        if allow_list:
            try:
                allow_list_data = json.loads(allow_list)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="allow_list格式错误，应为JSON数组"
                ) from None

        try:
            fill_color_tuple = tuple(int(c.strip()) for c in fill_color.split(","))
            if len(fill_color_tuple) != 3:
                raise ValueError("颜色格式错误")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="fill_color格式错误，应为: R,G,B，如: 0,0,0",
            ) from None

        processor = get_image_processor()
        result = processor.process(
            image=pil_image,
            mosaic_style=mosaic_style,
            fill_color=fill_color_tuple,
            entities=entities_list,
            allow_list=allow_list_data,
            score_threshold=score_threshold,
        )

        if return_metadata:
            pii_entities = [
                ImagePIIEntityResponse(
                    entity_type=entity.entity_type,
                    text=entity.text,
                    bbox={
                        "left": entity.bbox[0],
                        "top": entity.bbox[1],
                        "width": entity.bbox[2],
                        "height": entity.bbox[3],
                    },
                    score=entity.score,
                )
                for entity in result.pii_entities
            ]

            data = ImageAnonymizeData(
                pii_entities=pii_entities,
                ocr_text=result.ocr_result.text if result.ocr_result else "",
                ocr_confidence=result.ocr_result.confidence if result.ocr_result else 0.0,
            )

            return APIResponse(
                code=200,
                message="success",
                data=data.model_dump(),
            )

        output_buffer = BytesIO()
        result.processed_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        logger.info(f"图像脱敏完成: 发现 {len(result.pii_entities)} 个PII实体")

        return StreamingResponse(
            output_buffer,
            media_type="image/png",
            headers={
                "X-PII-Count": str(len(result.pii_entities)),
                "Content-Disposition": f"attachment; filename=redacted_{image.filename or 'image.png'}",
            },
        )

    except UnsupportedImageFormatError as e:
        logger.error(f"图像格式错误: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from None
    except OCRError as e:
        logger.error(f"OCR错误: {e}")
        raise HTTPException(status_code=500, detail=f"OCR识别失败: {e}") from None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图像处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"图像处理失败: {e}") from None


@router.post(
    "/analyze",
    summary="图像PII分析",
    description="识别图像中的PII信息，返回PII实体列表，不进行脱敏处理。",
)
async def analyze_image(
    image: Annotated[UploadFile, File(..., description="要分析的图像文件")],
    entities: Annotated[
        str | None,
        Form(description="要识别的PII类型，JSON数组格式"),
    ] = None,
    allow_list: Annotated[
        str | None,
        Form(description="白名单，JSON数组格式"),
    ] = None,
    score_threshold: Annotated[
        float | None,
        Form(description="置信度阈值，0-1之间，不指定时使用配置文件中的按类型阈值"),
    ] = None,
) -> APIResponse:
    """
    图像PII分析

    Args:
        image: 上传的图像文件
        entities: 要识别的PII类型列表
        allow_list: 白名单列表
        score_threshold: 置信度阈值，None时使用配置文件中的按类型阈值

    Returns:
        PII分析结果
    """
    import json

    logger.info(f"收到图像分析请求: filename={image.filename}")

    validate_image_file(image)

    try:
        image_bytes = await image.read()

        if len(image_bytes) > settings.max_image_size:
            raise HTTPException(
                status_code=400,
                detail="图像大小超出限制",
            )

        pil_image = Image.open(BytesIO(image_bytes))

        entities_list: list[str] | None = None
        if entities:
            try:
                entities_list = json.loads(entities)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="entities格式错误") from None

        allow_list_data: list[str] | None = None
        if allow_list:
            try:
                allow_list_data = json.loads(allow_list)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="allow_list格式错误") from None

        processor = get_image_processor()
        pii_entities = processor.analyze_only(
            image=pil_image,
            entities=entities_list,
            allow_list=allow_list_data,
            score_threshold=score_threshold,
        )

        entity_responses = [
            ImagePIIEntityResponse(
                entity_type=entity.entity_type,
                text=entity.text,
                bbox={
                    "left": entity.bbox[0],
                    "top": entity.bbox[1],
                    "width": entity.bbox[2],
                    "height": entity.bbox[3],
                },
                score=entity.score,
            )
            for entity in pii_entities
        ]

        ocr_result = processor._redactor.get_ocr_result()

        data = ImageAnalyzeData(
            pii_entities=entity_responses,
            ocr_text=ocr_result.text if ocr_result else "",
            has_pii=len(pii_entities) > 0,
        )

        logger.info(f"图像分析完成: 发现 {len(pii_entities)} 个PII实体")

        return APIResponse(
            code=200,
            message="success",
            data=data.model_dump(),
        )

    except UnsupportedImageFormatError as e:
        logger.error(f"图像格式错误: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from None
    except OCRError as e:
        logger.error(f"OCR错误: {e}")
        raise HTTPException(status_code=500, detail=f"OCR识别失败: {e}") from None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图像分析异常: {e}")
        raise HTTPException(status_code=500, detail=f"图像分析失败: {e}") from None


@router.get(
    "/mosaic-styles",
    summary="获取支持的马赛克样式",
    description="返回系统支持的所有马赛克样式。",
)
async def get_mosaic_styles() -> APIResponse:
    """
    获取支持的马赛克样式

    Returns:
        马赛克样式列表
    """
    styles = [
        {
            "name": style.value,
            "description": {
                "pixel": "像素块马赛克 - 将区域划分为像素块并取平均色",
                "blur": "高斯模糊 - 对区域应用高斯模糊效果",
                "fill": "纯色填充 - 用指定颜色覆盖区域",
            }.get(style.value, ""),
        }
        for style in MosaicStyle
    ]

    return APIResponse(
        code=200,
        message="success",
        data={"styles": styles},
    )
