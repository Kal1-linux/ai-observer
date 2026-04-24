#!/usr/bin/env bash
# Emergency backup - uploads .cast file directly to mempalace

CAST_FILE="$1"

if [ -z "$CAST_FILE" ] || [ ! -f "$CAST_FILE" ]; then
    echo "Usage: ./backup-cast.sh session-YYYYMMDD-HHMMSS.cast"
    exit 1
fi

echo "📦 Backing up $CAST_FILE to mempalace..."

RESULT=$(cat "$CAST_FILE" | ssh root@192.168.1.137 "cd /root/mempalace && source venv/bin/activate && python - <<'PY'
from mempalace.mcp_server import tool_add_drawer
import sys
from datetime import datetime

data = sys.stdin.read()

result = tool_add_drawer(
    wing='ai-observer',
    room='backup-casts',
    content=data,
    source_file='$CAST_FILE',
    added_by='backup-script'
)

if result.get('success'):
    print('SUCCESS')
else:
    print(f\"FAILED: {result}\")
PY
")

if echo "$RESULT" | grep -q "SUCCESS"; then
    echo "✅ Backed up to mempalace: ai-observer/backup-casts"
else
    echo "❌ Backup failed: $RESULT"
    exit 1
fi
