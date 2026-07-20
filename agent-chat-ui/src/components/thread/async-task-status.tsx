"use client";

import { useEffect, useRef, useState } from "react";
import { useStreamContext } from "@/providers/Stream";
import type { AsyncTask } from "@/providers/Stream";
import type { Message } from "@langchain/langgraph-sdk";
import {
  LoaderCircle,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getContentString } from "./utils";
import { findOutputPaths } from "./output-path";

const POLL_INTERVAL_MS = 5000;
const DONE_DISPLAY_MS = 8000;

// Same terminal-status set as deepagents' AsyncSubAgentMiddleware
// (_TERMINAL_STATUSES in async_subagents.py) — once every tracked task
// lands in one of these, there's nothing left to poll for.
const TERMINAL = new Set(["success", "error", "cancelled", "timeout", "interrupted"]);

type ReportPhase = "assembling" | "done" | null;

function TaskStatusIcon({ status }: { status: string }) {
  if (!TERMINAL.has(status)) {
    return (
      <LoaderCircle className="size-3 shrink-0 animate-spin text-muted-foreground" />
    );
  }
  if (status === "success") {
    return <CheckCircle2 className="size-3 shrink-0 text-green-600" />;
  }
  return <XCircle className="size-3 shrink-0 text-red-500" />;
}

// A run created server-side by the completion notifier (see
// completion_notifier.py) doesn't push into this tab's SSE stream — only
// runs the browser itself submitted do. So this badge polls the thread's
// state directly instead of relying on `stream.values`, which is a snapshot
// of the browser's own stream and can go stale the moment a background
// task's notifier wakes the thread from the server side.
//
// Beyond "N tasks running", this also distinguishes "assembling the report"
// (all research tasks terminal, but the thread is still busy — the
// weekly-newsletter skill's final assembly turn) from "report ready" (all
// terminal, thread idle, and an /outputs/*.html path shows up in the last AI
// message). "Assembling" needs a second call to `threads.get` for the
// thread's own status, since a finished-but-idle thread with no report yet
// (e.g. every genre failed) looks identical to "still assembling" if you
// only look at async_tasks.
export function AsyncTaskStatus({ threadId }: { threadId: string | null }) {
  const stream = useStreamContext();
  const [tasks, setTasks] = useState<Record<string, AsyncTask>>({});
  const [reportPhase, setReportPhase] = useState<ReportPhase>(null);
  const [reportPath, setReportPath] = useState<string | null>(null);
  const [justFinished, setJustFinished] = useState(false);
  const [expanded, setExpanded] = useState(false);
  // Task-id-set (sorted, joined) this badge has already resolved a report
  // outcome for — found a path, or confirmed there's nothing to assemble.
  // Persists across the polling effect's re-runs (unlike local closure vars
  // in poll()) so a later, unrelated busy period on the same thread (e.g. a
  // different skill's tool calls) can't resurrect "Assembling newsletter"
  // for a report that was already delivered or abandoned.
  const resolvedTaskKeyRef = useRef<string | null>(null);

  useEffect(() => {
    if (!threadId) {
      setTasks({});
      setReportPhase(null);
      setReportPath(null);
      setJustFinished(false);
      return;
    }
    const activeThreadId = threadId;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    // Local, not React state: tracks whether *this* watch session has ever
    // seen a non-terminal task or an in-progress assembly, so we only flash
    // "done" on a genuine transition, not on every poll tick.
    let hadWorkInFlight = false;

    async function poll() {
      try {
        const state = await stream.client.threads.getState(activeThreadId);
        const values = state.values as Record<string, unknown> | undefined;
        const nextTasks = (values?.async_tasks ?? {}) as Record<string, AsyncTask>;
        const messages = (values?.messages ?? []) as Message[];
        if (cancelled) return;

        setTasks(nextTasks);
        const taskList = Object.values(nextTasks);
        const taskKey = taskList
          .map((t) => t.task_id)
          .sort()
          .join(",");
        const stillRunning = taskList.some((t) => !TERMINAL.has(t.status));
        const allTerminal = taskList.length > 0 && !stillRunning;

        let path: string | null = null;
        if (allTerminal) {
          const lastAi = [...messages].reverse().find((m) => m.type === "ai");
          if (lastAi) {
            const found = findOutputPaths(getContentString(lastAi.content));
            if (found.length) path = found[found.length - 1];
          }
        }
        setReportPath(path);

        if (stillRunning) {
          hadWorkInFlight = true;
          setReportPhase(null);
          timer = setTimeout(poll, POLL_INTERVAL_MS);
          return;
        }

        if (allTerminal && path) {
          resolvedTaskKeyRef.current = taskKey;
          setReportPhase("done");
          if (hadWorkInFlight) {
            setJustFinished(true);
            setTimeout(() => setJustFinished(false), DONE_DISPLAY_MS);
          }
          hadWorkInFlight = false;
          return;
        }

        if (allTerminal) {
          // Already resolved this exact task set (found a report, or
          // confirmed there's nothing to assemble) on an earlier poll — a
          // later, unrelated busy period on this thread (a different skill
          // entirely) isn't this report reopening, so don't re-enter
          // "assembling" for it.
          if (resolvedTaskKeyRef.current === taskKey) {
            setReportPhase(null);
            hadWorkInFlight = false;
            return;
          }
          // Research is done but no report path yet — check whether the
          // thread is actively assembling it, or has stopped (e.g. every
          // genre failed, so there's nothing to assemble).
          const thread = await stream.client.threads.get(activeThreadId);
          if (cancelled) return;
          if (thread.status === "busy") {
            hadWorkInFlight = true;
            setReportPhase("assembling");
            timer = setTimeout(poll, POLL_INTERVAL_MS);
            return;
          }
          resolvedTaskKeyRef.current = taskKey;
          setReportPhase(null);
          if (hadWorkInFlight) {
            setJustFinished(true);
            setTimeout(() => setJustFinished(false), DONE_DISPLAY_MS);
          }
          hadWorkInFlight = false;
        }
      } catch {
        if (!cancelled) timer = setTimeout(poll, POLL_INTERVAL_MS);
      }
    }

    poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
    // Re-run whenever a turn finishes, in case it launched new tasks —
    // `stream.isLoading` flips false right after the browser's own launch
    // turn completes, which is the moment new task IDs would first appear.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId, stream.isLoading]);

  const taskList = Object.values(tasks);
  const running = taskList.filter((t) => !TERMINAL.has(t.status));
  const showSpinner = running.length > 0 || reportPhase === "assembling";

  if (running.length === 0 && !reportPhase && !justFinished) return null;

  const headline =
    running.length > 0
      ? `${taskList.length - running.length}/${taskList.length} researching`
      : reportPhase === "assembling"
        ? "Assembling report..."
        : reportPhase === "done"
          ? "Report ready"
          : "Research complete";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className={cn(
          "flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs",
          showSpinner
            ? "text-muted-foreground"
            : "border-green-200 bg-green-50 text-green-700",
        )}
      >
        {showSpinner ? (
          <LoaderCircle className="size-3 animate-spin" />
        ) : (
          <CheckCircle2 className="size-3" />
        )}
        <span>{headline}</span>
        {expanded ? (
          <ChevronUp className="size-3" />
        ) : (
          <ChevronDown className="size-3" />
        )}
      </button>

      {expanded && (
        <div className="absolute right-0 z-10 mt-1 w-64 rounded-md border bg-white p-2 shadow-md">
          <ul className="flex flex-col gap-1.5">
            {taskList.map((t) => (
              <li key={t.task_id} className="flex items-center gap-2 text-xs">
                <TaskStatusIcon status={t.status} />
                <span className="truncate">{t.label || t.agent_name}</span>
              </li>
            ))}
            {(reportPhase || reportPath) && (
              <li className="flex items-center gap-2 border-t pt-1.5 text-xs font-medium">
                {reportPhase === "assembling" ? (
                  <LoaderCircle className="size-3 shrink-0 animate-spin text-muted-foreground" />
                ) : (
                  <CheckCircle2 className="size-3 shrink-0 text-green-600" />
                )}
                <span className="truncate">
                  {reportPhase === "assembling"
                    ? "Assembling newsletter"
                    : "Newsletter"}
                </span>
                {reportPath && threadId && (
                  <a
                    href={`/api/sandbox-download?threadId=${encodeURIComponent(threadId)}&path=${encodeURIComponent(reportPath)}`}
                    className="ml-auto text-muted-foreground hover:text-foreground"
                  >
                    <Download className="size-3" />
                  </a>
                )}
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
