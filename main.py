"""
CN PII Anonymization 入口文件

提供API服务启动入口。
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

import uvicorn

from cn_pii_anonymization.config.settings import settings
from cn_pii_anonymization.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def main() -> None:
    """
    启动API服务
    """
    logger.info(f"启动 {settings.app_name} v{settings.app_version}")
    logger.info(f"服务地址: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"API文档: http://{settings.api_host}:{settings.api_port}/docs")

    uvicorn.run(
        "cn_pii_anonymization.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
