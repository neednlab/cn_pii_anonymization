"""检查PaddlePaddle设备支持"""

import paddle

print(f"Paddle version: {paddle.__version__}")
print(f"Compiled with CUDA: {paddle.is_compiled_with_cuda()}")
print(f"Device count: {paddle.device.cuda.device_count() if paddle.is_compiled_with_cuda() else 0}")

try:
    available_devices = paddle.device.get_available_device()
    print(f"Available devices: {available_devices}")
except Exception as e:
    print(f"Error getting devices: {e}")

try:
    paddle.device.set_device("gpu:0")
    print("GPU device set successfully!")
except Exception as e:
    print(f"Cannot set GPU: {e}")
