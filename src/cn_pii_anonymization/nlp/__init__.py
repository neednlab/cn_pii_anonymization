"""
NLP引擎模块

提供中文NLP处理能力，包括：
- PaddleNLP LAC引擎：分词和词性标注
- PaddleNLP信息抽取引擎：姓名和地址识别
"""

from cn_pii_anonymization.nlp.ie_engine import PaddleNLPInfoExtractionEngine
from cn_pii_anonymization.nlp.nlp_engine import (
    PaddleNlpArtifacts,
    PaddleNLPEngine,
    PaddleNlpEngineProvider,
)

__all__ = [
    "PaddleNLPEngine",
    "PaddleNlpArtifacts",
    "PaddleNlpEngineProvider",
    "PaddleNLPInfoExtractionEngine",
]
