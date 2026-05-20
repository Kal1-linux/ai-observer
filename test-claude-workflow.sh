#!/bin/bash
echo "🧪 Testing claude-observed full workflow"
echo ""
echo "1. Starting claude-observed..."
echo "2. You'll interact with Claude for ~2 minutes"
echo "3. Ask Claude: 'Who is Nikhil?' (test mempalace auto-search)"
echo "4. Ask Claude: 'What can you help me with?'"
echo "5. Type /exit to end"
echo ""
echo "After exit, we'll verify:"
echo "  - Session recorded"
echo "  - Session analyzed"
echo "  - Stored in mempalace claude-sessions wing"
echo ""
read -p "Press Enter to start..."

./claude-observed
