"use client";

import { Platform } from "@/types";
import { PLATFORMS } from "@/lib/platforms";

interface PlatformSelectorProps {
  selected: Platform[];
  onToggle: (platform: Platform) => void;
}

const PLATFORM_COLORS: Record<Platform, string> = {
  twitter: "var(--color-twitter)",
  linkedin: "var(--color-linkedin)",
  instagram: "var(--color-instagram)",
  email: "var(--color-email)",
  "video-script": "var(--color-video)",
};

export default function PlatformSelector({
  selected,
  onToggle,
}: PlatformSelectorProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-[var(--color-text-primary)]">
        Platforms
      </label>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {PLATFORMS.map((p) => {
          const isSelected = selected.includes(p.id);
          const color = PLATFORM_COLORS[p.id];
          return (
            <button
              key={p.id}
              onClick={() => onToggle(p.id)}
              className={`rounded-xl border px-4 py-3 text-left transition ${
                isSelected
                  ? "border-[var(--color-border-light)] bg-[var(--color-surface)]"
                  : "border-[var(--color-border)] bg-[var(--color-background)] opacity-50 hover:opacity-75"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold text-white"
                  style={{ backgroundColor: color }}
                >
                  {p.icon}
                </span>
                <span className="text-sm font-medium">{p.name}</span>
              </div>
              <div className="mt-1.5 text-xs text-[var(--color-text-muted)]">
                {p.characterLimit
                  ? `${p.characterLimit.toLocaleString()} char limit`
                  : "No limit"}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
