"""
异常定义模块

定义项目中使用的所有自定义异常类。
"""


class CNPIIError(Exception):
    """基础异常类"""

    def __init__(self, message: str = "PII处理错误"):
        self.message = message
        super().__init__(self.message)


class OCRError(CNPIIError):
    """OCR识别异常"""

    def __init__(self, message: str = "OCR识别失败"):
        super().__init__(message)


class UnsupportedImageFormatError(CNPIIError):
    """不支持的图像格式异常"""

    def __init__(self, format_name: str = "", supported_formats: list[str] | None = None):
        supported = supported_formats or ["png", "jpg", "jpeg", "bmp"]
        message = f"不支持的图像格式: {format_name}，支持的格式: {', '.join(supported)}"
        super().__init__(message)


class PIIRecognitionError(CNPIIError):
    """PII识别异常"""

    def __init__(self, entity_type: str = "", message: str = "PII识别失败"):
        self.entity_type = entity_type
        full_message = f"{entity_type}识别失败: {message}" if entity_type else message
        super().__init__(full_message)


class AnonymizationError(CNPIIError):
    """匿名化处理异常"""

    def __init__(self, message: str = "匿名化处理失败"):
        super().__init__(message)


class InvalidPIIFormatError(CNPIIError):
    """无效的PII格式异常"""

    def __init__(self, pii_type: str, value: str = ""):
        message = f"无效的{pii_type}格式"
        if value:
            message += f": {value}"
        super().__init__(message)


class ConfigurationError(CNPIIError):
    """配置错误异常"""

    def __init__(self, config_name: str = "", message: str = "配置错误"):
        full_message = f"配置项'{config_name}'错误: {message}" if config_name else message
        super().__init__(full_message)
