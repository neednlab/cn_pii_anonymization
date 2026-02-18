"""
完整性能测试脚本

测试完整的图像脱敏流程，包括初始化时间。
"""

import time
from pathlib import Path

from PIL import Image

from cn_pii_anonymization.core.image_redactor import CNPIIImageRedactorEngine
from cn_pii_anonymization.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def test_full_performance(image_path: str, iterations: int = 3) -> dict:
    """
    测试完整性能

    Args:
        image_path: 图像文件路径
        iterations: 测试迭代次数

    Returns:
        性能测试结果
    """
    image = Image.open(image_path)
    logger.info(f"图像尺寸: {image.size}")

    results = {
        "image_path": image_path,
        "image_size": image.size,
        "iterations": iterations,
        "runs": [],
    }

    for i in range(iterations):
        logger.info(f"\n{'='*60}")
        logger.info(f"第 {i+1}/{iterations} 次测试")
        logger.info(f"{'='*60}")

        # 重置单例
        CNPIIImageRedactorEngine.reset()

        run_result = {"iteration": i + 1}

        # 完整流程计时
        start_total = time.time()

        # 1. 初始化
        start = time.time()
        engine = CNPIIImageRedactorEngine()
        init_time = time.time() - start
        run_result["init_time"] = init_time
        logger.info(f"[1] 引擎初始化: {init_time:.2f}s")

        # 2. 完整脱敏
        start = time.time()
        redacted = engine.redact(image)
        redact_time = time.time() - start
        run_result["redact_time"] = redact_time
        logger.info(f"[2] 脱敏处理: {redact_time:.2f}s")

        total_time = time.time() - start_total
        run_result["total_time"] = total_time
        logger.info(f"[总] 完整耗时: {total_time:.2f}s")

        results["runs"].append(run_result)

    # 计算平均值
    avg_init = sum(r["init_time"] for r in results["runs"]) / iterations
    avg_redact = sum(r["redact_time"] for r in results["runs"]) / iterations
    avg_total = sum(r["total_time"] for r in results["runs"]) / iterations

    results["summary"] = {
        "avg_init_time": avg_init,
        "avg_redact_time": avg_redact,
        "avg_total_time": avg_total,
    }

    logger.info(f"\n{'='*60}")
    logger.info("性能测试总结")
    logger.info(f"{'='*60}")
    logger.info(f"平均初始化时间: {avg_init:.2f}s")
    logger.info(f"平均脱敏处理时间: {avg_redact:.2f}s")
    logger.info(f"平均完整耗时: {avg_total:.2f}s")
    logger.info(f"目标: < 30s")
    logger.info(f"结果: {'✓ 达标' if avg_total < 30 else '✗ 未达标'}")

    return results


if __name__ == "__main__":
    image_path = "./data/z2.png"
    results = test_full_performance(image_path, iterations=3)
