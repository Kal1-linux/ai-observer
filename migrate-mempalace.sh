#!/usr/bin/env bash
set -euo pipefail

# ==============================
# MemPalace Migration Script
# ==============================
# Migrates mempalace data from one server to another
# Usage: ./migrate-mempalace.sh <source-host> <target-host>

SOURCE_HOST="${1:-root@192.168.1.137}"
TARGET_HOST="${2:-}"

if [ -z "$TARGET_HOST" ]; then
    echo "Usage: $0 <source-host> <target-host>"
    echo "Example: $0 root@192.168.1.137 root@192.168.1.200"
    exit 1
fi

echo "🔄 MemPalace Migration"
echo "Source: $SOURCE_HOST"
echo "Target: $TARGET_HOST"
echo ""

# Check source exists
echo "📊 Checking source..."
SOURCE_SIZE=$(ssh "$SOURCE_HOST" "du -sh ~/.mempalace 2>/dev/null | cut -f1" || echo "NOT FOUND")
if [ "$SOURCE_SIZE" = "NOT FOUND" ]; then
    echo "❌ Source mempalace not found at $SOURCE_HOST"
    exit 1
fi
echo "✅ Source: $SOURCE_SIZE"

# Create backup on source
BACKUP_NAME="mempalace-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
echo ""
echo "📦 Creating backup on source..."
ssh "$SOURCE_HOST" "cd ~ && tar czf $BACKUP_NAME .mempalace"
echo "✅ Backup created: $BACKUP_NAME"

# Transfer to target
echo ""
echo "🚀 Transferring to target..."
ssh "$SOURCE_HOST" "cat ~/$BACKUP_NAME" | ssh "$TARGET_HOST" "cat > /tmp/$BACKUP_NAME"
echo "✅ Transfer complete"

# Extract on target
echo ""
echo "📂 Extracting on target..."
ssh "$TARGET_HOST" "cd ~ && tar xzf /tmp/$BACKUP_NAME && rm /tmp/$BACKUP_NAME"
echo "✅ Extracted"

# Verify
echo ""
echo "🔍 Verifying..."
TARGET_SIZE=$(ssh "$TARGET_HOST" "du -sh ~/.mempalace 2>/dev/null | cut -f1" || echo "FAILED")
if [ "$TARGET_SIZE" = "FAILED" ]; then
    echo "❌ Verification failed"
    exit 1
fi

echo "✅ Target: $TARGET_SIZE"
echo ""
echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Update q-observed script with new host: $TARGET_HOST"
echo "2. Test connection: ssh $TARGET_HOST 'cd /root/mempalace && source venv/bin/activate && python -c \"from mempalace.mcp_server import tool_status; print(tool_status())\"'"
echo "3. Keep backup on source: ssh $SOURCE_HOST ls -lh ~/$BACKUP_NAME"
