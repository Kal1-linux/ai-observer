#!/usr/bin/env bash
# Claude Reasoning Effort Toggle for Claude Code
# Controls reasoning/effort level via CLAUDE_CODE_EFFORT_LEVEL variable in ~/.bashrc

case "$1" in
    on|high)
        sed -i '/CLAUDE_CODE_EFFORT_LEVEL/d' ~/.bashrc 2>/dev/null || true
        echo "export CLAUDE_CODE_EFFORT_LEVEL=high" >> ~/.bashrc
        echo "✅ Claude effort enabled (set to high - more reasoning)"
        echo "🔄 Run: source ~/.bashrc"
        ;;
    max)
        sed -i '/CLAUDE_CODE_EFFORT_LEVEL/d' ~/.bashrc 2>/dev/null || true
        echo "export CLAUDE_CODE_EFFORT_LEVEL=max" >> ~/.bashrc
        echo "✅ Claude effort enabled (set to max - maximum reasoning)"
        echo "🔄 Run: source ~/.bashrc"
        ;;
    off|low)
        sed -i '/CLAUDE_CODE_EFFORT_LEVEL/d' ~/.bashrc 2>/dev/null || true
        echo "export CLAUDE_CODE_EFFORT_LEVEL=low" >> ~/.bashrc
        echo "✅ Claude effort disabled (set to low - faster responses)"
        echo "🔄 Run: source ~/.bashrc"
        ;;
    status)
        if grep -q "CLAUDE_CODE_EFFORT_LEVEL=low" ~/.bashrc 2>/dev/null; then
            echo "❌ Claude effort is LOW (fast mode)"
        elif grep -q "CLAUDE_CODE_EFFORT_LEVEL=high" ~/.bashrc 2>/dev/null; then
            echo "✅ Claude effort is HIGH (reasoning mode)"
        elif grep -q "CLAUDE_CODE_EFFORT_LEVEL=max" ~/.bashrc 2>/dev/null; then
            echo "🔥 Claude effort is MAX (maximum reasoning mode)"
        elif grep -q "CLAUDE_CODE_EFFORT_LEVEL=" ~/.bashrc 2>/dev/null; then
            CURRENT_VAL=$(grep "CLAUDE_CODE_EFFORT_LEVEL=" ~/.bashrc | cut -d'=' -f2)
            echo "ℹ️ Claude effort is set to: $CURRENT_VAL"
        else
            echo "⚠️  Claude effort not configured (default: auto)"
        fi
        ;;
    *)
        echo "Usage: ./claude-toggle.sh [on|off|high|max|low|status]"
        echo ""
        echo "  on/high - Set effort to HIGH (reasoning mode)"
        echo "  max     - Set effort to MAX (maximum reasoning)"
        echo "  off/low - Set effort to LOW (fast mode)"
        echo "  status  - Check current effort state"
        exit 1
        ;;
esac
