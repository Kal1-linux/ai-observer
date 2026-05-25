#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$DIR/venv"

echo "🤖 Mempalace SaaS - Secure Client"
echo "---------------------------------"

# 1. Take a fake terminal session
RAW_SESSION="User deployed a server to 192.168.0.44 using AWS Key AKIAIOSFODNN7EXAMPLE and anthropic key sk-ant-api03-abcdefg. They emailed pratham@example.com."
echo "📝 Raw Terminal Session: $RAW_SESSION"

# 2. Run it through the local scrubber
echo "🧹 Scrubbing local secrets (PII/AWS Keys)..."
SCRUBBED_SESSION=$(echo "$RAW_SESSION" | "$VENV_DIR/bin/python3" "$DIR/mempalace_cli/scrubber.py")

echo "🔒 Scrubbed Output: $SCRUBBED_SESSION"

# 3. Send to Cloud FastAPI Server
echo "🚀 Sending clean data to Cloud API..."
JSON_PAYLOAD=$(printf '{"content": "%s"}' "$SCRUBBED_SESSION")

curl -s -X POST "http://127.0.0.1:8000/mempalace_add" \
     -H "Authorization: Bearer test-token-123" \
     -H "Content-Type: application/json" \
     -d "$JSON_PAYLOAD"

echo -e "\n\n🎉 End-to-End Pipeline Complete!"
