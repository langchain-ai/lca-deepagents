#!/usr/bin/env bash
# Start the mock mail server, the chat UI, then launch langgraph dev.
# Run from the sales_assistant_sandbox directory: ./start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill any leftover mail server or chat UI from a previous run.
for PORT in 5002 3000 3001; do
    OLD_PID=$(lsof -ti ":$PORT" 2>/dev/null || true)
    if [ -n "$OLD_PID" ]; then
        echo "Port $PORT already in use (PID $OLD_PID) — killing it ..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
    fi
done

echo "Starting mock mail server on http://127.0.0.1:5002 ..."
uv run python "$SCRIPT_DIR/mcp/mock_mail_server.py" &
MAIL_PID=$!

echo "Starting agent-chat-ui on http://localhost:3000 ..."
AGENT_CHAT_UI_DIR="$(cd "$SCRIPT_DIR/../../../agent-chat-ui" && pwd)"
"$AGENT_CHAT_UI_DIR/start.sh" &
UI_PID=$!

# Optional: langchain-ai/deep-agents-ui, for trying it side-by-side with
# agent-chat-ui. Not part of the lesson — only runs if that sibling repo
# happens to exist on this machine (~/Documents/Github/deep-agents-ui).
# It has no async-subagent or real-sandbox file support (see m5.5 notes),
# so the newsletter/async-task/sandbox-files features won't show up here.
DEEP_AGENTS_UI_DIR="$HOME/Documents/Github/deep-agents-ui"
DEEP_AGENTS_UI_PID=""
if [ -d "$DEEP_AGENTS_UI_DIR" ]; then
    echo "Starting deep-agents-ui on http://localhost:3001 ..."
    (
        cd "$DEEP_AGENTS_UI_DIR"
        if [ ! -d node_modules ]; then
            echo "Installing deep-agents-ui dependencies (yarn install) ..."
            yarn install
        fi
        yarn dev --port 3001
    ) &
    DEEP_AGENTS_UI_PID=$!
fi

# Kill the mail server, the chat UI, and stop any running sandboxes on
# Ctrl-C, normal exit, or TERM — so a student closing this script doesn't
# keep paying for sandbox compute until idle_ttl_seconds catches up.
cleanup() {
    # `set -e` applies inside a trap too. On a real Ctrl-C, the mail server
    # and chat UI are in the same process group as this script and often die
    # from the same SIGINT before these lines run — so `kill` on an
    # already-dead PID returns non-zero, and without `|| true` that would
    # abort cleanup() right here, silently skipping the sandbox-stop step.
    kill "$MAIL_PID" 2>/dev/null || true
    kill "$UI_PID" 2>/dev/null || true
    [ -n "$DEEP_AGENTS_UI_PID" ] && kill "$DEEP_AGENTS_UI_PID" 2>/dev/null || true
    # pnpm/yarn run dev spawns `next dev` as a child, not a replacement,
    # process — killing the parent PID alone can leave it (and
    # next-server) orphaned.
    pkill -f "next dev" 2>/dev/null || true
    wait "$MAIL_PID" "$UI_PID" 2>/dev/null || true
    echo "Stopping any running sandboxes ..."
    uv run python "$SCRIPT_DIR/stop_sandboxes.py" || true
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

# langgraph dev's local queue defaults to 1 worker slot. Async subagents
# (genre-researcher) each hold a slot for their whole run, so the default
# starves the main thread of a slot to handle new messages while they're
# in flight — see docs.langchain.com/oss/python/deepagents/async-subagents.
uv run langgraph dev --n-jobs-per-worker 10
