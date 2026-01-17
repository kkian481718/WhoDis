// WhoDis - 前端 JavaScript

const API_BASE = '';

// DOM 元素
const scanBtn = document.getElementById('scanBtn');
const deepScanCheckbox = document.getElementById('deepScan');
const statusEl = document.getElementById('status');
const progressBar = document.getElementById('progressBar');
const deviceList = document.getElementById('deviceList');
const analysisSection = document.getElementById('analysisSection');
const analysisContent = document.getElementById('analysisContent');

// 狀態
let isScanning = false;

// 掃描網路
async function scanNetwork() {
    if (isScanning) return;

    isScanning = true;
    scanBtn.disabled = true;
    const deepScan = deepScanCheckbox.checked;

    // 更新 UI
    statusEl.textContent = deepScan ? '深度掃描中...（可能需要較長時間）' : '掃描中...';
    progressBar.classList.remove('hidden');
    deviceList.innerHTML = '';
    analysisSection.classList.add('hidden');
    analysisContent.textContent = '';

    try {
        // 1. 執行掃描
        const response = await fetch(`${API_BASE}/api/scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ deep_scan: deepScan })
        });

        const data = await response.json();
        const devices = data.devices || [];

        // 2. 顯示裝置
        progressBar.classList.add('hidden');
        renderDevices(devices);
        statusEl.textContent = `✓ 發現 ${devices.length} 個裝置`;

        // 3. AI 分析（如果有裝置且沒有錯誤）
        if (devices.length > 0 && !devices.some(d => d.error)) {
            statusEl.textContent = `✓ 發現 ${devices.length} 個裝置，AI 分析中...`;
            await analyzeDevices(devices);
            statusEl.textContent = `完成 · ${devices.length} 個裝置`;
        }

    } catch (error) {
        console.error('Scan error:', error);
        statusEl.textContent = `錯誤: ${error.message}`;
        progressBar.classList.add('hidden');
    } finally {
        isScanning = false;
        scanBtn.disabled = false;
    }
}

// 渲染裝置列表
function renderDevices(devices) {
    if (!devices.length) {
        deviceList.innerHTML = '<p class="empty-state">未發現任何裝置</p>';
        return;
    }

    deviceList.innerHTML = devices.map(device => {
        if (device.error) {
            return `
                <div class="device-card error-card">
                    <div class="device-icon">⚠️</div>
                    <div class="device-info">
                        <div class="device-name">錯誤</div>
                        <div class="device-subtitle">${device.error}</div>
                    </div>
                </div>
            `;
        }

        const icon = getDeviceIcon(device.vendor || '');
        const hostname = device.hostname;
        const displayName = hostname || device.ip;
        const subtitle = hostname
            ? `${device.ip} · ${device.vendor || '未知裝置'}`
            : device.vendor || '未知裝置';

        const ports = device.ports || [];
        const portsHtml = ports.length > 0
            ? `<div class="device-ports">${ports.slice(0, 4).map(p =>
                `<span class="port-tag">${p.service}</span>`
            ).join('')}${ports.length > 4 ? `<span class="port-tag">+${ports.length - 4}</span>` : ''}</div>`
            : '';

        return `
            <div class="device-card">
                <div class="device-icon">${icon}</div>
                <div class="device-info">
                    <div class="device-name">${displayName}</div>
                    <div class="device-subtitle">${subtitle}</div>
                    ${portsHtml}
                </div>
                <div class="device-mac">${device.mac || ''}</div>
            </div>
        `;
    }).join('');
}

// 根據廠商取得圖示
function getDeviceIcon(vendor) {
    const v = vendor.toLowerCase();
    if (v.includes('apple')) return '🍎';
    if (v.includes('intel') || v.includes('msi') || v.includes('asus') || v.includes('gigabyte')) return '💻';
    if (v.includes('cisco') || v.includes('gateway') || v.includes('tp-link') || v.includes('d-link') || v.includes('router')) return '📶';
    if (v.includes('google')) return '📱';
    if (v.includes('samsung')) return '📱';
    return '📟';
}

// AI 分析
async function analyzeDevices(devices) {
    analysisSection.classList.remove('hidden');
    analysisContent.textContent = '分析中...';

    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ devices })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let text = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.response) {
                            text += data.response;
                            analysisContent.textContent = text;
                        }
                        if (data.done) break;
                    } catch (e) {
                        // 忽略解析錯誤
                    }
                }
            }
        }

    } catch (error) {
        console.error('Analysis error:', error);
        analysisContent.textContent = `分析失敗: ${error.message}`;
    }
}

// 事件綁定
scanBtn.addEventListener('click', scanNetwork);
