"""
图像处理单元测试

测试马赛克操作符和图像处理相关组件。
"""

import pytest
from PIL import Image

from cn_pii_anonymization.operators.mosaic_operator import (
    GaussianBlurOperator,
    MosaicStyle,
    PixelMosaicOperator,
    SolidFillOperator,
    create_mosaic_operator,
)


class TestPixelMosaicOperator:
    """像素块马赛克操作符测试"""

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """创建测试图像"""
        return Image.new("RGB", (100, 100), color=(255, 255, 255))

    @pytest.fixture
    def operator(self) -> PixelMosaicOperator:
        """创建马赛克操作符"""
        return PixelMosaicOperator(block_size=10)

    def test_init(self, operator: PixelMosaicOperator) -> None:
        """测试初始化"""
        assert operator._block_size == 10

    def test_init_with_invalid_block_size(self) -> None:
        """测试无效块大小初始化"""
        operator = PixelMosaicOperator(block_size=0)
        assert operator._block_size == 1

        operator = PixelMosaicOperator(block_size=-5)
        assert operator._block_size == 1

    def test_apply(self, operator: PixelMosaicOperator, sample_image: Image.Image) -> None:
        """测试应用马赛克"""
        bbox = (10, 10, 50, 50)
        result = operator.apply(sample_image, bbox)

        assert result.size == sample_image.size
        assert result.mode == sample_image.mode

    def test_apply_with_invalid_bbox(
        self,
        operator: PixelMosaicOperator,
        sample_image: Image.Image,
    ) -> None:
        """测试无效边界框"""
        bbox = (50, 50, 10, 10)
        result = operator.apply(sample_image, bbox)

        assert result.size == sample_image.size


class TestGaussianBlurOperator:
    """高斯模糊操作符测试"""

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """创建测试图像"""
        return Image.new("RGB", (100, 100), color=(255, 255, 255))

    @pytest.fixture
    def operator(self) -> GaussianBlurOperator:
        """创建模糊操作符"""
        return GaussianBlurOperator(radius=15)

    def test_init(self, operator: GaussianBlurOperator) -> None:
        """测试初始化"""
        assert operator._radius == 15

    def test_init_with_invalid_radius(self) -> None:
        """测试无效半径初始化"""
        operator = GaussianBlurOperator(radius=0)
        assert operator._radius == 1

    def test_apply(self, operator: GaussianBlurOperator, sample_image: Image.Image) -> None:
        """测试应用模糊"""
        bbox = (10, 10, 50, 50)
        result = operator.apply(sample_image, bbox)

        assert result.size == sample_image.size


class TestSolidFillOperator:
    """纯色填充操作符测试"""

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """创建测试图像"""
        return Image.new("RGB", (100, 100), color=(255, 255, 255))

    @pytest.fixture
    def operator(self) -> SolidFillOperator:
        """创建填充操作符"""
        return SolidFillOperator(fill_color=(0, 0, 0))

    def test_init(self, operator: SolidFillOperator) -> None:
        """测试初始化"""
        assert operator._fill_color == (0, 0, 0)

    def test_apply(self, operator: SolidFillOperator, sample_image: Image.Image) -> None:
        """测试应用填充"""
        bbox = (10, 10, 50, 50)
        result = operator.apply(sample_image, bbox)

        assert result.size == sample_image.size

        pixel = result.getpixel((30, 30))
        assert pixel == (0, 0, 0)


class TestCreateMosaicOperator:
    """马赛克操作符工厂函数测试"""

    def test_create_pixel_operator(self) -> None:
        """测试创建像素块马赛克操作符"""
        operator = create_mosaic_operator("pixel", block_size=10)
        assert isinstance(operator, PixelMosaicOperator)

    def test_create_blur_operator(self) -> None:
        """测试创建模糊操作符"""
        operator = create_mosaic_operator("blur", radius=15)
        assert isinstance(operator, GaussianBlurOperator)

    def test_create_fill_operator(self) -> None:
        """测试创建填充操作符"""
        operator = create_mosaic_operator("fill", fill_color=(128, 128, 128))
        assert isinstance(operator, SolidFillOperator)

    def test_create_with_enum(self) -> None:
        """测试使用枚举创建操作符"""
        operator = create_mosaic_operator(MosaicStyle.PIXEL)
        assert isinstance(operator, PixelMosaicOperator)

    def test_create_with_invalid_style(self) -> None:
        """测试无效样式"""
        with pytest.raises(ValueError):
            create_mosaic_operator("invalid")


class TestMosaicStyle:
    """马赛克样式枚举测试"""

    def test_values(self) -> None:
        """测试枚举值"""
        assert MosaicStyle.PIXEL.value == "pixel"
        assert MosaicStyle.BLUR.value == "blur"
        assert MosaicStyle.FILL.value == "fill"

    def test_from_string(self) -> None:
        """测试从字符串创建枚举"""
        assert MosaicStyle("pixel") == MosaicStyle.PIXEL
        assert MosaicStyle("blur") == MosaicStyle.BLUR
        assert MosaicStyle("fill") == MosaicStyle.FILL
