"use client";

import { PlatformOutput } from "@/types";
import { getPlatformConfig } from "@/lib/platforms";
import CopyButton from "./CopyButton";

interface PlatformPreviewProps {
  output: PlatformOutput;
}

const PLATFORM_COLORS: Record<string, string> = {
  twitter: "var(--color-twitter)",
  linkedin: "var(--color-linkedin)",
  instagram: "var(--color-instagram)",
  email: "var(--color-email)",
  "video-script": "var(--color-video)",
};

function TwitterPreview({ content }: { content: string }) {
  const tweets = content
    .split(/---+/)
    .map((t) => t.trim())
    .filter(Boolean);
  return (
    <div className="space-y-3">
      {tweets.map((tweet, i) => (
        <div
          key={i}
          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-4"
        >
          <div className="mb-2 flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-[var(--color-twitter)]" />
            <div>
              <div className="text-sm font-semibold">You</div>
              <div className="text-xs text-[var(--color-text-muted)]">
                @yourhandle
              </div>
            </div>
            <div className="ml-auto text-xs text-[var(--color-text-muted)]">
              {i + 1}/{tweets.length}
            </div>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{tweet}</p>
          <div className="mt-2 text-xs text-[var(--color-text-muted)]">
            {tweet.length}/280
            {tweet.length > 280 && (
              <span className="ml-1 text-[var(--color-danger)]">
                Over limit!
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function LinkedInPreview({ content }: { content: string }) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
      <div className="mb-3 flex items-center gap-2">
        <div className="h-10 w-10 rounded-full bg-[var(--color-linkedin)]" />
        <div>
          <div className="text-sm font-semibold">Your Name</div>
          <div className="text-xs text-[var(--color-text-muted)]">
            Your headline
          </div>
        </div>
      </div>
      <div className="whitespace-pre-wrap text-sm leading-relaxed">
        {content}
      </div>
      <div className="mt-4 flex gap-6 border-t border-[var(--color-border)] pt-3 text-xs text-[var(--color-text-muted)]">
        <span>Like</span>
        <span>Comment</span>
        <span>Repost</span>
        <span>Send</span>
      </div>
    </div>
  );
}

function InstagramPreview({ content }: { content: string }) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] overflow-hidden">
      <div className="flex aspect-square items-center justify-center bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400">
        <span className="text-4xl opacity-50">Your Image</span>
      </div>
      <div className="p-4">
        <div className="mb-2 flex gap-4 text-[var(--color-text-muted)]">
          <span>&#9825;</span>
          <span>&#9741;</span>
          <span>&#9993;</span>
        </div>
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          <span className="font-semibold">yourhandle </span>
          {content}
        </div>
      </div>
    </div>
  );
}

function EmailPreview({ content }: { content: string }) {
  const lines = content.split("\n");
  let subject = "";
  let preview = "";
  let bodyLines: string[] = [];

  let bodyStarted = false;
  for (const line of lines) {
    if (line.toLowerCase().startsWith("subject:")) {
      subject = line.replace(/^subject:\s*/i, "");
    } else if (line.toLowerCase().startsWith("preview:")) {
      preview = line.replace(/^preview:\s*/i, "");
    } else if (bodyStarted || line.trim() !== "") {
      bodyStarted = true;
      bodyLines.push(line);
    }
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] overflow-hidden">
      <div className="border-b border-[var(--color-border)] bg-[var(--color-surface)] p-4 space-y-1.5">
        <div className="flex gap-2 text-xs">
          <span className="text-[var(--color-text-muted)]">From:</span>
          <span>you@yourbrand.com</span>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="text-[var(--color-text-muted)]">To:</span>
          <span>subscriber@email.com</span>
        </div>
        {subject && (
          <div className="text-sm font-semibold">{subject}</div>
        )}
        {preview && (
          <div className="text-xs text-[var(--color-text-muted)] italic">
            {preview}
          </div>
        )}
      </div>
      <div className="whitespace-pre-wrap p-4 text-sm leading-relaxed">
        {bodyLines.join("\n")}
      </div>
    </div>
  );
}

function VideoScriptPreview({ content }: { content: string }) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] overflow-hidden">
      <div className="flex items-center gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">
        <div className="h-3 w-3 rounded-full bg-[var(--color-video)]" />
        <span className="text-xs font-medium text-[var(--color-text-muted)]">
          VIDEO SCRIPT
        </span>
      </div>
      <div className="whitespace-pre-wrap p-4 text-sm font-mono leading-relaxed">
        {content}
      </div>
      <div className="border-t border-[var(--color-border)] px-4 py-2 text-xs text-[var(--color-text-muted)]">
        ~{Math.round(content.split(/\s+/).length / 2.5)}s at speaking pace
      </div>
    </div>
  );
}

const PREVIEW_COMPONENTS: Record<
  string,
  React.ComponentType<{ content: string }>
> = {
  twitter: TwitterPreview,
  linkedin: LinkedInPreview,
  instagram: InstagramPreview,
  email: EmailPreview,
  "video-script": VideoScriptPreview,
};

export default function PlatformPreview({ output }: PlatformPreviewProps) {
  const config = getPlatformConfig(output.platform);
  const PreviewComponent = PREVIEW_COMPONENTS[output.platform];
  const color = PLATFORM_COLORS[output.platform] || "var(--color-accent)";

  if (!config) return null;

  return (
    <div className="animate-fade-in space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="flex h-6 w-6 items-center justify-center rounded text-xs font-bold text-white"
            style={{ backgroundColor: color }}
          >
            {config.icon}
          </span>
          <h3 className="text-sm font-semibold">{config.name}</h3>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs ${
              output.isOverLimit
                ? "text-[var(--color-danger)]"
                : "text-[var(--color-text-muted)]"
            }`}
          >
            {output.characterCount.toLocaleString()} chars
            {config.characterLimit &&
              ` / ${config.characterLimit.toLocaleString()}`}
          </span>
          <CopyButton text={output.content} />
        </div>
      </div>
      {PreviewComponent && <PreviewComponent content={output.content} />}
    </div>
  );
}
