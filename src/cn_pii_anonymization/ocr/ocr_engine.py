"""
OCR引擎模块

封装PaddleOCR引擎，提供中文OCR识别能力。
"""

import os

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_onednn_backend"] = "0"
os.environ["FLAGS_disable_onednn_backend"] = "1"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_json_format_model"] = "0"
os.environ["PADDLE_PDX_USE_PIR_TRT"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["PADDLE_PDX_MODEL_SOURCE"] = "bos"

import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image

from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.utils.exceptions import OCRError
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


def _patch_paddle_predictor_option():
    """
    Monkey patch PaddlePredictorOption

    PaddleX在设置设备类型时会强制启用PIR API（见pp_option.py:225-226）：
        if device_type in ("gpu", "cpu"):
            os.environ["FLAGS_enable_pir_api"] = "1"

    同时，_get_default_config方法默认设置enable_new_ir=True，
    这会导致模型使用PIR格式加载，与OneDNN不兼容。

    此函数patch这些行为，强制禁用PIR API和new_ir。
    """
    try:
        from paddlex.inference.utils.pp_option import PaddlePredictorOption

        original_setter = PaddlePredictorOption.device_type.fset
        original_get_default_config = PaddlePredictorOption._get_default_config

        @functools.wraps(original_setter)
        def patched_setter(self, device_type):
            original_setter(self, device_type)
            if device_type in ("gpu", "cpu"):
                os.environ["FLAGS_enable_pir_api"] = "0"
                logger.debug("已阻止PaddleX强制启用PIR API")

        @functools.wraps(original_get_default_config)
        def patched_get_default_config(self):
            config = original_get_default_config(self)
            config["enable_new_ir"] = False
            return config

        PaddlePredictorOption.device_type = property(
            PaddlePredictorOption.device_type.fget,
            patched_setter,
            PaddlePredictorOption.device_type.fdel,
        )
        PaddlePredictorOption._get_default_config = patched_get_default_config
        logger.debug("已patch PaddlePredictorOption (device_type setter + _get_default_config)")
    except Exception as e:
        logger.warning(f"Patch PaddlePredictorOption失败: {e}")


_PATCHED = False


def _ensure_patched():
    """确保patch只执行一次"""
    global _PATCHED
    if not _PATCHED:
        _patch_paddle_predictor_option()
        _PATCHED = True


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
        return {
            "text": self.text,
            "bounding_boxes": [
                {
                    "text": bb[0],
                    "left": bb[1],
                    "top": bb[2],
                    "width": bb[3],
                    "height": bb[4],
                }
                for bb in self.bounding_boxes
            ],
            "confidence": self.confidence,
        }


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


class PaddleOCREngine(BaseOCREngine):
    """
    PaddleOCR引擎

    封装PaddleOCR，提供中文OCR识别能力。
    支持PP-OCRv5模型，识别准确率高。

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
            det_thresh: 文本检测像素阈值，值越小检测越敏感，默认从配置读取
            det_box_thresh: 文本检测框阈值，值越小检测越敏感，默认从配置读取
            det_limit_side_len: 图像边长限制，默认从配置读取
            model_dir: 本地模型目录路径，如果指定则使用本地模型而不下载
            ocr_version: OCR版本，默认从配置读取
        """
        self._language = language
        self._use_gpu = use_gpu
        self._use_angle_cls = use_angle_cls
        self._det_thresh = det_thresh if det_thresh is not None else settings.ocr_det_thresh
        self._det_box_thresh = (
            det_box_thresh if det_box_thresh is not None else settings.ocr_det_box_thresh
        )
        self._det_limit_side_len = (
            det_limit_side_len
            if det_limit_side_len is not None
            else settings.ocr_det_limit_side_len
        )
        self._model_dir = model_dir if model_dir is not None else settings.ocr_model_dir
        self._ocr_version = ocr_version if ocr_version is not None else settings.ocr_version
        self._ocr: Any = None
        self._available: bool | None = None

        if settings.ocr_use_gpu:
            self._use_gpu = True

        self._device = "gpu" if self._use_gpu else "cpu"

        logger.debug(
            f"PaddleOCR引擎初始化: language={language}, device={self._device}, "
            f"det_thresh={self._det_thresh}, det_box_thresh={self._det_box_thresh}, "
            f"model_dir={self._model_dir}, ocr_version={self._ocr_version}"
        )

    def _init_ocr(self) -> Any:
        """延迟初始化PaddleOCR实例"""
        if self._ocr is None:
            _ensure_patched()
            try:
                from pathlib import Path

                from paddleocr import PaddleOCR

                ocr_params = {
                    "lang": self._language,
                    "use_textline_orientation": False,  # 禁用文本行方向分类，避免坐标偏移
                    "use_doc_orientation_classify": False,  # 禁用文档方向分类，避免坐标偏移
                    "use_doc_unwarping": False,  # 禁用文档矫正，避免坐标偏移
                    "device": self._device,
                    "text_det_thresh": self._det_thresh,
                    "text_det_box_thresh": self._det_box_thresh,
                    "text_det_limit_side_len": self._det_limit_side_len,
                    "enable_mkldnn": False,
                    "ocr_version": self._ocr_version,
                }

                if self._model_dir:
                    model_path = Path(self._model_dir)
                    det_model_dir = model_path / "PP-OCRv4_mobile_det"
                    rec_model_dir = model_path / "PP-OCRv4_mobile_rec"

                    if det_model_dir.exists() and rec_model_dir.exists():
                        ocr_params["text_detection_model_dir"] = str(det_model_dir)
                        ocr_params["text_recognition_model_dir"] = str(rec_model_dir)
                        logger.info(f"使用本地模型: det={det_model_dir}, rec={rec_model_dir}")
                    else:
                        logger.warning(f"本地模型目录不完整，将使用在线模型: {self._model_dir}")

                self._ocr = PaddleOCR(**ocr_params)
                logger.info(
                    f"PaddleOCR初始化成功: language={self._language}, device={self._device}, "
                    f"det_thresh={self._det_thresh}, det_box_thresh={self._det_box_thresh}"
                )
            except Exception as e:
                logger.error(f"PaddleOCR初始化失败: {e}")
                raise OCRError(f"PaddleOCR初始化失败: {e}") from e
        return self._ocr

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
        try:
            logger.debug(f"开始OCR识别，图像尺寸: {image.size}")

            ocr = self._init_ocr()

            img_array = np.array(image)

            if img_array.ndim == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.ndim == 3 and img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]

            result = ocr.ocr(img_array)

            logger.debug(f"OCR原始返回类型: {type(result)}")
            logger.debug(f"OCR原始返回内容: {result}")

            text, bounding_boxes, confidence = self._parse_result(result)

            ocr_result = OCRResult(
                text=text,
                bounding_boxes=bounding_boxes,
                confidence=confidence,
            )

            logger.debug(f"OCR识别完成，文本长度: {len(text)}，边界框数量: {len(bounding_boxes)}")

            return ocr_result

        except OCRError:
            raise
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            raise OCRError(f"OCR识别失败: {e}") from e

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
        if not result:
            return "", [], 0.0

        texts = []
        bounding_boxes = []
        confidences = []

        first_result = result[0]

        if isinstance(first_result, dict) and "rec_texts" in first_result:
            rec_texts = first_result.get("rec_texts", [])
            rec_scores = first_result.get("rec_scores", [1.0] * len(rec_texts))
            rec_boxes = first_result.get("rec_boxes", None)
            rec_polys = first_result.get("rec_polys", [])
            dt_polys = first_result.get("dt_polys", [])

            for i, text in enumerate(rec_texts):
                if not text or not text.strip():
                    continue

                conf = rec_scores[i] if i < len(rec_scores) else 1.0
                texts.append(text)
                confidences.append(float(conf))

                # 优先使用rec_boxes（如果可用），因为它提供更准确的边界框坐标
                if rec_boxes is not None and i < len(rec_boxes):
                    box = rec_boxes[i]
                    left = int(box[0])
                    top = int(box[1])
                    right = int(box[2])
                    bottom = int(box[3])
                    width = right - left
                    height = bottom - top
                elif i < len(rec_polys):
                    poly = rec_polys[i]
                    if hasattr(poly, "shape"):
                        x_coords = poly[:, 0].tolist()
                        y_coords = poly[:, 1].tolist()
                    elif isinstance(poly, (list, tuple)):
                        x_coords = [p[0] for p in poly]
                        y_coords = [p[1] for p in poly]
                    else:
                        x_coords = [0]
                        y_coords = [0]

                    left = int(min(x_coords))
                    top = int(min(y_coords))
                    right = int(max(x_coords))
                    bottom = int(max(y_coords))
                    width = right - left
                    height = bottom - top
                elif i < len(dt_polys):
                    poly = dt_polys[i]
                    if hasattr(poly, "shape"):
                        x_coords = poly[:, 0].tolist()
                        y_coords = poly[:, 1].tolist()
                    elif isinstance(poly, (list, tuple)):
                        x_coords = [p[0] for p in poly]
                        y_coords = [p[1] for p in poly]
                    else:
                        x_coords = [0]
                        y_coords = [0]

                    left = int(min(x_coords))
                    top = int(min(y_coords))
                    right = int(max(x_coords))
                    bottom = int(max(y_coords))
                    width = right - left
                    height = bottom - top
                else:
                    left, top, width, height = 0, 0, 0, 0

                bounding_boxes.append((text, left, top, width, height))
        elif hasattr(first_result, "rec_texts"):
            rec_texts = first_result.rec_texts
            rec_scores = getattr(first_result, "rec_scores", [1.0] * len(rec_texts))
            rec_polys = getattr(first_result, "rec_polys", [])
            dt_polys = getattr(first_result, "dt_polys", [])

            polys = rec_polys if rec_polys else dt_polys

            for i, text in enumerate(rec_texts):
                if not text or not text.strip():
                    continue

                conf = rec_scores[i] if i < len(rec_scores) else 1.0
                texts.append(text)
                confidences.append(float(conf))

                if i < len(polys):
                    poly = polys[i]
                    if hasattr(poly, "shape"):
                        x_coords = poly[:, 0].tolist()
                        y_coords = poly[:, 1].tolist()
                    elif isinstance(poly, (list, tuple)):
                        x_coords = [p[0] for p in poly]
                        y_coords = [p[1] for p in poly]
                    else:
                        x_coords = [0]
                        y_coords = [0]

                    left = int(min(x_coords))
                    top = int(min(y_coords))
                    right = int(max(x_coords))
                    bottom = int(max(y_coords))
                    width = right - left
                    height = bottom - top
                else:
                    left, top, width, height = 0, 0, 0, 0

                bounding_boxes.append((text, left, top, width, height))
        elif isinstance(first_result, list):
            for line in first_result:
                if not line:
                    continue

                if isinstance(line, dict):
                    text = line.get("text", "")
                    conf = line.get("confidence", 1.0)
                    box = line.get("box", None)

                    if not text.strip():
                        continue

                    texts.append(text)
                    confidences.append(float(conf))

                    if box:
                        left = int(box.get("left", 0))
                        top = int(box.get("top", 0))
                        width = int(box.get("width", 0))
                        height = int(box.get("height", 0))
                    else:
                        left, top, width, height = 0, 0, 0, 0

                    bounding_boxes.append((text, left, top, width, height))
                elif isinstance(line, (list, tuple)) and len(line) >= 2:
                    box = line[0]
                    text_info = line[1]

                    text = text_info[0] if isinstance(text_info, (list, tuple)) else str(text_info)
                    conf = (
                        text_info[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) > 1
                        else 1.0
                    )

                    if not text.strip():
                        continue

                    texts.append(text)
                    confidences.append(float(conf))

                    if isinstance(box, (list, tuple)) and len(box) >= 4:
                        x_coords = [point[0] for point in box]
                        y_coords = [point[1] for point in box]
                        left = int(min(x_coords))
                        top = int(min(y_coords))
                        right = int(max(x_coords))
                        bottom = int(max(y_coords))
                        width = right - left
                        height = bottom - top
                    else:
                        left, top, width, height = 0, 0, 0, 0

                    bounding_boxes.append((text, left, top, width, height))

        full_text = "\n".join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return full_text, bounding_boxes, avg_confidence

    def is_available(self) -> bool:
        """
        检查PaddleOCR是否可用

        Returns:
            bool: 是否可用
        """
        if self._available is not None:
            return self._available

        try:
            self._init_ocr()
            self._available = True
            logger.info("PaddleOCR引擎可用")
            return True
        except Exception as e:
            self._available = False
            logger.warning(f"PaddleOCR不可用: {e}")
            return False

    def get_supported_languages(self) -> list[str]:
        """
        获取支持的语言列表

        Returns:
            支持的语言代码列表
        """
        return [
            "ch",
            "en",
            "korean",
            "japan",
            "chinese_cht",
            "ta",
            "te",
            "ka",
            "latin",
            "arabic",
            "cyrillic",
            "devanagari",
        ]


class CNTesseractOCREngine(BaseOCREngine):
    """
    Tesseract OCR引擎（已弃用）

    此类已被弃用，请使用PaddleOCREngine。
    """

    def __init__(self, language: str = "chi_sim+eng") -> None:
        """初始化Tesseract引擎（已弃用）"""
        import warnings

        warnings.warn(
            "CNTesseractOCREngine已弃用，请使用PaddleOCREngine",
            DeprecationWarning,
            stacklevel=2,
        )
        self._language = language

    def recognize(self, image: Image.Image) -> OCRResult:
        """识别图像中的文本（已弃用）"""
        raise OCRError("CNTesseractOCREngine已弃用，请使用PaddleOCREngine")

    def is_available(self) -> bool:
        """检查是否可用（已弃用）"""
        return False

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表（已弃用）"""
        return []
