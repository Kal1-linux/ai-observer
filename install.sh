#!/usr/bin/env bash
# AI Observer - One-command installation
set -e

echo "🚀 Installing AI Observer..."

# Check dependencies
command -v asciinema >/dev/null || { echo "❌ asciinema not found. Install: sudo apt install asciinema"; exit 1; }
command -v python3 >/dev/null || { echo "❌ python3 not found"; exit 1; }
command -v q >/dev/null || { echo "❌ Q CLI not found"; exit 1; }

# Get config
read -p "Mempalace server IP [${MEMPALACE_SERVER}]: " SERVER
SERVER=${SERVER:-${MEMPALACE_SERVER}}
read -p "Your username [$(whoami)]: " USERNAME
USERNAME=${USERNAME:-$(whoami)}

# Create config
cat > config.env <<EOF
MEMPALACE_SERVER=$SERVER
USERNAME=$USERNAME
EOF

echo "✅ Config saved to config.env"

# Test SSH
echo "🔐 Testing SSH connection..."
ssh -o ConnectTimeout=5 root@$SERVER "echo 'SSH OK'" || { echo "❌ SSH failed"; exit 1; }

# Make scripts executable
chmod +x q-observed search-sessions migrate-mempalace.sh backup/*.sh

# Create alias
SHELL_RC="$HOME/.bashrc"
[[ "$SHELL" == *"zsh"* ]] && SHELL_RC="$HOME/.zshrc"

if ! grep -q "alias q=" "$SHELL_RC" 2>/dev/null; then
    echo "alias q='$(pwd)/q-observed'" >> "$SHELL_RC"
    echo "✅ Added alias 'q' to $SHELL_RC"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  q              # Start observed Q session"
echo "  ./search-sessions  # Search past work"
echo ""
echo "Reload shell: source $SHELL_RC"
