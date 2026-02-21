import time

from PIL import Image

from cn_pii_anonymization.core.image_redactor import CNPIIImageRedactorEngine


def main(image_path: str, redacted_image_path: str) -> dict:
    """
    测试完整性能

    Args:
        image_path: 图像文件路径
        redacted_image_path: 脱敏后图像文件路径

    Returns:
        性能测试结果
    """
    image = Image.open(image_path)


    results = {
        "image_path": image_path,
        "image_size": image.size,
        "runs": [],
    }

    CNPIIImageRedactorEngine.reset()
    run_result = {}

    # 完整流程计时
    start_total = time.time()

    # 1. 初始化
    start = time.time()
    engine = CNPIIImageRedactorEngine()
    init_time = time.time() - start
    run_result["init_time"] = init_time

    # 2. 完整脱敏
    start = time.time()
    redacted = engine.redact(image)
    redacted.save(redacted_image_path)
    redact_time = time.time() - start
    run_result["redact_time"] = redact_time

    total_time = time.time() - start_total
    run_result["total_time"] = total_time

    results["runs"].append(run_result)

    return results


if __name__ == "__main__":
    image_path = "./data/z2.png"
    redacted_image_path = "./data/z2_redacted.png"

    results = main(image_path, redacted_image_path)
    print(results)
