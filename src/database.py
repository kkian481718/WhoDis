import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 資料庫檔案路徑
DB_PATH = Path(__file__).parent / "whodis.db"


class Database:
    """SQLite 資料庫管理類別，用於儲存掃描歷史"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()
    
    def _init_db(self):
        """初始化資料庫結構"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 掃描記錄表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    device_count INTEGER,
                    subnet TEXT,
                    deep_scan INTEGER DEFAULT 0
                )
            """)
            
            # 裝置記錄表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER,
                    ip TEXT,
                    mac TEXT,
                    vendor TEXT,
                    hostname TEXT,
                    open_ports TEXT,
                    FOREIGN KEY (scan_id) REFERENCES scans(id)
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def save_scan(self, devices, subnet, deep_scan=False):
        """
        儲存掃描結果
        :param devices: 裝置列表
        :param subnet: 掃描的子網
        :param deep_scan: 是否為深度掃描
        :return: 掃描記錄 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入掃描記錄
            cursor.execute("""
                INSERT INTO scans (device_count, subnet, deep_scan)
                VALUES (?, ?, ?)
            """, (len(devices), subnet, 1 if deep_scan else 0))
            
            scan_id = cursor.lastrowid
            
            # 插入裝置記錄
            for device in devices:
                if "error" in device:
                    continue
                    
                ports_json = json.dumps(device.get("ports", []))
                cursor.execute("""
                    INSERT INTO devices (scan_id, ip, mac, vendor, hostname, open_ports)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    scan_id,
                    device.get("ip"),
                    device.get("mac"),
                    device.get("vendor"),
                    device.get("hostname"),
                    ports_json
                ))
            
            conn.commit()
            logger.info(f"Saved scan #{scan_id} with {len(devices)} devices")
            return scan_id
    
    def get_scan_history(self, limit=20):
        """
        取得掃描歷史記錄
        :param limit: 最多回傳幾筆
        :return: 掃描記錄列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, scan_time, device_count, subnet, deep_scan
                FROM scans
                ORDER BY scan_time DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_scan_details(self, scan_id):
        """
        取得特定掃描的詳細資訊
        :param scan_id: 掃描記錄 ID
        :return: 掃描資訊與裝置列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 取得掃描資訊
            cursor.execute("""
                SELECT id, scan_time, device_count, subnet, deep_scan
                FROM scans WHERE id = ?
            """, (scan_id,))
            scan_row = cursor.fetchone()
            
            if not scan_row:
                return None
            
            scan_info = dict(scan_row)
            
            # 取得裝置列表
            cursor.execute("""
                SELECT ip, mac, vendor, hostname, open_ports
                FROM devices WHERE scan_id = ?
            """, (scan_id,))
            
            devices = []
            for row in cursor.fetchall():
                device = dict(row)
                device["ports"] = json.loads(device.pop("open_ports") or "[]")
                devices.append(device)
            
            scan_info["devices"] = devices
            return scan_info
    
    def delete_scan(self, scan_id):
        """刪除掃描記錄"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM devices WHERE scan_id = ?", (scan_id,))
            cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            conn.commit()
            logger.info(f"Deleted scan #{scan_id}")


# 全域資料庫實例
_db = None

def get_database():
    """取得全域資料庫實例"""
    global _db
    if _db is None:
        _db = Database()
    return _db


if __name__ == "__main__":
    # 測試用
    db = Database()
    
    # 模擬掃描結果
    fake_devices = [
        {"ip": "192.168.1.1", "mac": "AA:BB:CC:DD:EE:01", "vendor": "Cisco", "hostname": "router", "ports": [{"port": 80, "service": "HTTP"}]},
        {"ip": "192.168.1.10", "mac": "AA:BB:CC:DD:EE:02", "vendor": "Apple", "hostname": None, "ports": []},
    ]
    
    scan_id = db.save_scan(fake_devices, "192.168.1.0/24", deep_scan=True)
    print(f"Saved scan: {scan_id}")
    
    history = db.get_scan_history()
    print(f"History: {history}")
    
    details = db.get_scan_details(scan_id)
    print(f"Details: {details}")
