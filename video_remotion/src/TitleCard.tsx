import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

interface Props {
  text: string;
}

export const TitleCard: React.FC<Props> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const showDurationFrames = 3 * fps;

  if (frame > showDurationFrames) return null;

  const scale = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    durationInFrames: 15,
    config: { damping: 10, mass: 0.5 },
  });

  const fadeOut = interpolate(
    frame,
    [showDurationFrames - 10, showDurationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: fadeOut,
        zIndex: 10,
      }}
    >
      <div
        style={{
          background: "rgba(0,0,0,0.75)",
          borderRadius: 20,
          padding: "30px 50px",
          transform: `scale(${scale})`,
        }}
      >
        <span
          style={{
            fontFamily: "Arial Black, Arial, sans-serif",
            fontWeight: 900,
            fontSize: 64,
            color: "#FFFFFF",
            textTransform: "uppercase",
            textAlign: "center",
            display: "block",
            maxWidth: 800,
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};
