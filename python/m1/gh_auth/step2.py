# python/m1/gh_auth/step2.py
"""GitHub MCP — Step 2: PKCE + browser consent, capture the authorization code.

Step 1 discovered the authorization server and the required scopes.
Step 2 takes the next leg of the OAuth sequence and stops at the
**authorization code**:
  1. Resolve the authorization server's real OAuth endpoints via RFC 8414
     discovery (so this program runs standalone).
  2. Generate PKCE (code_verifier + code_challenge).
  3. Build the authorization URL and open the browser for login + consent.
  4. Catch the ?code= redirect on a one-shot localhost listener.

We deliberately STOP here. The code is short-lived and single-use; Step 3
exchanges it (with the code_verifier + client_secret) for an access token.

Requires in .env:
  GITHUB_CLIENT_ID

When registering your OAuth App at github.com/settings/developers, use
  http://127.0.0.1
as the Authorization callback URL. GitHub validates the host but not the port
for loopback addresses (RFC 8252), so the script can use an ephemeral port.

Run:  uv run python m1/gh_auth/step2.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

ISSUER = "https://github.com/login/oauth"
DISCOVERY_URL = "https://github.com/.well-known/oauth-authorization-server"

TRUSTED_GITHUB_HOSTS = {"github.com", "api.github.com"}


def _trusted_github_host(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    return host in TRUSTED_GITHUB_HOSTS


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def discover_endpoints() -> dict:
    """Resolve OAuth endpoints via RFC 8414, or derive from the issuer URL.

    GitHub does not publish an RFC 8414 discovery document; the endpoints
    are derived from the issuer base URL as a fallback.
    """
    if not _trusted_github_host(DISCOVERY_URL):
        raise SystemExit(f"Refusing to fetch discovery from: {DISCOVERY_URL}")
    try:
        with httpx.Client(trust_env=False, timeout=15) as client:
            data = client.get(DISCOVERY_URL).json()
        auth_ep = data.get("authorization_endpoint")
        token_ep = data.get("token_endpoint")
        if auth_ep and token_ep:
            return {"authorization_endpoint": auth_ep, "token_endpoint": token_ep}
    except (httpx.HTTPError, ValueError):
        pass
    # Fallback: derive from issuer (github.com/login/oauth → .../authorize, .../access_token)
    base = ISSUER.rstrip("/")
    return {
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/access_token",
    }


def capture_code(authorization_endpoint: str, client_id: str, scope: str) -> dict:
    """Run the PKCE authorization-code flow up to (and only to) the code.

    Returns {code, code_verifier, redirect_uri}.
    """
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    state = secrets.token_urlsafe(16)

    captured: dict[str, str] = {}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if params.get("state", [None])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State mismatch. Close this tab and re-run.")
                return
            captured["code"] = params.get("code", [""])[0]
            captured["error"] = params.get("error", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h3>Authorized. You can close this tab.</h3>")
            done.set()

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    redirect_uri = f"http://127.0.0.1:{server.server_address[1]}/"

    auth_url = authorization_endpoint + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })

    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"\nRedirect (loopback) listener: {redirect_uri}")
    print(f"Opening your browser to approve {scope!r} access...")
    print(f"If it doesn't open, paste this URL:\n{auth_url}\n")
    webbrowser.open(auth_url)

    if not done.wait(timeout=300):
        server.shutdown()
        raise SystemExit("Timed out waiting for consent.")
    server.shutdown()

    if captured.get("error") or not captured.get("code"):
        raise SystemExit(f"Consent failed: {captured.get('error') or 'no code returned'}")

    return {"code": captured["code"], "code_verifier": verifier, "redirect_uri": redirect_uri}


def main() -> None:
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    if not client_id:
        raise SystemExit("Set GITHUB_CLIENT_ID in .env (your GitHub OAuth App client ID).")

    scope = os.environ.get("GITHUB_SCOPE", "repo read:user")

    endpoints = discover_endpoints()
    result = capture_code(endpoints["authorization_endpoint"], client_id, scope)

    code = result["code"]
    shown = code[:12] + "..." if len(code) > 12 else "(short)"
    print("\nCaptured authorization code (truncated): "
          f"{shown}  [{len(code)} chars]")
    print("It is short-lived and single-use. Step 3 will exchange it (with the")
    print("code_verifier + client_secret) for an access token and retry tools/call.")

    state_file = Path(__file__).resolve().parent.parent.parent / ".m1_github_state.json"
    state_file.write_text(json.dumps({
        "code": result["code"],
        "code_verifier": result["code_verifier"],
        "redirect_uri": result["redirect_uri"],
    }))
    print(f"\nState saved to {state_file.name} — run Step 3 now (code expires in minutes).")


if __name__ == "__main__":
    main()
