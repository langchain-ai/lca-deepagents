# python/m1/gh_auth/github_agent.py
"""GitHub MCP agent — OAuth via the MCP SDK's built-in flow.

The MCP SDK's OAuthClientProvider handles PKCE, discovery, and token exchange.
GitHubTokenStorage pre-seeds the registered client credentials so the SDK skips
dynamic client registration (which GitHub does not support).

Run:  uv run python m1/gh_auth/github_agent.py
"""

from __future__ import annotations

import asyncio
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
import httpx
from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

from models import model

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

TOKEN_FILE = Path(__file__).resolve().parent.parent.parent / ".m1_github_token"

MCP_URL = "https://api.githubcopilot.com/mcp/"
REDIRECT_URI = "http://127.0.0.1:8765/"
SCOPE = "repo read:user"


class GitHubOAuthClientProvider(OAuthClientProvider):
    """OAuthClientProvider with two GitHub-specific fixes:

    1. Scope: the SDK replaces client_metadata.scope with the full list from
       GitHub's PRM scopes_supported. We restore the intended scope before the
       authorization URL is built.
    2. Token response: GitHub returns URL-encoded form data by default; adding
       Accept: application/json forces a JSON response the SDK can parse.
    """

    def __init__(self, *args, requested_scope: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._requested_scope = requested_scope

    async def _perform_authorization_code_grant(self) -> tuple[str, str]:
        self.context.client_metadata.scope = self._requested_scope
        return await super()._perform_authorization_code_grant()

    async def _exchange_token_authorization_code(
        self, auth_code: str, code_verifier: str, *, token_data: dict | None = {}
    ) -> httpx.Request:
        req = await super()._exchange_token_authorization_code(
            auth_code, code_verifier, token_data=token_data
        )
        req.headers["Accept"] = "application/json"
        return req


class GitHubTokenStorage:
    """Pre-seeds client credentials so the SDK skips dynamic client registration."""

    def __init__(self, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def get_tokens(self) -> OAuthToken | None:
        if TOKEN_FILE.exists():
            raw = TOKEN_FILE.read_text().strip()
            if raw:
                try:
                    return OAuthToken.model_validate_json(raw)
                except Exception:
                    return OAuthToken(access_token=raw, token_type="Bearer")
        return None

    async def set_tokens(self, tokens: OAuthToken) -> None:
        TOKEN_FILE.write_text(tokens.model_dump_json())

    async def get_client_info(self) -> OAuthClientInformationFull:
        return OAuthClientInformationFull(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uris=[REDIRECT_URI],
            token_endpoint_auth_method="client_secret_post",
        )

    async def set_client_info(self, info: OAuthClientInformationFull) -> None:
        pass  # credentials come from .env, not from registration


async def open_browser(url: str) -> None:
    print(f"Opening browser for GitHub login ({SCOPE})...")
    print(f"If it doesn't open, paste this URL:\n{url}\n")
    webbrowser.open(url)


async def wait_for_callback() -> tuple[str, str | None]:
    """Loopback server that captures the authorization code from GitHub's redirect."""
    result: dict[str, str] = {}
    done = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            params = parse_qs(urlparse(self.path).query)
            result["code"] = params.get("code", [""])[0]
            result["state"] = params.get("state", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h3>Authorized. You can close this tab.</h3>")
            done.set()

        def log_message(self, *a): pass

    port = int(urlparse(REDIRECT_URI).port or 80)
    server = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    if not done.wait(timeout=300):
        server.shutdown()
        raise SystemExit("Timed out waiting for OAuth callback.")
    server.shutdown()
    return result["code"], result.get("state")


async def main() -> None:
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env.")

    auth = GitHubOAuthClientProvider(
        server_url=MCP_URL,
        client_metadata=OAuthClientMetadata(
            redirect_uris=[REDIRECT_URI],
            scope=SCOPE,
            token_endpoint_auth_method="client_secret_post",
        ),
        storage=GitHubTokenStorage(client_id, client_secret),
        redirect_handler=open_browser,
        callback_handler=wait_for_callback,
        requested_scope=SCOPE,
    )

    client = MultiServerMCPClient({
        "github": {
            "transport": "streamable_http",
            "url": MCP_URL,
            "auth": auth,
        }
    })

    async with client.session("github") as session:
        tools = await load_mcp_tools(session)
        print(f"github: {len(tools)} tool(s) available")

        agent = create_deep_agent(model=model, tools=tools)
        print("Running agent...\n")
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": (
                "What is my GitHub username and what repositories do I have?"
            )}]
        })
        print("\n" + result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
