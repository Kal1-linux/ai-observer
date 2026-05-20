#!/bin/bash
set -e

echo "🚀 Starting AI Observer Environment..."

# Start mempalace MCP server in background
cd /home/aiuser/mempalace
source venv/bin/activate
python -m mempalace.mcp_server &
MEMPALACE_PID=$!

# Configure Q CLI MCP
cat > /home/aiuser/.config/amazonq/mcp.json << 'EOF'
{
  "mcpServers": {
    "mempalace": {
      "command": "python",
      "args": ["-m", "mempalace.mcp_server"],
      "cwd": "/home/aiuser/mempalace",
      "env": {
        "VIRTUAL_ENV": "/home/aiuser/mempalace/venv"
      }
    }
  }
}
EOF

# Configure Claude MCP
cat > /home/aiuser/.claude/settings.json << 'EOF'
{
  "mcpServers": {
    "mempalace": {
      "command": "python",
      "args": ["-m", "mempalace.mcp_server"],
      "cwd": "/home/aiuser/mempalace",
      "env": {
        "VIRTUAL_ENV": "/home/aiuser/mempalace/venv"
      }
    }
  },
  "permissions": {
    "allow": ["Bash", "Read", "Write", "Edit"],
    "defaultMode": "bypassPermissions"
  }
}
EOF

# Copy CLAUDE.md protocol
cp /home/aiuser/ai-observer/CLAUDE.md /home/aiuser/.claude/

# Update ai-observer config
cat > /home/aiuser/ai-observer/config.env << 'EOF'
MEMPALACE_SERVER=localhost
USERNAME=aiuser
EOF

echo "✅ Environment ready!"
echo ""
echo "📋 Available commands:"
echo "  cd ai-observer && ./q-observed      # Start Q with recording"
echo "  cd ai-observer && ./claude-observed # Start Claude with recording"
echo "  cd ai-observer && ./search-sessions # Search past work"
echo ""
echo "🧠 Mempalace MCP server running (PID: $MEMPALACE_PID)"
echo ""

# Keep container running
exec "$@"
