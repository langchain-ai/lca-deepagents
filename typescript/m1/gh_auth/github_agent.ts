// typescript/m1/gh_auth/github_agent.ts
/**
 * GitHub MCP agent — OAuth via the MCP SDK's OAuthClientProvider interface.
 *
 * GitHubTokenStorage implements OAuthClientProvider directly (the MCP
 * TypeScript SDK has no OAuthClientProvider base class to subclass, unlike
 * the Python SDK). It pre-seeds the registered client credentials so the SDK
 * skips dynamic client registration (which GitHub does not support), and
 * drives the browser-consent + loopback-callback dance itself inside
 * redirectToAuthorization.
 *
 * Run:  pnpm tsx ./m1/gh_auth/github_agent.ts
 */

import { exec } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { config as loadDotenv } from "dotenv";
import { createDeepAgent } from "deepagents";
import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { auth } from "@modelcontextprotocol/sdk/client/auth.js";
import type { OAuthClientProvider } from "@modelcontextprotocol/sdk/client/auth.js";
import type {
  OAuthClientInformationFull,
  OAuthClientMetadata,
  OAuthTokens,
} from "@modelcontextprotocol/sdk/shared/auth.js";

import { model } from "../../models.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ENV_PATH = path.resolve(HERE, "../../.env");
loadDotenv({ path: ENV_PATH, override: true });

const TOKEN_FILE = path.resolve(HERE, "../../.m1_github_token");

const MCP_URL = "https://api.githubcopilot.com/mcp/";
const REDIRECT_URI = "http://127.0.0.1:8765/";
const SCOPE = "repo read:user";

function openBrowser(url: string): void {
  const cmd =
    process.platform === "darwin" ? "open" : process.platform === "win32" ? "start" : "xdg-open";
  exec(`${cmd} "${url}"`);
}

class GitHubTokenStorage implements OAuthClientProvider {
  private codeVerifierValue?: string;
  private pendingCode?: string;

  constructor(
    private clientId: string,
    private clientSecret: string
  ) {}

  get redirectUrl(): string {
    return REDIRECT_URI;
  }

  get clientMetadata(): OAuthClientMetadata {
    return {
      redirect_uris: [REDIRECT_URI],
      scope: SCOPE,
      token_endpoint_auth_method: "client_secret_post",
    };
  }

  clientInformation(): OAuthClientInformationFull {
    return {
      client_id: this.clientId,
      client_secret: this.clientSecret,
      redirect_uris: [REDIRECT_URI],
      token_endpoint_auth_method: "client_secret_post",
    };
  }

  saveClientInformation(): void {
    // GitHub is pre-registered (see clientInformation); nothing to persist.
  }

  tokens(): OAuthTokens | undefined {
    if (!existsSync(TOKEN_FILE)) return undefined;
    const raw = readFileSync(TOKEN_FILE, "utf8").trim();
    if (!raw) return undefined;
    try {
      return JSON.parse(raw);
    } catch {
      return { access_token: raw, token_type: "Bearer" };
    }
  }

  saveTokens(tokens: OAuthTokens): void {
    writeFileSync(TOKEN_FILE, JSON.stringify(tokens));
  }

  saveCodeVerifier(codeVerifier: string): void {
    this.codeVerifierValue = codeVerifier;
  }

  codeVerifier(): string {
    if (!this.codeVerifierValue) throw new Error("No code verifier saved.");
    return this.codeVerifierValue;
  }

  /** Take (and clear) the authorization code captured by the last redirectToAuthorization call. */
  takePendingCode(): string | undefined {
    const code = this.pendingCode;
    this.pendingCode = undefined;
    return code;
  }

  async redirectToAuthorization(authorizationUrl: URL): Promise<void> {
    const expectedState = authorizationUrl.searchParams.get("state");

    console.log(`Opening browser for GitHub login (${SCOPE})...`);
    console.log(`If it doesn't open, paste this URL:\n${authorizationUrl}\n`);

    const code = await new Promise<string>((resolve, reject) => {
      const server = createServer((req, res) => {
        const params = new URL(req.url ?? "/", REDIRECT_URI).searchParams;
        if (params.get("state") !== expectedState) {
          res.writeHead(400);
          res.end("State mismatch. Close this tab and re-run.");
          return;
        }
        res.writeHead(200, { "Content-Type": "text/html" });
        res.end("<h3>Authorized. You can close this tab.</h3>");

        const authCode = params.get("code") ?? "";
        const error = params.get("error") ?? "";
        server.close();
        if (error || !authCode) {
          reject(new Error(`Consent failed: ${error || "no code returned"}`));
          return;
        }
        resolve(authCode);
      });

      const timeout = setTimeout(() => {
        server.close();
        reject(new Error("Timed out waiting for consent."));
      }, 300_000);
      timeout.unref();

      server.listen(8765, "127.0.0.1", () => openBrowser(authorizationUrl.toString()));
    });

    this.pendingCode = code;
  }
}

async function main(): Promise<void> {
  const clientId = process.env.GITHUB_CLIENT_ID;
  const clientSecret = process.env.GITHUB_CLIENT_SECRET;
  if (!clientId || !clientSecret) {
    throw new Error("Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env.");
  }

  const authProvider = new GitHubTokenStorage(clientId, clientSecret);

  function makeClient() {
    return new MultiServerMCPClient({
      github: { transport: "http", url: MCP_URL, authProvider },
    });
  }

  let client = makeClient();
  try {
    let tools;
    try {
      tools = await client.getTools();
    } catch (err) {
      // First run: connect() throws once redirectToAuthorization captures a code,
      // because the SDK's auth() orchestrator always reports "REDIRECT" on the
      // attempt that triggered the browser flow, even though our own
      // redirectToAuthorization already has the code in hand by the time it
      // resolves. Feed that code back through auth() to do the actual token
      // exchange, then reconnect on a fresh client — the failed one can't retry.
      const code = authProvider.takePendingCode();
      if (!code) throw err;

      const result = await auth(authProvider, { serverUrl: MCP_URL, authorizationCode: code });
      if (result !== "AUTHORIZED") throw err;

      await client.close();
      client = makeClient();
      tools = await client.getTools();
    }

    console.log(`github: ${tools.length} tool(s) available`);

    const agent = createDeepAgent({ model, tools });
    console.log("Running agent...\n");
    const result = await agent.invoke({
      messages: [
        {
          role: "user",
          content: "What is my GitHub username and what repositories do I have?",
        },
      ],
    });
    console.log(`\n${result.messages.at(-1)?.content}`);
  } finally {
    await client.close();
  }
}

main().catch((exc) => {
  console.error(exc instanceof Error ? exc.message : exc);
  process.exit(1);
});
