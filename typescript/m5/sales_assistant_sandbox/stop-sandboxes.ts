// typescript/m5/sales_assistant_sandbox/stop-sandboxes.ts
/**
 * Stop this lesson's running sandboxes.
 *
 * Run on shutdown by start.sh so a student closing langgraphjs dev stops
 * billing for sandbox compute immediately, instead of waiting out
 * idleTtlSeconds. Only touches sandboxes named "thread-*" (this project's
 * naming convention from agent.ts) that are currently "ready" — never
 * touches other sandboxes in the workspace.
 */
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { config as loadEnv } from "dotenv";
import { SandboxClient } from "langsmith/sandbox";

const HERE = dirname(fileURLToPath(import.meta.url));

// Load the key explicitly from typescript/.env rather than relying on the
// ambient shell environment, which may hold an unrelated LANGSMITH_API_KEY
// (e.g. from an outer shell/session) that silently points at the wrong
// workspace — this bit us once already when building this lesson.
const ENV_PATH = join(HERE, "..", "..", ".env");
const env = loadEnv({ path: ENV_PATH, override: true }).parsed ?? {};

async function main() {
  const client = new SandboxClient({ apiKey: env.LANGSMITH_API_KEY });
  const sandboxes = await client.listSandboxes();
  const targets = sandboxes.filter(
    (sb) => sb.name.startsWith("thread-") && sb.status === "ready"
  );
  for (const sb of targets) {
    try {
      await client.stopSandbox(sb.name);
      console.log(`Stopped sandbox ${sb.name}`);
    } catch (exc) {
      console.log(`Could not stop sandbox ${sb.name}: ${exc}`);
    }
  }
}

await main();
