/**
 * PII Shield - Web Demo
 * 个人信息脱敏演示应用
 *
 * 功能：
 * 1. 文本模式：输入文本，识别并脱敏PII信息
 * 2. 图片模式：上传图片，识别并脱敏图片中的PII信息
 *
 * API 端点：
 * - POST /api/v1/text/anonymize - 文本脱敏
 * - POST /api/v1/image/anonymize - 图片脱敏
 */

// ============================================
// 配置
// ============================================
const CONFIG = {
    // API 基础地址 - 根据实际部署情况修改
    API_BASE_URL: 'http://localhost:8000',
    // 支持的图片格式
    SUPPORTED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    // 最大图片大小 (10MB)
    MAX_IMAGE_SIZE: 10 * 1024 * 1024,
};

// ============================================
// 状态管理
// ============================================
const state = {
    currentMode: 'text', // 'text' | 'image'
    isProcessing: false,
    textInput: '',
    imageFile: null,
    imagePreviewUrl: null,
    resultImageUrl: null,
    lastResult: null,
};

// ============================================
// DOM 元素引用
// ============================================
const elements = {
    // 模式切换
    modeTabs: document.querySelectorAll('.mode-tab'),
    textMode: document.getElementById('textMode'),
    imageMode: document.getElementById('imageMode'),

    // 设置面板
    anonymizeType: document.getElementById('anonymizeType'),
    mosaicStyle: document.getElementById('mosaicStyle'),
    imageStyleSetting: document.getElementById('imageStyleSetting'),

    // 文本模式
    textInput: document.getElementById('textInput'),
    textOutput: document.getElementById('textOutput'),
    clearTextBtn: document.getElementById('clearTextBtn'),
    pasteTextBtn: document.getElementById('pasteTextBtn'),
    copyResultBtn: document.getElementById('copyResultBtn'),

    // 图片模式
    uploadArea: document.getElementById('uploadArea'),
    imageInput: document.getElementById('imageInput'),
    uploadPreview: document.getElementById('uploadPreview'),
    previewImage: document.getElementById('previewImage'),
    clearImageBtn: document.getElementById('clearImageBtn'),
    imageOutput: document.getElementById('imageOutput'),
    downloadImageBtn: document.getElementById('downloadImageBtn'),

    // 操作按钮
    resetBtn: document.getElementById('resetBtn'),
    anonymizeBtn: document.getElementById('anonymizeBtn'),
    btnText: document.getElementById('btnText'),

    // 统计
    statsBar: document.getElementById('statsBar'),
    statEntities: document.getElementById('statEntities'),
    statTypes: document.getElementById('statTypes'),
    statTime: document.getElementById('statTime'),

    // Toast
    toast: document.getElementById('toast'),
};

// ============================================
// 工具函数
// ============================================

/**
 * 显示 Toast 提示
 * @param {string} message - 提示消息
 * @param {string} type - 类型: 'success' | 'error'
 * @param {number} duration - 显示时长(毫秒)
 */
function showToast(message, type = 'success', duration = 3000) {
    const toast = elements.toast;
    const icon = toast.querySelector('.toast-icon');
    const msg = toast.querySelector('.toast-message');

    // 设置内容和样式
    msg.textContent = message;
    toast.className = `toast ${type}`;
    icon.textContent = type === 'success' ? '✓' : '✕';

    // 显示
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // 自动隐藏
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

/**
 * 设置加载状态
 * @param {boolean} loading - 是否加载中
 */
function setLoading(loading) {
    state.isProcessing = loading;
    elements.anonymizeBtn.disabled = loading;

    if (loading) {
        elements.btnText.innerHTML = '<div class="spinner"></div> 处理中...';
    } else {
        elements.btnText.textContent = '开始脱敏';
    }
}

/**
 * 更新统计信息
 * @param {Object} stats - 统计信息
 */
function updateStats(stats) {
    elements.statsBar.style.display = 'flex';
    elements.statEntities.textContent = stats.entities || 0;
    elements.statTypes.textContent = stats.types || 0;
    elements.statTime.textContent = `${stats.time || 0}ms`;
}

/**
 * 隐藏统计信息
 */
function hideStats() {
    elements.statsBar.style.display = 'none';
}

// ============================================
// 模式切换
// ============================================

/**
 * 切换工作模式
 * @param {string} mode - 'text' | 'image'
 */
function switchMode(mode) {
    state.currentMode = mode;

    // 更新标签样式
    elements.modeTabs.forEach(tab => {
        if (tab.dataset.mode === mode) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // 切换内容显示
    if (mode === 'text') {
        elements.textMode.classList.remove('hidden');
        elements.imageMode.classList.add('hidden');
        elements.imageStyleSetting.style.display = 'none';
    } else {
        elements.textMode.classList.add('hidden');
        elements.imageMode.classList.remove('hidden');
        elements.imageStyleSetting.style.display = 'flex';
    }

    // 隐藏统计
    hideStats();
}

// ============================================
// 文本模式功能
// ============================================

/**
 * 清空文本输入
 */
function clearText() {
    elements.textInput.value = '';
    state.textInput = '';
    resetTextOutput();
    hideStats();
}

/**
 * 粘贴文本
 */
async function pasteText() {
    try {
        const text = await navigator.clipboard.readText();
        elements.textInput.value = text;
        state.textInput = text;
        showToast('已粘贴剪贴板内容');
    } catch (err) {
        showToast('无法访问剪贴板，请手动粘贴', 'error');
    }
}

/**
 * 复制结果
 */
async function copyResult() {
    const outputText = elements.textOutput.textContent;
    if (!outputText || elements.textOutput.classList.contains('empty')) {
        showToast('没有可复制的内容', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(outputText);
        showToast('已复制到剪贴板');
    } catch (err) {
        showToast('复制失败', 'error');
    }
}

/**
 * 重置文本输出区域
 */
function resetTextOutput() {
    elements.textOutput.innerHTML = `
        <div class="image-placeholder">
            <div class="image-placeholder-icon">📝</div>
            <p>脱敏后的文本将显示在这里</p>
        </div>
    `;
    elements.textOutput.classList.add('empty');
}

/**
 * 显示文本脱敏结果
 * @param {Object} result - API 返回的结果
 */
function displayTextResult(result) {
    const data = result.data;
    const anonymizedText = data.anonymized_text;
    const entities = data.pii_entities || [];

    // 构建带高亮的结果文本
    let highlightedText = data.original_text;
    const entityTypeColors = {
        'CN_PHONE_NUMBER': 'highlight-phone',
        'CN_EMAIL_ADDRESS': 'highlight-email',
        'CN_ID_CARD': 'highlight-idcard',
        'CN_NAME': 'highlight-name',
        'CN_BANK_CARD': 'highlight-bank',
        'CN_ADDRESS': 'highlight-address',
        'CN_PASSPORT': 'highlight-idcard',
    };

    // 按位置倒序排序，避免替换时位置偏移
    const sortedEntities = [...entities].sort((a, b) => b.start - a.start);

    // 替换为脱敏后的文本并添加高亮
    for (const entity of sortedEntities) {
        const colorClass = entityTypeColors[entity.entity_type] || 'highlight-name';
        const before = highlightedText.substring(0, entity.start);
        const after = highlightedText.substring(entity.end);
        const masked = `<span class="${colorClass}" title="${entity.entity_type} (${(entity.score * 100).toFixed(1)}%)">${entity.anonymized_text}</span>`;
        highlightedText = before + masked + after;
    }

    elements.textOutput.innerHTML = highlightedText;
    elements.textOutput.classList.remove('empty');

    // 更新统计
    const uniqueTypes = new Set(entities.map(e => e.entity_type));
    updateStats({
        entities: entities.length,
        types: uniqueTypes.size,
        time: state.lastProcessingTime || 0,
    });
}

/**
 * 执行文本脱敏
 */
async function anonymizeText() {
    const text = elements.textInput.value.trim();
    if (!text) {
        showToast('请输入要脱敏的文本', 'error');
        return;
    }

    setLoading(true);
    const startTime = Date.now();

    try {
        const operatorType = elements.anonymizeType.value;
        const operators = {};

        // 构建操作符配置
        const entityTypes = [
            'CN_PHONE_NUMBER',
            'CN_EMAIL_ADDRESS',
            'CN_ID_CARD',
            'CN_NAME',
            'CN_BANK_CARD',
            'CN_ADDRESS',
            'CN_PASSPORT',
        ];

        entityTypes.forEach(type => {
            operators[type] = {
                type: operatorType,
                masking_char: '*',
                keep_prefix: 0,
                keep_suffix: 0,
            };
        });

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/text/anonymize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                operators: operators,
                language: 'zh',
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '请求失败');
        }

        const result = await response.json();
        state.lastProcessingTime = Date.now() - startTime;
        state.lastResult = result;

        displayTextResult(result);
        showToast('脱敏完成');

    } catch (error) {
        console.error('文本脱敏失败:', error);
        showToast(`脱敏失败: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

// ============================================
// 图片模式功能
// ============================================

/**
 * 处理图片文件选择
 * @param {File} file - 图片文件
 */
function handleImageSelect(file) {
    // 验证文件类型
    if (!CONFIG.SUPPORTED_IMAGE_TYPES.includes(file.type)) {
        showToast('不支持的图片格式', 'error');
        return;
    }

    // 验证文件大小
    if (file.size > CONFIG.MAX_IMAGE_SIZE) {
        showToast('图片大小超过限制 (最大10MB)', 'error');
        return;
    }

    state.imageFile = file;

    // 创建预览
    const reader = new FileReader();
    reader.onload = (e) => {
        state.imagePreviewUrl = e.target.result;
        elements.previewImage.src = e.target.result;
        elements.uploadPreview.classList.remove('hidden');
        elements.uploadArea.classList.add('has-image');
    };
    reader.readAsDataURL(file);

    hideStats();
    resetImageOutput();
}

/**
 * 处理拖拽上传
 * @param {DragEvent} e - 拖拽事件
 */
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    elements.uploadArea.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleImageSelect(files[0]);
    }
}

/**
 * 清空图片
 */
function clearImage() {
    state.imageFile = null;
    state.imagePreviewUrl = null;
    elements.imageInput.value = '';
    elements.previewImage.src = '';
    elements.uploadPreview.classList.add('hidden');
    elements.uploadArea.classList.remove('has-image');
    resetImageOutput();
    hideStats();
}

/**
 * 重置图片输出区域
 */
function resetImageOutput() {
    elements.imageOutput.innerHTML = `
        <div class="image-placeholder">
            <div class="image-placeholder-icon">🎨</div>
            <p>脱敏后的图片将显示在这里</p>
        </div>
    `;
    elements.imageOutput.classList.remove('has-image');
    state.resultImageUrl = null;
}

/**
 * 显示图片脱敏结果
 * @param {Blob} imageBlob - 图片数据
 * @param {number} piiCount - PII实体数量
 * @param {number} processingTime - 处理耗时
 */
function displayImageResult(imageBlob, piiCount, processingTime) {
    const url = URL.createObjectURL(imageBlob);
    state.resultImageUrl = url;

    elements.imageOutput.innerHTML = `<img src="${url}" alt="脱敏结果">`;
    elements.imageOutput.classList.add('has-image');

    // 更新统计
    updateStats({
        entities: piiCount,
        types: piiCount > 0 ? 1 : 0,
        time: processingTime,
    });
}

/**
 * 执行图片脱敏
 */
async function anonymizeImage() {
    if (!state.imageFile) {
        showToast('请先上传图片', 'error');
        return;
    }

    setLoading(true);
    const startTime = Date.now();

    try {
        const formData = new FormData();
        formData.append('image', state.imageFile);
        formData.append('mosaic_style', elements.mosaicStyle.value);

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/image/anonymize`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '请求失败');
        }

        const piiCount = parseInt(response.headers.get('X-PII-Count') || '0');
        const processingTime = Date.now() - startTime;

        const imageBlob = await response.blob();
        displayImageResult(imageBlob, piiCount, processingTime);
        showToast('脱敏完成');

    } catch (error) {
        console.error('图片脱敏失败:', error);
        showToast(`脱敏失败: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * 下载脱敏后的图片
 */
function downloadImage() {
    if (!state.resultImageUrl) {
        showToast('没有可下载的图片', 'error');
        return;
    }

    const link = document.createElement('a');
    link.href = state.resultImageUrl;
    link.download = `anonymized_${state.imageFile?.name || 'image.png'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast('开始下载');
}

// ============================================
// 通用功能
// ============================================

/**
 * 重置所有内容
 */
function resetAll() {
    if (state.currentMode === 'text') {
        clearText();
    } else {
        clearImage();
    }
    hideStats();
    showToast('已重置');
}

/**
 * 执行脱敏操作
 */
async function anonymize() {
    if (state.currentMode === 'text') {
        await anonymizeText();
    } else {
        await anonymizeImage();
    }
}

// ============================================
// 事件绑定
// ============================================

function initEventListeners() {
    // 模式切换
    elements.modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            switchMode(tab.dataset.mode);
        });
    });

    // 文本模式
    elements.clearTextBtn.addEventListener('click', clearText);
    elements.pasteTextBtn.addEventListener('click', pasteText);
    elements.copyResultBtn.addEventListener('click', copyResult);

    // 图片模式 - 文件选择
    elements.imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleImageSelect(e.target.files[0]);
        }
    });

    // 图片模式 - 拖拽上传
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);

    // 图片模式 - 清空图片
    elements.clearImageBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearImage();
    });

    // 图片模式 - 下载
    elements.downloadImageBtn.addEventListener('click', downloadImage);

    // 通用操作
    elements.resetBtn.addEventListener('click', resetAll);
    elements.anonymizeBtn.addEventListener('click', anonymize);

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter 执行脱敏
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            anonymize();
        }
    });
}

// ============================================
// 初始化
// ============================================

function init() {
    initEventListeners();
    console.log('PII Shield Web Demo 已加载');
    console.log('快捷键: Ctrl+Enter 执行脱敏');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
