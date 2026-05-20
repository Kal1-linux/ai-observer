# Docker Setup with Q CLI and Claude Code

## Quick Start (Scripts Only)

```bash
docker-compose up -d
docker exec -it ai-observer bash
```

## Full Setup (Q CLI + Claude Code)

### Step 1: Start Container
```bash
docker-compose up -d
docker exec -it ai-observer bash
```

### Step 2: Install Q CLI (Inside Container)
```bash
# Download Q CLI installer
curl -fsSL https://d3vv6lp55qjaqc.cloudfront.net/items/q-cli-install.sh | bash

# Or copy from host
exit
docker cp ~/.local/bin/q ai-observer:/home/aiuser/.local/bin/
docker exec -it ai-observer bash
```

### Step 3: Install Claude Code (Inside Container)
```bash
# Download Claude Code
wget https://claude.ai/download/linux -O claude-code.deb
sudo dpkg -i claude-code.deb

# Or copy from host
exit
docker cp /usr/local/bin/claude ai-observer:/usr/local/bin/
docker exec -it ai-observer bash
```

### Step 4: Copy Configs (From Host)
```bash
# Exit container first
exit

# Copy Q config
docker cp ~/.config/amazonq/mcp.json ai-observer:/home/aiuser/.config/amazonq/

# Copy Claude config
docker cp ~/.claude/settings.json ai-observer:/home/aiuser/.claude/

# Copy SSH keys
docker cp ~/.ssh/id_rsa ai-observer:/home/aiuser/.ssh/
docker cp ~/.ssh/id_rsa.pub ai-observer:/home/aiuser/.ssh/

# Fix permissions
docker exec ai-observer chmod 600 /home/aiuser/.ssh/id_rsa
```

### Step 5: Test
```bash
docker exec -it ai-observer bash
cd ai-observer
./q-observed      # Test Q CLI
./claude-observed # Test Claude Code
```

## Alternative: Use Host Installation

**Recommended:** Use ai-observer on your host machine where Q and Claude are already installed.

```bash
cd /home/prathammodi/ai-observer
./q-observed      # Already working
./claude-observed # Already working
```

Docker is best for:
- Sharing the project
- CI/CD testing
- Clean environment testing

Your host setup is already perfect! ✅
