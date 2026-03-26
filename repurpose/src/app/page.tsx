"use client";

import { useState, useEffect, useCallback } from "react";
import { Platform, Tone, SourceType, PlatformOutput, HistoryEntry } from "@/types";
import Header from "@/components/Header";
import ContentInput from "@/components/ContentInput";
import ToneSelector from "@/components/ToneSelector";
import PlatformSelector from "@/components/PlatformSelector";
import OutputPanel from "@/components/OutputPanel";
import HistorySidebar from "@/components/HistorySidebar";
import { getHistory, addToHistory, clearHistory } from "@/lib/history";

export default function Home() {
  const [content, setContent] = useState("");
  const [sourceType, setSourceType] = useState<SourceType>("blog-post");
  const [tone, setTone] = useState<Tone>("professional");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([
    "twitter",
    "linkedin",
    "instagram",
    "email",
    "video-script",
  ]);
  const [outputs, setOutputs] = useState<PlatformOutput[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  const togglePlatform = (platform: Platform) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  const handleGenerate = useCallback(async () => {
    if (!content.trim() || content.trim().length < 50) {
      setError("Please enter at least 50 characters of content.");
      return;
    }
    if (!selectedPlatforms.length) {
      setError("Select at least one platform.");
      return;
    }

    setError(null);
    setIsLoading(true);
    setOutputs([]);

    try {
      const res = await fetch("/api/repurpose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          sourceType,
          platforms: selectedPlatforms,
          tone,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Failed to generate content.");
      }

      setOutputs(data.outputs);

      const entry: HistoryEntry = {
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        sourceSnippet: content.slice(0, 120),
        sourceType,
        tone,
        platforms: selectedPlatforms,
        outputs: data.outputs,
      };
      addToHistory(entry);
      setHistory(getHistory());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }, [content, sourceType, selectedPlatforms, tone]);

  const handleHistorySelect = (entry: HistoryEntry) => {
    setOutputs(entry.outputs);
    setIsHistoryOpen(false);
  };

  const handleClearHistory = () => {
    clearHistory();
    setHistory([]);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        handleGenerate();
      }
      if (e.key === "Escape" && isHistoryOpen) {
        setIsHistoryOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleGenerate, isHistoryOpen]);

  const canGenerate =
    content.trim().length >= 50 && selectedPlatforms.length > 0 && !isLoading;

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        onHistoryToggle={() => setIsHistoryOpen(true)}
        historyCount={history.length}
      />

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        <div className="grid gap-8 lg:grid-cols-[1fr,1fr]">
          {/* Left: Input */}
          <div className="space-y-6">
            <ContentInput
              content={content}
              sourceType={sourceType}
              onContentChange={setContent}
              onSourceTypeChange={setSourceType}
            />
            <ToneSelector tone={tone} onToneChange={setTone} />
            <PlatformSelector
              selected={selectedPlatforms}
              onToggle={togglePlatform}
            />

            {error && (
              <div className="rounded-lg border border-[var(--color-danger)] bg-red-500/10 px-4 py-3 text-sm text-[var(--color-danger)]">
                {error}
              </div>
            )}

            <button
              onClick={handleGenerate}
              disabled={!canGenerate}
              className="w-full rounded-xl bg-[var(--color-accent)] py-3.5 text-sm font-semibold text-white transition hover:bg-[var(--color-accent-hover)] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="h-4 w-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="3"
                      className="opacity-25"
                    />
                    <path
                      d="M4 12a8 8 0 018-8"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                  </svg>
                  Generating...
                </span>
              ) : (
                <>Generate All Platforms &nbsp; &#8984;&#9166;</>
              )}
            </button>
          </div>

          {/* Right: Output */}
          <div className="lg:border-l lg:border-[var(--color-border)] lg:pl-8">
            <OutputPanel outputs={outputs} isLoading={isLoading} />
          </div>
        </div>
      </main>

      <HistorySidebar
        isOpen={isHistoryOpen}
        entries={history}
        onClose={() => setIsHistoryOpen(false)}
        onSelect={handleHistorySelect}
        onClear={handleClearHistory}
      />
    </div>
  );
}
