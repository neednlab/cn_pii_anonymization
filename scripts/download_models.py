"""
模型预下载脚本

在首次运行服务前，执行此脚本预先下载所有需要的模型。
避免服务启动时因网络问题导致模型下载失败。

使用方法:
    uv run python scripts/download_models.py
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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cn_pii_anonymization.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def _patch_paddle_predictor_option():
    """
    Monkey patch PaddlePredictorOption

    PaddleX在设置设备类型时会强制启用PIR API，
    同时_get_default_config方法默认设置enable_new_ir=True。
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


_patch_paddle_predictor_option()


def download_paddlenlp_models() -> None:
    """下载PaddleNLP LAC模型"""
    logger.info("=" * 50)
    logger.info("开始下载 PaddleNLP LAC 模型...")
    logger.info("=" * 50)

    try:
        from paddlenlp import Taskflow

        lac = Taskflow("lexical_analysis", model="lac")
        lac("测试文本")
        logger.info("PaddleNLP LAC 模型下载完成!")
    except Exception as e:
        logger.error(f"PaddleNLP LAC 模型下载失败: {e}")
        raise


def download_paddleocr_models() -> None:
    """下载PaddleOCR模型"""
    logger.info("=" * 50)
    logger.info("开始下载 PaddleOCR 模型...")
    logger.info("=" * 50)

    try:
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(
            lang="ch",
            use_textline_orientation=True,
            device="cpu",
            ocr_version="PP-OCRv4",
        )

        import numpy as np
        from PIL import Image

        test_image = Image.new("RGB", (100, 50), color=(255, 255, 255))
        ocr.ocr(np.array(test_image))

        logger.info("PaddleOCR 模型下载完成!")
    except Exception as e:
        logger.error(f"PaddleOCR 模型下载失败: {e}")
        raise


def main() -> None:
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始预下载所有模型...")
    logger.info("=" * 60)

    download_paddlenlp_models()
    download_paddleocr_models()

    logger.info("=" * 60)
    logger.info("所有模型下载完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
