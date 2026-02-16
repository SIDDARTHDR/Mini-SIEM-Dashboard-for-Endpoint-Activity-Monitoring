# chrome_agent.py
"""
Chrome History Agent: Reads Chrome browsing history and sends normalized events to SIEM ingester.
Maps Chrome visits into: action=browse, user=<windows_user>, url=<visited_url>
"""

import socket
import sqlite3
import time
import shutil
import os
import getpass
from pathlib import Path
from datetime import datetime

UDP_HOST = "127.0.0.1"
UDP_PORT = 514
DEVICE_NAME = "LAPTOP-ASUS"

def get_chrome_history_path():
    """Find Chrome History DB for current user."""
    username = getpass.getuser()
    chrome_path = Path(f"C:/Users/{username}/AppData/Local/Google/Chrome/User Data/Default/History")
    if chrome_path.exists():
        return str(chrome_path)
    return None

def copy_chrome_history(src):
    """Copy Chrome History (Chrome locks the live DB, so we copy first)."""
    dst = "chrome_history_copy.db"
    try:
        shutil.copy2(src, dst)
        return dst
    except Exception as e:
        print(f"[CHROME] Error copying History: {e}")
        return None

def send_event(line: str):
    """Send a syslog‑style line via UDP to ingester."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        msg = f"<13>{timestamp} localhost {line}"
        s.sendto(msg.encode(), (UDP_HOST, UDP_PORT))
        s.close()
        print(f"[CHROME] Sent: {line[:80]}...")
    except Exception as e:
        print(f"[CHROME] Error sending event: {e}")

def read_chrome_visits(db_path, last_seen_time=0):
    visits = []
    max_time = last_seen_time

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            v.visit_time,
            u.url,
            u.title
        FROM visits v
        JOIN urls u ON v.url = u.id
        WHERE v.visit_time > ?
        ORDER BY v.visit_time ASC
    """, (last_seen_time,))

    for row in cur.fetchall():
        vt = row["visit_time"]
        if vt > max_time:
            max_time = vt

        visits.append({
            "visit_time": vt,
            "url": row["url"],
            "title": row["title"]
        })

    conn.close()
    return visits, max_time


def chrome_monitor_loop():
    """Main loop: periodically read Chrome History and send new visits."""
    chrome_path = get_chrome_history_path()
    
    if not chrome_path:
        print("[CHROME] Chrome History not found. Is Chrome installed?")
        return
    
    print(f"[CHROME] Found Chrome History at: {chrome_path}")
    
    last_seen_time = 0
    check_interval = 1  # seconds
    
    while True:
        try:
            # Copy the locked History DB
            copy_path = copy_chrome_history(chrome_path)
            if not copy_path:
                time.sleep(check_interval)
                continue
            
            # Read new visits
            visits, last_seen_time = read_chrome_visits(copy_path, last_seen_time)
            
            # Send each as a normalized event
            username = getpass.getuser()
            for visit in visits:
                url = visit['url']
                title = visit['title']
                
                # Build normalized log line
                line = f"chrome host={DEVICE_NAME} user={username} url={url} title={title} action=browse status=success"
                send_event(line)
            
            # Clean up copy
            try:
                os.remove(copy_path)
            except:
                pass
            
            time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\n[CHROME] Agent stopped.")
            break
        except Exception as e:
            print(f"[CHROME] Error in loop: {e}")
            time.sleep(check_interval)

if __name__ == "__main__":
    print("[CHROME] Chrome History Agent starting...")
    chrome_monitor_loop()
