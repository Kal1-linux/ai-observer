#!/usr/bin/env bash
# RTK Mode Toggle for Q CLI
# RTK (Runtime Token Knowledge) scans your filesystem for context but slows startup

case "$1" in
    on)
        sed -i '/AMAZONQ_RTK_ENABLED/d' ~/.bashrc
        echo "export AMAZONQ_RTK_ENABLED=true" >> ~/.bashrc
        echo "✅ RTK enabled (slower startup, more context)"
        echo "🔄 Run: source ~/.bashrc"
        ;;
    off)
        sed -i '/AMAZONQ_RTK_ENABLED/d' ~/.bashrc
        echo "export AMAZONQ_RTK_ENABLED=false" >> ~/.bashrc
        echo "✅ RTK disabled (faster startup)"
        echo "🔄 Run: source ~/.bashrc"
        ;;
    status)
        if grep -q "AMAZONQ_RTK_ENABLED=false" ~/.bashrc 2>/dev/null; then
            echo "❌ RTK is OFF (fast mode)"
        elif grep -q "AMAZONQ_RTK_ENABLED=true" ~/.bashrc 2>/dev/null; then
            echo "✅ RTK is ON (context mode)"
        else
            echo "⚠️  RTK not configured (default: ON)"
        fi
        ;;
    *)
        echo "Usage: ./rtk-toggle.sh [on|off|status]"
        echo ""
        echo "  on      - Enable RTK (more context, slower)"
        echo "  off     - Disable RTK (faster startup)"
        echo "  status  - Check current RTK state"
        exit 1
        ;;
esac
