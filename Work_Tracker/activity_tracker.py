#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import datetime
import mysql.connector
from mysql.connector import Error

# ====== Configuration ======
LOG_FILE = "/home/bhaskar/Documents/Work_Tracker/activity_tracker.log"
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "activity_tracker",
    "raise_on_warnings": False,
    "autocommit": True
}
POLL_INTERVAL = 2
LASTX_LINES = 30
# ===========================

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def now():
    return datetime.datetime.now()

def write_logfile(s):
    ts = now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {s}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception as e:
        sys.stderr.write(f"Failed to write log file: {e}\n")

def get_mysql_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        write_logfile(f"MySQL connection error: {e}")
        return None

def init_mysql():
    try:
        conn = get_mysql_connection()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        conn.database = MYSQL_CONFIG['database']
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_time DATETIME NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                details TEXT
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        write_logfile("MySQL initialization completed.")
    except Error as e:
        write_logfile(f"MySQL init error: {e}")

def insert_mysql(event_type, details=""):
    try:
        conn = get_mysql_connection()
        if not conn:
            write_logfile(f"Skipping DB insert for {event_type}, no connection.")
            return
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO activity_log (event_time, event_type, details) VALUES (%s, %s, %s)",
            (now(), event_type, details)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        write_logfile(f"MySQL insert failed ({event_type}): {e}")

def log_event(event_type, details=""):
    write_logfile(f"EVENT: {event_type} -- {details}")
    insert_mysql(event_type, details)

# Helpers for session detection
def get_current_session_id():
    try:
        user = os.getenv("USER") or subprocess.check_output(["whoami"], text=True).strip()
        out = subprocess.check_output(["loginctl", "list-sessions", "--no-legend"], text=True)
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == user:
                return parts[0]
    except Exception as e:
        write_logfile(f"get_current_session_id error: {e}")
    return None

def session_locked_hint(session_id):
    if not session_id:
        return None
    try:
        out = subprocess.check_output(
            ["loginctl", "show-session", session_id, "-p", "LockedHint"],
            text=True
        ).strip()
        if "yes" in out.lower():
            return True
        if "no" in out.lower():
            return False
    except Exception as e:
        write_logfile(f"session_locked_hint error: {e}")
    return None

# Helpers for suspend/shutdown detection via last -x
def read_lastx():
    try:
        out = subprocess.check_output(["last", "-x", "-n", str(LASTX_LINES)], text=True, stderr=subprocess.DEVNULL)
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        return lines
    except Exception as e:
        write_logfile(f"read_lastx error: {e}")
        return []

def detect_system_events(prev_seen):
    lines = read_lastx()
    new_seen = set(prev_seen)
    new_events = []

    for l in lines:
        key = l
        if key in prev_seen:
            continue
        lower = l.lower()
        if any(k in lower for k in ("suspend", "sleep", "suspended", "systemd-suspend")):
            new_events.append(("suspend", l))
            new_seen.add(key)
        elif any(k in lower for k in ("shutdown", "poweroff", "system-down")):
            new_events.append(("shutdown", l))
            new_seen.add(key)
        elif any(k in lower for k in ("reboot", "system boot")):
            new_events.append(("boot", l))
            new_seen.add(key)

    return new_events, new_seen

def main_loop():
    write_logfile("Activity tracker main loop starting.")
    session_id = get_current_session_id()
    if not session_id:
        write_logfile("WARNING: Could not determine session id; lock/unlock detection may not work until session appears.")
    last_locked = session_locked_hint(session_id)
    seen_lastx = set(read_lastx())

    log_event("login", f"script_start (session={session_id})")
    if last_locked is True:
        log_event("LOCKED", "initial state")
    elif last_locked is False:
        log_event("UNLOCKED", "initial state")

    try:
        while True:
            new_session = get_current_session_id()
            if new_session and new_session != session_id:
                session_id = new_session
                write_logfile(f"Session id changed => {session_id}")

            locked = session_locked_hint(session_id)
            if locked is not None and locked != last_locked:
                if locked:
                    log_event("LOCKED", f"session={session_id}")
                else:
                    log_event("UNLOCKED", f"session={session_id}")
                last_locked = locked

            events, seen_lastx = detect_system_events(seen_lastx)
            for ev_type, details in events:
                if ev_type == "suspend":
                    log_event("SUSPEND", details)
                elif ev_type == "shutdown":
                    log_event("SHUTDOWN", details)
                elif ev_type == "boot":
                    log_event("BOOT/RESUME", details)

            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log_event("SCRIPT STOPPED MANUALLY", "")
    except Exception as e:
        write_logfile(f"Unhandled exception in main loop: {e}")
        log_event("ERROR", str(e))

if __name__ == "__main__":
    init_mysql()
    main_loop()
