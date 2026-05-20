# Docker Deployment

## Quick Start with Docker

```bash
# 1. Clone the repo
git clone https://github.com/kal1-linux/ai-observer.git
cd ai-observer

# 2. Build and run
docker-compose up -d

# 3. Enter the container
docker exec -it ai-observer bash

# 4. Start using
./q-observed      # For Q CLI
./claude-observed # For Claude Code
```

## What's Included

The Docker container includes:
- ✅ Ubuntu 22.04 base
- ✅ Python 3 + pip
- ✅ Mempalace MCP server (auto-started)
- ✅ ai-observer scripts
- ✅ Q CLI MCP config
- ✅ Claude Code MCP config
- ✅ asciinema, jq, git
- ✅ All dependencies

## Persistent Data

Sessions and mempalace data are stored in volumes:
- `./sessions` - Recorded session files
- `./mempalace-data` - Knowledge graph database

## Manual Build

```bash
# Build image
docker build -t ai-observer .

# Run container
docker run -it --name ai-observer \
  -v $(pwd)/sessions:/home/aiuser/.ai-observer/casts \
  -v $(pwd)/mempalace-data:/home/aiuser/mempalace/data \
  -p 8080:8080 \
  ai-observer
```

## Configuration

All configs are auto-generated on container start:
- Q CLI: `~/.config/amazonq/mcp.json`
- Claude: `~/.claude/settings.json`
- ai-observer: `~/ai-observer/config.env`

## Ports

- `8080` - Mempalace MCP server
- `2222` - SSH (optional, for remote access)

## Environment Variables

Set in `docker-compose.yml`:
- `MEMPALACE_SERVER=localhost`
- `USERNAME=aiuser`

## Troubleshooting

**Check mempalace is running:**
```bash
ps aux | grep mempalace
```

**Restart mempalace:**
```bash
cd ~/mempalace
source venv/bin/activate
python -m mempalace.mcp_server &
```

**View logs:**
```bash
docker logs ai-observer
```

## Production Deployment

For production, use a separate mempalace server:

1. Update `docker-compose.yml`:
```yaml
environment:
  - MEMPALACE_SERVER=your.server.ip
```

2. Update MCP configs to use SSH:
```json
{
  "command": "ssh",
  "args": ["root@your.server.ip", "cd /root/mempalace && ..."]
}
```
