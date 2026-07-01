#!/usr/bin/env bash
# Start the mock mail server then launch langgraph dev.
# Run from the sales_assistant directory: ./start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting mock mail server on http://127.0.0.1:5001 ..."
uv run python "$SCRIPT_DIR/mcp/mock_mail_server.py" &
MAIL_PID=$!
trap "kill $MAIL_PID 2>/dev/null; wait $MAIL_PID 2>/dev/null" EXIT

# Wait until the server accepts connections (up to 10 seconds).
for i in $(seq 1 10); do
    if curl -s --max-time 1 http://127.0.0.1:5001/ >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "Mail server up (PID $MAIL_PID). Starting langgraph dev ..."
cd "$SCRIPT_DIR"
uv run langgraph dev
