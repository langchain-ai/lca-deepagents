# python/m1/gh_auth/step3.py
"""GitHub MCP — Step 3: exchange the authorization code for an access token
and retry the gated tools/call.

Step 2 saved the authorization code and PKCE code_verifier to
.m1_github_state.json. This program:
  1. Reads that state.
  2. Resolves the token_endpoint via RFC 8414 discovery.
  3. POSTs code + code_verifier + client credentials to the token endpoint.
  4. Retries the gated tools/call with Authorization: Bearer.
  5. Prints the tool result.
  6. Deletes the state file (code was single-use).

Requires in .env:
  GITHUB_CLIENT_ID
  GITHUB_CLIENT_SECRET

Run immediately after Step 2 — the authorization code expires in minutes.
  uv run python m1/gh_auth/step3.py
"""

from __future__ import annotations

import json
import os
import urllib.parse
from pathlib import Path

import httpx
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

STATE_FILE = Path(__file__).resolve().parent.parent.parent / ".m1_github_state.json"
TOKEN_FILE = Path(__file__).resolve().parent.parent.parent / ".m1_github_token"

ISSUER = "https://github.com/login/oauth"
DISCOVERY_URL = "https://github.com/.well-known/oauth-authorization-server"

MCP_URL = "https://api.githubcopilot.com/mcp/"
MCP_HEADERS_BASE = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}

TRUSTED_GITHUB_HOSTS = {"github.com", "api.github.com"}


def _trusted_github_host(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    return host in TRUSTED_GITHUB_HOSTS


def _parse_json(resp: httpx.Response) -> dict:
    """Parse a response that may be plain JSON or SSE (data: {...} lines)."""
    ct = resp.headers.get("content-type", "")
    if "text/event-stream" in ct:
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload and payload != "[DONE]":
                    return json.loads(payload)
        return {}
    return resp.json()


def load_state() -> dict:
    if not STATE_FILE.exists():
        raise SystemExit(
            f"State file not found: {STATE_FILE.name}\n"
            "Run step2.py first."
        )
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"Could not read state file: {exc}") from exc


def discover_token_endpoint() -> str:
    """Resolve the token endpoint via RFC 8414, or derive from the issuer URL."""
    if not _trusted_github_host(DISCOVERY_URL):
        raise SystemExit(f"Refusing to fetch discovery from: {DISCOVERY_URL}")
    try:
        with httpx.Client(trust_env=False, timeout=15) as client:
            data = client.get(DISCOVERY_URL).json()
        token_ep = data.get("token_endpoint")
        if token_ep:
            return token_ep
    except (httpx.HTTPError, ValueError):
        pass
    # GitHub does not publish RFC 8414; derive from issuer URL.
    return ISSUER.rstrip("/") + "/access_token"


def exchange_code(
    token_endpoint: str,
    state: dict,
    client_id: str,
    client_secret: str,
) -> str:
    if not _trusted_github_host(token_endpoint):
        raise SystemExit(
            f"Refusing to POST to untrusted token endpoint: {token_endpoint}"
        )
    with httpx.Client(trust_env=False, timeout=15) as client:
        resp = client.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": state["code"],
                "code_verifier": state["code_verifier"],
                "redirect_uri": state["redirect_uri"],
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        raise SystemExit(
            f"Token exchange failed {resp.status_code}: {resp.text[:200]}"
        )
    token = resp.json().get("access_token")
    if not token:
        raise SystemExit(f"Token response missing access_token: {resp.text[:200]}")
    return token


def retry_tools_call(access_token: str) -> None:
    headers = {**MCP_HEADERS_BASE, "Authorization": f"Bearer {access_token}"}
    with httpx.Client(trust_env=False, timeout=15) as client:
        client.post(MCP_URL, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "m1-github-step3", "version": "0.1"},
            },
        }, headers=headers)

        resp = client.post(MCP_URL, json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_me", "arguments": {}},
        }, headers=headers)

    print(f"tools/call  -> HTTP {resp.status_code} {resp.reason_phrase}")
    try:
        data = _parse_json(resp)
    except (json.JSONDecodeError, ValueError):
        print(f"  (could not parse response: {resp.text[:200]})")
        return
    result = data.get("result", {})
    content = result.get("content", [])
    for item in content:
        if item.get("type") == "text":
            print(item["text"])


def main() -> None:
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit(
            "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env."
        )

    state = load_state()

    token_endpoint = discover_token_endpoint()
    print(f"Token endpoint: {token_endpoint}\n")

    print("Exchanging authorization code for access token...")
    access_token = exchange_code(token_endpoint, state, client_id, client_secret)
    shown = access_token[:12] + "..." if len(access_token) > 12 else "(short)"
    print(f"Access token (truncated): {shown}  [{len(access_token)} chars]")

    STATE_FILE.unlink(missing_ok=True)
    print("State file deleted (code was single-use).")
    TOKEN_FILE.write_text(access_token)
    print(f"Access token saved to {TOKEN_FILE.name}.\n")

    print("Retrying tools/call with Bearer token:")
    retry_tools_call(access_token)


if __name__ == "__main__":
    main()
