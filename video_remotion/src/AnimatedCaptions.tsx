import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import type { WordTiming } from "./types";

const WORDS_PER_GROUP = 4;

interface Props {
  words: WordTiming[];
  position: "bottom" | "center";
}

export const AnimatedCaptions: React.FC<Props> = ({ words, position }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const groups: WordTiming[][] = [];
  for (let i = 0; i < words.length; i += WORDS_PER_GROUP) {
    groups.push(words.slice(i, i + WORDS_PER_GROUP));
  }

  const activeGroup = groups.find((g) => {
    const start = g[0].start;
    const end = g[g.length - 1].end;
    return currentTime >= start && currentTime <= end + 0.3;
  });

  if (!activeGroup) return null;

  const groupStart = activeGroup[0].start;
  const enterFrame = groupStart * fps;
  const scale = spring({ frame, fps, from: 0.8, to: 1, durationInFrames: 8, config: { damping: 12 } });

  const opacity = interpolate(
    frame,
    [enterFrame, enterFrame + 4],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: position === "bottom" ? 200 : undefined,
        top: position === "center" ? "50%" : undefined,
        transform: position === "center" ? `translateY(-50%) scale(${scale})` : `scale(${scale})`,
        display: "flex",
        justifyContent: "center",
        flexWrap: "wrap",
        gap: 12,
        padding: "0 60px",
        opacity,
      }}
    >
      {activeGroup.map((w, i) => {
        const isActive = currentTime >= w.start && currentTime <= w.end;
        const isPast = currentTime > w.end;
        return (
          <span
            key={`${w.start}-${i}`}
            style={{
              fontFamily: "Arial Black, Arial, sans-serif",
              fontWeight: 900,
              fontSize: 72,
              textTransform: "uppercase",
              color: isActive ? "#FFD700" : isPast ? "#FFFFFF" : "rgba(255,255,255,0.5)",
              textShadow: isActive
                ? "0 0 20px rgba(255,215,0,0.8), 3px 3px 0 #000"
                : "3px 3px 0 #000, -1px -1px 0 #000",
              transition: "color 0.05s",
              lineHeight: 1.1,
            }}
          >
            {w.word.trim()}
          </span>
        );
      })}
    </div>
  );
};
