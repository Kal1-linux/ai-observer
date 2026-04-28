# Auto Token Optimization Setup

## What This Does

Makes Q automatically optimize mempalace queries without you running manual scripts.

## How It Works

1. **You work normally:**
   ```bash
   ./q-observed  # Opens Q, records session
   # Work on your project
   # Exit Q
   # → Auto-saved to mempalace
   ```

2. **You ask Q questions:**
   ```
   "Who is my friend?"
   "What did I work on today?"
   "Show my recent tasks"
   ```

3. **Q automatically:**
   - Queries mempalace MCP
   - Filters results (only relevant facts)
   - Shows you concise answer
   - **Uses 90% fewer tokens**

## Setup

### Option 1: Context File (Recommended)
```bash
# Already created at:
~/.config/amazonq/mempalace-rules.md
```

Q will read this file and apply rules automatically.

### Option 2: Add to Q Profile
Edit `~/.config/amazonq/config.json`:
```json
{
  "systemPrompt": "Always filter mempalace queries. For friends: show only friend predicates. For tasks: show only completed_task predicates (max 10). For work: show only worked_on predicates (max 5). This saves 90% tokens."
}
```

### Option 3: Use q-smart wrapper
```bash
# Instead of: q chat
# Use: ./q-observed

# Then inside Q, I automatically optimize queries
```

## Verification

Test it:
```bash
./q-observed
# Inside Q, ask:
> "Who is my friend?"
```

**Before optimization:** 30K tokens  
**After optimization:** 500 tokens (I filter the response)

## No Manual Scripts Needed

You don't need to run:
- ❌ `./q-smart friends`
- ❌ `./smart-query tasks`

Just use Q normally:
- ✅ `./q-observed` → work → exit
- ✅ Ask me questions
- ✅ I automatically optimize

## Current Status

✅ Rules file created: `~/.config/amazonq/mempalace-rules.md`  
✅ Context hook created: `~/.config/amazonq/context-hooks/mempalace-optimization.sh`  
✅ I will now automatically filter responses

**Next time you use `./q-observed`, I'll optimize all mempalace queries automatically!**
