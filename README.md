# AI Observer

Automatic session recording and memory extraction for Q CLI.

## What it does

1. **Records** every Q chat session with asciinema
2. **Extracts** key information (what you worked on, decisions, learnings)
3. **Stores** in mempalace (both drawer storage + knowledge graph)
4. **Remembers** across sessions - no need to re-explain context

## Usage

Instead of running `q chat`, run:

```bash
./q-observed
```

That's it! Work normally, and when you exit Q:
- Session is saved as `session-YYYYMMDD-HHMMSS.cast`
- Key information is automatically extracted and stored in mempalace
- Facts added to knowledge graph for easy retrieval
- Next time, Q can recall what you worked on

## Search past work

**Option 1: Ask Q directly**
```
"What did I work on today?"
"What tasks did I complete this week?"
```

**Option 2: Quick search script**
```bash
./search-sessions
```

**Option 3: Analytics dashboard**
```bash
./stats.sh
```

## Replay a session

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

## Files

- `q-observed` - Main script (use this instead of `q chat`)
- `search-sessions` - Quick search for all sessions
- `stats.sh` - Analytics dashboard (sessions/day, top tech, trends)
- `install.sh` - One-command setup for new machines
- `setup-backup-cron.sh` - Enable automatic daily backups
- `migrate-mempalace.sh` - Helper for server migration
- `config.env` - Configuration (server IP, username)
- `session-*.cast` - Recorded sessions (replayable with asciinema)
- Memory stored in mempalace at 192.168.1.137

## Requirements

- asciinema (`sudo apt install asciinema` or `brew install asciinema`)
- Q CLI with mempalace MCP server
- SSH access to mempalace server (192.168.1.137)
- Python 3 (for parsing)

## Features

✅ Deterministic storage (no LLM hallucination)  
✅ Knowledge graph integration  
✅ Session replay capability  
✅ Clean parsing (filters UI noise)  
✅ Fast SSH connection reuse  
✅ Duplicate detection  
✅ Searchable by Q across sessions  
✅ Robust error handling

## Stats

- **54 sessions** recorded and stored
- **59+ facts** in knowledge graph
- **100% reliability** after April 24 fixes
- **Top tech**: mempalace, SSH, bash, EKS, Kubernetes

## Installation (New Machine)

```bash
./install.sh
```

This will:
- Check dependencies
- Configure server/username
- Test SSH connection
- Create shell alias
- Make all scripts executable

## Optional: Enable Daily Backups

```bash
./setup-backup-cron.sh
```

## Status

✅ **PRODUCTION READY** - Battle-tested and fully operational
