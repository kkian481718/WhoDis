# WhoDis - AI 驅動的本地網絡掃描器

WhoDis 是一個類似 GlassWire 的 Windows 應用程式，結合了網絡掃描與本地 AI 分析功能。

## ✅ 已實作功能

- **網絡掃描**: 使用 ARP 協定掃描區域網絡設備
- **設備識別**: 解析廠商名稱 (MAC Vendor)
- **Port 掃描**: 偵測裝置開放的服務埠（可選深度掃描）
- **主機名稱解析**: DNS 反查 + NetBIOS 查詢
- **掃描歷史**: SQLite 自動儲存掃描記錄
- **AI 安全分析**: 利用本地 Ollama 模型分析潛在風險
- **網頁介面**: FastAPI + HTML/JS 現代化 UI

## 安裝需求

### 1. 系統環境
- Windows 10/11
- Python 3.10+
- **Npcap**: 必須安裝 [Npcap](https://npcap.com/#download) (安裝時請勾選 "Install Npcap in WinPcap API-compatible Mode")

### 2. AI 模型 (Ollama)
請確保已安裝 [Ollama](https://ollama.com/) 並下載模型：
```bash
ollama run qwen3:8b
```
保持 Ollama 在背景運行 (API 監聽於 localhost:11434)。

### 3. Conda 環境
本專案使用 **Conda** 管理 Python 環境，環境名稱為 `whodis`。

```bash
# 建立環境 (首次使用)
conda create -n whodis python=3.10

# 啟用環境
conda activate whodis
```

### 4. Python 套件
```bash
pip install -r requirements.txt
pip install fastapi uvicorn
```

## 如何執行

**重要**: 由於需要發送原始網絡封包 (ARP)，必須以**系統管理員 (Administrator)** 身分執行終端機。

```bash
# 啟動 FastAPI 網頁伺服器
python src/app.py
```

瀏覽器會自動開啟 `http://localhost:8000`

## 專案結構

```
src/
├── app.py        # FastAPI 主程式
├── scanner.py    # 網路掃描模組（ARP + Port 掃描）
├── analyzer.py   # AI 分析模組
├── database.py   # SQLite 資料庫
└── static/       # 前端頁面
    ├── index.html
    ├── styles.css
    └── app.js
```

## 疑難排解
- **PermissionError**: 請確認是否已用管理員權限開啟終端機
- **Scapy 錯誤**: 確保已安裝 Npcap 並啟用了 WinPcap 兼容模式
- **Ollama 連接失敗**: 請確認 Ollama 服務正在運行 (`http://localhost:11434`)
