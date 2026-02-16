# CN PII Anonymization 开发进度

## 文档信息

| 项目 | 内容 |
|------|------|
| **文档名称** | 开发进度记录 |
| **创建日期** | 2026-02-13 |
| **最后更新** | 2026-02-15 |

---

## 开发阶段概览

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1** | 基础框架搭建、核心识别器实现 | ✅ 已完成 |
| **Phase 2** | 文本处理管道、API接口开发 | ✅ 已完成 |
| **Phase 3** | 图像处理管道、OCR集成 | ✅ 已完成 |
| **Phase 4** | 测试完善、文档编写 | ✅ 已完成 |
| **Phase 5** | 性能优化、部署上线 | ✅ 已完成 |

---

## 详细进度记录

### 2026-02-13 - Phase 1 完成

#### 已完成任务

1. **项目结构搭建**
   - 创建完整的目录结构
   - 配置pyproject.toml（依赖管理、ruff配置、pytest配置）
   - 创建所有模块的`__init__.py`文件

2. **配置模块 (config/)**
   - `settings.py`: 应用配置类，使用pydantic-settings管理
   - `recognizer_config.yaml`: 识别器配置文件

3. **工具模块 (utils/)**
   - `logger.py`: Loguru日志配置
   - `exceptions.py`: 自定义异常类定义

4. **核心模块 (core/)**
   - `analyzer.py`: CNPIIAnalyzerEngine - 中文PII分析器引擎（单例模式）
   - `anonymizer.py`: CNPIIAnonymizerEngine - 中文PII匿名化引擎（单例模式）

5. **识别器模块 (recognizers/)**
   - `base.py`: CNPIIRecognizer - 中文PII识别器基类
   - `phone_recognizer.py`: CNPhoneRecognizer - 手机号识别器 (P0) ✅
   - `id_card_recognizer.py`: CNIDCardRecognizer - 身份证识别器 (P0) ✅
   - `bank_card_recognizer.py`: CNBankCardRecognizer - 银行卡识别器 (P0) ✅
   - `passport_recognizer.py`: CNPassportRecognizer - 护照号识别器 (P0) ✅
   - `email_recognizer.py`: CNEmailRecognizer - 邮箱识别器 (P1) ✅

6. **操作符模块 (operators/)**
   - `mask_operator.py`: CNMaskOperator - 掩码操作符
   - `fake_operator.py`: CNFakeOperator - 假名替换操作符

7. **处理器模块 (processors/)**
   - `text_processor.py`: TextProcessor - 文本PII处理器

8. **测试模块 (tests/)**
   - `conftest.py`: pytest配置和fixtures
   - `unit/test_recognizers.py`: 识别器单元测试
   - `unit/test_operators.py`: 操作符单元测试
   - `unit/test_processors.py`: 处理器单元测试
   - `integration/test_text_pipeline.py`: 文本管道集成测试

#### 技术亮点

1. **识别器验证机制**
   - 手机号：验证11位格式、运营商号段
   - 身份证：地区码验证、出生日期验证、校验码验证
   - 银行卡：Luhn算法校验、BIN码识别
   - 护照：新版/旧版/港澳台格式支持
   - 邮箱：格式验证、常见域名识别

2. **引擎设计**
   - 单例模式确保全局唯一实例
   - 懒加载NLP模型
   - 可扩展的识别器注册机制

3. **操作符设计**
   - 灵活的掩码配置（前缀/后缀保留）
   - 邮箱域名特殊处理
   - Faker集成生成假数据

---

### 2026-02-13 - Phase 2 完成

#### 已完成任务

1. **API数据模型 (api/schemas/)**
   - `request.py`: 请求数据模型
     - `TextAnonymizeRequest`: 文本匿名化请求
     - `TextAnalyzeRequest`: 文本分析请求
     - `OperatorConfigRequest`: 操作符配置请求
   - `response.py`: 响应数据模型
     - `APIResponse`: 统一API响应模型
     - `ErrorResponse`: 错误响应模型
     - `PIIEntityResponse`: PII实体响应模型
     - `TextAnonymizeData`: 文本匿名化响应数据
     - `TextAnalyzeData`: 文本分析响应数据

2. **API路由 (api/routes/)**
   - `text.py`: 文本处理路由
     - `POST /api/v1/text/anonymize`: 文本匿名化接口
     - `POST /api/v1/text/analyze`: 文本分析接口
     - `GET /api/v1/text/entities`: 获取支持的实体类型

3. **API中间件 (api/middleware/)**
   - `logging.py`: 日志中间件
     - `LoggingMiddleware`: 请求日志记录
     - `CORSMiddleware`: CORS配置辅助类

4. **API应用入口 (api/)**
   - `app.py`: FastAPI应用
     - 应用生命周期管理
     - 全局异常处理
     - 健康检查端点
     - 根路径端点

5. **入口文件更新**
   - `main.py`: 服务启动入口

6. **API测试**
   - `tests/integration/test_api.py`: API集成测试
     - 健康检查测试
     - 文本匿名化测试
     - 文本分析测试
     - 支持实体类型测试

#### 技术亮点

1. **API设计**
   - RESTful风格接口设计
   - 统一的请求/响应模型
   - OpenAPI文档自动生成
   - 输入验证和错误处理

2. **中间件**
   - 请求日志记录（请求ID、处理时间）
   - CORS跨域支持

3. **异常处理**
   - 自定义PII异常处理器
   - 通用异常处理器
   - 标准化错误响应格式

---

### 2026-02-13 - Phase 3 完成

#### 已完成任务

1. **依赖安装**
   - `presidio-image-redactor>=0.0.50`: 图像PII处理
   - `pytesseract>=0.3.10`: OCR引擎接口
   - `python-multipart>=0.0.22`: 表单数据处理

2. **OCR引擎模块 (ocr/)**
   - `ocr_engine.py`: OCR引擎封装
     - `OCREngine`: OCR引擎抽象基类
     - `CNTesseractOCREngine`: 中文Tesseract OCR引擎
     - `OCRResult`: OCR识别结果数据类
     - 支持中文简体+英文识别
     - 支持边界框提取和置信度计算

3. **图像脱敏引擎 (core/)**
   - `image_redactor.py`: CNPIIImageRedactorEngine
     - 单例模式设计
     - 整合OCR识别和PII分析
     - 支持边界框合并处理
     - 支持多种马赛克样式

4. **马赛克操作符 (operators/)**
   - `mosaic_operator.py`: 图像马赛克操作
     - `MosaicStyle`: 马赛克样式枚举（pixel/blur/fill）
     - `PixelMosaicOperator`: 像素块马赛克
     - `GaussianBlurOperator`: 高斯模糊
     - `SolidFillOperator`: 纯色填充
     - `create_mosaic_operator`: 工厂函数

5. **图像处理器 (processors/)**
   - `image_processor.py`: ImageProcessor
     - `ImagePIIEntity`: 图像PII实体数据类
     - `ImageProcessResult`: 图像处理结果数据类
     - 支持文件、字节、PIL图像多种输入
     - 支持仅分析模式（不脱敏）

6. **图像API数据模型 (api/schemas/)**
   - `ImagePIIEntityResponse`: 图像PII实体响应模型
   - `ImageAnonymizeData`: 图像匿名化响应数据
   - `ImageAnalyzeData`: 图像分析响应数据

7. **图像处理API路由 (api/routes/)**
   - `image.py`: 图像处理路由
     - `POST /api/v1/image/anonymize`: 图像脱敏接口
     - `POST /api/v1/image/analyze`: 图像分析接口
     - `GET /api/v1/image/mosaic-styles`: 获取马赛克样式

8. **配置更新**
   - `settings.py`: 添加OCR相关配置
     - `ocr_language`: OCR语言设置
     - `ocr_config`: OCR配置参数
     - `mosaic_block_size`: 默认马赛克块大小
     - `mosaic_blur_radius`: 默认模糊半径

9. **测试模块**
   - `tests/unit/test_image_operators.py`: 马赛克操作符单元测试
   - `tests/integration/test_image_api.py`: 图像API集成测试

#### 技术亮点

1. **OCR引擎设计**
   - 抽象基类支持多种OCR引擎
   - 中文+英文混合识别
   - 边界框和置信度信息提取
   - Tesseract可用性检测

2. **图像处理流程**
   - OCR识别 → PII分析 → 边界框合并 → 马赛克处理
   - 支持重叠区域合并
   - 支持白名单过滤

3. **马赛克样式**
   - 像素块马赛克：可配置块大小
   - 高斯模糊：可配置模糊半径
   - 纯色填充：可配置填充颜色

4. **API设计**
   - 支持返回处理后的图像或元数据
   - 支持多种马赛克样式选择
   - 完善的错误处理和验证

---

### 2026-02-14 - Phase 4 完成

#### 已完成任务

1. **测试修复**
   - 修复测试用例中的无效身份证号（校验码验证）
   - 修复测试用例中的银行卡号（Luhn校验）
   - 统一测试数据格式

2. **识别器单元测试完善 (tests/unit/test_recognizers.py)**
   - 手机号识别器测试：
     - 参数化测试覆盖多种格式
     - 格式验证测试
     - 上下文关键词测试
   - 身份证识别器测试：
     - 参数化测试覆盖多种格式
     - 省份代码验证测试
     - 出生日期验证测试
     - 校验码验证测试
   - 银行卡识别器测试：
     - 参数化测试覆盖多种格式
     - Luhn算法校验测试
     - 置信度计算测试
     - 银行BIN码测试
   - 护照识别器测试：
     - 参数化测试覆盖多种格式
     - 格式验证测试（新版/旧版/港澳台）
   - 邮箱识别器测试：
     - 参数化测试覆盖多种格式
     - 格式验证测试
     - 置信度计算测试
     - 常见域名测试
   - 识别器集成测试：
     - 多识别器同时工作测试
     - 无误报测试

3. **核心引擎单元测试 (tests/unit/test_engines.py)**
   - 分析器引擎测试：
     - 手机号/身份证分析测试
     - 多实体分析测试
     - 分数阈值过滤测试
     - 白名单过滤测试
     - 空文本/无PII文本测试
     - 单例模式测试
   - 匿名化引擎测试：
     - 手机号/身份证匿名化测试
     - 多实体匿名化测试
     - 空文本/无PII文本测试
     - 单例模式测试
   - 引擎集成测试：
     - 完整管道测试
     - 文本结构保持测试
     - 指定实体类型测试

4. **OCR引擎单元测试 (tests/unit/test_ocr_engine.py)**
   - OCRResult数据类测试：
     - 初始化测试
     - to_dict转换测试
     - 默认置信度测试
   - CNTesseractOCREngine测试：
     - 初始化测试（默认/自定义参数）
     - 可用性检测测试
     - OCR识别测试
     - 错误处理测试
     - 边界框提取测试
     - 置信度计算测试
     - 支持语言获取测试
   - 缓存测试

5. **性能测试 (tests/performance/test_performance.py)**
   - 分析性能测试：
     - 短文本分析性能
     - 长文本分析性能
   - 匿名化性能测试：
     - 短文本匿名化性能
     - 长文本匿名化性能
   - 完整管道性能测试
   - 识别器性能测试：
     - 手机号识别速度
     - 身份证识别速度
     - 混合识别速度
   - 并发处理测试

6. **测试覆盖率报告**
   - 总覆盖率：**85%**
   - 核心模块覆盖率：
     - analyzer.py: 97%
     - anonymizer.py: 92%
     - text_processor.py: 100%
     - ocr_engine.py: 90%
   - 识别器模块覆盖率：
     - phone_recognizer.py: 94%
     - id_card_recognizer.py: 97%
     - bank_card_recognizer.py: 90%
     - passport_recognizer.py: 92%
     - email_recognizer.py: 96%

7. **依赖更新**
   - 添加 pytest-benchmark 用于性能测试

#### 测试统计

- **总测试数量**: 165个测试用例
- **单元测试**: 139个
- **集成测试**: 18个
- **性能测试**: 8个

#### 性能基准

| 测试项 | 平均时间 |
|--------|----------|
| 短文本分析 | ~3ms |
| 短文本匿名化 | ~65μs |
| 手机号识别 | ~3ms |
| 身份证识别 | ~2.9ms |
| 完整管道处理 | ~3.6ms |

---

### 2026-02-14 - Phase 5 完成

#### 已完成任务

1. **P2级别PII识别器 (recognizers/)**
   - `address_recognizer.py`: CNAddressRecognizer - 中国地址识别器
     - 支持NER结果集成
     - 基于省份关键词和地址关键词的置信度计算
   - `name_recognizer.py`: CNNameRecognizer - 中文姓名识别器
     - 支持NER结果集成
   

2. **识别器模块更新**
   - 更新 `__init__.py` 导出新识别器
   - 更新 `analyzer.py` 注册新识别器

3. **单元测试扩展 (tests/unit/test_recognizers.py)**
   - 地址识别器测试：
     - 参数化测试覆盖多种地址格式
     - 地址验证测试
     - 省份识别测试
     - 置信度计算测试
   - 姓名识别器测试：
     - 参数化测试覆盖多种姓名格式
     - 姓名验证测试
     - 姓氏识别测试
     - 复姓识别测试
   - P2识别器集成测试

4. **Docker部署配置**
   - `Dockerfile`: 多阶段构建镜像
     - 基于Python 3.12-slim
     - 安装中文语言包
     - 配置健康检查
   - `docker-compose.yml`: 服务编排配置
     - 端口映射配置
     - 环境变量配置
     - 日志配置
     - 资源限制配置

#### 测试统计

- **总测试数量**: 69个识别器测试用例
- **新增测试**: 22个（地址+姓名+集成）

---

### 2026-02-14 - Phase 5 完成（续）

#### 已完成任务

1. **项目文档编写**
   - `README.md`: 完整的项目文档
     - 项目简介和核心功能说明
     - 支持的 PII 类型表格
     - 安装指南
     - 快速开始示例（文本处理、图像处理、API 服务）
     - 完整的 API 文档（请求/响应示例）
     - 匿名化操作说明（掩码、假名替换）
     - 马赛克样式说明（像素块、高斯模糊、纯色填充）
     - 配置说明（环境变量、识别器配置）
     - 开发指南（项目结构、运行测试、代码规范）
     - 部署指南（Docker、Docker Compose、生产环境建议）
     - 性能指标表格
     - 常见问题解答
     - 许可证、致谢和贡献指南

---

## 里程碑状态

| 里程碑 | 描述 | 状态 |
|--------|------|------|
| **M1** | 完成P0级别PII识别器（手机号、身份证、银行卡、护照） | ✅ 已完成 |
| **M2** | 完成文本处理管道和API接口 | ✅ 已完成 |
| **M3** | 完成图像处理管道 | ✅ 已完成 |
| **M4** | 完成P1级别PII识别器（邮箱） | ✅ 已完成 |
| **M5** | 完成P2级别PII识别器（地址、姓名） | ✅ 已完成 |
| **M6** | 完成性能优化和部署 | ✅ 已完成 |

---

## 下一步计划

所有开发任务已完成！项目可以进行以下后续工作：

1. 生产环境部署和监控配置
2. 持续集成/持续部署(CI/CD)流程配置
3. 用户反馈收集和识别器优化


---

### 2026-02-15 - 姓名和地址识别方案升级

#### 已完成任务

1. **信息抽取引擎模块 (nlp/ie_engine.py)**
   - 新增 `PaddleNLPInfoExtractionEngine` 类
   - 封装PaddleNLP Taskflow的`information_extraction`方法
   - Schema默认为 `['地址', '姓名']`
   - 提供 `extract()`, `extract_addresses()`, `extract_names()` 方法
   - 支持延迟初始化和GPU加速

2. **姓名识别器重构 (recognizers/name_recognizer.py)**
   - 从LAC NER改为使用信息抽取(IE)方法
   - 新增 `ie_engine` 参数，接收信息抽取引擎实例
   - 新增 `set_ie_engine()` 方法
   - 置信度直接采用IE返回的probability结果

3. **地址识别器重构 (recognizers/address_recognizer.py)**
   - 从LAC NER改为使用信息抽取(IE)方法
   - 新增 `ie_engine` 参数，接收信息抽取引擎实例
   - 新增 `MIN_ADDRESS_LENGTH = 6` 常量，过滤短地址
   - 新增 `set_ie_engine()` 方法
   - 置信度直接采用IE返回的probability结果

4. **分析器引擎更新 (core/analyzer.py)**
   - 新增 `_ie_engine` 属性
   - 新增 `_setup_ie_engine()` 方法
   - 识别器注册分为两类：
     - 正则表达式识别器（手机号、身份证、银行卡、护照、邮箱）
     - 信息抽取识别器（地址、姓名）
   - 新增 `get_ie_engine()` 方法

5. **NLP模块导出更新 (nlp/__init__.py)**
   - 新增导出 `PaddleNLPInfoExtractionEngine`

6. **测试脚本 (scripts/test_ie_integration.py)**
   - 新增IE引擎集成测试脚本
   - 测试姓名和地址识别功能
   - 测试地址长度过滤功能

#### 技术变更说明

| 变更项 | 变更前 | 变更后 |
|--------|--------|--------|
| 姓名识别方式 | LAC NER (lexical_analysis) | 信息抽取 (information_extraction) |
| 地址识别方式 | LAC NER (lexical_analysis) | 信息抽取 (information_extraction) |
| 置信度来源 | 内部计算 | IE返回的probability |
| 地址过滤 | 无 | 长度<6字符的地址被过滤 |

#### 测试验证

- ✅ 代码检查通过 (ruff check)
- ✅ 姓名识别功能正常
- ✅ 地址识别功能正常
- ✅ 地址长度过滤功能正常
- ✅ 置信度正确使用IE返回值


---

### 2026-02-15 - 图像脱敏引擎简化

#### 已完成任务

1. **移除跨行PII扩展功能**
   - 移除 `_expand_address_bbox` 方法（地址边界框扩展）
   - 移除 `_find_adjacent_boxes_below` 方法（查找下方相邻框）

2. **简化 _analyze_ocr_result 方法**
   - 移除地址跨行扩展逻辑
   - 移除 `analyzed_indices` 索引跟踪
   - 仅保留对检测出的PII实体区域进行脱敏

3. **更新文档字符串**
   - 更新 `_analyze_ocr_result` 方法的文档说明

#### 技术变更说明

| 变更项 | 变更前 | 变更后 |
|--------|--------|--------|
| 地址处理 | 自动扩展边界框覆盖相邻行 | 仅处理检测到的PII区域 |
| 跨行识别 | 支持地址跨行扩展 | 不支持跨行扩展 |
| 代码复杂度 | 较高（包含相邻框查找和合并逻辑） | 简化（直接处理检测到的区域） |

#### 测试验证

- ✅ 代码检查通过 (ruff check)
- ✅ 代码格式化通过 (ruff format)

---

### 2026-02-15 - NLP引擎简化

#### 已完成任务

1. **移除NLP引擎中的NER识别逻辑**
   - 移除 `NER_TAG_MAP` 常量
   - 移除 `_extract_entities` 方法
   - 修改 `process_text` 方法，不再调用NER识别

2. **更新文档说明**
   - 更新模块文档字符串，说明NER已迁移至ie_engine.py
   - 更新 `PaddleNlpArtifacts` 类文档，说明entities始终为空
   - 更新 `PaddleNLPEngine` 类文档，移除NER功能说明

#### 技术变更说明

| 变更项 | 变更前 | 变更后 |
|--------|--------|--------|
| NER识别位置 | nlp_engine.py (LAC lexical_analysis) | ie_engine.py (information_extraction) |
| process_text返回 | entities包含NER识别结果 | entities始终为空列表 |
| NER_TAG_MAP | 用于映射LAC标签到Presidio实体类型 | 已移除 |

#### 测试验证

- ✅ 代码检查通过 (ruff check)
- ✅ 代码格式化通过 (ruff format)

---

### 2026-02-16 - IE引擎地址schema扩展

#### 已完成任务

1. **信息抽取引擎更新 (nlp/ie_engine.py)**
   - 新增 `ADDRESS_SCHEMA_KEYS` 类常量：`{"地址", "具体地址"}`
   - 修改 `extract_addresses` 方法：
     - 支持识别"地址"和"具体地址"两种schema类型的地址信息
     - 动态检测当前schema中包含的地址类型key
     - 遍历所有地址类型key提取地址信息
   - 更新 `DEFAULT_SCHEMA` 为 `["地址", "具体地址", "姓名"]`

2. **地址识别器更新 (recognizers/address_recognizer.py)**
   - 新增 `ADDRESS_SCHEMA_KEYS` 类常量：`{"地址", "具体地址"}`
   - 修改缓存处理逻辑，支持从"地址"和"具体地址"两种key提取地址信息

3. **分析器引擎更新 (core/analyzer.py)**
   - 更新IE引擎schema为 `["地址", "具体地址", "姓名"]`

#### 技术变更说明

| 变更项 | 变更前 | 变更后 |
|--------|--------|--------|
| 地址schema支持 | 仅支持"地址" | 支持"地址"和"具体地址" |
| DEFAULT_SCHEMA | ["地址", "姓名"] | ["地址", "具体地址", "姓名"] |
| schema检查方式 | 硬编码检查"地址" | 使用ADDRESS_SCHEMA_KEYS集合动态检查 |
| 地址提取逻辑 | 仅提取"地址"key | 遍历所有地址类型key提取 |

#### 测试验证

- ✅ 代码检查通过 (ruff check)
- ✅ 代码格式化通过 (ruff format)
- ✅ IE引擎extract_addresses方法正确识别"具体地址"
- ✅ 地址识别器正确识别"北京市朝阳区建国门外大街1号"

---

## 问题记录

| 日期 | 问题描述 | 解决方案 | 状态 |
|------|----------|----------|------|
| 2026-02-13 | RecognizerRegistry语言配置问题 | 在创建RecognizerRegistry时设置supported_languages=["zh"] | ✅ 已解决 |
| 2026-02-13 | 手机号识别器重复匹配问题 | 实现结果合并逻辑，去除重叠匹配 | ✅ 已解决 |
| 2026-02-13 | FastAPI StreamingResponse返回类型问题 | 在路由装饰器中设置response_model=None | ✅ 已解决 |
| 2026-02-13 | HTTPException被异常处理器捕获问题 | 添加HTTPException异常处理器，并在路由中显式重新抛出 | ✅ 已解决 |
| 2026-02-14 | Tesseract OCR需要额外安装 | 将OCR引擎替换为PaddleOCR，无需额外安装 | ✅ 已解决 |
| 2026-02-14 | PaddleOCR新版本API参数变化 | 更新参数：使用device替代use_gpu，移除show_log和cls参数 | ✅ 已解决 |
| 2026-02-14 | PaddlePaddle Windows OneDNN兼容性问题 | 设置环境变量FLAGS_use_mkldnn=0禁用OneDNN | ✅ 已解决 |
| 2026-02-14 | numpy版本兼容性问题 | 需要重新安装依赖解决二进制兼容性 | ✅ 已解决 |
| 2026-02-14 | spaCy Windows兼容性问题 | 将NLP引擎迁移到PaddleNLP，统一使用PaddlePaddle框架 | ✅ 已解决 |
| 2026-02-14 | 小尺寸图像OCR识别不到文本 | 添加可配置的OCR检测阈值参数(det_thresh, det_box_thresh)，降低默认det_box_thresh为0.5 | ✅ 已解决 |
| 2026-02-14 | PaddlePaddle 3.0 PIR API与OneDNN不兼容 | 设置环境变量FLAGS_enable_pir_api=0禁用PIR API | ✅ 已解决 |
| 2026-02-15 | 图像脱敏边界框合并算法缺陷 | 使用连通分量算法替代线性合并，确保所有重叠框正确合并 | ✅ 已解决 |
| 2026-02-15 | 地址跨行未脱敏 | 实现地址边界框向下扩展，自动覆盖相邻OCR行 | ✅ 已解决 |
| 2026-02-15 | 地址扩展误合并上方内容 | 修改为只向下扩展，并增加高度限制过滤异常框 | ✅ 已解决 |
| 2026-02-15 | 图像脱敏地址和手机号未正确识别 | 修改score_threshold参数默认值为None，使用配置文件中的按类型阈值而非全局阈值 | ✅ 已解决 |
| 2026-02-15 | 收货地址标题被误打码，甲25号写字楼230室未完全打码 | 禁用OCR文档预处理功能（use_doc_orientation_classify=False, use_doc_unwarping=False），避免UVDoc文档校正导致的坐标偏移 | ✅ 已解决 |

---

## 备注

- 项目使用Python 3.12
- 使用uv进行依赖管理
- 遵循PEP 8和ruff代码规范
- API文档地址: http://localhost:8000/docs
- 图像处理使用PaddleOCR引擎
- NLP处理使用PaddleNLP LAC模型
