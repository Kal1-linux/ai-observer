#!/usr/bin/env bash
source "$(dirname "$0")/config.env"
exec ssh -o ControlMaster=auto \
    -o ControlPath=~/.ssh/mempalace-%r@%h:%p \
    -o ControlPersist=yes \
    "root@$MEMPALACE_SERVER" \
    "cd /root/mempalace && /root/mempalace/venv/bin/python -m mempalace.mcp_server"
