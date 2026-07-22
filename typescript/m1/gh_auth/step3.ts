// typescript/m1/gh_auth/step3.ts
/**
 * GitHub MCP — Step 3: exchange the authorization code for an access token
 * and retry the gated tools/call.
 *
 * Step 2 saved the authorization code and PKCE code_verifier to
 * .m1_github_state.json. This program:
 *   1. Reads that state.
 *   2. Resolves the token_endpoint via RFC 8414 discovery.
 *   3. POSTs code + code_verifier + client credentials to the token endpoint.
 *   4. Retries the gated tools/call with Authorization: Bearer.
 *   5. Prints the tool result.
 *   6. Deletes the state file (code was single-use).
 *
 * Requires in .env:
 *   GITHUB_CLIENT_ID
 *   GITHUB_CLIENT_SECRET
 *
 * Run immediately after Step 2 — the authorization code expires in minutes.
 *   pnpm tsx ./m1/gh_auth/step3.ts
 */

import { existsSync, readFileSync, writeFileSync, unlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { config as loadDotenv } from "dotenv";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENV_PATH = path.resolve(HERE, "../../.env");
loadDotenv({ path: ENV_PATH, override: true });

const STATE_FILE = path.resolve(HERE, "../../.m1_github_state.json");
const TOKEN_FILE = path.resolve(HERE, "../../.m1_github_token");

const ISSUER = "https://github.com/login/oauth";
const DISCOVERY_URL = "https://github.com/.well-known/oauth-authorization-server";

const MCP_URL = "https://api.githubcopilot.com/mcp/";
const MCP_HEADERS_BASE = {
  Accept: "application/json, text/event-stream",
  "Content-Type": "application/json",
};

const TRUSTED_GITHUB_HOSTS = new Set(["github.com", "api.github.com"]);
const REASON_PHRASES: Record<number, string> = { 200: "OK", 401: "Unauthorized" };

function trustedGithubHost(url: string): boolean {
  return TRUSTED_GITHUB_HOSTS.has(new URL(url).hostname);
}

function reasonPhrase(status: number): string {
  return REASON_PHRASES[status] || "";
}

interface StateFile {
  code: string;
  code_verifier: string;
  redirect_uri: string;
}

function loadState(): StateFile {
  if (!existsSync(STATE_FILE)) {
    throw new Error(`State file not found: ${path.basename(STATE_FILE)}\nRun step2.ts first.`);
  }
  try {
    return JSON.parse(readFileSync(STATE_FILE, "utf8"));
  } catch (exc) {
    throw new Error(`Could not read state file: ${exc}`, { cause: exc });
  }
}

async function discoverTokenEndpoint(): Promise<string> {
  if (!trustedGithubHost(DISCOVERY_URL)) {
    throw new Error(`Refusing to fetch discovery from: ${DISCOVERY_URL}`);
  }
  try {
    const data = (await (await fetch(DISCOVERY_URL)).json()) as Record<string, unknown>;
    const tokenEp = data.token_endpoint as string | undefined;
    if (tokenEp) return tokenEp;
  } catch {
    // fall through to derived endpoint below
  }
  // GitHub does not publish RFC 8414; derive from issuer URL.
  return `${ISSUER.replace(/\/$/, "")}/access_token`;
}

async function exchangeCode(
  tokenEndpoint: string,
  state: StateFile,
  clientId: string,
  clientSecret: string
): Promise<string> {
  if (!trustedGithubHost(tokenEndpoint)) {
    throw new Error(`Refusing to POST to untrusted token endpoint: ${tokenEndpoint}`);
  }
  const resp = await fetch(tokenEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code: state.code,
      code_verifier: state.code_verifier,
      redirect_uri: state.redirect_uri,
      client_id: clientId,
      client_secret: clientSecret,
    }),
  });
  if (resp.status !== 200) {
    throw new Error(`Token exchange failed ${resp.status}: ${(await resp.text()).slice(0, 200)}`);
  }
  const data = (await resp.json()) as Record<string, unknown>;
  const token = data.access_token as string | undefined;
  if (!token) {
    throw new Error(`Token response missing access_token: ${JSON.stringify(data).slice(0, 200)}`);
  }
  return token;
}

function parseJsonOrSse(contentType: string, text: string): Record<string, unknown> {
  if (contentType.includes("text/event-stream")) {
    for (const line of text.split("\n")) {
      if (line.startsWith("data:")) {
        const payload = line.slice(5).trim();
        if (payload && payload !== "[DONE]") return JSON.parse(payload);
      }
    }
    return {};
  }
  return JSON.parse(text);
}

async function retryToolsCall(accessToken: string): Promise<void> {
  const headers = { ...MCP_HEADERS_BASE, Authorization: `Bearer ${accessToken}` };

  await fetch(MCP_URL, {
    method: "POST",
    headers,
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2025-06-18",
        capabilities: {},
        clientInfo: { name: "m1-github-step3", version: "0.1" },
      },
    }),
  });

  const resp = await fetch(MCP_URL, {
    method: "POST",
    headers,
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 2,
      method: "tools/call",
      params: { name: "get_me", arguments: {} },
    }),
  });

  console.log(`tools/call  -> HTTP ${resp.status} ${reasonPhrase(resp.status)}`);
  const text = await resp.text();
  let data: Record<string, unknown>;
  try {
    data = parseJsonOrSse(resp.headers.get("content-type") || "", text);
  } catch {
    console.log(`  (could not parse response: ${text.slice(0, 200)})`);
    return;
  }
  const result = (data.result as Record<string, unknown>) || {};
  const content = (result.content as Array<Record<string, unknown>>) || [];
  for (const item of content) {
    if (item.type === "text") console.log(item.text);
  }
}

async function main(): Promise<void> {
  const clientId = process.env.GITHUB_CLIENT_ID;
  const clientSecret = process.env.GITHUB_CLIENT_SECRET;
  if (!clientId || !clientSecret) {
    throw new Error("Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env.");
  }

  const state = loadState();

  const tokenEndpoint = await discoverTokenEndpoint();
  console.log(`Token endpoint: ${tokenEndpoint}\n`);

  console.log("Exchanging authorization code for access token...");
  const accessToken = await exchangeCode(tokenEndpoint, state, clientId, clientSecret);
  const shown = accessToken.length > 12 ? `${accessToken.slice(0, 12)}...` : "(short)";
  console.log(`Access token (truncated): ${shown}  [${accessToken.length} chars]`);

  unlinkSync(STATE_FILE);
  console.log("State file deleted (code was single-use).");
  writeFileSync(TOKEN_FILE, accessToken);
  console.log(`Access token saved to ${path.basename(TOKEN_FILE)}.\n`);

  console.log("Retrying tools/call with Bearer token:");
  await retryToolsCall(accessToken);
}

main().catch((exc) => {
  console.error(exc instanceof Error ? exc.message : exc);
  process.exit(1);
});
