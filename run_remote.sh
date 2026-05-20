#!/usr/bin/env bash
# Helper to run commands on Mempalace server via SSH
# Usage: source run_remote.sh; run_remote "command"
# Or: bash run_remote.sh "command"

source "$(dirname "$0")/config.env" 2>/dev/null || {
    MEMPALACE_SERVER=192.168.1.137
    USERNAME=$(whoami)
}
export MEMPALACE_SERVER USERNAME

run_remote() {
    ssh "root@$MEMPALACE_SERVER" "$@"
}

# If script is executed (not sourced), run the command directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ $# -eq 0 ]; then
        echo "Usage: $0 <command>"
        exit 1
    fi
    run_remote "$@"
fi
