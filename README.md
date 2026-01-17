# WhoDis - AI 驅動的本地網絡掃描器

WhoDis 是一個類似 GlassWire 的 Windows 桌面應用程式，結合了網絡掃描與本地 AI 分析功能。

## 功能
- **網絡掃描**: 使用 ARP 協定掃描區域網絡設備。
- **設備識別**: 解析廠商名稱 (MAC Vendor)。
- **AI 安全分析**: 利用本地 Ollama 模型 (qwen2.5:3b) 分析潛在風險。
- **現代化介面**: 基於 Flet 的深色模式儀表板。

## 安裝需求

### 1. 系統環境
- Windows 10/11
- Python 3.10+
- **Npcap**: 必須安裝 [Npcap](https://npcap.com/#download) (安裝時請勾選 "Install Npcap in WinPcap API-compatible Mode")，這是 Scapy 在 Windows 上運作所必需的。

### 2. AI 模型 (Ollama)
請確保已安裝 [Ollama](https://ollama.com/) 並下載 `qwen2.5:3b` 模型：
```bash
ollama run qwen2.5:3b
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
在 `whodis` 環境啟用後，安裝所需套件：
```bash
pip install -r requirements.txt
```

## 如何執行

**重要**: 由於需要發送原始網絡封包 (ARP)，必須以**系統管理員 (Administrator)** 身分執行終端機。

```bash
# 在專案根目錄下
python src/main.py
```

## 疑難排解 Information
- **PermissionError**: 請確認是否已用管理員權限開啟終端機。
- **Scapy 錯誤**: 確保已安裝 Npcap 並啟用了 WinPcap 兼容模式。
- **Ollama 連接失敗**: 請確認 Ollama 服務正在運行 (`http://localhost:11434`)。
