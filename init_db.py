# init_db.py
import sqlite3

DB_PATH = "logs.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        host TEXT,
        user TEXT,
        action TEXT,
        status TEXT,
        ip TEXT,
        rawjson TEXT        -- <--- important
    )
    """
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        rule TEXT,
        severity TEXT,
        ip TEXT,
        user TEXT,
        host TEXT,
        details TEXT
    )
    """
)

conn.commit()
conn.close()
