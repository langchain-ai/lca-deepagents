import { NextRequest, NextResponse } from "next/server";
import { SandboxClient, LangSmithResourceNotFoundError } from "langsmith/sandbox";

// Lists a thread's sandbox /outputs/ folder directly, independent of
// whether (or how) the assistant's message text mentions a file — see
// sandbox-download/route.ts for the existing per-file download route this
// panel links into.
export const runtime = "nodejs";

const THREAD_ID_RE = /^[a-zA-Z0-9-]{1,100}$/;

// Fixed command string — no client input is interpolated into it, so
// there's no injection surface even though it runs inside the sandbox's
// shell-command execution path.
//
// %TS prints seconds with GNU find's full fractional part (e.g.
// "39.6489742380") — trimmed below in parseListing rather than in the
// command itself, since find's printf precision modifiers (e.g. `%.0TS`)
// aren't actually supported on the time directives and silently produce an
// empty field instead of an error.
const LIST_COMMAND =
  "find /outputs -maxdepth 1 -type f -printf '%f\\t%s\\t%TY-%Tm-%TdT%TH:%TM:%TS\\n'";

type SandboxFile = { name: string; size: number; modifiedAt: string };

function parseListing(stdout: string): SandboxFile[] {
  return stdout
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .map((line) => {
      const [name, size, modifiedAt] = line.split("\t");
      // Drop the fractional seconds find's %TS tacks on, e.g.
      // "2026-07-19T18:11:39.6489742380" -> "2026-07-19T18:11:39".
      const cleanModifiedAt = (modifiedAt ?? "").replace(/\.\d+$/, "");
      return { name, size: Number(size) || 0, modifiedAt: cleanModifiedAt };
    })
    .filter((f) => f.name);
}

export async function GET(request: NextRequest) {
  const threadId = request.nextUrl.searchParams.get("threadId");

  if (!threadId || !THREAD_ID_RE.test(threadId)) {
    return NextResponse.json({ error: "Invalid threadId" }, { status: 400 });
  }

  const client = new SandboxClient({ apiKey: process.env.LANGSMITH_API_KEY });

  try {
    const sandbox = await client.getSandbox(`thread-${threadId}`);
    const result = await sandbox.run(LIST_COMMAND);
    if (result.exit_code !== 0) {
      return NextResponse.json({ files: [] });
    }
    return NextResponse.json({ files: parseListing(result.stdout) });
  } catch (error) {
    // No sandbox for this thread is a normal, expected state — e.g. a
    // non-sandboxed backend (like the plain sales_assistant lesson), or a
    // thread whose sandbox hasn't been created yet. Treat it the same as
    // an empty /outputs/ folder rather than surfacing it as an error, so
    // this panel degrades gracefully instead of showing "Request failed."
    if (error instanceof LangSmithResourceNotFoundError) {
      return NextResponse.json({ files: [] });
    }
    return NextResponse.json(
      { error: "Could not reach the sandbox" },
      { status: 502 },
    );
  }
}
