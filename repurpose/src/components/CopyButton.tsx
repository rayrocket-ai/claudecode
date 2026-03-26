"use client";

import { useState } from "react";

interface CopyButtonProps {
  text: string;
}

export default function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="rounded-md px-2.5 py-1 text-xs font-medium transition hover:bg-[var(--color-surface-hover)]"
      style={{
        color: copied ? "var(--color-success)" : "var(--color-text-muted)",
      }}
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}
