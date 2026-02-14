"""
测试 PaddleOCR enable_mkldnn=False 方法
"""

import os

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_onednn_backend"] = "0"
os.environ["FLAGS_disable_onednn_backend"] = "1"
os.environ["FLAGS_enable_pir_api"] = "0"

import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

print("=" * 60)
print("测试 PaddleOCR enable_mkldnn=False 方法")
print("=" * 60)

try:
    print("\n正在初始化 PaddleOCR...")
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="ch",
        enable_mkldnn=False,
    )
    print("PaddleOCR 初始化成功!")

    print("\n正在创建测试图像...")
    test_image = Image.new("RGB", (200, 100), color=(255, 255, 255))
    
    print("正在执行 OCR 识别...")
    result = ocr.ocr(np.array(test_image))
    
    print("\nOCR 识别成功!")
    print(f"结果: {result}")
    
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
