#!/usr/bin/env bash
# Backup all .cast files from today

cd "$(dirname "$0")/.."
TODAY=$(date +%Y%m%d)

echo "📦 Backing up all sessions from $TODAY..."

count=0
for file in session-${TODAY}-*.cast; do
    if [ -f "$file" ]; then
        echo "Uploading $file..."
        ./backup/backup-cast.sh "$file" && ((count++))
    fi
done

echo "✅ Backup complete: $count files uploaded"
