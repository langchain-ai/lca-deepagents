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
CORRECT_KEY=$(node -e "require('dotenv').config({path: '$ENV_FILE'}); console.log(process.env.LANGSMITH_API_KEY || '')")

if [ -z "$CORRECT_KEY" ]; then
    echo "Could not read LANGSMITH_API_KEY from $ENV_FILE — check that file exists and has the key set." >&2
    exit 1
fi

echo "Starting agent-chat-ui on http://localhost:3000 ..."
exec env -u LANGSMITH_API_KEY LANGSMITH_API_KEY="$CORRECT_KEY" pnpm run dev
