# Linux Application Usage Tracker

A lightweight Linux-based application that tracks application usage and logs the data into a MySQL database. The project also includes a web-based frontend using Flask and Flask-SocketIO, and a system service to run the tracker in the background.

## 🔧 Features

- Tracks which applications are being used on a Linux system
- Logs usage data to a MySQL database
- Provides a Flask web interface for viewing activity
- Runs as a background service using `systemd`
- Real-time updates via WebSockets (Flask-SocketIO)

## 🧰 Technologies Used

- Python
- Flask
- Flask-SocketIO
- MySQL
- systemd (for service creation)
- eventlet (for async support)
- Linux system commands

## 📦 Installation

### 1. Clone the Repository

```bash
git clone git@github.com:your-username/your-repo-name.git
cd your-repo-name

Create & Activate Virtual Environment (Optional but Recommended)
python3 -m venv venv
source venv/bin/activate

Configure MySQL
connection = mysql.connector.connect(
    host='localhost',
    user='your-username',
    password='your-password',
    database='your-database'
)


Setting Up the Service
sudo nano /etc/systemd/system/app-tracker.service

Paste
[Unit]
Description=Linux App Usage Tracker
After=network.target

[Service]
User=your-linux-username
ExecStart=/usr/bin/python3 /home/your-user/path-to-project/app.py
WorkingDirectory=/home/your-user/path-to-project/
Restart=always

[Install]
WantedBy=multi-user.target


Enable and Start the Service

sudo systemctl daemon-reload
sudo systemctl enable app-tracker
sudo systemctl start app-tracker



Check Status

sudo systemctl status app-tracker



Example Use Cases
Productivity tracking for personal use

System monitoring for teams

Research on app usage patterns




---

### ✅ Final Steps:
1. Replace placeholders like:
   - `your-username`
   - `your-repo-name`
   - `your-linux-username`
   - `your-password`
   - `/home/your-user/path-to-project/`
   - `Your Name`

2. Add the file:

```bash
git add README.md
git commit -m "Add complete README"
git push




- Priyanshu Srivastava
