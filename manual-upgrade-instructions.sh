#!/bin/bash
# Simple manual approach to add filtered tool

echo "📝 Creating patch file..."

cat > /tmp/mempalace_patch.txt << 'EOF'
INSTRUCTIONS:
1. SSH to mempalace server: ssh root@${MEMPALACE_SERVER}
2. cd /root/mempalace
3. Backup: cp mempalace/mcp_server.py mempalace/mcp_server.py.backup_manual
4. Edit: nano mempalace/mcp_server.py

STEP 1: Add function before line 345 (before "# ==================== AGENT DIARY"):

def tool_kg_query_filtered(entity, predicate_filter=None, limit=10, as_of=None, direction="both"):
    result = tool_kg_query(entity=entity, as_of=as_of, direction=direction)
    if not result or "facts" not in result:
        return result
    facts = result["facts"]
    if predicate_filter:
        facts = [f for f in facts if predicate_filter.lower() in f.get("predicate", "").lower()]
    return {"entity": entity, "predicate_filter": predicate_filter, "facts": facts[:limit], "count": len(facts[:limit])}


STEP 2: Add tool registration after line 493 (after "handler": tool_kg_query,):

    "mempalace_kg_query_filtered": {
        "description": "Query KG with server-side filtering (90%+ token savings)",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "predicate_filter": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["entity"],
        },
        "handler": tool_kg_query_filtered,
    },

STEP 3: Test:
source venv/bin/activate
python3 -c "from mempalace.mcp_server import tool_kg_query_filtered; print(tool_kg_query_filtered('prathammodi', 'friend', 10))"

STEP 4: Restart Q CLI to use new tool
EOF

cat /tmp/mempalace_patch.txt
echo ""
echo "✅ Instructions saved to /tmp/mempalace_patch.txt"
echo ""
echo "OR use current working solution:"
echo "  ./q-smart friends    # Already optimized, works today"
