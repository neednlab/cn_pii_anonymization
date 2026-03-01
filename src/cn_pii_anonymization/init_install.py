"""
初始化安装脚本

用户通过PyPI安装后可运行此脚本来自动下载并初始化NLP模型。
模型包括：
- information_extraction: 信息抽取模型（用于姓名、地址识别）
- lexical_analysis: 分词模型

使用方法：
    python -c "from cn_pii_anonymization.init_install import main; main()"
"""

import time

from paddlenlp import Taskflow

from cn_pii_anonymization import TextProcessor

# 信息抽取模型的schema定义
IE_SCHEMA = ["地址", "姓名", "具体地址", "人名"]


def print_banner() -> None:
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║       CN PII Anonymization - 模型初始化工具                    ║
║       中国个人信息脱敏库 - NLP模型下载与初始化                     ║
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

        # 创建Taskflow会自动下载模型
        ie = Taskflow(
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
        from paddlenlp import Taskflow

        start_time = time.time()

        # 创建Taskflow会自动下载模型
        lac = Taskflow(
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
