// typescript/m1/gh_auth/step1.ts
/**
 * GitHub MCP — Step 1: probe the server and discover what it requires.
 *
 * Sends an unauthenticated initialize request to the GitHub MCP server.
 * The 401 response carries a WWW-Authenticate header (RFC 9728) that points
 * to the resource metadata — which names the authorization server and the
 * scopes the server accepts. No credentials are used here.
 *
 * Run:  pnpm tsx ./m1/gh_auth/step1.ts
 */

const DEFAULT_URL = "https://api.githubcopilot.com/mcp/";
const ALLOWED_MCP_HOSTS = new Set(["api.githubcopilot.com", "localhost", "127.0.0.1"]);
const TRUSTED_GITHUB_HOSTS = new Set(["github.com", "api.github.com"]);

const URL_ = process.env.GITHUB_MCP_URL || DEFAULT_URL;

const HEADERS = {
  Accept: "application/json, text/event-stream",
  "Content-Type": "application/json",
};

// Node's fetch doesn't populate Response.statusText from the server, unlike
// Python's httpx; fall back to the standard reason phrase for codes this lab sees.
const REASON_PHRASES: Record<number, string> = { 200: "OK", 401: "Unauthorized" };
function reasonPhrase(status: number): string {
  return REASON_PHRASES[status] || "";
}

function requireTrustedHost(url: string): void {
  const host = new URL(url).hostname;
  if (!ALLOWED_MCP_HOSTS.has(host)) {
    throw new Error(
      `Refusing to probe untrusted host '${host}'. ` +
        `Allowed: ${[...ALLOWED_MCP_HOSTS].sort()}. ` +
        "Set GITHUB_MCP_URL to override."
    );
  }
}

function trustedGithubHost(url: string): boolean {
  return TRUSTED_GITHUB_HOSTS.has(new URL(url).hostname);
}

async function post(url: string, method: string, params?: Record<string, unknown>) {
  const body: Record<string, unknown> = { jsonrpc: "2.0", id: 1, method };
  if (params !== undefined) body.params = params;
  return fetch(url, { method: "POST", headers: HEADERS, body: JSON.stringify(body) });
}

function resourceMetadataUrl(challenge: string | null): string | undefined {
  if (!challenge) return undefined;
  const marker = "resource_metadata=";
  const idx = challenge.indexOf(marker);
  if (idx === -1) return undefined;
  const rest = challenge.slice(idx + marker.length).trim();
  if (rest.startsWith('"')) {
    return rest.slice(1).split('"', 1)[0];
  }
  return rest.split(",", 1)[0].trim();
}

async function showResourceMetadata(url: string): Promise<Record<string, unknown> | undefined> {
  const host = new URL(url).hostname;
  const trusted = ALLOWED_MCP_HOSTS.has(host) || TRUSTED_GITHUB_HOSTS.has(host);
  if (!trusted) {
    console.log("  (skipping metadata fetch: untrusted host)");
    return undefined;
  }
  try {
    const resp = await fetch(url);
    console.log(`  HTTP ${resp.status}`);
    const data = (await resp.json()) as Record<string, unknown>;
    for (const key of ["resource", "authorization_servers", "scopes_supported"]) {
      if (key in data) console.log(`  ${key}: ${JSON.stringify(data[key])}`);
    }
    return data;
  } catch (exc) {
    console.log(`  (could not fetch metadata: ${exc})`);
    return undefined;
  }
}

async function showAuthEndpoints(issuer: string): Promise<void> {
  if (!trustedGithubHost(issuer)) {
    console.log(`  (skipping: untrusted issuer host '${new URL(issuer).hostname}')`);
    return;
  }
  const discoveryUrl = `${issuer.replace(/\/$/, "")}/.well-known/oauth-authorization-server`;
  try {
    const data = (await (await fetch(discoveryUrl)).json()) as Record<string, unknown>;
    const authEp = data.authorization_endpoint;
    const tokenEp = data.token_endpoint;
    if (authEp && tokenEp) {
      console.log("\n----- Step 1 result -----");
      console.log(`  authorization_endpoint: ${authEp}`);
      console.log(`  token_endpoint:         ${tokenEp}`);
      return;
    }
  } catch {
    // fall through to derived endpoints below
  }

  // GitHub does not serve an RFC 8414 document; derive endpoints from the
  // issuer URL (https://github.com/login/oauth → .../authorize, .../access_token).
  const base = issuer.replace(/\/$/, "");
  console.log("\n----- Step 1 result -----");
  console.log(`  authorization_endpoint: ${base}/authorize`);
  console.log(`  token_endpoint:         ${base}/access_token`);
}

async function main(): Promise<void> {
  requireTrustedHost(URL_);
  console.log(`Probing ${URL_}  (no credentials)\n`);

  const init = await post(URL_, "initialize", {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "m1-github-step1", version: "0.1" },
  });
  console.log(`initialize  -> HTTP ${init.status} ${reasonPhrase(init.status)}`);

  const challenge = init.headers.get("www-authenticate");
  if (challenge) {
    console.log(`\nWWW-Authenticate: ${challenge}`);
  }

  const metaUrl = resourceMetadataUrl(challenge);
  if (metaUrl) {
    console.log(`\nProtected-resource metadata: ${metaUrl}`);
    const data = await showResourceMetadata(metaUrl);
    const servers = (data?.authorization_servers as string[] | undefined) || [];
    if (servers.length > 0) {
      await showAuthEndpoints(servers[0]);
    }
  }
}

main().catch((exc) => {
  console.error(`Request failed: ${exc}`);
  process.exit(1);
});
