"""
PaddleNLP信息抽取引擎模块

封装PaddleNLP Taskflow的information_extraction方法，
用于姓名和地址的精确识别。
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

from typing import Any, ClassVar

from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


class PaddleNLPInfoExtractionEngine:
    """
    PaddleNLP信息抽取引擎

    封装PaddleNLP Taskflow的information_extraction方法，
    用于姓名和地址的精确识别。

    相比LAC NER，信息抽取模型对特定实体类型的识别更加准确。

    Attributes:
        _ie_engine: 信息抽取Taskflow实例
        _schema: 抽取schema，定义要识别的实体类型

    Example:
        >>> engine = PaddleNLPInfoExtractionEngine()
        >>> result = engine.extract("刘先生住在广东省深圳市南山区粤海街道科兴科学园B栋。")
        >>> print(result)
        [{'地址': [{'text': '广东省深圳市南山区粤海街道科兴科学园B栋', 'probability': 0.95}]}]
    """

    DEFAULT_SCHEMA: ClassVar[list[str]] = ["地址", "姓名"]

    def __init__(
        self,
        schema: list[str] | None = None,
        use_gpu: bool = False,
    ) -> None:
        """
        初始化信息抽取引擎

        Args:
            schema: 要抽取的实体类型列表，默认为['地址', '姓名']
            use_gpu: 是否使用GPU加速
        """
        self._schema = schema or self.DEFAULT_SCHEMA.copy()
        self._use_gpu = use_gpu
        self._ie_engine: Any = None
        self._initialized = False
        self._init_error: str | None = None
        logger.debug(
            f"PaddleNLP信息抽取引擎初始化: schema={self._schema}, use_gpu={use_gpu}"
        )

    def load(self) -> None:
        """加载引擎"""
        self._init_ie_engine()

    def _init_ie_engine(self) -> None:
        """延迟初始化信息抽取模型"""
        if self._initialized or self._init_error:
            return

        try:
            from paddlenlp import Taskflow

            self._ie_engine = Taskflow(
                "information_extraction",
                schema=self._schema,
                device="gpu" if self._use_gpu else "cpu",
            )
            self._initialized = True
            logger.info(
                f"PaddleNLP信息抽取模型初始化成功: schema={self._schema}, use_gpu={self._use_gpu}"
            )
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"PaddleNLP信息抽取模型初始化失败: {e}")
            self._initialized = True

    def extract(self, text: str) -> list[dict]:
        """
        从文本中抽取信息

        Args:
            text: 待抽取的文本

        Returns:
            抽取结果列表，每个元素是一个字典，包含实体类型和对应的文本

        Example:
            >>> result = engine.extract("张三住在北京市朝阳区")
            >>> # 返回: [{'姓名': [{'text': '张三', 'probability': 0.9}],
            >>> #         '地址': [{'text': '北京市朝阳区', 'probability': 0.85}]}]
        """
        if not text:
            return []

        try:
            self._init_ie_engine()

            if self._ie_engine is None:
                logger.warning("信息抽取引擎未初始化，无法进行抽取")
                return []

            result = self._ie_engine(text)
            logger.debug(f"信息抽取结果: {result}")
            return result if result else []

        except Exception as e:
            logger.error(f"信息抽取失败: {e}")
            return []

    def extract_addresses(self, text: str) -> list[dict]:
        """
        仅抽取地址信息

        Args:
            text: 待抽取的文本

        Returns:
            地址列表，每个元素包含text和probability
        """
        if "地址" not in self._schema:
            logger.warning("当前schema不包含'地址'类型，无法抽取地址")
            return []

        result = self.extract(text)
        addresses = []

        for item in result:
            if "地址" in item:
                for addr in item["地址"]:
                    addresses.append(
                        {
                            "text": addr.get("text", ""),
                            "probability": addr.get("probability", 0.85),
                        }
                    )

        logger.debug(f"抽取到 {len(addresses)} 个地址: {addresses}")
        return addresses

    def extract_names(self, text: str) -> list[dict]:
        """
        仅抽取姓名信息

        Args:
            text: 待抽取的文本

        Returns:
            姓名列表，每个元素包含text和probability
        """
        if "姓名" not in self._schema:
            logger.warning("当前schema不包含'姓名'类型，无法抽取姓名")
            return []

        result = self.extract(text)
        names = []

        for item in result:
            if "姓名" in item:
                for name in item["姓名"]:
                    names.append(
                        {
                            "text": name.get("text", ""),
                            "probability": name.get("probability", 0.85),
                        }
                    )

        logger.debug(f"抽取到 {len(names)} 个姓名: {names}")
        return names

    def is_loaded(self) -> bool:
        """检查引擎是否已加载"""
        return self._initialized and self._ie_engine is not None

    def get_schema(self) -> list[str]:
        """获取当前schema"""
        return self._schema.copy()

    def set_schema(self, schema: list[str]) -> None:
        """
        设置新的schema（需要重新初始化引擎）

        Args:
            schema: 新的实体类型列表
        """
        if schema != self._schema:
            self._schema = schema
            self._ie_engine = None
            self._initialized = False
            self._init_error = None
            logger.info(f"Schema已更新为: {schema}，引擎将在下次使用时重新初始化")
