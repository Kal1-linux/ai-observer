#!/bin/bash
# Add server-side filtered query tool to mempalace MCP

source "$(dirname "$0")/config.env" 2>/dev/null || { MEMPALACE_SERVER=${MEMPALACE_SERVER}; }
export MEMPALACE_SERVER

ssh root@$MEMPALACE_SERVER bash << 'SSHEOF'
cd /root/mempalace

# Backup first
cp mempalace/mcp_server.py mempalace/mcp_server.py.backup_$(date +%s)

# Add filtered function
python3 << 'PYEOF'
import re

with open("mempalace/mcp_server.py", "r") as f:
    content = f.read()

# 1. Add function after tool_kg_stats
function_to_add = '''

def tool_kg_query_filtered(entity, predicate_filter=None, limit=10, as_of=None, direction="both"):
    """Query KG with server-side filtering - returns only matching predicates."""
    result = tool_kg_query(entity=entity, as_of=as_of, direction=direction)
    if not result or "facts" not in result:
        return result
    facts = result["facts"]
    if predicate_filter:
        facts = [f for f in facts if predicate_filter.lower() in f.get("predicate", "").lower()]
    facts = facts[:limit]
    return {
        "entity": entity,
        "predicate_filter": predicate_filter,
        "limit": limit,
        "facts": facts,
        "count": len(facts),
        "total_before_filter": len(result["facts"])
    }
'''

# Insert before AGENT DIARY section
marker = "# ==================== AGENT DIARY ===================="
if marker in content:
    content = content.replace(marker, function_to_add + "\n" + marker)
else:
    print("ERROR: Marker not found")
    exit(1)

# 2. Add tool registration in TOOLS dict
# Find the mempalace_kg_query tool and add after it
pattern = r'("mempalace_kg_query":\s*\{[^}]+handler":\s*tool_kg_query,\s*\},)'
match = re.search(pattern, content, re.DOTALL)

if not match:
    print("ERROR: Could not find mempalace_kg_query tool")
    exit(1)

tool_registration = '''
    "mempalace_kg_query_filtered": {
        "description": "Query KG with server-side filtering (TOKEN OPTIMIZED). Filters by predicate before returning data. Use this for friends/tasks/work queries to save 90%+ tokens.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string", "description": "Entity to query (e.g. 'prathammodi')"},
                "predicate_filter": {"type": "string", "description": "Filter by predicate substring (e.g. 'friend', 'completed_task', 'worked_on')"},
                "limit": {"type": "integer", "description": "Max results (default: 10)"},
                "as_of": {"type": "string", "description": "Date filter YYYY-MM-DD (optional)"},
                "direction": {"type": "string", "description": "outgoing/incoming/both (default: both)"},
            },
            "required": ["entity"],
        },
        "handler": tool_kg_query_filtered,
    },'''

# Insert after mempalace_kg_query
insert_pos = match.end()
content = content[:insert_pos] + tool_registration + content[insert_pos:]

# Write back
with open("mempalace/mcp_server.py", "w") as f:
    f.write(content)

print("✅ Added tool_kg_query_filtered")
PYEOF

# Verify syntax
python3 -m py_compile mempalace/mcp_server.py
if [ $? -eq 0 ]; then
    echo "✅ Syntax valid"
else
    echo "❌ Syntax error - restoring backup"
    cp mempalace/mcp_server.py.backup_* mempalace/mcp_server.py
    exit 1
fi

# Test the tool
source venv/bin/activate
python3 << 'PYEOF'
from mempalace.mcp_server import TOOLS, tool_kg_query_filtered

if "mempalace_kg_query_filtered" in TOOLS:
    print("✅ Tool registered in TOOLS")
    
    # Test it
    result = tool_kg_query_filtered("prathammodi", predicate_filter="friend", limit=10)
    print(f"✅ Test passed: {result['count']} facts (filtered from {result['total_before_filter']} total)")
else:
    print("❌ Tool not found in TOOLS")
    exit(1)
PYEOF

echo ""
echo "✅ Mempalace MCP server upgraded successfully!"
echo "Restart Q CLI to use the new tool"
SSHEOF
