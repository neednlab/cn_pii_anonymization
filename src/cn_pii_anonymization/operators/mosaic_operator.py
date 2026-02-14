"""
马赛克操作符模块

提供图像PII区域的马赛克处理操作。
"""

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


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


class PixelMosaicOperator(MosaicOperator):
    """
    像素块马赛克操作符

    将指定区域划分为像素块并取平均色，实现马赛克效果。

    Attributes:
        block_size: 像素块大小

    Example:
        >>> operator = PixelMosaicOperator(block_size=10)
        >>> result = operator.apply(image, (100, 100, 200, 150))
    """

    def __init__(self, block_size: int = 10) -> None:
        """
        初始化像素块马赛克操作符

        Args:
            block_size: 像素块大小，默认为10像素
        """
        self._block_size = max(1, block_size)
        logger.debug(f"像素块马赛克操作符初始化: block_size={self._block_size}")

    def apply(
        self,
        image: Image.Image,
        bbox: tuple[int, int, int, int],
    ) -> Image.Image:
        """
        应用像素块马赛克效果

        Args:
            image: PIL图像对象
            bbox: 边界框 (left, top, right, bottom)

        Returns:
            处理后的图像
        """
        result = image.copy()
        x1, y1, x2, y2 = bbox

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            logger.warning(f"无效的边界框: {bbox}")
            return result

        region = result.crop((x1, y1, x2, y2))

        small_width = max(1, width // self._block_size)
        small_height = max(1, height // self._block_size)

        small = region.resize(
            (small_width, small_height),
            resample=Image.Resampling.NEAREST,
        )

        mosaic = small.resize(
            (width, height),
            resample=Image.Resampling.NEAREST,
        )

        result.paste(mosaic, (x1, y1))

        logger.debug(f"已应用像素块马赛克: bbox={bbox}")
        return result


class GaussianBlurOperator(MosaicOperator):
    """
    高斯模糊操作符

    对指定区域应用高斯模糊效果。

    Attributes:
        radius: 模糊半径

    Example:
        >>> operator = GaussianBlurOperator(radius=15)
        >>> result = operator.apply(image, (100, 100, 200, 150))
    """

    def __init__(self, radius: int = 15) -> None:
        """
        初始化高斯模糊操作符

        Args:
            radius: 模糊半径，默认为15
        """
        self._radius = max(1, radius)
        logger.debug(f"高斯模糊操作符初始化: radius={self._radius}")

    def apply(
        self,
        image: Image.Image,
        bbox: tuple[int, int, int, int],
    ) -> Image.Image:
        """
        应用高斯模糊效果

        Args:
            image: PIL图像对象
            bbox: 边界框 (left, top, right, bottom)

        Returns:
            处理后的图像
        """
        result = image.copy()
        x1, y1, x2, y2 = bbox

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            logger.warning(f"无效的边界框: {bbox}")
            return result

        region = result.crop((x1, y1, x2, y2))

        blurred = region.filter(ImageFilter.GaussianBlur(self._radius))

        result.paste(blurred, (x1, y1))

        logger.debug(f"已应用高斯模糊: bbox={bbox}")
        return result


class SolidFillOperator(MosaicOperator):
    """
    纯色填充操作符

    用指定颜色填充指定区域。

    Attributes:
        fill_color: 填充颜色 (R, G, B)

    Example:
        >>> operator = SolidFillOperator(fill_color=(0, 0, 0))
        >>> result = operator.apply(image, (100, 100, 200, 150))
    """

    def __init__(self, fill_color: tuple[int, int, int] = (0, 0, 0)) -> None:
        """
        初始化纯色填充操作符

        Args:
            fill_color: 填充颜色 (R, G, B)，默认为黑色
        """
        self._fill_color = fill_color
        logger.debug(f"纯色填充操作符初始化: fill_color={fill_color}")

    def apply(
        self,
        image: Image.Image,
        bbox: tuple[int, int, int, int],
    ) -> Image.Image:
        """
        应用纯色填充

        Args:
            image: PIL图像对象
            bbox: 边界框 (left, top, right, bottom)

        Returns:
            处理后的图像
        """
        result = image.copy()
        x1, y1, x2, y2 = bbox

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            logger.warning(f"无效的边界框: {bbox}")
            return result

        draw = ImageDraw.Draw(result)
        draw.rectangle((x1, y1, x2, y2), fill=self._fill_color)

        logger.debug(f"已应用纯色填充: bbox={bbox}, color={self._fill_color}")
        return result


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
