import { NextRequest, NextResponse } from "next/server";
import { SandboxClient, LangSmithSandboxNotReadyError } from "langsmith/sandbox";

// Non-agentic extraction: reads a file straight out of a thread's sandbox
// via the sandbox SDK's dataplane, with no LLM tool call involved.
export const runtime = "nodejs";

const THREAD_ID_RE = /^[a-zA-Z0-9-]{1,100}$/;

const CONTENT_TYPES: Record<string, string> = {
  png: "image/png",
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  gif: "image/gif",
  svg: "image/svg+xml",
  pdf: "application/pdf",
  csv: "text/csv",
  txt: "text/plain",
  md: "text/markdown",
  json: "application/json",
  html: "text/html",
};

// Allows nested paths under /outputs/ (e.g. /outputs/customers/Foo.txt), not
// just a flat filename — but still blocks traversal and header-injection
// characters: every path segment must be a plain filename component, and
// "." / ".." segments are rejected explicitly, since the character class
// alone would otherwise still match them.
const OUTPUT_PREFIX = "/outputs/";
const SEGMENT_RE = /^[A-Za-z0-9._-]+$/;
const MAX_PATH_LENGTH = 255;

function isSafeOutputPath(path: string): boolean {
  if (path.length > MAX_PATH_LENGTH || !path.startsWith(OUTPUT_PREFIX)) {
    return false;
  }
  const segments = path.slice(OUTPUT_PREFIX.length).split("/");
  return segments.every(
    (segment) => segment !== "." && segment !== ".." && SEGMENT_RE.test(segment),
  );
}

// The platform auto-resumes a stopped sandbox on the first dataplane
// request, but a request that lands before it's ready throws
// LangSmithSandboxNotReadyError rather than blocking until ready — so a
// stopped sandbox needs a couple of retries here, not a restart call.
const READ_RETRY_ATTEMPTS = 3;
const READ_RETRY_DELAY_MS = 1500;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function readWithRetry(
  sandbox: Awaited<ReturnType<SandboxClient["getSandbox"]>>,
  path: string,
): Promise<Uint8Array> {
  for (let attempt = 1; attempt <= READ_RETRY_ATTEMPTS; attempt++) {
    try {
      return await sandbox.read(path);
    } catch (error) {
      const isLastAttempt = attempt === READ_RETRY_ATTEMPTS;
      if (!(error instanceof LangSmithSandboxNotReadyError) || isLastAttempt) {
        throw error;
      }
      await sleep(READ_RETRY_DELAY_MS);
    }
  }
  throw new Error("unreachable");
}

export async function GET(request: NextRequest) {
  const threadId = request.nextUrl.searchParams.get("threadId");
  const path = request.nextUrl.searchParams.get("path");

  if (!threadId || !THREAD_ID_RE.test(threadId)) {
    return NextResponse.json({ error: "Invalid threadId" }, { status: 400 });
  }
  if (!path || !isSafeOutputPath(path)) {
    return NextResponse.json({ error: "Invalid path" }, { status: 400 });
  }

  const client = new SandboxClient({ apiKey: process.env.LANGSMITH_API_KEY });

  try {
    const sandbox = await client.getSandbox(`thread-${threadId}`);
    const content = await readWithRetry(sandbox, path);
    const extension = path.split(".").pop()?.toLowerCase() ?? "";
    const filename = path.split("/").pop() ?? "download";

    return new NextResponse(Buffer.from(content), {
      headers: {
        "Content-Type": CONTENT_TYPES[extension] ?? "application/octet-stream",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
  } catch (error) {
    if (error instanceof LangSmithSandboxNotReadyError) {
      return NextResponse.json(
        { error: "Sandbox is starting, please try again in a moment." },
        { status: 503 },
      );
    }
    return NextResponse.json(
      { error: "File not found" },
      { status: 404 },
    );
  }
}
