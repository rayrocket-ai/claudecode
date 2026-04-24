import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

export interface LowerThirdProps {
  name: string;
  title?: string;
  startAtSecond: number;
  durationSeconds: number;
  accentColor?: string;
  backgroundColor?: string;
}

export const LowerThird: React.FC<LowerThirdProps> = ({
  name,
  title,
  startAtSecond,
  durationSeconds,
  accentColor = "#FF5A00",
  backgroundColor = "rgba(10,10,10,0.92)",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  if (t < startAtSecond || t > startAtSecond + durationSeconds) return null;

  const enterFrame = startAtSecond * fps;
  const exitFrame = (startAtSecond + durationSeconds) * fps;

  const slideIn = spring({
    frame: frame - enterFrame,
    fps,
    from: -600,
    to: 0,
    durationInFrames: 18,
    config: { damping: 14, mass: 0.8 },
  });

  const slideOut = interpolate(
    frame,
    [exitFrame - 10, exitFrame],
    [0, -600],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const translateX = frame < exitFrame - 10 ? slideIn : slideOut;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 140,
        left: 60,
        display: "flex",
        alignItems: "center",
        transform: `translateX(${translateX}px)`,
      }}
    >
      <div style={{ width: 8, height: 72, background: accentColor, marginRight: 18 }} />
      <div
        style={{
          background: backgroundColor,
          padding: "16px 28px",
          borderRadius: 4,
        }}
      >
        <div
          style={{
            fontFamily: "Arial Black, sans-serif",
            fontSize: 36,
            fontWeight: 900,
            color: "#FFFFFF",
            textTransform: "uppercase",
            letterSpacing: 1,
            lineHeight: 1.1,
          }}
        >
          {name}
        </div>
        {title && (
          <div
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: 22,
              fontWeight: 400,
              color: "rgba(255,255,255,0.8)",
              marginTop: 4,
            }}
          >
            {title}
          </div>
        )}
      </div>
    </div>
  );
};
