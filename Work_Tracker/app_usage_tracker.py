#!/usr/bin/env python3
import subprocess
import time
from datetime import datetime
from activity_tracker import write_logfile, get_mysql_connection  # import helpers

POLL_INTERVAL = 5  # seconds

def get_active_window_title():
    try:
        title = subprocess.check_output(
            ["xdotool", "getactivewindow", "getwindowname"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return title
    except Exception as e:
        write_logfile(f"Failed to get active window: {e}")
        return None

def extract_app_name(window_title):
    if not window_title:
        return None
    for sep in [' - ', ':']:
        if sep in window_title:
            # Often app name is last part, but this can be adjusted
            return window_title.split(sep)[-1].strip()
    return window_title.strip()

def log_app_usage(conn, app_name, window_title):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO app_usage (event_time, app_name, window_title) VALUES (%s, %s, %s)",
            (datetime.now(), app_name, window_title)
        )
        conn.commit()
        cur.close()
    except Exception as e:
        write_logfile(f"MySQL insert failed (app_usage): {e}")

def main():
    conn = get_mysql_connection()
    if not conn:
        write_logfile("Cannot connect to MySQL, exiting app usage tracker.")
        return

    last_app = None

    write_logfile("App usage tracker started.")

    try:
        while True:
            window_title = get_active_window_title()
            app_name = extract_app_name(window_title)

            if app_name != last_app and app_name is not None:
                log_app_usage(conn, app_name, window_title)
                write_logfile(f"App switched: {last_app} -> {app_name}")
                last_app = app_name

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        write_logfile("App usage tracker stopped manually.")
    except Exception as e:
        write_logfile(f"Unhandled exception in app usage tracker: {e}")
    finally:
        if conn.is_connected():
            conn.close()

if __name__ == "__main__":
    main()
