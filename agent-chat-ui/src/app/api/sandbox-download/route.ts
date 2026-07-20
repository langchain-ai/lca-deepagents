import { NextRequest, NextResponse } from "next/server";
import { SandboxClient } from "langsmith/sandbox";

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

// Restricted to a flat /outputs/<filename> shape: no traversal, no nested
// directories, no characters that could smuggle a header value.
const OUTPUT_PATH_RE = /^\/outputs\/[A-Za-z0-9._-]{1,255}$/;

function isSafeOutputPath(path: string): boolean {
  return OUTPUT_PATH_RE.test(path);
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
    const content = await sandbox.read(path);
    const extension = path.split(".").pop()?.toLowerCase() ?? "";
    const filename = path.split("/").pop() ?? "download";

    return new NextResponse(Buffer.from(content), {
      headers: {
        "Content-Type": CONTENT_TYPES[extension] ?? "application/octet-stream",
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: "File not found" },
      { status: 404 },
    );
  }
}
