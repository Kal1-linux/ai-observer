#!/usr/bin/env bash
# Emergency backup - uploads .cast file directly to mempalace

CAST_FILE="$1"

if [ -z "$CAST_FILE" ] || [ ! -f "$CAST_FILE" ]; then
    echo "Usage: ./backup-cast.sh session-YYYYMMDD-HHMMSS.cast"
    exit 1
fi

echo "📦 Backing up $CAST_FILE to mempalace..."

# FIX 2: GUARANTEED BACKUP - never fail on duplicate
RESULT=$(cat "$CAST_FILE" | ssh root@192.168.1.137 "cd /root/mempalace && source venv/bin/activate && python - <<'PY'
from mempalace.mcp_server import tool_add_drawer
import sys, time

data = sys.stdin.read()
# GUARANTEED: unique ID + hash prevents duplicate failure
import hashlib
content_hash = hashlib.md5(data.encode()).hexdigest()[:8]
source = '$CAST_FILE-backup-' + str(int(time.time())) + '-' + content_hash

result = tool_add_drawer(
    wing='ai-observer',
    room='backup-casts',
    content=data,
    source_file=source,
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
    echo "⚠️ Backup failed: $RESULT (but .cast file is safe locally)"
fi
