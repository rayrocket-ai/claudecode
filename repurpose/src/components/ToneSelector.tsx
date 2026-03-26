"use client";

import { Tone } from "@/types";

interface ToneSelectorProps {
  tone: Tone;
  onToneChange: (tone: Tone) => void;
}

const TONES: { value: Tone; label: string; description: string }[] = [
  {
    value: "professional",
    label: "Professional",
    description: "Polished and authoritative",
  },
  {
    value: "casual",
    label: "Casual",
    description: "Friendly and conversational",
  },
  {
    value: "witty",
    label: "Witty",
    description: "Clever with personality",
  },
];

export default function ToneSelector({ tone, onToneChange }: ToneSelectorProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-[var(--color-text-primary)]">
        Tone
      </label>
      <div className="grid grid-cols-3 gap-3">
        {TONES.map((t) => (
          <button
            key={t.value}
            onClick={() => onToneChange(t.value)}
            className={`rounded-xl border px-4 py-3 text-left transition ${
              tone === t.value
                ? "border-[var(--color-accent)] bg-[var(--color-accent-subtle)] ring-1 ring-[var(--color-accent)]"
                : "border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-border-light)]"
            }`}
          >
            <div className="text-sm font-medium">{t.label}</div>
            <div className="mt-0.5 text-xs text-[var(--color-text-muted)]">
              {t.description}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
