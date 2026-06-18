import sys
import json
import time
import hashlib
import pathlib
import urllib.request
import urllib.parse

ADC_PATH = pathlib.Path.home() / ".config/gcloud/application_default_credentials.json"

_GMAIL_URL = "https://gmailmcp.googleapis.com/mcp/v1"
TOKEN_FILE = (
    pathlib.Path.home()
    / ".deepagents/.state/mcp-tokens"
    / f"gmail-{hashlib.sha256(_GMAIL_URL.encode()).hexdigest()[:16]}.json"
)


def main() -> None:
    if not ADC_PATH.exists():
        print("No gcloud credentials found. Run:\n")
        print(
            "  gcloud auth application-default login"
            " --scopes=https://www.googleapis.com/auth/gmail.readonly\n"
        )
        print("Then re-run this script.")
        sys.exit(1)

    adc = json.loads(ADC_PATH.read_text())

    if adc.get("type") != "authorized_user":
        print(f"Expected authorized_user credentials, got: {adc.get('type')!r}")
        print("Re-run: gcloud auth application-default login --scopes=...")
        sys.exit(1)

    # Exchange the stored refresh token for a fresh access token
    body = urllib.parse.urlencode({
        "client_id": adc["client_id"],
        "client_secret": adc["client_secret"],
        "refresh_token": adc["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            token_resp = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"Token exchange failed ({exc.code}): {body}")
        sys.exit(1)

    expires_in = token_resp.get("expires_in", 3600)

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(
        json.dumps(
            {
                "version": 1,
                "tokens": {
                    "access_token": token_resp["access_token"],
                    "token_type": "bearer",
                    "refresh_token": adc["refresh_token"],
                    "expires_in": expires_in,
                },
                "expires_at": time.time() + expires_in,
            },
            separators=(",", ":"),
        )
    )

    print(f"Gmail token written to {TOKEN_FILE}")
    print("Run: uv run ./m1/mcp_agent.py")


main()
