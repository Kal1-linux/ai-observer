#!/bin/bash
# Complete setup for ai-observer with Q CLI and Claude Code

set -e

echo "🚀 AI Observer - Complete Setup"
echo ""

# 1. Check Q CLI
if ! command -v q &> /dev/null; then
    echo "❌ Q CLI not found"
    echo "Install from: https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-getting-started-installing.html"
    exit 1
fi
echo "✅ Q CLI found: $(q --version)"

# 2. Check Claude Code
if ! command -v claude &> /dev/null; then
    echo "⚠️  Claude Code not found (optional)"
    echo "Install from: https://claude.ai/download"
else
    echo "✅ Claude Code found: $(claude --version)"
fi

# 3. Check dependencies
for cmd in python3 jq asciinema ssh; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ Missing: $cmd"
        exit 1
    fi
done
echo "✅ All dependencies installed"

# 4. Configure mempalace
if [ ! -f config.env ]; then
    cp config.env.example config.env
    echo ""
    echo "📝 Edit config.env with your mempalace server details:"
    echo "   MEMPALACE_SERVER=your.server.ip"
    echo "   USERNAME=your_username"
    echo ""
    read -p "Press Enter to edit config.env..."
    ${EDITOR:-nano} config.env
fi

source config.env

# 5. Test SSH connection
echo ""
echo "🔐 Testing SSH connection to $MEMPALACE_SERVER..."
if ssh -o ConnectTimeout=5 -o ControlMaster=auto -o ControlPath=/tmp/ssh-mempalace-%r@%h:%p -o ControlPersist=yes root@$MEMPALACE_SERVER "echo 'SSH OK'" 2>/dev/null; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed"
    echo "Fix: ssh-copy-id root@$MEMPALACE_SERVER"
    exit 1
fi

# 6. Test mempalace
echo ""
echo "🧠 Testing mempalace..."
TEST_RESULT=$(ssh root@$MEMPALACE_SERVER "cd /root/mempalace && source venv/bin/activate && python3 -c 'from mempalace.mcp_server import tool_status; print(tool_status())'" 2>&1)
if echo "$TEST_RESULT" | grep -q "total_drawers"; then
    echo "✅ Mempalace working"
else
    echo "❌ Mempalace not responding"
    echo "$TEST_RESULT"
    exit 1
fi

# 7. Create directories
mkdir -p ~/.ai-observer/{casts,logs}
mkdir -p ./failed-sessions

# 8. Make scripts executable
chmod +x q-observed claude-observed search-sessions latest-sessions stats.sh rtk-toggle.sh

# 9. Configure RTK (disable for speed)
if ! grep -q "AMAZONQ_RTK_ENABLED" ~/.bashrc 2>/dev/null; then
    echo ""
    read -p "Disable RTK for faster Q startup? (recommended) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "export AMAZONQ_RTK_ENABLED=false" >> ~/.bashrc
        echo "✅ RTK disabled (use ./rtk-toggle.sh to change)"
    fi
fi

# 10. Add to PATH (optional)
if ! grep -q "ai-observer" ~/.bashrc; then
    echo ""
    read -p "Add ai-observer to PATH? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "export PATH=\"$(pwd):\$PATH\"" >> ~/.bashrc
        echo "✅ Added to PATH - restart shell or run: source ~/.bashrc"
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Usage:"
echo "  ./q-observed       # Start Q with recording"
echo "  ./claude-observed  # Start Claude with recording"
echo "  ./search-sessions  # Search past work"
echo "  ./rtk-toggle.sh    # Toggle RTK mode"
echo ""
echo "Test it: ./q-observed"
