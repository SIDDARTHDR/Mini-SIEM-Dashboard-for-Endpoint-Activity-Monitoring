🛡️ Mini-SIEM Dashboard for Endpoint Activity Monitoring
📌 Overview

The Mini-SIEM Dashboard is a lightweight Security Information and Event Management (SIEM) system designed to monitor endpoint activity, collect security logs, detect suspicious behavior, and visualize events through a real-time dashboard.

This project demonstrates how a SIEM works by implementing:

->Log collection from endpoints
->Log ingestion and normalization
->Threat detection using detection rules
->Alert generation
->Real-time monitoring dashboard
It is designed for educational, research, and demonstration purposes.

🎯 Objectives

->Monitor endpoint activities such as:
    -User logins
    -Website browsing
    -File access
    -System events
->Detect suspicious and malicious behavior
->Generate alerts based on detection rules
->Provide a real-time security monitoring dashboard
->Simulate a real SIEM architecture on a small scale

🧱 System Architecture
                        Endpoint Agents
                            │
                            │ (Syslog UDP events)
                            ▼
                        Log Ingester (ingester.py)
                            │
                            ▼
                        SQLite Database (logs.db)
                            │
                            ├── Detection Engine (rules.py)
                            │        │
                            │        ▼
                            │     Alerts Table
                            │
                            ▼
                        FastAPI Backend (main.py)
                            │
                            ▼
                        Web Dashboard (Browser UI)

⚙️ Components
1. Endpoint Agents - These collect activity from endpoints and send logs.

Chrome History Agent (chrome_agent.py)
->Monitors Chrome browsing history
->Sends visited URLs, user, and timestamp
->Example event:
  chrome host=LAPTOP user=admin url=https://example.com action=browse status=success

Windows Security Agent (windows_agent.py)
->Monitors Windows Security Event Logs
->Detects file access activity
->Uses Windows Event IDs (e.g., 4663)

Log Simulator (test_sender.py)
Simulates:
->Brute force attacks
->Admin creation
->Login attempts

2. Log Ingester (ingester.py)
->Listens on UDP port 514
->Receives syslog-formatted messages
->Parses logs into structured format
->Stores logs into SQLite database

Stored fields:

->timestamp
->host
->user
->action
->status
->ip
->raw event data

3. Database (logs.db)
Tables:
logs table - Stores all endpoint events.
alerts table - Stores detected security alerts.

Database initialized using:  init_db.py

4. Detection Engine (rules.py)
Continuously analyzes logs and detects threats.

Implemented detection rules:
🚨 Malicious Website Detection
Detects browsing of suspicious domains from:  threat_db.py
Example:
      malware.com
      phishingsite.com

🚨 Brute Force Detection (MITRE ATT&CK T1110)
Detects:
->Multiple failed login attempts
->Followed by successful login

🚨 Off-hours Admin Creation Detection (T1136)
Detects user creation outside business hours.

5. Dashboard Backend (main.py)
Built using FastAPI
Provides APIs:
            GET /alerts
            GET /timeline
            GET /

6. Web Dashboard

Features:
->Real-time alerts
->User activity timeline
->Website browsing visibility
->Auto-refresh every 5 seconds

Displays:
->Alerts severity
->User activity
->IP address
->Website URLs
->System events

💻 Technologies Used
Technology	          Purpose
Python	          -  Core development
FastAPI	          -  Backend API
SQLite	          -  Database
Syslog (UDP)	    -  Log transmission
HTML/CSS/JS	      -  Dashboard UI
pywin32	          -  Windows event monitoring
Socket Programming-	Log communication


🚀 Installation and Setup
Step 1: Clone the repository
git clone https://github.com/your-username/mini-siem-dashboard.git
cd mini-siem-dashboard

Step 2: Install dependencies
pip install fastapi uvicorn pywin32

Step 3: Initialize Database
python init_db.py

Step 4: Start Log Ingester
python ingester.py

Step 5: Start Detection Engine
python rules.py

Step 6: Start Endpoint Agents

Chrome Agent: python chrome_agent.py
Windows Agent: python windows_agent.py
Simulator: python test_sender.py --brute

Step 7: Start Dashboard Server 
uvicorn main:app --reload

Step 8: Open Dashboard
Open in browser: http://127.0.0.1:8000

📊 Features
✅ Real-time log monitoring
✅ Endpoint activity tracking
✅ Malicious website detection
✅ Brute force detection
✅ Admin activity monitoring
✅ Alert generation
✅ Live dashboard visualization
✅ Lightweight and fast
✅ Easy to extend

🔍 Example Use Cases
->Security monitoring for small networks
->Cybersecurity learning and research
->Understanding SIEM architecture
->Demonstrating threat detection
->Academic projects and demonstrations

📁 Project Structure
mini-siem/
│
├── chrome_agent.py
├── windows_agent.py
├── ingester.py
├── rules.py
├── main.py
├── init_db.py
├── threat_db.py
├── test_sender.py
├── logs.db
└── README.md

🔐 Future Improvements
->Add authentication monitoring
->Integrate machine learning threat detection
->Add email alerts
->Add Elasticsearch integration
->Add distributed agents
->Add real network monitoring

🎓 Educational Value
This project demonstrates core SIEM concepts:
->Log collection
->Log parsing
->Event normalization
->Threat detection
->Alert generation
->Security monitoring dashboard

👨‍💻 Author
Siddarth
Cybersecurity & Software Development Project

📜 License
This project is for educational purposes.
