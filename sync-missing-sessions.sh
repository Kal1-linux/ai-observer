#!/usr/bin/env bash
# Sync missing sessions to mempalace

STORED_SESSIONS=(
"session-20260423-062246"
"session-20260423-065009"
"session-20260423-070019"
"session-20260423-070317"
"session-20260423-071523"
"session-20260423-090700"
"session-20260423-100131"
"session-20260423-125020"
"session-20260423-133703"
"session-20260423-184733"
"session-20260423-185450"
"session-20260423-191116"
"session-20260423-192852"
"session-20260423-193716"
"session-20260423-195007"
"session-20260424-055312"
"session-20260424-061815"
"session-20260424-062552"
"session-20260424-063002"
"session-20260424-063356"
"session-20260424-064400"
)

echo "🔍 Finding missing sessions..."
missing=0

for cast in session-*.cast; do
    name=$(basename "$cast" .cast)
    found=0
    for stored in "${STORED_SESSIONS[@]}"; do
        if [ "$name" = "$stored" ]; then
            found=1
            break
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo "❌ Missing: $cast"
        ((missing++))
    fi
done

echo ""
echo "📊 Summary:"
echo "  Total local: 51"
echo "  Stored: ${#STORED_SESSIONS[@]}"
echo "  Missing: $missing"
echo ""

if [ $missing -gt 0 ]; then
    read -p "Backup all missing sessions to mempalace? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Starting backup..."
        for cast in session-*.cast; do
            name=$(basename "$cast" .cast)
            found=0
            for stored in "${STORED_SESSIONS[@]}"; do
                if [ "$name" = "$stored" ]; then
                    found=1
                    break
                fi
            done
            
            if [ $found -eq 0 ]; then
                echo "Backing up $cast..."
                ./backup/backup-cast.sh "$cast"
            fi
        done
        echo "✅ Backup complete!"
    fi
fi
