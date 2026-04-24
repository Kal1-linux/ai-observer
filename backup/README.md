# Backup Scripts

Emergency backup tools to save .cast files directly to mempalace if normal processing fails.

## Usage

**Backup single session:**
```bash
cd backup
./backup-cast.sh ../session-20260424-063356.cast
```

**Backup all today's sessions:**
```bash
cd backup
./backup-today.sh
```

## What it does

- Uploads raw .cast file to mempalace
- Stores in `ai-observer/backup-casts` room
- No parsing, no analysis - just raw backup
- Your data is never lost

## When to use

- If q-observed fails to store session
- If JSON extraction fails
- As a safety net for important sessions
- End of day backup

## Storage location

All backups go to: `mempalace → ai-observer/backup-casts`

You can retrieve them later and reprocess with the main script.
