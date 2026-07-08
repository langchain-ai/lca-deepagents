#!/usr/bin/env bash
# Start the mock mail server then launch langgraph dev.
# Run from the sales_assistant directory: ./start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill any leftover mail server from a previous run.
OLD_PID=$(lsof -ti :5002 2>/dev/null || true)
if [ -n "$OLD_PID" ]; then
    echo "Port 5002 already in use (PID $OLD_PID) — killing it ..."
    kill "$OLD_PID" 2>/dev/null || true
    sleep 1
fi

echo "Starting mock mail server on http://127.0.0.1:5002 ..."
npx tsx "$SCRIPT_DIR/mcp/mock_mail_server.ts" &
MAIL_PID=$!

# Kill the mail server on Ctrl-C, normal exit, or TERM.
cleanup() {
    kill "$MAIL_PID" 2>/dev/null
    wait "$MAIL_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

# Wait until the server accepts connections (up to 10 seconds).
for i in $(seq 1 10); do
    if curl -s --max-time 1 http://127.0.0.1:5002/ >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "Mail server up (PID $MAIL_PID). Starting langgraph dev ..."
cd "$SCRIPT_DIR"

pnpm exec langgraphjs dev "$@"
