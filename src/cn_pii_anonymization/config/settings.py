"""
应用配置模块

使用pydantic-settings管理应用配置，支持从环境变量和.env文件加载配置。
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类

    支持从环境变量和.env文件加载配置。

    Attributes:
        app_name: 应用名称
        app_version: 应用版本
        debug: 调试模式
        api_host: API服务主机
        api_port: API服务端口
        log_level: 日志级别
        log_file: 日志文件路径
        nlp_model: PaddleNLP模型名称
        nlp_use_gpu: NLP是否使用GPU
        ocr_language: OCR语言设置
        ocr_use_gpu: OCR是否使用GPU
        ocr_use_angle_cls: OCR是否使用方向分类器
        ocr_det_thresh: OCR文本检测像素阈值
        ocr_det_box_thresh: OCR文本检测框阈值
        ocr_det_limit_side_len: OCR图像边长限制
        max_image_size: 最大图像大小(字节)
        supported_image_formats: 支持的图像格式列表
        mosaic_block_size: 默认马赛克块大小
        mosaic_blur_radius: 默认模糊半径
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "CN PII Anonymization"
    app_version: str = "0.1.0"
    debug: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    nlp_model: str = "lac"
    nlp_use_gpu: bool = False

    ocr_language: str = "ch"
    ocr_use_gpu: bool = False
    ocr_use_angle_cls: bool = True
    ocr_det_thresh: float = 0.3
    ocr_det_box_thresh: float = 0.5
    ocr_det_limit_side_len: int = 960
    ocr_model_dir: str | None = None
    ocr_version: str = "PP-OCRv4"

    max_image_size: int = 10 * 1024 * 1024
    supported_image_formats: list[str] = Field(
        default_factory=lambda: ["png", "jpg", "jpeg", "bmp", "gif", "webp"]
    )

    mosaic_block_size: int = 10
    mosaic_blur_radius: int = 15

    @property
    def log_file_path(self) -> Path:
        """获取日志文件的完整路径"""
        return Path(self.log_file)


settings = Settings()
