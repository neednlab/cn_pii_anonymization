"""
图片脱敏性能测试脚本

测试优化前后的性能对比。
"""

import time
from pathlib import Path

from PIL import Image

from cn_pii_anonymization.core.image_redactor import CNPIIImageRedactorEngine
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)


def test_image_redaction_performance(image_path: str, iterations: int = 3) -> None:
    """
    测试图片脱敏性能

    Args:
        image_path: 图片路径
        iterations: 测试迭代次数
    """
    image_path = Path(image_path)
    if not image_path.exists():
        logger.error(f"图片不存在: {image_path}")
        return

    logger.info(f"加载测试图片: {image_path}")
    image = Image.open(image_path)
    logger.info(f"图片尺寸: {image.size}")

    # 初始化引擎（首次加载会有初始化开销）
    logger.info("初始化图像脱敏引擎...")
    init_start = time.time()
    engine = CNPIIImageRedactorEngine()
    init_time = time.time() - init_start
    logger.info(f"引擎初始化耗时: {init_time:.2f}秒")

    # 进行多次测试取平均值
    times = []
    for i in range(iterations):
        logger.info(f"\n--- 第 {i + 1}/{iterations} 次测试 ---")
        start_time = time.time()

        result = engine.redact(image)

        elapsed = time.time() - start_time
        times.append(elapsed)
        logger.info(f"处理耗时: {elapsed:.2f}秒")

        # 获取OCR结果统计
        ocr_result = engine.get_ocr_result()
        if ocr_result:
            logger.info(f"OCR识别到 {len(ocr_result.bounding_boxes)} 个文本区域")
            logger.info(f"OCR文本总长度: {len(ocr_result.text)} 字符")

    # 计算统计数据
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    logger.info("\n" + "=" * 50)
    logger.info("性能测试结果:")
    logger.info(f"  平均处理时间: {avg_time:.2f}秒")
    logger.info(f"  最短处理时间: {min_time:.2f}秒")
    logger.info(f"  最长处理时间: {max_time:.2f}秒")
    logger.info("=" * 50)

    # 保存结果图片
    output_path = image_path.parent / f"{image_path.stem}_redacted{image_path.suffix}"
    result.save(output_path)
    logger.info(f"结果已保存: {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python test_performance.py <图片路径> [迭代次数]")
        print("示例: python test_performance.py data/a1.png 3")
        sys.exit(1)

    image_path = sys.argv[1]
    iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    test_image_redaction_performance(image_path, iterations)
