# 问题修复记录

## 最近一次修复

| 项目 | 内容 |
|------|------|
| **修复时间** | 2026-02-18 10:28:15 |
| **问题描述** | `.env` 文件中配置 `DEBUG=false`，但运行脚本时控制台仍然输出 DEBUG 级别日志 |
| **问题原因** | 脚本文件（`full_performance_test.py`、`download_models.py`）没有调用 `setup_logging()` 初始化日志系统。Loguru 默认日志级别是 DEBUG，只有调用 `setup_logging()` 后才会读取 `.env` 中的 `LOG_LEVEL` 配置 |
| **修复方式** | 在脚本中添加 `setup_logging()` 调用，确保日志系统正确初始化 |
| **修复结果** | DEBUG 级别日志不再输出，日志级别正确遵循 `.env` 配置 |

---

## 修改文件列表

### 1. `scripts/full_performance_test.py`
- 添加 `setup_logging` 导入
- 在 `logger = get_logger(__name__)` 之前调用 `setup_logging()`

### 2. `scripts/download_models.py`
- 添加 `setup_logging` 导入
- 在 `logger = get_logger(__name__)` 之前调用 `setup_logging()`

### 3. `main.py`
- 添加 `setup_logging` 导入
- 在 `logger = get_logger(__name__)` 之前调用 `setup_logging()`

### 4. `src/cn_pii_anonymization/ocr/ocr_engine.py`
- 将模块级别的 `_patch_paddle_predictor_option()` 调用改为延迟执行
- 新增 `_ensure_patched()` 函数，确保 patch 只执行一次
- 在 `PaddleOCREngine._init_ocr()` 方法中调用 `_ensure_patched()`

### 5. `src/cn_pii_anonymization/utils/logger.py`
- 修改 `setup_logging()` 函数，实现 DEBUG 模式与日志级别自动关联
- 当 `DEBUG=true` 时，自动使用 DEBUG 日志级别
- 当 `DEBUG=false` 时，使用 `.env` 中配置的 `LOG_LEVEL`（默认 INFO）

---

## 历史修复记录

| 日期 | 问题 | 修复方式 |
|------|------|----------|
| 2026-02-18 | DEBUG日志未按配置过滤 | 添加 setup_logging() 调用 |
| 2026-02-18 | 图像识别脱敏处理时间过长 | IE预过滤 + OCR参数优化 + PII边界框缓存 |
| 2026-02-16 | 图片身份证号未识别（OCR错误导致19位） | OCR错误容错机制 |
| 2026-02-16 | OCR图片手机号银行卡号未脱敏 | 相邻文本框合并 + 手机号识别器排除逻辑 |
| 2026-02-16 | 邮箱和护照识别问题 | 修正 recognition_metadata 中的 recognizer_identifier |
| 2026-02-16 | 地址遗漏识别问题 | 修复批量调用返回格式不一致 |
| 2026-02-15 | 图片脱敏性能问题 | 批量分析+IE缓存优化 |

---

## 详细修复记录

### 2026-02-18 DEBUG日志未按配置过滤

**问题背景：**
用户在 `.env` 文件中配置了 `DEBUG=false`，但运行 `full_performance_test.py` 脚本时，控制台仍然输出 DEBUG 级别的日志信息。

**问题分析：**
1. `.env` 文件中的 `DEBUG` 配置项和日志级别是两个独立的设置
2. 日志级别由 `LOG_LEVEL` 配置项控制，默认值为 `INFO`
3. 脚本没有调用 `setup_logging()` 初始化日志系统
4. Loguru 默认日志级别是 DEBUG，所以所有 `logger.debug()` 的日志都会输出
5. 只有调用 `setup_logging()` 后，才会读取 `.env` 中的 `LOG_LEVEL` 配置

**修复方案：**
在脚本中添加 `setup_logging()` 调用：

```python
# 修复前
from cn_pii_anonymization.utils.logger import get_logger

logger = get_logger(__name__)

# 修复后
from cn_pii_anonymization.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
```

**受影响的脚本：**
- `scripts/full_performance_test.py`
- `scripts/download_models.py`

**其他脚本说明：**
- `scripts/test_nlp.py`：直接使用 paddlenlp，不使用项目日志系统
- `scripts/test_ocr_mkldnn.py`：直接使用 print 输出，不使用项目日志系统
- `scripts/check_device.py`：直接使用 print 输出，不使用项目日志系统

### 2026-02-18 图像识别脱敏处理时间过长

**问题背景：**
用户使用 `z2.png` 图片进行测试，发现身份证号 `412728 19761114 4009` 未被正确识别并脱敏。

**问题分析：**
1. OCR识别将身份证号分割成三个文本框：
   - `'412728'`
   - `'319761114'` ← **OCR错误**：多识别了一个 `3`，应该是 `19761114`
   - `'4009'`
2. 合并后变成 `4127283197611144009`（19位数字）
3. 身份证识别器只匹配18位数字，无法识别19位数字

**修复方案：**

1. **新增OCR错误正则**：
   - 添加 `ID_CARD_OCR_ERROR_PATTERN` 匹配19位数字

2. **OCR错误容错机制**：
   - 添加 `_handle_ocr_errors()` 方法处理19位数字情况
   - 添加 `_try_fix_ocr_error()` 方法尝试修复
   - 优先检查常见错误位置（如第6位，即出生年份开头）

**修复代码：**

```python
# id_card_recognizer.py - OCR错误容错
ID_CARD_OCR_ERROR_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
    r"(?<![a-zA-Z\d])[1-9](?:\s*\d){18}(?![a-zA-Z\d])"
)

def _handle_ocr_errors(self, text: str) -> list[RecognizerResult]:
    """处理OCR识别错误的情况"""
    results = []
    for match in self.ID_CARD_OCR_ERROR_PATTERN.finditer(text):
        ocr_text = match.group()
        ocr_text_clean = ocr_text.replace(" ", "")
        if len(ocr_text_clean) != 19:
            continue
        valid_id_card = self._try_fix_ocr_error(ocr_text_clean)
        if valid_id_card:
            logger.info(f"OCR错误容错: 从 '{ocr_text_clean}' 修复为 '{valid_id_card}'")
            result = self._create_result(...)
            results.append(result)
    return results

def _try_fix_ocr_error(self, ocr_text: str) -> str | None:
    """尝试修复OCR错误，移除19位数字中的每一位"""
    if len(ocr_text) != 19:
        return None
    priority_positions = [6, 7, 8, 0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    for pos in priority_positions:
        if pos >= len(ocr_text):
            continue
        candidate = ocr_text[:pos] + ocr_text[pos + 1 :]
        if self._validate_id_card(candidate):
            return candidate
    return None
```

**测试结果：**
- 身份证号 `4127283197611144009` 成功修复为 `412728197611144009`
- 置信度 0.90（略低于正常识别的 0.95）
- 图片脱敏成功处理了7个PII区域

### 2026-02-16 OCR图片手机号银行卡号未脱敏

**问题背景：**
用户使用 `z2.png` 图片进行测试，发现手机号和银行卡号未脱敏。

**问题分析：**
1. OCR识别将连续的数字分割成多个独立的文本框：
   - 手机号 `13912345678` 被分割成 `'139'` 和 `'12345678'` 两个文本框
   - 银行卡号 `6217560800040101015` 被分割成 `'62175'`、`'6080'`、`'0040'`、`'101015'` 四个文本框
   - 身份证号 `11010519950824352X` 被分割成 `'110105'`、`'19950824'`、`'352X'` 三个文本框
2. 手机号识别器将身份证号中的子串 `19950824352` 误识别为手机号
3. 手机号识别器将银行卡号中的子串 `17560800040` 误识别为手机号

**修复方案：**

1. **相邻文本框合并**：
   - 在 `_analyze_ocr_result()` 方法中，先调用 `_merge_adjacent_text_boxes()` 合并相邻文本框
   - 按垂直位置分组（同一行的文本框）
   - 按水平位置排序，合并水平间距小于阈值的文本框
   - 阈值从10像素增加到20像素，以适应银行卡号的间距

2. **手机号识别器排除逻辑**：
   - 添加 `_is_part_of_id_card()` 方法：检查匹配位置前后是否有足够的数字/X，判断是否是身份证号的一部分
   - 添加 `_is_part_of_bank_card()` 方法：检查匹配位置前后是否有超过5位数字，判断是否是银行卡号的一部分
   - 在 `analyze()` 方法中，先排除身份证号和银行卡号的子串，再返回结果

**修复代码：**

```python
# image_redactor.py - 相邻文本框合并
def _merge_adjacent_text_boxes(
    self,
    boxes: list[tuple[str, int, int, int, int]],
    max_horizontal_gap: int = 20,
    max_vertical_diff: int = 5,
) -> list[tuple[str, int, int, int, int]]:
    # 按垂直位置分组
    # 按水平位置排序并合并
    ...
```

```python
# phone_recognizer.py - 排除身份证号子串
def _is_part_of_id_card(self, text: str, start: int, end: int) -> bool:
    # 检查前面是否有6位以上数字
    # 检查后面是否有1位以上数字/X
    # 判断是否构成18位身份证号
    ...

# phone_recognizer.py - 排除银行卡号子串
def _is_part_of_bank_card(self, text: str, start: int, end: int) -> bool:
    # 检查前后数字总数是否超过5位
    ...
```

**测试结果：**
- 手机号 `13912345678` 正确识别
- 银行卡号 `6217560800040101015` 正确识别
- 身份证号子串 `19950824352` 被正确过滤
- 银行卡号子串 `17560800040` 被正确过滤

### 2026-02-16 邮箱和护照识别问题

**问题背景：**
用户报告 "zhangsan@example.com" 等邮箱地址无法被识别为PII。经检查发现护照识别器存在相同问题。

**问题分析：**
1. `CNEmailRecognizer` 和 `CNPassportRecognizer` 使用内部 `_pattern_recognizer` 进行实际识别
2. `_pattern_recognizer` 返回的结果中 `recognition_metadata['recognizer_identifier']` 是内部识别器的 id
3. Presidio 的 `_enhance_using_context` 方法按 `recognizer.id` 过滤结果时，由于 id 不匹配，结果被丢弃

**修复代码：**
```python
def _validate_results(
    self,
    text: str,
    results: list[RecognizerResult],
) -> list[RecognizerResult]:
    valid_results = []
    for result in results:
        # ... 验证逻辑 ...
        if is_valid:
            # 修正 recognition_metadata，确保与外层识别器一致
            result.recognition_metadata[
                RecognizerResult.RECOGNIZER_NAME_KEY
            ] = self.name
            result.recognition_metadata[
                RecognizerResult.RECOGNIZER_IDENTIFIER_KEY
            ] = self.id
            valid_results.append(result)
    return valid_results
```

**其他识别器检查结果：**
- `CNPhoneRecognizer`: 直接实现 `analyze` 方法，使用 `_create_result` 创建结果，无问题
- `CNIDCardRecognizer`: 直接实现 `analyze` 方法，使用 `_create_result` 创建结果，无问题
- `CNBankCardRecognizer`: 直接实现 `analyze` 方法，使用 `_create_result` 创建结果，无问题
- `CNAddressRecognizer`: 直接实现 `analyze` 方法，使用 `_create_result` 创建结果，无问题
- `CNNameRecognizer`: 直接实现 `analyze` 方法，使用 `_create_result` 创建结果，无问题

### 2026-02-16 地址遗漏识别问题

**问题背景：**
在性能优化后，发现部分地址无法被正确识别，如"甲25号写字楼230室"。

**问题分析：**
1. IE引擎本身能正确识别地址（验证通过）
2. 问题出在 `extract_batch()` 方法的返回格式
3. PaddleNLP Taskflow 批量调用返回格式与单个调用不同：
   - 单个调用：`ie("text")` → `[{'地址': [...]}]`
   - 批量调用：`ie(["text1", "text2"])` → `[{'地址': [...]}, {'地址': [...]}]`
4. 在 `extract_batch()` 中，每个 `result` 是字典而非列表，导致识别器无法正确解析

**修复代码：**
```python
# 修复前
results_map[orig_text] = result if result else []

# 修复后
if result and isinstance(result, dict):
    results_map[orig_text] = [result]  # 包装成列表格式
else:
    results_map[orig_text] = []
```

### 2026-02-15 图片脱敏性能问题

**问题背景：**
使用图片脱敏功能时，如果OCR结果文字较多，单张图片的处理时间很长。

**问题分析：**
1. OCR文本框串行PII分析：对每个OCR文本框串行调用分析器
2. IE引擎重复调用：每个文本框都会单独调用IE引擎进行姓名/地址识别
3. 缺乏文本去重：相同文本被重复分析

**修复方式：**
1. 实现批量分析方法 `analyze_batch()`：预先批量调用IE引擎处理所有文本
2. 添加IE结果缓存机制：识别器支持缓存，避免重复调用IE引擎
3. 文本去重优化：对OCR结果进行去重，相同文本只分析一次
4. IE引擎批量处理：添加 `extract_batch()` 方法支持批量文本处理
