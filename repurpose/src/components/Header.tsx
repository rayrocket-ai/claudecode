"use client";

interface HeaderProps {
  onHistoryToggle: () => void;
  historyCount: number;
}

export default function Header({ onHistoryToggle, historyCount }: HeaderProps) {
  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-accent)] text-lg font-bold">
            R
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight">Repurpose</h1>
            <p className="text-xs text-[var(--color-text-muted)]">
              AI Content Repurposing Tool
            </p>
          </div>
        </div>
        <button
          onClick={onHistoryToggle}
          className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-text-secondary)] transition hover:border-[var(--color-border-light)] hover:text-[var(--color-text-primary)]"
        >
          History
          {historyCount > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--color-accent-subtle)] px-1 text-xs text-[var(--color-accent)]">
              {historyCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
