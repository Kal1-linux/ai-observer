#!/bin/bash
# Copy your Q and Claude configs to Docker build context

echo "📋 Copying Q CLI config..."
mkdir -p .docker-configs/.config/amazonq
cp ~/.config/amazonq/mcp.json .docker-configs/.config/amazonq/ 2>/dev/null || echo "Q config not found"

echo "📋 Copying Claude config..."
mkdir -p .docker-configs/.claude
cp ~/.claude/settings.json .docker-configs/.claude/ 2>/dev/null || echo "Claude config not found"

echo "📋 Copying SSH keys..."
mkdir -p .docker-configs/.ssh
cp ~/.ssh/id_* .docker-configs/.ssh/ 2>/dev/null || echo "SSH keys not found"
cp ~/.ssh/config .docker-configs/.ssh/ 2>/dev/null || true

echo "✅ Configs copied to .docker-configs/"
echo "Now run: docker-compose build"
