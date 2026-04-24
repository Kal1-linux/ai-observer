#!/usr/bin/env bash
# Setup automatic daily backups
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add cron job for daily backup at 11:59 PM
CRON_CMD="59 23 * * * $SCRIPT_DIR/backup/backup-today.sh >> $SCRIPT_DIR/backup.log 2>&1"

(crontab -l 2>/dev/null | grep -v backup-today.sh; echo "$CRON_CMD") | crontab -

echo "✅ Backup cron job installed"
echo "📅 Runs daily at 11:59 PM"
echo "📝 Logs: $SCRIPT_DIR/backup.log"
crontab -l | grep backup-today
