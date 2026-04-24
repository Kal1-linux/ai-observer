#!/usr/bin/env bash
# Backfill missing sessions to mempalace

for CAST_FILE in session-20260424-080548.cast \
                 session-20260424-080940.cast \
                 session-20260424-081740.cast \
                 session-20260424-083246.cast \
                 session-20260424-083452.cast; do
    
    if [ ! -f "$CAST_FILE" ]; then
        echo "⚠️ $CAST_FILE not found, skipping"
        continue
    fi
    
    echo "📦 Processing $CAST_FILE..."
    
    # Parse session
    SESSION_TEXT=$(python3 - "$CAST_FILE" <<'PY'
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
filtered = []
capture = False

for line in text.splitlines():
    line = line.strip()
    if line.startswith(">"): capture = True
    if not capture: continue
    if any(x in line.lower() for x in ["did you know", "mcp server", "loading", "ctrl +", 
        "help all commands", "commands:", "usage:", "using tool:", "allow this action", 
        "running", "with the param", "completed in", "purpose:", "you are chatting with",
        "thinking...", "━━━", "╭─", "│", "╰─"]): continue
    if line: filtered.append(line)

print("\n".join(filtered))
PY
)
    
    if [ ${#SESSION_TEXT} -lt 50 ]; then
        echo "⚠️ Session too small, using minimal fallback"
        SESSION_TEXT="Backfilled session - content too small to parse"
    fi
    
    # Create fallback JSON
    JSON=$(jq -n \
        --arg text "$SESSION_TEXT" \
        --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg file "$CAST_FILE" \
        '{
            project: "ai-observer",
            timestamp: $ts,
            summary: ("Backfilled session: " + $file),
            tasks: [],
            decisions: [],
            commands: [],
            problems: [],
            learnings: [],
            files_created: [],
            files_modified: [],
            technologies: [],
            tags: ["backfill", "manual-recovery"],
            raw_text: $text
        }')
    
    # Store via SSH
    RESULT=$(ssh root@192.168.1.137 bash <<SSHEOF 2>&1
cd /root/mempalace && source venv/bin/activate && python3 <<PYEOF
from mempalace.mcp_server import tool_add_drawer
import json, time

data = '''$JSON'''
source = '$CAST_FILE-backfill-' + str(int(time.time()))

result = tool_add_drawer(
    wing='ai-observer',
    room='sessions',
    content=data,
    source_file=source,
    added_by='backfill-script'
)

if result.get('success'):
    print('SUCCESS')
else:
    print(f"FAILED: {result}")
PYEOF
SSHEOF
)
    
    if echo "$RESULT" | grep -q "SUCCESS"; then
        echo "✅ $CAST_FILE backfilled"
    else
        echo "❌ $CAST_FILE failed: $RESULT"
    fi
    
done

echo ""
echo "✅ Backfill complete"
