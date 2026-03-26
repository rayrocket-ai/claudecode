"use client";

import { PlatformOutput } from "@/types";
import PlatformPreview from "./PlatformPreview";

interface OutputPanelProps {
  outputs: PlatformOutput[];
  isLoading: boolean;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-3">
          <div className="loading-shimmer h-5 w-32 rounded" />
          <div className="loading-shimmer h-40 w-full rounded-xl" />
        </div>
      ))}
    </div>
  );
}

export default function OutputPanel({ outputs, isLoading }: OutputPanelProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Generating...</h2>
        <LoadingSkeleton />
      </div>
    );
  }

  if (!outputs.length) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="mb-4 text-5xl opacity-20">&#10024;</div>
        <h2 className="text-lg font-semibold text-[var(--color-text-secondary)]">
          Your repurposed content will appear here
        </h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Paste your content, pick your platforms, and hit Generate
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h2 className="text-lg font-semibold">
        Results{" "}
        <span className="text-sm font-normal text-[var(--color-text-muted)]">
          ({outputs.length} platform{outputs.length !== 1 ? "s" : ""})
        </span>
      </h2>
      {outputs.map((output) => (
        <PlatformPreview key={output.platform} output={output} />
      ))}
    </div>
  );
}
