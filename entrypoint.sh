#!/bin/bash
set -e

mkdir -p /app/app/logs

# Start MCP server in background
python3 /app/mcp-server/server.py &

for i in $(seq 1 15); do
    python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1',55001)); s.close()" 2>/dev/null && break
    sleep 1
done

# Start FastAPI app in background
python3 /app/app/main.py &

for i in $(seq 1 60); do
    python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('127.0.0.1',55000)); s.close()" 2>/dev/null && break
    sleep 1
done

LOG=$(ls -t /app/app/logs/*.jsonl 2>/dev/null | head -1)

if [ -z "$LOG" ]; then
    echo "⚠ No log file — waiting on app"
    wait
    exit $?
fi

echo ""
echo "→ $LOG"
echo ""

exec python3 /app/app/log_viewer.py "$LOG"
