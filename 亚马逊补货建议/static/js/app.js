/**
 * 亚马逊补货建议系统 - 主要JavaScript文件
 * 包含全局函数和通用功能
 */

// 全局变量
window.AmazonReplenishment = {
    version: '1.0.0',
    debug: false,
    apiBaseUrl: '/api',
    currentUser: null,
    settings: {}
};

/**
 * 页面加载完成后执行的初始化函数
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('亚马逊补货建议系统初始化...');
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化表单验证
    initializeFormValidation();
    
    // 绑定全局事件
    bindGlobalEvents();
    
    // 检查系统状态
    checkSystemStatus();
    
    console.log('系统初始化完成');
});

/**
 * 初始化Bootstrap工具提示
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * 初始化表单验证
 */
function initializeFormValidation() {
    // 获取所有需要验证的表单
    const forms = document.querySelectorAll('.needs-validation');
    
    // 为每个表单添加验证事件
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * 绑定全局事件
 */
function bindGlobalEvents() {
    // 绑定所有确认按钮
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('confirm-action')) {
            e.preventDefault();
            const message = e.target.getAttribute('data-confirm-message') || '确定要执行此操作吗？';
            if (confirm(message)) {
                // 执行原始操作
                const href = e.target.getAttribute('href');
                const onclick = e.target.getAttribute('onclick');
                
                if (href) {
                    window.location.href = href;
                } else if (onclick) {
                    eval(onclick);
                }
            }
        }
    });
    
    // 自动保存表单数据到localStorage
    const autoSaveForms = document.querySelectorAll('.auto-save');
    autoSaveForms.forEach(form => {
        const formId = form.id;
        if (formId) {
            // 加载保存的数据
            loadFormData(formId);
            
            // 监听表单变化
            form.addEventListener('input', function() {
                saveFormData(formId);
            });
        }
    });
}

/**
 * 检查系统状态
 */
function checkSystemStatus() {
    // 检查API连接状态
    fetch('/api/test-connection')
        .then(response => response.json())
        .then(data => {
            updateSystemStatus('api', data.success);
        })
        .catch(error => {
            updateSystemStatus('api', false);
            console.warn('API状态检查失败:', error);
        });
}

/**
 * 更新系统状态指示器
 */
function updateSystemStatus(component, isOnline) {
    const indicators = document.querySelectorAll(`.status-indicator.${component}`);
    indicators.forEach(indicator => {
        indicator.className = `status-indicator ${component} ${isOnline ? 'online' : 'offline'}`;
    });
}

/**
 * 保存表单数据到localStorage
 */
function saveFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem(`form_${formId}`, JSON.stringify(data));
}

/**
 * 从localStorage加载表单数据
 */
function loadFormData(formId) {
    const savedData = localStorage.getItem(`form_${formId}`);
    if (!savedData) return;
    
    try {
        const data = JSON.parse(savedData);
        const form = document.getElementById(formId);
        
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = data[key];
            }
        });
    } catch (error) {
        console.warn('加载表单数据失败:', error);
    }
}

/**
 * 清除保存的表单数据
 */
function clearFormData(formId) {
    localStorage.removeItem(`form_${formId}`);
}

/**
 * 显示确认对话框
 */
function showConfirmDialog(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

/**
 * 复制文本到剪贴板
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showAlert('success', '已复制到剪贴板');
        }).catch(function(err) {
            console.error('复制失败:', err);
            showAlert('danger', '复制失败');
        });
    } else {
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert('success', '已复制到剪贴板');
        } catch (err) {
            console.error('复制失败:', err);
            showAlert('danger', '复制失败');
        }
        document.body.removeChild(textArea);
    }
}

/**
 * 下载数据为文件
 */
function downloadData(data, filename, type = 'application/json') {
    const blob = new Blob([data], { type: type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化时间差
 */
function formatTimeDiff(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        return `${days}天前`;
    } else if (hours > 0) {
        return `${hours}小时前`;
    } else if (minutes > 0) {
        return `${minutes}分钟前`;
    } else {
        return '刚刚';
    }
}

/**
 * 防抖函数
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

/**
 * 节流函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 深度克隆对象
 */
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }
    
    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }
    
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (let key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
}

/**
 * 生成随机ID
 */
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * 验证邮箱格式
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * 验证URL格式
 */
function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

/**
 * 获取URL参数
 */
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * 设置URL参数
 */
function setUrlParameter(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
}

/**
 * 移除URL参数
 */
function removeUrlParameter(name) {
    const url = new URL(window.location);
    url.searchParams.delete(name);
    window.history.pushState({}, '', url);
}

/**
 * 滚动到页面顶部
 */
function scrollToTop(smooth = true) {
    window.scrollTo({
        top: 0,
        behavior: smooth ? 'smooth' : 'auto'
    });
}

/**
 * 滚动到指定元素
 */
function scrollToElement(elementId, offset = 0) {
    const element = document.getElementById(elementId);
    if (element) {
        const top = element.offsetTop - offset;
        window.scrollTo({
            top: top,
            behavior: 'smooth'
        });
    }
}

/**
 * 检查元素是否在视口中
 */
function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// 导出全局函数到window对象
window.AmazonReplenishment.utils = {
    copyToClipboard,
    downloadData,
    formatFileSize,
    formatTimeDiff,
    debounce,
    throttle,
    deepClone,
    generateId,
    validateEmail,
    validateUrl,
    getUrlParameter,
    setUrlParameter,
    removeUrlParameter,
    scrollToTop,
    scrollToElement,
    isElementInViewport,
    showConfirmDialog,
    saveFormData,
    loadFormData,
    clearFormData
};

console.log('亚马逊补货建议系统 JavaScript 库加载完成');
