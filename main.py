'''
from fastapi import FastAPI, HTTPException
import sqlite3
from fastapi.responses import HTMLResponse

DB_PATH = "logs.db"

app = FastAPI(title="Mini SIEM")

def get_conn():
    return sqlite3.connect(DB_PATH)

@app.get("/alerts")
def get_alerts(limit: int = 50):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT time, rule, severity, ip, user, host, details
            FROM alerts
            ORDER BY time DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "time": r[0],
                "rule": r[1],
                "severity": r[2],
                "ip": r[3],
                "user": r[4],
                "host": r[5],
                "details": r[6],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/timeline")
def timeline(host: str | None = None, limit: int = 100):
    try:
        conn = get_conn()
        cur = conn.cursor()
        if host:
            cur.execute(
                """
                SELECT timestamp, host, user, action, status, ip
                FROM logs
                WHERE host=?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (host, limit),
            )
        else:
            cur.execute(
                """
                SELECT timestamp, host, user, action, status, ip
                FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "time": r[0],
                "host": r[1],
                "user": r[2],
                "action": r[3],
                "status": r[4],
                "ip": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Mini SIEM Dashboard</title>
      <style>
        body { font-family: Arial, sans-serif; background:#0b1020; color:#e0e0e0; }
        h1 { color:#4fd1c5; }
        table { border-collapse: collapse; width:100%; margin-bottom:20px; }
        th, td { border:1px solid #444; padding:6px 8px; font-size:13px; }
        th { background:#1a2438; }
        .high { color:#ff6b6b; font-weight:bold; }
        .medium { color:#ffd166; }
      </style>
    </head>
    <body>
      <h1>Mini SIEM Dashboard</h1>

      <h2>Alerts</h2>
      <table id="alerts-table">
        <thead>
          <tr>
            <th>Time</th><th>Rule</th><th>Severity</th><th>IP</th><th>User</th><th>Details</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>

      <h2>Timeline (last 50 events)</h2>
      <table id="timeline-table">
        <thead>
          <tr>
            <th>Time</th><th>Host</th><th>User</th><th>Action</th><th>Status</th><th>IP</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>

      <script>
        async function loadAlerts() {
          const res = await fetch('/alerts?limit=50');
          const data = await res.json();
          const tbody = document.querySelector('#alerts-table tbody');
          tbody.innerHTML = '';
          data.forEach(a => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${a.time}</td>
              <td>${a.rule}</td>
              <td class="${a.severity}">${a.severity}</td>
              <td>${a.ip || ''}</td>
              <td>${a.user || ''}</td>
              <td>${a.details || ''}</td>
            `;
            tbody.appendChild(tr);
          });
        }

        async function loadTimeline() {
          const res = await fetch('/timeline?limit=50');
          const data = await res.json();
          const tbody = document.querySelector('#timeline-table tbody');
          tbody.innerHTML = '';
          data.forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${e.time}</td>
              <td>${e.host || ''}</td>
              <td>${e.user || ''}</td>
              <td>${e.action || ''}</td>
              <td>${e.status || ''}</td>
              <td>${e.ip || ''}</td>
            `;
            tbody.appendChild(tr);
          });
        }

        function refreshAll() {
          loadAlerts();
          loadTimeline();
        }

        refreshAll();
        setInterval(refreshAll, 5000); // refresh every 5s
      </script>
    </body>
    </html>
    """
'''
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
import json

DB_PATH = "logs.db"
app = FastAPI(title="Mini SIEM")


def get_conn():
    return sqlite3.connect(DB_PATH)


@app.get("/alerts")
def get_alerts(limit: int = 50):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT time, rule, severity, ip, user, host, details
            FROM alerts
            ORDER BY time DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "time": r[0],
                "rule": r[1],
                "severity": r[2],
                "ip": r[3],
                "user": r[4],
                "host": r[5],
                "details": r[6],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/timeline")
def timeline(host: str | None = None, limit: int = 100):
    """Return recent timeline entries with website metadata."""
    try:
        conn = get_conn()
        cur = conn.cursor()

        if host:
            cur.execute(
                """
                SELECT timestamp, host, user, action, status, ip, rawjson
                FROM logs
                WHERE host = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (host, limit),
            )
        else:
            cur.execute(
                """
                SELECT timestamp, host, user, action, status, ip, rawjson
                FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )

        rows = cur.fetchall()
        conn.close()

        timeline_entries = []
        for ts, host_val, user, action, status, ip, rawjson in rows:
            url = None
            title = None
            if rawjson:
                try:
                    data = json.loads(rawjson)
                    url = (
                        data.get("url")
                        or data.get("page_url")
                        or (data.get("request") or {}).get("url")
                    )
                    title = (
                        data.get("title")
                        or data.get("page_title")
                        or (data.get("tab") or {}).get("title")
                    )
                except Exception:
                    pass

            timeline_entries.append(
                {
                    "time": ts,
                    "host": host_val,
                    "user": user,
                    "action": action,
                    "status": status,
                    "ip": ip,
                    "url": url,
                    "title": title,
                }
            )

        return timeline_entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def ui():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Mini SIEM Dashboard</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      margin: 0;
      padding: 0;
    }
    h1, h2 {
      color: #f9fafb;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }
    .card {
      background: #020617;
      border-radius: 12px;
      border: 1px solid #1f2937;
      padding: 16px 20px;
      margin-bottom: 24px;
      box-shadow: 0 10px 25px rgba(15, 23, 42, 0.8);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      padding: 8px 10px;
      border-bottom: 1px solid #1f2937;
      text-align: left;
    }
    th {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #9ca3af;
      border-bottom: 1px solid #374151;
    }
    tr:nth-child(even) {
      background: rgba(15, 23, 42, 0.8);
    }
    tr:nth-child(odd) {
      background: rgba(15, 23, 42, 0.4);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 500;
    }
    .badge-critical {
      background: rgba(239, 68, 68, 0.1);
      color: #fecaca;
      border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .badge-high {
      background: rgba(248, 113, 113, 0.08);
      color: #fed7aa;
      border: 1px solid rgba(248, 113, 113, 0.4);
    }
    .badge-medium {
      background: rgba(234, 179, 8, 0.1);
      color: #facc15;
      border: 1px solid rgba(234, 179, 8, 0.4);
    }
    .badge-low {
      background: rgba(34, 197, 94, 0.12);
      color: #bbf7d0;
      border: 1px solid rgba(34, 197, 94, 0.5);
    }
    .pill {
      display: inline-flex;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      border: 1px solid #4b5563;
      color: #9ca3af;
      background: rgba(15, 23, 42, 0.7);
    }
    .pill-success {
      border-color: #16a34a;
      color: #bbf7d0;
    }
    .pill-fail {
      border-color: #ef4444;
      color: #fecaca;
    }
    .timestamp {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12px;
      color: #9ca3af;
    }
    .ip {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 12px;
      color: #e5e7eb;
      background: rgba(15, 23, 42, 0.8);
      padding: 2px 6px;
      border-radius: 6px;
      border: 1px solid #111827;
    }
    .host-user {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .host {
      font-weight: 500;
      color: #e5e7eb;
    }
    .user {
      font-size: 12px;
      color: #9ca3af;
    }
    .details {
      font-size: 13px;
      color: #d1d5db;
      max-width: 360px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .url-cell {
      font-size: 13px;
      max-width: 360px;
    }
    .url-title {
      font-weight: 500;
      color: #e5e7eb;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .url-link {
      display: block;
      font-size: 12px;
      color: #60a5fa;
      text-decoration: none;
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .url-link:hover {
      text-decoration: underline;
    }
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 10px;
    }
    .section-header small {
      color: #6b7280;
      font-size: 12px;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #10b981;
      box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 500;
      border: 1px solid #16a34a;
      color: #bbf7d0;
      background: rgba(6, 95, 70, 0.7);
    }
    .grid {
      display: grid;
      grid-template-columns: 2fr 3fr;
      gap: 24px;
    }
    @media (max-width: 900px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }
    .refresh-note {
      font-size: 11px;
      color: #6b7280;
      margin-top: 6px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <div>
        <h1 style="margin: 0 0 4px 0;">Mini SIEM</h1>
        <p style="margin: 0; font-size: 13px; color: #9ca3af;">
          Live alerts & user activity timeline
        </p>
      </div>
      <div class="status-badge">
        <span class="status-dot"></span>
        Agents connected
      </div>
    </div>

    <div class="grid">
      <!-- Alerts panel -->
      <div class="card">
        <div class="section-header">
          <h2 style="margin: 0;">Alerts</h2>
          <small>Last 50 alerts</small>
        </div>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Rule</th>
              <th>Severity</th>
              <th>IP</th>
              <th>User / Host</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody id="alerts-body">
            <tr><td colspan="6" style="text-align:center; padding:12px;">Loading...</td></tr>
          </tbody>
        </table>
        <p class="refresh-note">Auto-refreshes every 5 seconds.</p>
      </div>

      <!-- Timeline panel -->
      <div class="card">
        <div class="section-header">
          <h2 style="margin: 0;">User Timeline</h2>
          <small>Last 100 events</small>
        </div>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Host / User</th>
              <th>Action</th>
              <th>Status</th>
              <th>IP</th>
              <th>Website / URL</th>
            </tr>
          </thead>
          <tbody id="timeline-body">
            <tr><td colspan="6" style="text-align:center; padding:12px;">Loading...</td></tr>
          </tbody>
        </table>
        <p class="refresh-note">Auto-refreshes every 5 seconds.</p>
      </div>
    </div>
  </div>

  <script>
    async function fetchAlerts() {
      try {
        const res = await fetch('/alerts');
        const data = await res.json();
        const tbody = document.getElementById('alerts-body');
        tbody.innerHTML = '';

        if (!data.length) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:12px;">No alerts yet.</td></tr>';
          return;
        }

        for (const a of data) {
          const tr = document.createElement('tr');

          const severity = (a.severity || '').toLowerCase();
          let sevClass = 'badge-low';
          if (severity === 'critical') sevClass = 'badge-critical';
          else if (severity === 'high') sevClass = 'badge-high';
          else if (severity === 'medium') sevClass = 'badge-medium';

          tr.innerHTML = `
            <td><span class="timestamp">${a.time || ''}</span></td>
            <td>${a.rule || ''}</td>
            <td><span class="badge ${sevClass}">${a.severity || ''}</span></td>
            <td><span class="ip">${a.ip || ''}</span></td>
            <td>
              <div class="host-user">
                <span class="host">${a.host || ''}</span>
                <span class="user">${a.user || ''}</span>
              </div>
            </td>
            <td><div class="details" title="${a.details || ''}">${a.details || ''}</div></td>
          `;
          tbody.appendChild(tr);
        }
      } catch (e) {
        console.error('Failed to fetch alerts', e);
      }
    }

    async function fetchTimeline() {
      try {
        const res = await fetch('/timeline');
        const data = await res.json();
        const tbody = document.getElementById('timeline-body');
        tbody.innerHTML = '';

        if (!data.length) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:12px;">No events yet.</td></tr>';
          return;
        }

        for (const ev of data) {
          const tr = document.createElement('tr');

          let statusClass = 'pill';
          const statusVal = (ev.status || '').toLowerCase();
          if (statusVal === 'success' || statusVal === 'ok') {
            statusClass += ' pill-success';
          } else if (statusVal === 'fail' || statusVal === 'error' || statusVal === 'blocked') {
            statusClass += ' pill-fail';
          }

          // Website / URL cell content
          const hasUrl = !!ev.url;
          const urlTitle = ev.title || (hasUrl ? new URL(ev.url).hostname : '');
          const urlText = ev.url || '';

          const websiteCell = hasUrl
            ? `
              <div class="url-cell">
                <div class="url-title" title="${urlTitle}">${urlTitle}</div>
                <a class="url-link" href="${ev.url}" target="_blank" rel="noreferrer" title="${urlText}">
                  ${urlText}
                </a>
              </div>
            `
            : `<span style="font-size:12px; color:#6b7280;">—</span>`;

          tr.innerHTML = `
            <td><span class="timestamp">${ev.time || ''}</span></td>
            <td>
              <div class="host-user">
                <span class="host">${ev.host || ''}</span>
                <span class="user">${ev.user || ''}</span>
              </div>
            </td>
            <td>${ev.action || ''}</td>
            <td><span class="${statusClass}">${ev.status || ''}</span></td>
            <td><span class="ip">${ev.ip || ''}</span></td>
            <td>${websiteCell}</td>
          `;
          tbody.appendChild(tr);
        }
      } catch (e) {
        console.error('Failed to fetch timeline', e);
      }
    }

    fetchAlerts();
    fetchTimeline();
    setInterval(fetchAlerts, 5000);
    setInterval(fetchTimeline, 5000);
  </script>
</body>
</html>
"""
