import flet as ft
from scanner import NetworkScanner
from analyzer import AIAnalyzer
from database import get_database
import threading

def main(page: ft.Page):
    # ============================
    # 簡約風格設定
    # ============================
    page.title = "WhoDis"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#FAFAFA"
    page.padding = 40
    page.window_width = 900
    page.window_height = 700
    page.fonts = {"Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"}
    page.theme = ft.Theme(font_family="Inter")

    # 初始化模組
    scanner = NetworkScanner()
    analyzer = AIAnalyzer(model="qwen3:8b")

    # UI 狀態
    scan_results = []

    # ============================
    # 簡約標題
    # ============================
    header = ft.Container(
        content=ft.Column([
            ft.Text("WhoDis", size=28, weight=ft.FontWeight.W_700, color="#1A1A1A"),
            ft.Text("網路裝置掃描與 AI 安全分析", size=13, color="#888888"),
        ], spacing=4),
        margin=ft.Margin(0, 0, 0, 24),
    )

    # 狀態文字
    status_text = ft.Text("點擊按鈕開始掃描", color="#666666", size=13)
    progress_bar = ft.ProgressBar(width=200, color="#333333", bgcolor="#E0E0E0", visible=False)
    
    # AI 分析計時器
    ai_timer_text = ft.Text("", color="#888888", size=12, visible=False)

    # 深度掃描開關
    deep_scan_switch = ft.Switch(value=False, active_color="#1A1A1A")
    deep_scan_row = ft.Row([
        deep_scan_switch,
        ft.Text("深度掃描", size=13, color="#666666"),
        ft.Icon("help_outline", size=16, color="#AAAAAA", tooltip="偵測裝置開放的服務埠，需要較長時間"),
    ], spacing=8)

    # 設備列表
    devices_column = ft.Column(spacing=8)

    # 分析結果區域
    analysis_content = ft.Markdown(
        "",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        on_tap_link=lambda e: page.launch_url(e.data),
    )
    
    # AI 思考過程顯示區
    thinking_content = ft.Text("", color="#888888", size=12, italic=True)
    thinking_section = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.ProgressRing(width=16, height=16, stroke_width=2, color="#666666"),
                ft.Container(width=8),
                ft.Text("AI 正在思考中...", size=12, color="#666666", italic=True),
            ]),
            ft.Container(height=8),
            thinking_content,
        ]),
        bgcolor="#F9F9F9",
        padding=16,
        border_radius=8,
        border=ft.Border.all(1, "#E5E5E5"),
        visible=False,
    )

    analysis_section = ft.Container(
        content=ft.Column([
            ft.Text("AI 分析報告", size=14, weight=ft.FontWeight.W_600, color="#1A1A1A"),
            ft.Container(height=8),
            analysis_content,
        ], scroll=ft.ScrollMode.AUTO),
        bgcolor="#FFFFFF",
        padding=20,
        border_radius=8,
        border=ft.Border.all(1, "#E5E5E5"),
        visible=False,
    )

    def create_device_card(device):
        """簡約風格的設備卡片"""
        # 根據廠商決定圖示
        icon_name = "devices"
        vendor_lower = device.get('vendor', '').lower()
        
        if "apple" in vendor_lower:
            icon_name = "phone_iphone"
        elif any(x in vendor_lower for x in ["intel", "msi", "asus", "gigabyte"]):
            icon_name = "computer"
        elif any(x in vendor_lower for x in ["cisco", "gateway", "tp-link", "d-link"]):
            icon_name = "router"
        elif "google" in vendor_lower:
            icon_name = "android"

        # 主機名稱顯示
        hostname = device.get('hostname')
        display_name = hostname if hostname else device.get('ip', 'Unknown')
        subtitle = device.get('vendor', '未知裝置')
        if hostname:
            subtitle = f"{device.get('ip', '')} · {subtitle}"
        
        # Port 資訊
        ports = device.get('ports', [])
        ports_text = ""
        if ports:
            port_names = [f"{p['service']}" for p in ports[:4]]  # 最多顯示 4 個
            if len(ports) > 4:
                port_names.append(f"+{len(ports) - 4}")
            ports_text = " · ".join(port_names)

        # 建立卡片內容
        info_column = ft.Column([
            ft.Text(
                display_name,
                size=14,
                weight=ft.FontWeight.W_500,
                color="#1A1A1A"
            ),
            ft.Text(
                subtitle,
                size=12,
                color="#888888",
            ),
        ], spacing=2, expand=True)
        
        # 如果有 Port 資訊，加入顯示
        if ports_text:
            info_column.controls.append(
                ft.Container(
                    content=ft.Text(ports_text, size=11, color="#666666"),
                    bgcolor="#F0F0F0",
                    padding=ft.Padding(8, 4, 8, 4),
                    border_radius=4,
                    margin=ft.Margin(0, 4, 0, 0),
                )
            )

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon_name, size=20, color="#666666"),
                    width=40,
                    height=40,
                    bgcolor="#F5F5F5",
                    border_radius=8,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(width=12),
                info_column,
                ft.Text(
                    device.get('mac', ''),
                    size=11,
                    color="#AAAAAA",
                    font_family="monospace",
                ),
            ], alignment=ft.MainAxisAlignment.START),
            padding=16,
            bgcolor="#FFFFFF",
            border_radius=8,
            border=ft.Border.all(1, "#E5E5E5"),
        )

    def update_device_list(devices):
        devices_column.controls.clear()
        
        if not devices:
            devices_column.controls.append(
                ft.Container(
                    content=ft.Text("未發現任何裝置", color="#888888", size=13),
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            for d in devices:
                if "error" in d:
                    devices_column.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon("error_outline", color="#D32F2F", size=18),
                                ft.Container(width=8),
                                ft.Text(d['error'], color="#D32F2F", size=13)
                            ]),
                            padding=16,
                            bgcolor="#FFEBEE",
                            border_radius=8,
                        )
                    )
                else:
                    devices_column.controls.append(create_device_card(d))
        
        page.update()

    def run_scan_and_analyze(e):
        import time
        
        scan_btn.disabled = True
        status_text.value = "掃描中..."
        progress_bar.visible = True
        analysis_section.visible = False
        thinking_section.visible = False
        thinking_content.value = ""
        analysis_content.value = ""
        ai_timer_text.visible = False
        devices_column.controls.clear()
        page.update()

        def task():
            nonlocal scan_results
            try:
                # 取得深度掃描設定
                is_deep_scan = deep_scan_switch.value
                
                if is_deep_scan:
                    status_text.value = "深度掃描中...（可能需要較長時間）"
                    page.update()
                
                # 1. 掃描（含深度掃描選項）
                scan_results = scanner.scan(deep_scan=is_deep_scan)
                update_device_list(scan_results)
                progress_bar.visible = False
                
                # 儲存到資料庫
                if scan_results and not any("error" in d for d in scan_results):
                    db = get_database()
                    subnet = scanner.get_subnet(scanner.get_local_ip())
                    db.save_scan(scan_results, subnet, deep_scan=is_deep_scan)
                
                # 先顯示掃描結果，讓使用者看到發現了多少裝置
                device_count = len(scan_results)
                status_text.value = f"✓ 發現 {device_count} 個裝置，AI 分析中..."
                page.update()

                # 2. AI 分析 (串流模式)
                if scan_results and not any("error" in d for d in scan_results):
                    thinking_section.visible = True
                    analysis_section.visible = True
                    ai_timer_text.visible = True
                    ai_timer_text.value = "已等待 0 秒"
                    page.update()
                    
                    start_time = time.time()
                    accumulated_text = ""
                    
                    def update_timer():
                        """定時更新計時器"""
                        while thinking_section.visible:
                            elapsed = int(time.time() - start_time)
                            ai_timer_text.value = f"已等待 {elapsed} 秒"
                            try:
                                page.update()
                            except:
                                break
                            time.sleep(1)
                    
                    # 啟動計時器線程
                    import threading as th
                    timer_thread = th.Thread(target=update_timer, daemon=True)
                    timer_thread.start()
                    
                    # 使用串流模式獲取 AI 回應
                    for chunk in analyzer.analyze_network_stream(scan_results):
                        if chunk.get("thinking"):
                            # 顯示思考過程
                            thinking_content.value = chunk["thinking"]
                            page.update()
                        elif chunk.get("response"):
                            # 累積並顯示回應
                            accumulated_text += chunk["response"]
                            analysis_content.value = accumulated_text
                            page.update()
                    
                    # 完成後隱藏思考區
                    thinking_section.visible = False
                    ai_timer_text.visible = False
                    page.update()
                
                status_text.value = f"完成 · {len(scan_results)} 個裝置"
            except Exception as ex:
                status_text.value = f"錯誤: {str(ex)}"
                thinking_section.visible = False
            finally:
                progress_bar.visible = False
                ai_timer_text.visible = False
                scan_btn.disabled = False
                page.update()

        threading.Thread(target=task, daemon=True).start()

    # 簡約按鈕
    scan_btn = ft.FilledButton(
        "掃描網路",
        icon="search",
        on_click=run_scan_and_analyze,
        style=ft.ButtonStyle(
            color="#FFFFFF",
            bgcolor={"": "#1A1A1A", "hovered": "#333333"},
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding(24, 14, 24, 14),
            elevation=0,
        ),
    )

    # ============================
    # 主要版面
    # ============================
    main_content = ft.Column(
        [
            header,
            # 按鈕、深度掃描開關、進度條、狀態放同一行
            ft.Row(
                [
                    scan_btn, 
                    ft.Container(width=20), 
                    deep_scan_row,
                    ft.Container(width=20), 
                    progress_bar,
                    ft.Container(width=16),
                    status_text,
                    ft.Container(width=8),
                    ai_timer_text,
                ], 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            ft.Container(height=16),
            # AI 分析區 (在裝置列表上方)
            thinking_section,
            analysis_section,
            ft.Container(height=16),
            # 裝置列表
            ft.Text("裝置列表", size=14, weight=ft.FontWeight.W_600, color="#1A1A1A"),
            ft.Container(height=8),
            devices_column,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=0,
    )

    page.add(main_content)

if __name__ == "__main__":
    ft.app(target=main)
