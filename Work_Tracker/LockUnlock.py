import subprocess
import time
import getpass

# Get the current session ID
user = getpass.getuser()
session_id = subprocess.check_output(
    ["loginctl", "show-user", user]
).decode()

# Extract the session number
session_id = [
    line.split("=")[1]
    for line in session_id.splitlines()
    if line.startswith("Sessions=")
][0]

# Lock the session
subprocess.run(["loginctl", "lock-session", session_id])

# Wait 3 seconds
time.sleep(3)

# Unlock the session
subprocess.run(["loginctl", "unlock-session", session_id])
