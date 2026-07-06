# python/m1/gh_auth/step1.py
"""GitHub MCP — Step 1: probe the server and discover what it requires.

Sends an unauthenticated initialize request to the GitHub MCP server.
The 401 response carries a WWW-Authenticate header (RFC 9728) that points
to the resource metadata — which names the authorization server and the
scopes the server accepts. No credentials are used here.

Run:  uv run python m1/gh_auth/step1.py
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import httpx

DEFAULT_URL = "https://api.githubcopilot.com/mcp/"
ALLOWED_MCP_HOSTS = {"api.githubcopilot.com", "localhost", "127.0.0.1"}
TRUSTED_GITHUB_HOSTS = {"github.com", "api.github.com"}

URL = os.environ.get("GITHUB_MCP_URL", DEFAULT_URL)

HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}


def _require_trusted_host(url: str) -> None:
    host = urlsplit(url).hostname or ""
    if host not in ALLOWED_MCP_HOSTS:
        raise SystemExit(
            f"Refusing to probe untrusted host {host!r}. "
            f"Allowed: {sorted(ALLOWED_MCP_HOSTS)}. "
            "Set GITHUB_MCP_URL to override."
        )


def _trusted_github_host(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    return host in TRUSTED_GITHUB_HOSTS


def _post(client: httpx.Client, method: str, params: dict | None = None) -> httpx.Response:
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    return client.post(URL, json=body, headers=HEADERS)


def _resource_metadata_url(challenge: str | None) -> str | None:
    if not challenge:
        return None
    marker = "resource_metadata="
    if marker not in challenge:
        return None
    rest = challenge.split(marker, 1)[1].strip()
    if rest.startswith('"'):
        return rest[1:].split('"', 1)[0]
    return rest.split(",", 1)[0].strip()


def _show_resource_metadata(client: httpx.Client, url: str) -> dict | None:
    host = urlsplit(url).hostname or ""
    trusted = host in ALLOWED_MCP_HOSTS or host in TRUSTED_GITHUB_HOSTS
    if not trusted:
        print("  (skipping metadata fetch: untrusted host)")
        return None
    try:
        resp = client.get(url)
        print(f"  HTTP {resp.status_code}")
        data = resp.json()
        for key in ("resource", "authorization_servers", "scopes_supported"):
            if key in data:
                print(f"  {key}: {data[key]}")
        return data
    except (httpx.HTTPError, ValueError) as exc:
        print(f"  (could not fetch metadata: {exc})")
        return None


def _show_auth_endpoints(client: httpx.Client, issuer: str) -> None:
    """Resolve the authorization server endpoints.

    Tries RFC 8414 discovery first; falls back to deriving the endpoints
    from the issuer URL (GitHub does not publish a discovery document).
    """
    if not _trusted_github_host(issuer):
        print(f"  (skipping: untrusted issuer host {issuer!r})")
        return
    discovery_url = issuer.rstrip("/") + "/.well-known/oauth-authorization-server"
    try:
        data = client.get(discovery_url).json()
        auth_ep = data.get("authorization_endpoint")
        token_ep = data.get("token_endpoint")
        if auth_ep and token_ep:
            print("\n----- Step 1 result -----")
            print(f"  authorization_endpoint: {auth_ep}")
            print(f"  token_endpoint:         {token_ep}")
            return
    except (httpx.HTTPError, ValueError):
        pass

    # GitHub does not serve an RFC 8414 document; derive endpoints from the
    # issuer URL (https://github.com/login/oauth → .../authorize, .../access_token).
    base = issuer.rstrip("/")
    print("\n----- Step 1 result -----")
    print(f"  authorization_endpoint: {base}/authorize")
    print(f"  token_endpoint:         {base}/access_token")


def main() -> None:
    _require_trusted_host(URL)
    print(f"Probing {URL}  (no credentials)\n")

    try:
        with httpx.Client(trust_env=False, timeout=15) as client:
            init = _post(client, "initialize", {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "m1-github-step1", "version": "0.1"},
            })
            print(f"initialize  -> HTTP {init.status_code} {init.reason_phrase}")

            challenge = init.headers.get("www-authenticate")
            if challenge:
                print(f"\nWWW-Authenticate: {challenge}")

            meta_url = _resource_metadata_url(challenge)
            if meta_url:
                print(f"\nProtected-resource metadata: {meta_url}")
                data = _show_resource_metadata(client, meta_url)
                servers = (data or {}).get("authorization_servers") or []
                if servers:
                    _show_auth_endpoints(client, servers[0])
    except httpx.HTTPError as exc:
        raise SystemExit(f"Request failed: {exc}")


if __name__ == "__main__":
    main()
