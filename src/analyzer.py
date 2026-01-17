import requests
import json
import logging

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self, model="qwen2.5:3b", host="http://localhost:11434"):
        self.model = model
        self.host = host
        self.api_url = f"{host}/api/generate"

    def analyze_network(self, device_list):
        """
        發送設備列表給 Ollama 進行分析
        :param device_list: List of dictionaries containing device info
        :return: String (Analysis result)
        """
        if not device_list:
            return "No devices found to analyze."
        
        # 檢查是否有錯誤訊息 (例如權限不足)
        if "error" in device_list[0]:
            return f"Cannot analyze due to scanner error: {device_list[0]['error']}"

        # 有效化設備列表，移除不需要的欄位 (目前結構已經很簡潔)
        # 用 JSON 字串格式化列表
        devices_str = json.dumps(device_list, indent=2)

        prompt = f"""
You are a network security expert. Analyze the following list of devices discovered on a local network.
Briefly point out any suspicious devices, unknown vendors, or potential security risks.
Highlight normal infrastructure devices (routers, gateways) vs user devices.

Device List:
{devices_str}

Please provide a concise summary in Traditional Chinese.
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            logger.info(f"Sending request to Ollama ({self.model})...")
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            analysis = result.get("response", "No response from model.")
            return analysis

        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Please ensure Ollama is running (localhost:11434)."
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model may be processing a complex request."
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return f"Error during analysis: {str(e)}"

    def analyze_network_stream(self, device_list):
        """
        串流版本：逐步回傳 AI 分析結果，改善使用者體驗
        :param device_list: List of dictionaries containing device info
        :yields: Dict with 'thinking' or 'response' keys
        """
        if not device_list:
            yield {"response": "No devices found to analyze."}
            return
        
        if "error" in device_list[0]:
            yield {"response": f"Cannot analyze due to scanner error: {device_list[0]['error']}"}
            return

        devices_str = json.dumps(device_list, indent=2)

        prompt = f"""
You are a network security expert. Analyze the following list of devices discovered on a local network.
Briefly point out any suspicious devices, unknown vendors, or potential security risks.
Highlight normal infrastructure devices (routers, gateways) vs user devices.

Device List:
{devices_str}

Please provide a concise summary in Traditional Chinese.
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True  # 啟用串流模式
        }

        try:
            logger.info(f"Sending streaming request to Ollama ({self.model})...")
            
            # 先 yield 一個思考中的訊息
            yield {"thinking": "正在分析網路裝置清單..."}
            
            response = requests.post(self.api_url, json=payload, stream=True, timeout=180)
            response.raise_for_status()
            
            thinking_shown = False
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        
                        # 檢查是否有思考過程 (某些模型會提供)
                        if chunk.get("context") and not thinking_shown:
                            yield {"thinking": "模型正在推理中..."}
                            thinking_shown = True
                        
                        # 回傳實際的回應內容
                        if chunk.get("response"):
                            yield {"response": chunk["response"]}
                        
                        # 檢查是否完成
                        if chunk.get("done"):
                            break
                            
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.ConnectionError:
            yield {"response": "Error: Could not connect to Ollama. Please ensure Ollama is running (localhost:11434)."}
        except requests.exceptions.Timeout:
            yield {"response": "Error: Request timed out. The model may be processing a complex request."}
        except Exception as e:
            logger.error(f"Streaming analysis failed: {e}")
            yield {"response": f"Error during analysis: {str(e)}"}

if __name__ == "__main__":
    # 測試用
    analyzer = AIAnalyzer()
    fake_devices = [
        {"ip": "192.168.1.1", "mac": "AA:BB:CC:DD:EE:01", "vendor": "Cisco Systems"},
        {"ip": "192.168.1.10", "mac": "AA:BB:CC:DD:EE:02", "vendor": "Apple, Inc."},
        {"ip": "192.168.1.20", "mac": "AA:BB:CC:DD:EE:03", "vendor": "Unknown Vendor"},
    ]
    print(analyzer.analyze_network(fake_devices))
