"use client";

import { HistoryEntry } from "@/types";

interface HistorySidebarProps {
  isOpen: boolean;
  entries: HistoryEntry[];
  onClose: () => void;
  onSelect: (entry: HistoryEntry) => void;
  onClear: () => void;
}

function formatDate(timestamp: number): string {
  const d = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString();
}

const TONE_LABELS: Record<string, string> = {
  professional: "Pro",
  casual: "Casual",
  witty: "Witty",
};

export default function HistorySidebar({
  isOpen,
  entries,
  onClose,
  onSelect,
  onClear,
}: HistorySidebarProps) {
  if (!isOpen) return null;

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/50"
        onClick={onClose}
      />
      <div className="animate-slide-in fixed right-0 top-0 z-50 flex h-full w-96 max-w-[90vw] flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex items-center justify-between border-b border-[var(--color-border)] px-5 py-4">
          <h2 className="text-base font-semibold">History</h2>
          <button
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
          >
            Close
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {entries.length === 0 ? (
            <div className="py-12 text-center text-sm text-[var(--color-text-muted)]">
              No history yet
            </div>
          ) : (
            entries.map((entry) => (
              <button
                key={entry.id}
                onClick={() => onSelect(entry)}
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] p-3 text-left transition hover:border-[var(--color-border-light)]"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {formatDate(entry.timestamp)}
                  </span>
                  <span className="rounded bg-[var(--color-accent-subtle)] px-1.5 py-0.5 text-xs text-[var(--color-accent)]">
                    {TONE_LABELS[entry.tone] || entry.tone}
                  </span>
                </div>
                <p className="mt-1.5 line-clamp-2 text-sm text-[var(--color-text-secondary)]">
                  {entry.sourceSnippet}
                </p>
                <div className="mt-2 flex gap-1.5">
                  {entry.platforms.map((p) => (
                    <span
                      key={p}
                      className="rounded bg-[var(--color-surface-hover)] px-1.5 py-0.5 text-xs text-[var(--color-text-muted)]"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </button>
            ))
          )}
        </div>

        {entries.length > 0 && (
          <div className="border-t border-[var(--color-border)] p-4">
            <button
              onClick={onClear}
              className="w-full rounded-lg border border-[var(--color-border)] py-2 text-sm text-[var(--color-danger)] transition hover:bg-[var(--color-danger)] hover:text-white"
            >
              Clear All History
            </button>
          </div>
        )}
      </div>
    </>
  );
}
