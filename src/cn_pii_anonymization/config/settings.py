"""
应用配置模块

使用pydantic-settings管理应用配置，支持从环境变量和.env文件加载配置。
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScoreThresholdSettings:
    """
    识别器置信度阈值配置

    为每种PII识别器类型设置独立的置信度阈值。
    IE类识别器（姓名、地址）通常置信度较低，需要较低的阈值。
    正则类识别器（手机、身份证等）置信度固定为1.0，阈值影响较小。

    Attributes:
        default: 全局默认阈值
        cn_name: 姓名识别器阈值（IE模型，置信度通常0.3-0.6）
        cn_address: 地址识别器阈值（IE模型，置信度通常0.3-0.6）
        cn_phone_number: 手机号识别器阈值（正则匹配，置信度固定1.0）
        cn_id_card: 身份证识别器阈值（正则匹配，置信度固定1.0）
        cn_bank_card: 银行卡识别器阈值（正则匹配，置信度固定1.0）
        cn_passport: 护照识别器阈值（正则匹配，置信度固定1.0）
        cn_email: 邮箱识别器阈值（正则匹配，置信度固定1.0）
    """

    default: float = 0.35
    cn_name: float = 0.3
    cn_address: float = 0.3
    cn_phone_number: float = 0.5
    cn_id_card: float = 0.5
    cn_bank_card: float = 0.5
    cn_passport: float = 0.5
    cn_email: float = 0.5

    def __init__(
        self,
        default: float = 0.35,
        cn_name: float = 0.3,
        cn_address: float = 0.3,
        cn_phone_number: float = 0.5,
        cn_id_card: float = 0.5,
        cn_bank_card: float = 0.5,
        cn_passport: float = 0.5,
        cn_email: float = 0.5,
    ) -> None:
        self.default = default
        self.cn_name = cn_name
        self.cn_address = cn_address
        self.cn_phone_number = cn_phone_number
        self.cn_id_card = cn_id_card
        self.cn_bank_card = cn_bank_card
        self.cn_passport = cn_passport
        self.cn_email = cn_email

    def get_threshold(self, entity_type: str) -> float:
        """
        获取指定实体类型的阈值

        Args:
            entity_type: 实体类型名称

        Returns:
            该实体类型的阈值，未配置时返回默认阈值
        """
        threshold_map = {
            "CN_NAME": self.cn_name,
            "CN_ADDRESS": self.cn_address,
            "CN_PHONE_NUMBER": self.cn_phone_number,
            "CN_ID_CARD": self.cn_id_card,
            "CN_BANK_CARD": self.cn_bank_card,
            "CN_PASSPORT": self.cn_passport,
            "CN_EMAIL": self.cn_email,
        }
        return threshold_map.get(entity_type, self.default)

    def to_dict(self) -> dict[str, float]:
        """转换为字典"""
        return {
            "default": self.default,
            "CN_NAME": self.cn_name,
            "CN_ADDRESS": self.cn_address,
            "CN_PHONE_NUMBER": self.cn_phone_number,
            "CN_ID_CARD": self.cn_id_card,
            "CN_BANK_CARD": self.cn_bank_card,
            "CN_PASSPORT": self.cn_passport,
            "CN_EMAIL": self.cn_email,
        }


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
        score_threshold_default: 全局默认置信度阈值
        score_threshold_name: 姓名识别器阈值
        score_threshold_address: 地址识别器阈值
        score_threshold_phone: 手机号识别器阈值
        score_threshold_id_card: 身份证识别器阈值
        score_threshold_bank_card: 银行卡识别器阈值
        score_threshold_passport: 护照识别器阈值
        score_threshold_email: 邮箱识别器阈值
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

    score_threshold_default: float = Field(default=0.35, ge=0.0, le=1.0)
    score_threshold_name: float = Field(default=0.3, ge=0.0, le=1.0)
    score_threshold_address: float = Field(default=0.3, ge=0.0, le=1.0)
    score_threshold_phone: float = Field(default=0.5, ge=0.0, le=1.0)
    score_threshold_id_card: float = Field(default=0.5, ge=0.0, le=1.0)
    score_threshold_bank_card: float = Field(default=0.5, ge=0.0, le=1.0)
    score_threshold_passport: float = Field(default=0.5, ge=0.0, le=1.0)
    score_threshold_email: float = Field(default=0.5, ge=0.0, le=1.0)

    # 姓名识别器自定义列表配置
    # 允许通过的姓名列表（不需要被脱敏），使用逗号分隔
    name_allow_list: str = Field(default="")
    # 必须被脱敏的姓名列表（无论IE是否识别），使用逗号分隔
    name_deny_list: str = Field(default="")

    @property
    def log_file_path(self) -> Path:
        """获取日志文件的完整路径"""
        return Path(self.log_file)

    @property
    def score_thresholds(self) -> ScoreThresholdSettings:
        """获取识别器阈值配置对象"""
        return ScoreThresholdSettings(
            default=self.score_threshold_default,
            cn_name=self.score_threshold_name,
            cn_address=self.score_threshold_address,
            cn_phone_number=self.score_threshold_phone,
            cn_id_card=self.score_threshold_id_card,
            cn_bank_card=self.score_threshold_bank_card,
            cn_passport=self.score_threshold_passport,
            cn_email=self.score_threshold_email,
        )

    @property
    def parsed_name_allow_list(self) -> list[str]:
        """
        获取解析后的姓名允许列表

        将逗号分隔的字符串转换为列表，去除空白和空项。

        Returns:
            姓名允许列表
        """
        if not self.name_allow_list:
            return []
        return [name.strip() for name in self.name_allow_list.split(",") if name.strip()]

    @property
    def parsed_name_deny_list(self) -> list[str]:
        """
        获取解析后的姓名拒绝列表

        将逗号分隔的字符串转换为列表，去除空白和空项。

        Returns:
            姓名拒绝列表
        """
        if not self.name_deny_list:
            return []
        return [name.strip() for name in self.name_deny_list.split(",") if name.strip()]


settings = Settings()
