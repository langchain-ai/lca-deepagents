#!/usr/bin/env bash
# Start the mock mail server, the chat UI, then launch langgraph dev.
# Run from the sales_assistant directory: ./start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill any leftover mail server or chat UI from a previous run.
for PORT in 5002 3000; do
    OLD_PID=$(lsof -ti ":$PORT" 2>/dev/null || true)
    if [ -n "$OLD_PID" ]; then
        echo "Port $PORT already in use (PID $OLD_PID) — killing it ..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi
done

echo "Starting mock mail server on http://127.0.0.1:5002 ..."
npx tsx "$SCRIPT_DIR/mcp/mock_mail_server.ts" &
MAIL_PID=$!

echo "Starting agent-chat-ui on http://localhost:3000 ..."
AGENT_CHAT_UI_DIR="$(cd "$SCRIPT_DIR/../../../agent-chat-ui" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env" "$AGENT_CHAT_UI_DIR/start.sh" &
UI_PID=$!

# Kill the mail server and the chat UI on Ctrl-C, normal exit, or TERM.
cleanup() {
    kill "$MAIL_PID" 2>/dev/null || true
    kill "$UI_PID" 2>/dev/null || true
    # pnpm run dev spawns `next dev` as a child, not a replacement, process —
    # killing the parent PID alone can leave it (and next-server) orphaned.
    pkill -f "next dev" 2>/dev/null || true
    wait "$MAIL_PID" "$UI_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait until the server accepts connections (up to 10 seconds).
for i in $(seq 1 10); do
    if curl -s --max-time 1 http://127.0.0.1:5002/ >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "Mail server up (PID $MAIL_PID), chat UI starting (PID $UI_PID). Starting langgraph dev ..."
cd "$SCRIPT_DIR"

pnpm exec langgraphjs dev "$@"
