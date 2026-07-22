// typescript/m1/gh_auth/step2.ts
/**
 * GitHub MCP — Step 2: PKCE + browser consent, capture the authorization code.
 *
 * Step 1 discovered the authorization server and the required scopes.
 * Step 2 takes the next leg of the OAuth sequence and stops at the
 * **authorization code**:
 *   1. Resolve the authorization server's real OAuth endpoints via RFC 8414
 *      discovery (so this program runs standalone).
 *   2. Generate PKCE (code_verifier + code_challenge).
 *   3. Build the authorization URL and open the browser for login + consent.
 *   4. Catch the ?code= redirect on a one-shot localhost listener.
 *
 * We deliberately STOP here. The code is short-lived and single-use; Step 3
 * exchanges it (with the code_verifier + client_secret) for an access token.
 *
 * Requires in .env:
 *   GITHUB_CLIENT_ID
 *
 * When registering your OAuth App at github.com/settings/developers, use
 *   http://127.0.0.1:8765/
 * as the Authorization callback URL. This matches the fixed loopback listener used
 * by both this script and github_agent.ts.
 *
 * Run:  pnpm tsx ./m1/gh_auth/step2.ts
 */

import { exec } from "node:child_process";
import { randomBytes, createHash } from "node:crypto";
import { createServer } from "node:http";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { config as loadDotenv } from "dotenv";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENV_PATH = path.resolve(HERE, "../../.env");
loadDotenv({ path: ENV_PATH, override: true });

const ISSUER = "https://github.com/login/oauth";
const DISCOVERY_URL = "https://github.com/.well-known/oauth-authorization-server";

const TRUSTED_GITHUB_HOSTS = new Set(["github.com", "api.github.com"]);

function trustedGithubHost(url: string): boolean {
  return TRUSTED_GITHUB_HOSTS.has(new URL(url).hostname);
}

function b64url(raw: Buffer): string {
  return raw.toString("base64url");
}

function openBrowser(url: string): void {
  const cmd =
    process.platform === "darwin" ? "open" : process.platform === "win32" ? "start" : "xdg-open";
  exec(`${cmd} "${url}"`);
}

interface Endpoints {
  authorization_endpoint: string;
  token_endpoint: string;
}

async function discoverEndpoints(): Promise<Endpoints> {
  if (!trustedGithubHost(DISCOVERY_URL)) {
    throw new Error(`Refusing to fetch discovery from: ${DISCOVERY_URL}`);
  }
  try {
    const data = (await (await fetch(DISCOVERY_URL)).json()) as Record<string, unknown>;
    const authEp = data.authorization_endpoint as string | undefined;
    const tokenEp = data.token_endpoint as string | undefined;
    if (authEp && tokenEp) {
      return { authorization_endpoint: authEp, token_endpoint: tokenEp };
    }
  } catch {
    // fall through to derived endpoints below
  }
  // Fallback: derive from issuer (github.com/login/oauth → .../authorize, .../access_token)
  const base = ISSUER.replace(/\/$/, "");
  return {
    authorization_endpoint: `${base}/authorize`,
    token_endpoint: `${base}/access_token`,
  };
}

interface CapturedCode {
  code: string;
  code_verifier: string;
  redirect_uri: string;
}

async function captureCode(
  authorizationEndpoint: string,
  clientId: string,
  scope: string
): Promise<CapturedCode> {
  const verifier = b64url(randomBytes(32));
  const challenge = b64url(createHash("sha256").update(verifier).digest());
  const state = b64url(randomBytes(16));

  const redirectUri = "http://127.0.0.1:8765/";
  const authUrl = `${authorizationEndpoint}?${new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope,
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  })}`;

  return new Promise<CapturedCode>((resolve, reject) => {
    const server = createServer((req, res) => {
      const params = new URL(req.url ?? "/", redirectUri).searchParams;
      if (params.get("state") !== state) {
        res.writeHead(400);
        res.end("State mismatch. Close this tab and re-run.");
        return;
      }
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end("<h3>Authorized. You can close this tab.</h3>");

      const code = params.get("code") ?? "";
      const error = params.get("error") ?? "";
      server.close();
      if (error || !code) {
        reject(new Error(`Consent failed: ${error || "no code returned"}`));
        return;
      }
      resolve({ code, code_verifier: verifier, redirect_uri: redirectUri });
    });

    const timeout = setTimeout(() => {
      server.close();
      reject(new Error("Timed out waiting for consent."));
    }, 300_000);
    timeout.unref();

    server.listen(8765, "127.0.0.1", () => {
      console.log(`\nRedirect (loopback) listener: ${redirectUri}`);
      console.log(`Opening your browser to approve '${scope}' access...`);
      console.log(`If it doesn't open, paste this URL:\n${authUrl}\n`);
      openBrowser(authUrl);
    });
  });
}

async function main(): Promise<void> {
  const clientId = process.env.GITHUB_CLIENT_ID;
  if (!clientId) {
    throw new Error("Set GITHUB_CLIENT_ID in .env (your GitHub OAuth App client ID).");
  }

  const scope = process.env.GITHUB_SCOPE || "repo read:user";

  const endpoints = await discoverEndpoints();
  const result = await captureCode(endpoints.authorization_endpoint, clientId, scope);

  const code = result.code;
  const shown = code.length > 12 ? `${code.slice(0, 12)}...` : "(short)";
  console.log(`\nCaptured authorization code (truncated): ${shown}  [${code.length} chars]`);
  console.log("It is short-lived and single-use. Step 3 will exchange it (with the");
  console.log("code_verifier + client_secret) for an access token and retry tools/call.");

  const stateFile = path.resolve(HERE, "../../.m1_github_state.json");
  writeFileSync(
    stateFile,
    JSON.stringify({
      code: result.code,
      code_verifier: result.code_verifier,
      redirect_uri: result.redirect_uri,
    })
  );
  console.log(
    `\nState saved to ${path.basename(stateFile)} — run Step 3 now (code expires in minutes).`
  );
}

main().catch((exc) => {
  console.error(exc instanceof Error ? exc.message : exc);
  process.exit(1);
});
