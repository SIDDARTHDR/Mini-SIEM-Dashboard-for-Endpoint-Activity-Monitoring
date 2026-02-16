# windows_agent.py
import socket
import time
import win32evtlog  # from pywin32
import win32con
import getpass

UDP_HOST = "127.0.0.1"
UDP_PORT = 514

def send(line: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    msg = f"<13>{time.strftime('%Y-%m-%dT%H:%M:%S')} localhost {line}"
    s.sendto(msg.encode(), (UDP_HOST, UDP_PORT))
    s.close()

def tail_security_log(server="localhost", log_type="Security"):
    hand = win32evtlog.OpenEventLog(server, log_type)
    flags = win32con.EVENTLOG_BACKWARDS_READ | win32con.EVENTLOG_SEQUENTIAL_READ
    offset_record = 0

    while True:
        events = win32evtlog.ReadEventLog(hand, flags, offset_record)
        if not events:
            time.sleep(1)
            continue

        for ev in reversed(events):  # oldest first
            try:
                eid = ev.EventID

                # Existing login logic (4624/4625) ...

                # New: file/folder access 4663
                if eid == 4663:
                    inserts = ev.StringInserts or []
                    # Typical indexes for 4663:
                    # 0=SubjectUserSid, 1=SubjectUserName, 6=ObjectName, 9=AccessMask/AccessList
                    user = inserts[1] if len(inserts) > 1 else "unknown"
                    path = inserts[6] if len(inserts) > 6 else "unknown"
                    access = inserts[9] if len(inserts) > 9 else "unknown"

                    # Simplify access (contains 'ReadData', 'WriteData', etc.)
                    action_type = "read" if "Read" in access else (
                        "write" if "Write" in access or "Append" in access else "access"
                    )

                    line = f"file user={user} path=\"{path}\" access={action_type} action=file_access status=success"
                    send(line)

            except Exception:
                pass

        time.sleep(2)

if __name__ == "__main__":
    tail_security_log()
