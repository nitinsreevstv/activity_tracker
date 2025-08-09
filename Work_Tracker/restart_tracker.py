#!/usr/bin/env python3
import subprocess

scripts = [
    "/home/bhaskar/Documents/Work_Tracker/activity_tracker.py",
    "/home/bhaskar/Documents/Work_Tracker/app_usage_tracker.py"
]

services = [
    "activity_tracker.service",
    "app_usage_tracker.service"
]

def main():
    # Make scripts executable
    for script in scripts:
        subprocess.run(["chmod", "+x", script], check=True)
    
    # Reload systemd user daemon
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    
    # Restart services
    for service in services:
        subprocess.run(["systemctl", "--user", "restart", service], check=True)
    
    print("✅ Both activity_tracker.py and app_usage_tracker.py made executable and services restarted successfully.")

if __name__ == "__main__":
    main()
