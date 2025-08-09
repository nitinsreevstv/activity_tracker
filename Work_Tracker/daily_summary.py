#!/usr/bin/env python3
from datetime import datetime
from activity_tracker import get_mysql_connection, write_logfile

def get_days_with_events(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT DATE(event_time) FROM activity_log ORDER BY DATE(event_time)")
    days = [row[0] for row in cur.fetchall()]
    cur.close()
    return days

def get_events_for_day(conn, day):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT event_time, event_type FROM activity_log
        WHERE DATE(event_time) = %s
        ORDER BY event_time
    """, (day,))
    events = cur.fetchall()
    cur.close()
    return events

def calculate_summary(events):
    first_login = None
    last_logout = None
    total_active_seconds = 0

    last_active_start = None

    for ev in events:
        etype = ev["event_type"].lower()
        ts = ev["event_time"]

        if etype in ("login", "unlocked"):
            if not first_login:
                first_login = ts
            if last_active_start is None:
                last_active_start = ts

        elif etype in ("locked", "shutdown", "suspend"):
            if last_active_start:
                delta = (ts - last_active_start).total_seconds()
                if delta > 0:
                    total_active_seconds += delta
                last_logout = ts
                last_active_start = None

    if last_active_start:
        day_end = datetime.combine(events[0]["event_time"].date(), datetime.max.time())
        delta = (day_end - last_active_start).total_seconds()
        if delta > 0:
            total_active_seconds += delta
        last_logout = last_logout or day_end

    return first_login, last_logout, int(total_active_seconds)

def upsert_daily_summary(conn, day, first_login, last_logout, total_active_seconds):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INT AUTO_INCREMENT PRIMARY KEY,
            day DATE NOT NULL UNIQUE,
            first_login DATETIME,
            last_logout DATETIME,
            total_active_seconds INT
        )
    """)
    conn.commit()

    cur.execute("""
        INSERT INTO daily_summary (day, first_login, last_logout, total_active_seconds)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            first_login = VALUES(first_login),
            last_logout = VALUES(last_logout),
            total_active_seconds = VALUES(total_active_seconds)
    """, (day, first_login, last_logout, total_active_seconds))
    conn.commit()
    cur.close()

def main():
    conn = get_mysql_connection()
    if not conn:
        write_logfile("ERROR: Cannot connect to MySQL in daily_routine.")
        return

    days = get_days_with_events(conn)
    for day in days:
        events = get_events_for_day(conn, day)
        if not events:
            continue
        first_login, last_logout, total_active_seconds = calculate_summary(events)
        upsert_daily_summary(conn, day, first_login, last_logout, total_active_seconds)
        write_logfile(f"Processed {day}: first_login={first_login}, last_logout={last_logout}, active_hours={total_active_seconds/3600:.2f}")

    conn.close()

if __name__ == "__main__":
    main()
