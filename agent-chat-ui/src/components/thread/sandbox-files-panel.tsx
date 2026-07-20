"use client";

import { useState } from "react";
import { FolderOpen, Download, RefreshCw } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { TooltipIconButton } from "./tooltip-icon-button";
import { Button } from "../ui/button";
import { cn } from "@/lib/utils";

type SandboxFile = { name: string; size: number; modifiedAt: string };

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// A real listing of the thread's sandbox /outputs/ folder, independent of
// whether (or how) the assistant's message text happens to mention a file.
// The per-message inline download link in messages/ai.tsx still works the
// same as before — this panel doesn't replace it, just fills the gap where
// a file exists but the agent never named its exact path in the chat.
export function SandboxFilesPanel({ threadId }: { threadId: string | null }) {
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<SandboxFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (!threadId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/sandbox-files?threadId=${encodeURIComponent(threadId)}`,
      );
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      const data = await res.json();
      setFiles(data.files ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load files");
    } finally {
      setLoading(false);
    }
  }

  if (!threadId) return null;

  return (
    <Sheet
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (next) refresh();
      }}
    >
      <SheetTrigger asChild>
        <TooltipIconButton
          tooltip="Sandbox files"
          variant="ghost"
        >
          <FolderOpen className="size-5" />
        </TooltipIconButton>
      </SheetTrigger>
      <SheetContent
        side="right"
        className="sm:max-w-[480px]"
      >
        <SheetHeader>
          <SheetTitle>Sandbox files</SheetTitle>
        </SheetHeader>
        <div className="flex flex-col gap-3 overflow-y-auto px-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-muted-foreground text-sm">
              Everything in this thread's <code>/outputs/</code> folder.
            </p>
            <Button
              variant="ghost"
              size="icon"
              onClick={refresh}
              disabled={loading}
            >
              <RefreshCw className={cn("size-4", loading && "animate-spin")} />
              <span className="sr-only">Refresh</span>
            </Button>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!error && !loading && files.length === 0 && (
            <p className="text-muted-foreground text-sm">No files yet.</p>
          )}
          <ul className="flex flex-col gap-1">
            {files.map((f) => (
              <li
                key={f.name}
                className="flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm"
              >
                <div className="flex min-w-0 flex-col">
                  <span className="truncate font-medium">{f.name}</span>
                  <span className="text-muted-foreground truncate text-xs">
                    {formatSize(f.size)} · {f.modifiedAt}
                  </span>
                </div>
                <a
                  href={`/api/sandbox-download?threadId=${encodeURIComponent(threadId)}&path=${encodeURIComponent(`/outputs/${f.name}`)}`}
                  className="inline-flex shrink-0 items-center gap-1 rounded-md border px-2 py-1 text-xs hover:bg-muted"
                >
                  <Download className="size-3" />
                  Download
                </a>
              </li>
            ))}
          </ul>
        </div>
      </SheetContent>
    </Sheet>
  );
}
