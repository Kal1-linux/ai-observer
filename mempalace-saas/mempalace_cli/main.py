import sys
import os
import subprocess
import json
import re
import time
import tempfile
import urllib.request
from pathlib import Path

# Import the local scrubber logic
try:
    from .scrubber import scrub_text
except ImportError:
    print("❌ Error: scrubber.py not found in the package.")
    sys.exit(1)

# SaaS Cloud Settings
API_BASE_URL = os.environ.get("MEMPALACE_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_URL = f"{API_BASE_URL}/mempalace_add"
# In a real app, this would be loaded from os.environ or a config file
API_TOKEN = os.environ.get("MEMPALACE_API_KEY", "test-token-123") 

ANSI_ESCAPE = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

def parse_cast_file(cast_file_path):
    output = []
    try:
        with open(cast_file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0: continue # Skip header
                try:
                    event = json.loads(line)
                    # Asciinema format: [time, "o", "text output"]
                    if len(event) >= 3 and event[1] == "o":
                        output.append(event[2])
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        return ""
    
    # Strip ANSI colors and control characters
    raw_text = "".join(output)
    clean_text = ANSI_ESCAPE.sub('', raw_text)
    
    # Filter out empty lines to save space
    filtered = [line.strip() for line in clean_text.splitlines() if line.strip()]
    return "\n".join(filtered)

def upload_to_saas(scrubbed_text):
    payload = json.dumps({"content": scrubbed_text}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=payload, headers={
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    })
    
    try:
        # Silently attempt upload
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
    except Exception:
        pass

def main():
    if len(sys.argv) < 3 or sys.argv[1] != "run":
        print("Usage: python3 mempalace.py run <command>")
        print("Example: python3 mempalace.py run \"bash\"")
        sys.exit(1)
        
    command_to_run = " ".join(sys.argv[2:])
    
    # Create a temporary file for the asciinema recording
    with tempfile.NamedTemporaryFile(suffix=".cast", delete=False) as tmp:
        cast_file = tmp.name
        
    # Run asciinema in the foreground quietly
    try:
        subprocess.run(["asciinema", "rec", "-q", cast_file, "-c", command_to_run], check=True)
    except Exception:
        pass

    raw_text = parse_cast_file(cast_file)
    
    if len(raw_text) < 10:
        os.remove(cast_file)
        sys.exit(0)
        
    scrubbed_text = scrub_text(raw_text)
    
    upload_to_saas(scrubbed_text)
    
    # Cleanup local cast file to ensure privacy
    try:
        os.remove(cast_file)
    except OSError:
        pass

if __name__ == "__main__":
    main()
