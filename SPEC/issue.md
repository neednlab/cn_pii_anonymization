# 问题修复记录

## 最近一次修复

| 项目 | 内容 |
|------|------|
| **修复时间** | 2026-02-16 11:12:13 |
| **问题描述** | 邮箱识别器和护照识别器使用内部 `_pattern_recognizer` 委托识别，导致结果被 Presidio 过滤掉 |
| **问题原因** | `CNEmailRecognizer` 和 `CNPassportRecognizer` 委托给内部 `_pattern_recognizer` 进行识别，但返回结果中的 `recognition_metadata['recognizer_identifier']` 是内部识别器的 id，而非外层识别器的 id。Presidio 的 `_enhance_using_context` 方法使用 `recognizer.id` 过滤结果时，由于 id 不匹配，结果被错误过滤掉。 |
| **修复方式** | 在 `_validate_results()` 方法中，修正返回结果的 `recognition_metadata`，将 `recognizer_name` 和 `recognizer_identifier` 设置为外层识别器自身的值 |
| **修复结果** | 邮箱和护照识别恢复正常，所有测试通过 |

---

## 修改文件列表

### 1. `src/cn_pii_anonymization/recognizers/email_recognizer.py`
- 修改 `_validate_results()` 方法：添加对 `recognition_metadata` 的修正

### 2. `src/cn_pii_anonymization/recognizers/passport_recognizer.py`
- 修改 `_validate_results()` 方法：添加对 `recognition_metadata` 的修正

---

## 历史修复记录

| 日期 | 问题 | 修复方式 |
|------|------|----------|
| 2026-02-16 | 邮箱和护照识别问题 | 修正 recognition_metadata 中的 recognizer_identifier |
| 2026-02-16 | 地址遗漏识别问题 | 修复批量调用返回格式不一致 |
| 2026-02-15 | 图片脱敏性能问题 | 批量分析+IE缓存优化 |

---

## 详细修复记录

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
