import React from "react";
import { AbsoluteFill, OffthreadVideo } from "remotion";
import { AnimatedCaptions } from "./AnimatedCaptions";
import { BRollOverlay } from "./BRollOverlay";
import { TitleCard } from "./TitleCard";
import type { ReelProps } from "./types";

export const ReelComposition: React.FC<ReelProps> = ({
  videoSrc,
  words,
  brolls,
  title,
  captionStyle = "bottom",
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Base video layer */}
      <OffthreadVideo
        src={videoSrc}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />

      {/* B-roll overlay layer */}
      <BRollOverlay clips={brolls} />

      {/* Gradient overlay for caption readability */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "40%",
          background:
            "linear-gradient(transparent, rgba(0,0,0,0.7))",
          pointerEvents: "none",
        }}
      />

      {/* Animated captions */}
      <AnimatedCaptions words={words} position={captionStyle} />

      {/* Title card (shows for first 3 seconds) */}
      {title && <TitleCard text={title} />}
    </AbsoluteFill>
  );
};
