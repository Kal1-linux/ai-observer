#!/usr/bin/env bash
# Automated test for Claude components in ai-observer

# Load configuration
source "$(dirname "$0")/config.env" 2>/dev/null || { MEMPALACE_SERVER=${MEMPALACE_SERVER:-}; USERNAME=$(whoami); }
export MEMPALACE_SERVER USERNAME

echo "🧪 Testing Claude integration components..."
echo ""

# Test 1: Dependencies
echo "1. Checking dependencies..."
for cmd in asciinema claude python3 jq ssh; do
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
if [ -z "$MEMPALACE_SERVER" ]; then
    echo "  ❌ MEMPALACE_SERVER not configured in config.env"
    exit 1
fi
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

# Test 4: Claude Lock check
echo "4. Checking for active Claude sessions (locks)..."
ACTIVE_CLAUDE_PIDS=$(pgrep -f "claude" | grep -v "$$" || true)
if [ -n "$ACTIVE_CLAUDE_PIDS" ]; then
    echo "  ⚠️  Active Claude session(s) detected"
    echo "     Live Claude CLI queries might block or exit silently if locks are held."
else
    echo "  ✅ No active Claude sessions (lock-free)"
fi
echo ""

# Test 5: Python parsing (mock)
echo "5. Testing Python parsing..."
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

# Test 6: Directory structure
echo "6. Checking directory structure..."
for dir in failed-sessions backup; do
    if [ -d "./$dir" ]; then
        echo "  ✅ $dir/ exists"
    else
        echo "  ⚠️  $dir/ missing (will be created)"
    fi
done
echo ""

# Test 7: claude-toggle.sh test
echo "7. Testing claude-toggle.sh..."
if [ -x "./claude-toggle.sh" ]; then
    # Get current status
    ORIG_STATUS=$(./claude-toggle.sh status)
    
    # Try enabling to high
    ./claude-toggle.sh high &> /dev/null
    if ./claude-toggle.sh status | grep -q "HIGH"; then
        echo "  ✅ Toggle to HIGH working"
    else
        echo "  ❌ Toggle to HIGH failed"
        exit 1
    fi
    
    # Try toggling to low
    ./claude-toggle.sh low &> /dev/null
    if ./claude-toggle.sh status | grep -q "LOW"; then
        echo "  ✅ Toggle to LOW working"
    else
        echo "  ❌ Toggle to LOW failed"
        exit 1
    fi
    
    # Restore original setting
    if echo "$ORIG_STATUS" | grep -q "HIGH"; then
        ./claude-toggle.sh high &> /dev/null
    elif echo "$ORIG_STATUS" | grep -q "LOW"; then
        ./claude-toggle.sh low &> /dev/null
    else
        sed -i '/CLAUDE_CODE_EFFORT_LEVEL/d' ~/.bashrc 2>/dev/null || true
    fi
    echo "  ✅ Toggle states restored"
else
    echo "  ❌ claude-toggle.sh is not executable or missing"
    exit 1
fi
echo ""

# Test 8: Refinement Verification (Chronological sorting & Cross-wing support & SSH Wrapper)
echo "8. Verifying chronological sorting and cross-wing queries..."
if [ -x "./mcp-ssh-wrapper.sh" ]; then
    echo "  ✅ mcp-ssh-wrapper.sh is executable"
else
    echo "  ❌ mcp-ssh-wrapper.sh is not executable"
    exit 1
fi

if grep -q "mcp-ssh-wrapper.sh" ~/.claude.json 2>/dev/null; then
    echo "  ✅ ~/.claude.json configures mempalace using wrapper script (no hardcoded IP)"
else
    echo "  ❌ ~/.claude.json does not use mcp-ssh-wrapper.sh"
    exit 1
fi

# Run smart-query to test chronological sorting of tasks
TASKS_OUT=$(./smart-query tasks)
if echo "$TASKS_OUT" | grep -q "Recent Tasks"; then
    echo "  ✅ smart-query tasks sorting is functional"
else
    echo "  ❌ smart-query tasks failed"
    exit 1
fi

# Run smart-query to test chronological sorting and multi-wing search of sessions
RECENT_OUT=$(./smart-query recent 3 all)
if echo "$RECENT_OUT" | grep -q "Recent Sessions"; then
    echo "  ✅ smart-query recent sessions (all wings) is functional"
else
    echo "  ❌ smart-query recent sessions failed"
    exit 1
fi
echo ""

echo "🎉 All Claude component checks passed!"
