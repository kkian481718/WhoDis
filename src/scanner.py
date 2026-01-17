import logging
from scapy.all import ARP, Ether, srp, conf, get_if_list, get_if_addr
from mac_vendor_lookup import MacLookup
import socket
import os

# 設定 logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 預先初始化 MAC 查詢表（同步方式）
_mac_lookup = MacLookup()
try:
    _mac_lookup.update_vendors()  # 同步更新廠商資料庫
except Exception:
    pass  # 離線時忽略更新錯誤


def find_interface_for_network(target_subnet):
    """
    找到對應目標子網的網路介面
    例如：如果目標是 192.168.0.0/24，會找到 IP 為 192.168.0.x 的介面
    """
    target_prefix = ".".join(target_subnet.split("/")[0].split(".")[:3])  # e.g., "192.168.0"
    
    for iface in get_if_list():
        try:
            ip = get_if_addr(iface)
            if ip and ip.startswith(target_prefix):
                logger.info(f"Found matching interface: {iface} with IP {ip}")
                return iface
        except Exception:
            continue
    
    return None

class NetworkScanner:
    def __init__(self):
        pass  # 使用全域的 _mac_lookup

    def get_local_ip(self):
        """獲取本機 IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def get_subnet(self, ip):
        """簡單的子網掩碼計算，假設是 /24"""
        return ".".join(ip.split(".")[:3]) + ".0/24"

    def get_vendor(self, mac_address):
        """查詢 MAC 地址廠商（同步方式）"""
        try:
            return _mac_lookup.lookup(mac_address)
        except Exception:
            return "Unknown Vendor"

    def scan(self, target_ip=None):
        """
        掃描網路設備
        :param target_ip: 目標 IP 範圍 (例如 '192.168.1.0/24')
        :return: 設備列表 [{"ip": "...", "mac": "...", "vendor": "..."}, ...]
        """
        if not target_ip:
            local_ip = self.get_local_ip()
            target_ip = self.get_subnet(local_ip)
            logger.info(f"Auto-detected subnet: {target_ip}")

        logger.info(f"Scanning target: {target_ip}")
        
        # 構造 ARP 請求
        # Ether(dst="ff:ff:ff:ff:ff:ff") 表示廣播
        # ARP(pdst=target_ip) 表示查詢目標 IP
        arp = ARP(pdst=target_ip)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        try:
            # 找到正確的網路介面
            iface = find_interface_for_network(target_ip)
            if iface:
                logger.info(f"Using interface: {iface}")
            else:
                logger.warning(f"Could not find matching interface for {target_ip}, using default")
                iface = conf.iface
            
            # srp 發送並接收 Layer 2 數據包
            # timeout=3: 等待 3 秒 (增加 timeout 以確保收到回應)
            # verbose=0: 不顯示 Scapy 的輸出
            # iface: 明確指定網路介面
            result = srp(packet, timeout=3, verbose=0, iface=iface)[0]
        except PermissionError:
            logger.error("Permission denied. Please run as Administrator.")
            return [{"error": "Permission denied. Please run as Administrator."}]
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return [{"error": f"Scan failed: {str(e)}"}]

        devices = []
        for sent, received in result:
            # received.psrc 是 IP，received.hwsrc 是 MAC
            devices.append({
                "ip": received.psrc,
                "mac": received.hwsrc,
                "vendor": self.get_vendor(received.hwsrc)
            })

        logger.info(f"Found {len(devices)} devices.")
        return devices

if __name__ == "__main__":
    # 測試用
    scanner = NetworkScanner()
    print(scanner.scan())
