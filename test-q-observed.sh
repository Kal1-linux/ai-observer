#!/bin/bash
# Quick test of q-observed workflow (without actual Q chat)

# Load configuration
source "$(dirname "$0")/config.env" 2>/dev/null || { MEMPALACE_SERVER=${MEMPALACE_SERVER:-}; USERNAME=$(whoami); }
export MEMPALACE_SERVER USERNAME

echo "🧪 Testing q-observed components..."
echo ""

# Test 1: Dependencies
echo "1. Checking dependencies..."
for cmd in asciinema q python3 jq ssh; do
    if command -v $cmd &> /dev/null; then
        echo "  ✅ $cmd"
    else
        echo "  ❌ $cmd - MISSING"
        exit 1
    fi
done
echo ""

# Test 2: SSH connection
echo "2. Testing SSH to mempalace server..."
if ssh -o ConnectTimeout=5 root@${MEMPALACE_SERVER} "echo 'Connected'" &> /dev/null; then
    echo "  ✅ SSH connection OK"
else
    echo "  ❌ SSH connection FAILED"
    exit 1
fi
echo ""

# Test 3: Mempalace server
echo "3. Testing mempalace server..."
if ssh root@${MEMPALACE_SERVER} "cd /root/mempalace && test -f venv/bin/activate" &> /dev/null; then
    echo "  ✅ Mempalace server OK"
else
    echo "  ❌ Mempalace server FAILED"
    exit 1
fi
echo ""

# Test 4: Python parsing (mock)
echo "4. Testing Python parsing..."
TEST_CAST=$(mktemp --suffix=.cast)
cat > "$TEST_CAST" <<'EOF'
{"version": 2, "width": 80, "height": 24}
[0.1, "o", "> test command\n"]
[0.2, "o", "output\n"]
EOF

PARSED=$(python3 - "$TEST_CAST" <<'PY'
from pathlib import Path
import json, re, sys
file = Path(sys.argv[1])
ANSI = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
output = []
with file.open() as f:
    for i, line in enumerate(f):
        if i == 0: continue
        try:
            event = json.loads(line)
            if len(event) >= 3 and event[1] == "o":
                output.append(event[2])
        except: pass
text = ANSI.sub('', "".join(output))
print(text)
PY
)

if [ -n "$PARSED" ]; then
    echo "  ✅ Python parsing OK"
else
    echo "  ❌ Python parsing FAILED"
    rm "$TEST_CAST"
    exit 1
fi
rm "$TEST_CAST"
echo ""

# Test 5: JSON validation
echo "5. Testing jq validation..."
TEST_JSON='{"project":"test","timestamp":"2026-04-28T00:00:00Z"}'
if echo "$TEST_JSON" | jq -c . &> /dev/null; then
    echo "  ✅ jq validation OK"
else
    echo "  ❌ jq validation FAILED"
    exit 1
fi
echo ""

# Test 6: Directory structure
echo "6. Checking directory structure..."
if [ -d "./failed-sessions" ]; then
    echo "  ✅ failed-sessions/ exists"
else
    echo "  ⚠️  failed-sessions/ missing (will be created)"
fi

if [ -d "./backup" ]; then
    echo "  ✅ backup/ exists"
else
    echo "  ⚠️  backup/ missing"
fi
echo ""

echo "✅ All q-observed components working!"
echo ""
echo "How q-observed works:"
echo "  1. Records Q chat session with asciinema"
echo "  2. Parses .cast file to extract text"
echo "  3. Sends to Q for JSON analysis"
echo "  4. Validates JSON with jq"
echo "  5. Stores in mempalace via SSH"
echo "  6. Adds facts to knowledge graph"
echo "  7. Saves local backup to failed-sessions/"
echo ""
echo "Usage: ./q-observed"
echo "  (This will start Q chat and record everything)"
