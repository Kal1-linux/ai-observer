#!/bin/bash
set -e

echo "🚀 Starting AI Observer Environment..."

# Configure Q CLI MCP (SSH to remote mempalace)
cat > /home/aiuser/.config/amazonq/mcp.json << 'EOF'
{
  "mcpServers": {
    "mempalace": {
      "command": "ssh",
      "args": [
        "-o", "ControlMaster=auto",
        "-o", "ControlPath=/tmp/ssh-mempalace-%r@%h:%p",
        "-o", "ControlPersist=yes",
        "root@${MEMPALACE_SERVER}",
        "cd /root/mempalace && source venv/bin/activate && python -m mempalace.mcp_server"
      ]
    }
  }
}
EOF

# Configure Claude MCP (SSH to remote mempalace)
cat > /home/aiuser/.claude/settings.json << 'EOF'
{
  "mcpServers": {
    "mempalace": {
      "command": "ssh",
      "args": [
        "-o", "ControlMaster=auto",
        "-o", "ControlPath=/tmp/ssh-mempalace-%r@%h:%p",
        "-o", "ControlPersist=yes",
        "root@${MEMPALACE_SERVER}",
        "cd /root/mempalace && source venv/bin/activate && python -m mempalace.mcp_server"
      ]
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
cat > /home/aiuser/ai-observer/config.env << EOF
MEMPALACE_SERVER=${MEMPALACE_SERVER:-192.168.1.137}
USERNAME=${USERNAME:-aiuser}
EOF

echo "✅ Environment ready!"
echo ""
echo "📋 Available commands:"
echo "  cd ai-observer && ./q-observed      # Start Q with recording"
echo "  cd ai-observer && ./claude-observed # Start Claude with recording"
echo "  cd ai-observer && ./search-sessions # Search past work"
echo ""
echo "🔗 Mempalace: SSH to ${MEMPALACE_SERVER:-192.168.1.137}"
echo ""

# Keep container running
exec "$@"
