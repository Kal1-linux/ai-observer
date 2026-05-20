#!/usr/bin/env bash
# Helper to query Mempalace for any project from any agent.
# Usage: PROJECT=my-service ./project-query.sh <tool_name> "<python_args>"
# Example: PROJECT=my-service ./project-query.sh tool_kg_query "entity='prathammodi', direction='both'"

# Load configuration (MEMPALACE_SERVER)
source "$(dirname "$0")/config.env" 2>/dev/null || { MEMPALACE_SERVER=${MEMPALACE_SERVER}; }
export MEMPALACE_SERVER

# Default project name if not supplied
PROJECT="${PROJECT:-ai-observer}"

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <tool_name> \"<python_args>\""
    echo "Example: $0 tool_kg_query \"entity='prathammodi', direction='both'\""
    exit 1
fi

tool_name="$1"
shift
py_args="$*"

# Run the tool on the remote Mempalace server via SSH.
ssh "root@$MEMPALACE_SERVER" "cd /root/mempalace && source venv/bin/activate && python3 - <<'PY'
import json, sys
from mempalace.mcp_server import $tool_name

try:
    result = $tool_name($py_args)
    print(json.dumps(result, indent=2))
except Exception as e:
    print(json.dumps({'error': str(e)}, indent=2), file=sys.stderr)
PY"
