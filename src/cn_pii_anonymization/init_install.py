"""
初始化安装脚本

用户通过PyPI安装后可运行此脚本来自动下载并初始化NLP模型。
模型包括：
- information_extraction: 信息抽取模型（用于姓名、地址识别）
- lexical_analysis: 分词模型
"""

import os

# 与运行时（nlp/nlp_engine.py、nlp/ie_engine.py）保持一致的环境变量配置。
# 注意：必须使用 PIR=0（关闭 PIR API）：
#   1) PaddlePaddle 3.0 在 PIR 模式下动转静导出存在间歇性 bug
#      （"Cannot interpret '<VarType.FP32: 5>' as a data type"）；
#   2) PIR 模式下导出的静态模型为 inference.json 格式，而运行时（PIR=0）
#      期望 inference.pdmodel 格式，导致初始化结果无法被复用、首次使用还要重新转换。
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_onednn_backend"] = "0"
os.environ["FLAGS_disable_onednn_backend"] = "1"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_json_format_model"] = "0"
os.environ["PADDLE_PDX_USE_PIR_TRT"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["PADDLE_PDX_MODEL_SOURCE"] = "bos"

import time
from typing import Any

from paddlenlp import Taskflow

from cn_pii_anonymization import TextProcessor

# 信息抽取模型的schema定义
IE_SCHEMA = ["地址", "姓名", "具体地址", "人名"]


def print_banner() -> None:
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║       CN PII Anonymization - 模型初始化工具                   ║
║       中国个人信息脱敏库 - NLP模型下载与初始化                   ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_step(step: int, total: int, message: str) -> None:
    """打印步骤信息"""
    print(f"\n[步骤 {step}/{total}] {message}")
    print("-" * 60)


def print_success(message: str) -> None:
    """打印成功信息"""
    print(f"✓ {message}")


def print_error(message: str) -> None:
    """打印错误信息"""
    print(f"✗ {message}")


def create_taskflow(task: str, max_retries: int = 3, **kwargs) -> Any:
    """
    创建Taskflow实例（带重试机制）

    PaddlePaddle 3.0 在把动态图模型转换为静态推理模型（paddle.jit.save）时
    存在间歇性错误，典型报错为：
        "Cannot interpret '<VarType.FP32: 5>' as a data type"
    该错误只发生在首次转换时，重试通常即可成功。

    另外，若缓存目录中残留了格式不兼容的静态模型（例如 PIR 模式导出的
    inference.json，而当前期望 inference.pdmodel），Taskflow 会跳过转换
    直接加载导致失败。因此在失败时会先清理所有静态模型缓存目录，
    确保下一次尝试重新执行动转静转换。

    Args:
        task: Taskflow任务名称
        max_retries: 最大尝试次数（含首次）
        **kwargs: 传递给Taskflow的其他参数

    Returns:
        Taskflow实例

    Raises:
        RuntimeError: 多次重试后仍然失败
    """
    import glob
    import shutil

    from paddlenlp.utils.env import PPNLP_HOME

    taskflow_root = os.path.join(PPNLP_HOME, "taskflow")

    for attempt in range(1, max_retries + 1):
        try:
            return Taskflow(task, **kwargs)
        except Exception as e:
            # 清理所有静态推理模型缓存目录（含转换失败或格式不兼容的残留文件），
            # 确保重试时会重新执行动转静转换而不是加载损坏的模型
            for static_dir in glob.glob(os.path.join(taskflow_root, "**", "static"), recursive=True):
                shutil.rmtree(static_dir, ignore_errors=True)
            if attempt < max_retries:
                print(f"    ⚠ 初始化失败 ({type(e).__name__}: {e})，已清理模型缓存，第 {attempt + 1} 次重试...")
            else:
                raise RuntimeError(f"初始化失败: {e}") from e


def check_dependencies() -> bool:
    """
    检查必要的依赖是否已安装

    Returns:
        bool: 依赖是否满足
    """
    print_step(1, 4, "检查依赖环境")

    # 检查PaddlePaddle
    try:
        import paddle

        paddle_version = paddle.__version__
        print_success(f"PaddlePaddle 版本: {paddle_version}")
    except ImportError:
        print_error("未找到 PaddlePaddle，请先安装: pip install paddlepaddle")
        return False

    # 检查PaddleNLP
    try:
        import paddlenlp

        paddlenlp_version = paddlenlp.__version__
        print_success(f"PaddleNLP 版本: {paddlenlp_version}")
    except ImportError:
        print_error("未找到 PaddleNLP，请先安装: pip install paddlenlp")
        return False

    # 检查设备信息
    try:
        if paddle.is_compiled_with_cuda():
            gpu_count = paddle.device.cuda.device_count()
            if gpu_count > 0:
                print_success(f"检测到 CUDA GPU，数量: {gpu_count}")
            else:
                print_success("CUDA 可用但未检测到 GPU，将使用 CPU 模式")
        else:
            print_success("使用 CPU 模式运行")
    except Exception as e:
        print_success(f"设备检测完成 ({e})")

    return True


def download_ie_model() -> bool:
    """
    下载并初始化信息抽取模型

    Returns:
        bool: 是否成功
    """
    print_step(2, 4, "下载信息抽取模型 (information_extraction)")
    print("此模型用于识别姓名和地址等敏感信息")
    print(f"Schema: {IE_SCHEMA}")
    print("首次下载可能需要几分钟，请耐心等待...\n")

    try:
        start_time = time.time()

        # 创建Taskflow会自动下载模型（带重试，处理动转静转换的间歇性错误）
        ie = create_taskflow(
            "information_extraction",
            schema=IE_SCHEMA,
            device="cpu",
        )

        # 运行一次测试以完成模型加载
        test_text = "张三住在北京市朝阳区"
        result = ie(test_text)

        elapsed_time = time.time() - start_time
        print_success(f"信息抽取模型下载并初始化成功 (耗时: {elapsed_time:.1f}秒)")
        print_success(f"测试结果: {result}")
        return True

    except Exception as e:
        print_error(f"信息抽取模型下载失败: {e}")
        return False


def download_lac_model() -> bool:
    """
    下载并初始化分词模型

    Returns:
        bool: 是否成功
    """
    print_step(3, 4, "下载分词模型 (lexical_analysis)")
    print("此模型用于中文分词和词性标注")
    print("首次下载可能需要几分钟，请耐心等待...\n")

    try:
        start_time = time.time()

        # 创建Taskflow会自动下载模型（带重试，处理动转静转换的间歇性错误）
        lac = create_taskflow(
            "lexical_analysis",
            device="cpu",
        )

        # 运行一次测试以完成模型加载
        test_text = "这是一个测试句子"
        result = lac(test_text)

        elapsed_time = time.time() - start_time
        print_success(f"分词模型下载并初始化成功 (耗时: {elapsed_time:.1f}秒)")
        print_success(f"测试结果: {result}")
        return True

    except Exception as e:
        print_error(f"分词模型下载失败: {e}")
        return False


def verify_installation() -> bool:
    """
    验证安装是否成功

    Returns:
        bool: 是否验证成功
    """
    print_step(4, 4, "验证安装")

    try:
        # 测试文本处理
        test_text = """
        你好 章鹏辉，
        我是公司HR于涛，请把你的简历投递至徐汇区虹桥路1号A座907室。
        有任何问题咨询wenti@gmail.com或拨打13912345678。
        另外请再次确认你的如下信息是否正确：
        银行卡号:62175 1234 5678 901236
        身份证号:412728 19761114 4009
        护照号:E88329471
        """

        processor = TextProcessor()
        result = processor.process(test_text)

        print_success("TextProcessor 初始化成功")
        print_success(f"脱敏结果预览: {result.anonymized_text[:100]}...")
        return True

    except Exception as e:
        print_error(f"验证失败: {e}")
        return False


def main() -> int:
    """
    主函数：执行模型初始化流程

    Returns:
        int: 退出码，0表示成功，1表示失败
    """
    print_banner()
    print("模式: CPU")

    # 步骤1: 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装必要的依赖")
        return 1

    # 步骤2: 下载信息抽取模型
    if not download_ie_model():
        print("\n❌ 信息抽取模型下载失败")
        return 1

    # 步骤3: 下载分词模型
    if not download_lac_model():
        print("\n❌ 分词模型下载失败")
        return 1

    # 步骤4: 验证安装
    if not verify_installation():
        print("\n❌ 安装验证失败")
        return 1

    # 成功提示
    print("\n" + "=" * 60)
    print("🎉 恭喜！所有模型已成功下载并初始化！")
    print("=" * 60)
    print("\n现在您可以开始使用 cn_pii_anonymization 库了：")
    print("""
    from cn_pii_anonymization import TextProcessor

    processor = TextProcessor()
    result = processor.process("我的手机号是13812345678")
    print(result.anonymized_text)
""")
    print("更多使用方法请参考项目文档。")

    return 0


if __name__ == "__main__":
    main()
