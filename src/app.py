"""
WhoDis - FastAPI 網頁版
網路裝置掃描與 AI 安全分析
"""

import asyncio
import json
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scanner import NetworkScanner
from analyzer import AIAnalyzer
from database import get_database

# 初始化
app = FastAPI(title="WhoDis", description="網路裝置掃描與 AI 安全分析")
scanner = NetworkScanner()
analyzer = AIAnalyzer(model="qwen3:8b")

# 靜態檔案
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")


class ScanRequest(BaseModel):
    deep_scan: bool = False


@app.get("/", response_class=HTMLResponse)
async def index():
    """首頁"""
    html_file = static_path / "index.html"
    if html_file.exists():
        return html_file.read_text(encoding="utf-8")
    return "<h1>WhoDis</h1><p>正在載入...</p>"


@app.post("/api/scan")
async def scan_network(request: ScanRequest):
    """執行網路掃描"""
    # 在背景執行掃描（避免阻塞）
    loop = asyncio.get_event_loop()
    devices = await loop.run_in_executor(
        None, lambda: scanner.scan(deep_scan=request.deep_scan)
    )
    
    # 儲存到資料庫
    if devices and not any("error" in d for d in devices):
        db = get_database()
        subnet = scanner.get_subnet(scanner.get_local_ip())
        db.save_scan(devices, subnet, deep_scan=request.deep_scan)
    
    return {"devices": devices}


@app.post("/api/analyze")
async def analyze_devices(request: Request):
    """AI 分析裝置"""
    data = await request.json()
    devices = data.get("devices", [])
    
    if not devices:
        return {"analysis": "沒有裝置可分析"}
    
    # 使用串流回應
    async def generate():
        for chunk in analyzer.analyze_network_stream(devices):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        yield "data: {\"done\": true}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/history")
async def get_history(limit: int = 20):
    """取得掃描歷史"""
    db = get_database()
    history = db.get_scan_history(limit)
    return {"history": history}


@app.get("/api/history/{scan_id}")
async def get_scan_details(scan_id: int):
    """取得特定掃描詳情"""
    db = get_database()
    details = db.get_scan_details(scan_id)
    if details:
        return details
    return {"error": "找不到該掃描記錄"}


if __name__ == "__main__":
    print("🚀 WhoDis 啟動中...")
    print("📍 開啟瀏覽器: http://localhost:8000")
    webbrowser.open("http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
