#!/usr/bin/env bash
source "$(dirname "$0")/config.env" 2>/dev/null || { MEMPALACE_SERVER=${MEMPALACE_SERVER}; }
export MEMPALACE_SERVER
# RTK wrapper for mempalace MCP queries
# Compresses output before sending to Q

QUERY_TYPE="$1"
shift

case "$QUERY_TYPE" in
  friends)
    ssh root@$MEMPALACE_SERVER "cd /root/mempalace && python3 -c \"
from mempalace.mcp_server import search_palace
results = search_palace('friend', limit=10)
for r in results['results']:
    print(r['text'][:200])  # First 200 chars only
\"" | rtk summary
    ;;
  
  tasks)
    ssh root@$MEMPALACE_SERVER "cd /root/mempalace && python3 -c \"
from mempalace.mcp_server import search_palace
results = search_palace('task completed', wing='ai-observer', limit=5)
for r in results['results']:
    print(r['text'][:150])
\"" | rtk summary
    ;;
  
  recent)
    LIMIT="${1:-5}"
    ssh root@$MEMPALACE_SERVER "cd /root/mempalace && python3 -c \"
from mempalace.mcp_server import search_palace
results = search_palace('recent work', wing='ai-observer', limit=$LIMIT)
for r in results['results']:
    print(r['text'][:200])
\"" | rtk summary
    ;;
  
  *)
    echo "Usage: $0 {friends|tasks|recent [N]}"
    exit 1
    ;;
esac
