// Shared between messages/ai.tsx (inline download links) and
// async-task-status.tsx (the "report ready" check) so both recognize the
// same /outputs/<file> shape the sandbox filesystem actually produces.
export const OUTPUT_PATH_RE = /\/outputs\/[A-Za-z0-9._-]+\.[A-Za-z0-9]+/g;

export function findOutputPaths(text: string): string[] {
  return Array.from(new Set(text.match(OUTPUT_PATH_RE) ?? []));
}
