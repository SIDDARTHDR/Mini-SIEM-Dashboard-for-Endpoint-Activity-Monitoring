import sqlite3
from datetime import datetime, timedelta
import time
import json
from threat_db import SUSPICIOUS_DOMAINS
from urllib.parse import urlparse


DB_PATH = "logs.db"

def insert_alert(conn, rule, severity, ip=None, user=None, host=None, details=None):
    conn.execute(
        """
        INSERT INTO alerts (time, rule, severity, ip, user, host, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(timespec="seconds"),
            rule,
            severity,
            ip,
            user,
            host,
            details,
        ),
    )
    conn.commit()

def check_malicious_sites(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, host, user, rawjson
        FROM logs
        WHERE action='browse'
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    rows = cur.fetchall()

    for ts, host, user, rawjson in rows:
        if not rawjson:
            continue

        try:
            data = json.loads(rawjson)
            url = data.get("url")
            if not url:
                continue

            domain = urlparse(url).netloc.lower()
            print("[DEBUG] Checking domain:", domain)

            for bad, reason in SUSPICIOUS_DOMAINS.items():
                if bad in domain:
                    print("[ALERT] Match:", domain, reason)
                    insert_alert(
                        conn,
                        rule="Malicious website visited",
                        severity="high",
                        user=user,
                        host=host,
                        details=f"{domain} flagged: {reason}",
                    )
        except Exception as e:
            print("[RULE ERROR]", e)


def check_brute_force(conn, window_min=5, threshold=5):
    # multiple fails followed by success from same IP (T1110)
    window_start = (datetime.utcnow() - timedelta(minutes=window_min)).isoformat()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ip
        FROM logs
        WHERE timestamp >= ? AND action='login' AND status='fail' AND ip IS NOT NULL
        GROUP BY ip
        HAVING COUNT(*) >= ?
        """,
        (window_start, threshold),
    )
    ips = [row[0] for row in cur.fetchall()]

    for ip in ips:
        cur.execute(
            """
            SELECT 1
            FROM logs
            WHERE ip=? AND action='login' AND status='success'
              AND timestamp >= (
                SELECT MAX(timestamp)
                FROM logs
                WHERE ip=? AND action='login' AND status='fail'
              )
            LIMIT 1
            """,
            (ip, ip),
        )
        if cur.fetchone():
            insert_alert(
                conn,
                rule="Brute force then success (T1110)",
                severity="high",
                ip=ip,
                details=f"Multiple failed logins followed by success from {ip}",
            )


def check_offhours_admin(conn, business_start=9, business_end=18):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, timestamp, host, user, ip, rawjson
        FROM logs
        WHERE action = 'createuser'
        """
    )
    rows = cur.fetchall()

    for id_, ts, host, user, ip, rawjson in rows:
        hour = int(ts[11:13])  # crude hour extraction from ISO timestamp
        if not (business_start <= hour < business_end):
            insert_alert(
                conn,
                rule="Admin created off-hours T1136",
                severity="medium",
                ip=ip,
                user=user,
                host=host,
                details=f"User creation outside business hours at {ts}",
            )


def run_rules_loop(interval_seconds=30):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    while True:
        try:
            check_brute_force(conn)
            check_offhours_admin(conn)
            check_malicious_sites(conn)   # 🔥 ADD
        except Exception as e:
            print("[RULES ERROR]", e)
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_rules_loop()
