# AI Observer

Automatic session recording and memory extraction for Q CLI.

## What it does

1. **Records** every Q chat session with asciinema
2. **Extracts** key information (what you worked on, decisions, learnings)
3. **Stores** in mempalace (both drawer storage + knowledge graph)
4. **Remembers** across sessions - no need to re-explain context

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/ai-observer.git
cd ai-observer
./install.sh

# 2. Configure
cp config.env.example config.env
# Edit config.env with your mempalace server IP and username

# 3. Use instead of `q chat`
./q-observed
```

## Usage

Instead of running `q chat`, run:

```bash
./q-observed
```

Work normally, and when you exit Q:
- Session saved as `session-YYYYMMDD-HHMMSS.cast`
- Key information automatically extracted and stored
- Facts added to knowledge graph
- Next time, Q recalls what you worked on

## Search past work

**Ask Q directly:**
```
"What did I work on today?"
"What tasks did I complete this week?"
```

**Quick search:**
```bash
./search-sessions
```

**Analytics:**
```bash
./stats.sh
```

**Replay session:**
```bash
asciinema play session-20260424-063356.cast
```

## Architecture

```
Session Recording (asciinema)
    ↓
Local Parsing (Python - removes UI noise)
    ↓
AI Analysis (Q CLI - extracts structured JSON)
    ↓
Direct Storage (SSH → mempalace MCP server)
    ├─ Drawer: ai-observer/sessions (full JSON)
    └─ Knowledge Graph: facts about your work
```

## Requirements

- **asciinema** - `sudo apt install asciinema` or `brew install asciinema`
- **Q CLI** - with mempalace MCP server configured
- **SSH access** - to your mempalace server
- **Python 3** - for parsing (usually pre-installed)
- **jq** - `sudo apt install jq` or `brew install jq`

## Features

✅ Deterministic storage (no LLM hallucination)  
✅ Knowledge graph integration  
✅ Session replay capability  
✅ Clean parsing (filters UI noise)  
✅ Fast SSH connection reuse  
✅ Duplicate detection  
✅ Searchable by Q across sessions  
✅ Robust error handling with fallback  
✅ Local persistence for failed uploads

## Scripts

- `q-observed` - Main wrapper (use instead of `q chat`)
- `search-sessions` - Search all stored sessions
- `latest-sessions` - Show 5 most recent sessions
- `stats.sh` - Analytics dashboard
- `install.sh` - One-command setup
- `setup-backup-cron.sh` - Enable daily backups
- `migrate-mempalace.sh` - Server migration helper

## Configuration

Edit `config.env`:
```bash
MEMPALACE_SERVER=your.server.ip
USERNAME=your_username
```

## Optional: Daily Backups

```bash
./setup-backup-cron.sh
```

## How it works

1. **Recording**: asciinema captures terminal session
2. **Parsing**: Python removes UI noise, extracts user interactions
3. **Analysis**: Q CLI analyzes session, returns structured JSON
4. **Validation**: jq validates JSON (fallback if invalid)
5. **Storage**: SSH to mempalace server, store in ChromaDB
6. **Knowledge Graph**: Extract facts (worked_on, completed_task)
7. **Local Backup**: Save to `./failed-sessions/` for reliability

## Troubleshooting

**Session not stored?**
- Check `./failed-sessions/` for local backup
- Verify SSH connection: `ssh root@YOUR_SERVER`
- Check mempalace server is running

**Q analysis fails?**
- Fallback mode activates automatically
- Raw session text stored with `fallback` tag
- Check `./failed-sessions/` for JSON

**Permission denied?**
- Run: `chmod +x q-observed install.sh`

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

PRs welcome! This is a personal productivity tool that might help others.

## Status

✅ **PRODUCTION READY** - Battle-tested and fully operational
