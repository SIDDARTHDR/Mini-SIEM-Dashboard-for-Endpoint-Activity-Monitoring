'''

# ingester.py - CORRECTED VERSION
import socket
import sqlite3
import json
import re
from datetime import datetime

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 514
DB_PATH = "logs.db"

# Updated regex to handle chrome, auth, security, windows events
LOG_RE = re.compile(
    r'(?:chrome|auth|security|windows)\s+'
    r'(?:user=(\S+)\s+)?'
    r'(?:url=(\S+)\s+)?'
    r'(?:title=(.+?)\s+)?'
    r'(?:ip=([\d.]+|-)\s+)?'
    r'(?:action=(\S+)\s+)?'
    r'(?:status=(\S+))?'
)

def parse_log(line: str):
    """Parse syslog line into structured dict."""
    match = LOG_RE.search(line)
    if not match:
        print(f"[PARSE] No match for: {line[:60]}")
        return None
    
    user, url, title, ip, action, status = match.groups()
    
    # Extract timestamp from syslog header
    timestamp = datetime.now().isoformat()
    try:
        if '<' in line and 'localhost' in line:
            # Format: <13>2026-02-03T17:05:01 localhost ...
            parts = line.split('localhost')
            if len(parts) > 0:
                ts_part = parts[0].split('<')[1].split('>')[1].strip()
                if ts_part:
                    timestamp = ts_part
    except:
        pass
    
    data = {
        'timestamp': timestamp,
        'host': '127.0.0.1',
        'user': user or 'unknown',
        'action': action or 'unknown',
        'status': status or 'unknown',
        'ip': ip or '-',
        'url': url,
        'title': title,
        'raw': line
    }
    
    print(f"[INGEST] {data}")
    return data

def insert_log(data: dict):
    """Insert parsed log into database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO logs (timestamp, host, user, action, status, ip, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data['timestamp'],
        data['host'],
        data['user'],
        data['action'],
        data['status'],
        data['ip'],
        json.dumps({
            'url': data.get('url'),
            'title': data.get('title'),
            'raw': data.get('raw')
        })
    ))
    conn.commit()
    conn.close()

def listen():
    """Listen for syslog messages on UDP 514."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_HOST, LISTEN_PORT))
    print(f"[INGESTER] Listening on {LISTEN_HOST}:{LISTEN_PORT}")
    
    while True:
        data, addr = sock.recvfrom(2048)
        line = data.decode('utf-8', errors='ignore').strip()
        
        parsed = parse_log(line)
        if parsed:
            insert_log(parsed)

if __name__ == "__main__":
    listen()
'''

# ingester.py - FINAL FIXED VERSION
import socket
import json
import sqlite3
import re
from datetime import datetime

DB_PATH = "logs.db"
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 514

'''# Regex that matches: user=X action=Y status=Z url=... title=...
# Order doesn't matter because we use named groups
LOG_RE = re.compile(
    r'user=(\S+)'
    r'.*?'
    r'(?:url=(\S+))?'
    r'.*?'
    r'(?:title=([^|]*?))?'
    r'.*?'
    r'action=(\S+)'
    r'.*?'
    r'status=(\S+)'
    r'(?:\s+ip=(\S+))?'
)'''
'''
# ingester.py
LOG_RE = re.compile(
    r"user=(?P<user>\S+)"
    r"(?:\s+url=(?P<url>\S+))?"
    r"(?:\s+title=(?P<title>.*?))?"
    r"(?:\s+ip=(?P<ip>\S+))?"
    r"(?:\s+action=(?P<action>\S+))?"
    r"(?:\s+status=(?P<status>\S+))?"
)


def parse_log_line(line: str) -> dict | None:
    """Parse a syslog line into structured dict."""
    # Default timestamp
    timestamp = datetime.now().isoformat()

    # Try to extract timestamp from syslog prefix: "<13>2026-02-04T09:44:43 localhost ..."
    try:
        if "localhost" in line:
            parts = line.split("localhost", 1)
            ts_str = parts[0].split(">", 1)[-1].strip()
            if ts_str:
                timestamp = ts_str
    except Exception:
        pass

    m = LOG_RE.search(line)
    if not m:
        return None

    user   = m.group("user")   or "unknown"
    url    = m.group("url")
    title  = (m.group("title") or "").strip() or None
    ip     = m.group("ip")     or "-"
    action = m.group("action") or "unknown"
    status = m.group("status") or "unknown"

    return {
        "timestamp": timestamp,
        "host":      "127.0.0.1",
        "user":      user,
        "action":    action,
        "status":    status,
        "ip":        ip,
        "url":       url,
        "title":     title,
        "raw":       line,
    }
'''
FIELD_RE = re.compile(r'(\w+)=(".*?"|\S+)')

def parse_log_line(line: str):
    timestamp = datetime.now().isoformat()
    if "localhost" in line:
        try:
            ts = line.split(">",1)[1].split("localhost",1)[0].strip()
            timestamp = ts
        except:
            pass

    fields = dict(FIELD_RE.findall(line))

    return {
        "timestamp": timestamp,
        "host": fields.get("host","unknown"),
        "user": fields.get("user","unknown"),
        "action": fields.get("action","unknown"),
        "status": fields.get("status","unknown"),
        "ip": fields.get("ip","-"),
        "url": fields.get("url"),
        "title": fields.get("title"),
        "raw": line,
    }


def insert_log(data: dict):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.execute(
            """
            INSERT INTO logs (timestamp, host, user, action, status, ip, rawjson)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["timestamp"],
                data["host"],
                data["user"],
                data["action"],
                data["status"],
                data["ip"],
                json.dumps({
                    "url": data.get("url"),
                    "title": data.get("title"),
                    "raw": data.get("raw"),
                }),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("[INGEST] DB Error:", e)


def main():
    """Listen for syslog messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_HOST, LISTEN_PORT))
    print(f"[INGESTER] Listening on {LISTEN_HOST}:{LISTEN_PORT}")
    
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            line = data.decode('utf-8', errors='ignore').strip()
            
            parsed = parse_log_line(line)
            if parsed:
                insert_log(parsed)
            else:
                print(f"[INGEST] Parse failed: {line[:70]}")
        except Exception as e:
            print(f"[INGESTER] Error: {e}")

if __name__ == "__main__":
    main()
