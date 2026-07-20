#!/usr/bin/env bash
# Start agent-chat-ui for lesson m5.5, with LANGSMITH_API_KEY sourced from
# ../python/.env — the single source of truth for that key across this
# repo — rather than a copy in .env.local that can drift stale, and
# overriding any value the shell already has set (dotenv-style loaders,
# including Next.js's own, don't override an already-set env var).
# Run from this directory: ./start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CORRECT_KEY=$(cd "$SCRIPT_DIR/../python" && uv run python -c "
from dotenv import dotenv_values
print(dotenv_values('.env').get('LANGSMITH_API_KEY', ''))
")

if [ -z "$CORRECT_KEY" ]; then
    echo "Could not read LANGSMITH_API_KEY from python/.env — check that file exists and has the key set." >&2
    exit 1
fi

if [ ! -d node_modules ]; then
    echo "Installing dependencies (pnpm install) ..."
    pnpm install
fi

echo "Starting agent-chat-ui on http://localhost:3000 ..."
exec env -u LANGSMITH_API_KEY LANGSMITH_API_KEY="$CORRECT_KEY" pnpm run dev
