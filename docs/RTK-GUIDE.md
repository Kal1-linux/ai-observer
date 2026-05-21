# RTK Mode Guide

## What is RTK?

**RTK (Runtime Token Knowledge)** is a Q CLI feature that scans your filesystem to provide additional context. While useful, it significantly slows down Q startup time.

## Quick Commands

```bash
# Check current status
./rtk-toggle.sh status

# Disable RTK (faster startup - recommended)
./rtk-toggle.sh off
source ~/.bashrc

# Enable RTK (more context, slower)
./rtk-toggle.sh on
source ~/.bashrc
```

## When to Use Each Mode

### RTK OFF (Recommended) ⚡
- **Faster Q startup** (2-3 seconds)
- Still has full mempalace access
- Best for daily use
- All ai-observer features work normally

### RTK ON 🐌
- **Slower Q startup** (5-10+ seconds)
- Scans filesystem for additional context
- Only needed for specific use cases
- Not required for ai-observer functionality

## What We Did

1. Added `AMAZONQ_RTK_ENABLED=false` to `~/.bashrc`
2. This disables RTK globally for all Q sessions
3. Q still shows `[RTK ACTIVE PATH OVERRIDE]` message (cosmetic only)
4. Actual RTK scanning is disabled (confirmed by fast startup)

## Troubleshooting

**Q still slow?**
- Run: `./rtk-toggle.sh status`
- Verify it says "RTK is OFF"
- Restart terminal: `source ~/.bashrc`

**Message still shows?**
- The `[RTK ACTIVE PATH OVERRIDE]` message is just Q's output
- It doesn't mean RTK is actually running
- Check startup time: under 3 seconds = RTK is off

## Technical Details

RTK is controlled by the `AMAZONQ_RTK_ENABLED` environment variable:
- `false` = disabled (fast)
- `true` = enabled (slow)
- unset = enabled by default

The toggle script modifies `~/.bashrc` to set this variable permanently.
