# 问题修复记录

## 最近一次修复

| 项目 | 内容 |
|------|------|
| **修复时间** | 2026-02-16 12:08:00 |
| **问题描述** | OCR识别图片时，手机号和银行卡号未脱敏 |
| **问题原因** | 1. OCR将连续数字分割成多个独立文本框，导致PII识别器无法识别完整号码；2. 手机号识别器将身份证号和银行卡号中的子串误识别为手机号 |
| **修复方式** | 1. 在图像处理器中添加相邻文本框合并逻辑，将同一行水平相邻的文本框合并；2. 增大文本框合并阈值（从10像素增加到20像素）；3. 在手机号识别器中添加排除身份证号和银行卡号子串的逻辑 |
| **修复结果** | 手机号、银行卡号正确识别并脱敏，身份证号和银行卡号中的子串不再被误识别为手机号 |

---

## 修改文件列表

### 1. `src/cn_pii_anonymization/core/image_redactor.py`
- 新增 `_merge_adjacent_text_boxes()` 方法：合并同一行中水平相邻的文本框
- 修改 `_analyze_ocr_result()` 方法：在分析前先合并相邻文本框
- 参数调整：`max_horizontal_gap` 从10像素增加到20像素

### 2. `src/cn_pii_anonymization/recognizers/phone_recognizer.py`
- 新增 `_is_part_of_id_card()` 方法：检查匹配位置是否是身份证号的一部分
- 新增 `_is_part_of_bank_card()` 方法：检查匹配位置是否是银行卡号的一部分
- 修改 `analyze()` 方法：添加对身份证号和银行卡号子串的过滤逻辑

---

## 历史修复记录

| 日期 | 问题 | 修复方式 |
|------|------|----------|
| 2026-02-16 | OCR图片手机号银行卡号未脱敏 | 相邻文本框合并 + 手机号识别器排除逻辑 |
| 2026-02-16 | 邮箱和护照识别问题 | 修正 recognition_metadata 中的 recognizer_identifier |
| 2026-02-16 | 地址遗漏识别问题 | 修复批量调用返回格式不一致 |
| 2026-02-15 | 图片脱敏性能问题 | 批量分析+IE缓存优化 |

---

## 详细修复记录

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
