#!/usr/bin/env bash
# Start agent-chat-ui, with LANGSMITH_API_KEY sourced from the calling
# lesson's .env file (rather than a copy in .env.local that can drift
# stale), overriding any value the shell already has set (dotenv-style
# loaders, including Next.js's own, don't override an already-set env var).
#
# The caller picks which .env to read via ENV_FILE (e.g. typescript/.env
# for a TypeScript lesson); it defaults to python/.env so lessons that
# don't set it keep working unchanged. Read with Node's dotenv package
# (already a dependency of this app) rather than Python, since a lesson
# that only needs this UI shouldn't require a working Python install.
# Run from this directory: ./start.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d node_modules ]; then
    echo "Installing dependencies (pnpm install) ..."
    pnpm install
fi

ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/../python/.env}"
# `override: true` so the file's value wins over an already-set shell var, and
# `.parsed` so the value comes straight from the file rather than through
# process.env at all. Either alone would fix this; both together mean it can't
# silently pick up an outer shell's key pointing at a different workspace.
# `quiet: true` stops dotenv v17+ printing its startup banner to stdout, which
# would otherwise be captured into CORRECT_KEY along with the key itself.
CORRECT_KEY=$(node -e "const parsed = require('dotenv').config({path: '$ENV_FILE', override: true, quiet: true}).parsed || {}; process.stdout.write(parsed.LANGSMITH_API_KEY || '')")

if [ -z "$CORRECT_KEY" ]; then
    echo "Could not read LANGSMITH_API_KEY from $ENV_FILE — check that file exists and has the key set." >&2
    exit 1
fi

echo "Starting agent-chat-ui on http://localhost:3000 ..."
exec env -u LANGSMITH_API_KEY LANGSMITH_API_KEY="$CORRECT_KEY" pnpm run dev
