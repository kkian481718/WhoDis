---
name: who_dis_network_scanner
description: AI 驅動的本地網絡掃描器與安全分析工具 (Local Network Scanner and AI Security Analyzer)
version: 1.0.0
os: windows
dependencies:
  - python>=3.10
  - npcap
  - oligama
---

# WhoDis Network Scanner Skill

是一個類似 GlassWire 的 Windows 桌面應用程式，結合了網絡掃描與本地 AI 分析功能。此 Skill 定義了如何與 WhoDis 應用程式互動以及其運作原理。

## 📂 專案結構 (Project Structure)

本 Skill 包含以下核心檔案，位於 `src/` 目錄中：

1.  **`src/scanner.py`**:
    *   負責使用 ARP 協定掃描區域網絡。
    *   嘗試解析 MAC Address 對應的廠商 (Vendor)。
    *   **注意**: 需要 Npcap 支援才能在 Windows 上運作。

2.  **`src/analyzer.py`**:
    *   介接本地 Ollama AI 模型 (`qwen2.5:3b`)。
    *   接收 `scanner.py` 的掃描結果，分析潛在的安全風險。
    *   提供繁體中文的風險評估報告。

3.  **`src/main.py`**:
    *   主程式入口。
    *   建立 Flet GUI 介面。
    *   顯示掃描按鈕、即時進度與 AI 分析結果。

4.  **`requirements.txt`**:
    *   專案依賴列表 (`flet`, `scapy`, `ollama` 等)。

## 🚀 安裝與設定 (Setup)

在使用此工具之前，請確保滿足以下條件：

### 1. 系統依賴
*   **Windows 10/11**
*   **Npcap**: 必須安裝 [Npcap](https://npcap.com/#download)，並在安裝時勾選 **"Install Npcap in WinPcap API-compatible Mode"**。

### 2. AI 模型設定
請確保 [Ollama](https://ollama.com/) 已安裝並正在執行：
```powershell
ollama pull qwen2.5:3b
ollama run qwen2.5:3b
# 請保持 Ollama 視窗在背景運行
```

### 3. Python 環境
```powershell
pip install -r requirements.txt
```

## 🛠️ 使用指令 (Usage)

由於 Scapy 涉及底層網絡封包操作，**必須以系統管理員身分 (Run as Administrator)** 執行。

### 啟動應用程式
```powershell
# 請確保終端機具有管理員權限
python src/main.py
```

## ⚠️ 疑難排解 (Troubleshooting)

*   **Scapy/Permission Error**: 如果遇到權限錯誤或無法發送封包，請確認是否已安裝 Npcap 並且是以管理員身分執行 Python。
*   **AI 無回應**: 檢查 Ollama 是否在 `http://localhost:11434` 正常運作。
