"use client";

import { SourceType } from "@/types";

interface ContentInputProps {
  content: string;
  sourceType: SourceType;
  onContentChange: (value: string) => void;
  onSourceTypeChange: (value: SourceType) => void;
}

const SOURCE_TYPES: { value: SourceType; label: string }[] = [
  { value: "blog-post", label: "Blog Post" },
  { value: "article", label: "Article" },
  { value: "video-transcript", label: "Video Transcript" },
  { value: "other", label: "Other" },
];

export default function ContentInput({
  content,
  sourceType,
  onContentChange,
  onSourceTypeChange,
}: ContentInputProps) {
  const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  const charCount = content.length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-[var(--color-text-primary)]">
          Source Content
        </label>
        <select
          value={sourceType}
          onChange={(e) => onSourceTypeChange(e.target.value as SourceType)}
          className="rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-sm text-[var(--color-text-secondary)] outline-none transition focus:border-[var(--color-accent)]"
        >
          {SOURCE_TYPES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>
      <textarea
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        placeholder="Paste your blog post, article, or video transcript here..."
        rows={10}
        className="w-full resize-y rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm leading-relaxed text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none transition focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)]"
      />
      <div className="flex gap-4 text-xs text-[var(--color-text-muted)]">
        <span>{wordCount} words</span>
        <span>{charCount.toLocaleString()} characters</span>
        {charCount > 15000 && (
          <span className="text-[var(--color-warning)]">
            Content will be truncated to 15,000 characters
          </span>
        )}
      </div>
    </div>
  );
}
