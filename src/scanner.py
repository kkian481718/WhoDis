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
    # 常見 Port 對應服務名稱
    PORT_SERVICES = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        139: "NetBIOS",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        993: "IMAPS",
        995: "POP3S",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        8080: "HTTP-Proxy",
        8443: "HTTPS-Alt",
    }
    
    # 預設掃描的 Port 列表
    DEFAULT_PORTS = [22, 80, 443, 445, 3389, 8080]
    
    def __init__(self):
        pass  # 使用全域的 _mac_lookup

    def get_service_name(self, port):
        """取得 Port 對應的服務名稱"""
        return self.PORT_SERVICES.get(port, f"Port-{port}")

    def port_scan(self, ip, ports=None, timeout=0.5):
        """
        TCP Connect 掃描指定 IP 的埠
        :param ip: 目標 IP
        :param ports: 要掃描的埠列表，預設為 DEFAULT_PORTS
        :param timeout: 連線超時秒數
        :return: 開放的埠列表 [{"port": 80, "service": "HTTP"}, ...]
        """
        if ports is None:
            ports = self.DEFAULT_PORTS
        
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append({
                        "port": port,
                        "service": self.get_service_name(port)
                    })
                sock.close()
            except Exception:
                pass
        return open_ports

    def get_hostname(self, ip):
        """
        取得 IP 對應的主機名稱
        優先使用 DNS 反向查詢，失敗則嘗試 NetBIOS（僅 Windows）
        :param ip: 目標 IP
        :return: 主機名稱或 None
        """
        # 1. DNS 反向查詢
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            if hostname and hostname != ip:
                return hostname
        except (socket.herror, socket.gaierror):
            pass
        
        # 2. NetBIOS 查詢（僅 Windows）
        if os.name == 'nt':
            try:
                import subprocess
                result = subprocess.run(
                    ['nbtstat', '-A', ip],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                # 解析 nbtstat 輸出找到主機名稱
                for line in result.stdout.split('\n'):
                    if '<00>' in line and 'UNIQUE' in line:
                        parts = line.split()
                        if parts:
                            return parts[0].strip()
            except Exception:
                pass
        
        return None

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

    def scan(self, target_ip=None, deep_scan=False):
        """
        掃描網路設備
        :param target_ip: 目標 IP 範圍 (例如 '192.168.1.0/24')
        :param deep_scan: 是否執行深度掃描（Port 掃描），會花較長時間
        :return: 設備列表 [{"ip": "...", "mac": "...", "vendor": "...", "hostname": "...", "ports": [...]}, ...]
        """
        if not target_ip:
            local_ip = self.get_local_ip()
            target_ip = self.get_subnet(local_ip)
            logger.info(f"Auto-detected subnet: {target_ip}")

        logger.info(f"Scanning target: {target_ip}, deep_scan={deep_scan}")
        
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
            ip = received.psrc
            mac = received.hwsrc
            
            device = {
                "ip": ip,
                "mac": mac,
                "vendor": self.get_vendor(mac),
                "hostname": self.get_hostname(ip),
                "ports": []
            }
            
            # 深度掃描：Port 掃描
            if deep_scan:
                logger.info(f"Port scanning {ip}...")
                device["ports"] = self.port_scan(ip)
            
            devices.append(device)

        logger.info(f"Found {len(devices)} devices.")
        return devices

if __name__ == "__main__":
    # 測試用
    scanner = NetworkScanner()
    print(scanner.scan())
