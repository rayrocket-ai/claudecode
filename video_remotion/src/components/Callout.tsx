import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

export interface CalloutProps {
  text: string;
  startAtSecond: number;
  durationSeconds: number;
  x?: number | string;
  y?: number | string;
  accentColor?: string;
  backgroundColor?: string;
  textColor?: string;
  fontSize?: number;
}

export const Callout: React.FC<CalloutProps> = ({
  text,
  startAtSecond,
  durationSeconds,
  x = "50%",
  y = "25%",
  accentColor = "#FF5A00",
  backgroundColor = "rgba(10,10,10,0.92)",
  textColor = "#FFFFFF",
  fontSize = 56,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  if (t < startAtSecond || t > startAtSecond + durationSeconds) return null;

  const enterFrame = startAtSecond * fps;
  const exitFrame = (startAtSecond + durationSeconds) * fps;

  const scale = spring({
    frame: frame - enterFrame,
    fps,
    from: 0.85,
    to: 1,
    durationInFrames: 12,
    config: { damping: 12, mass: 0.6 },
  });

  const opacity = interpolate(
    frame,
    [enterFrame, enterFrame + 4, exitFrame - 6, exitFrame],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${scale})`,
        opacity,
        padding: "24px 36px",
        borderRadius: 16,
        background: backgroundColor,
        borderLeft: `6px solid ${accentColor}`,
        fontFamily: "Menlo, 'SF Mono', monospace",
        fontWeight: 700,
        fontSize,
        color: textColor,
        maxWidth: "80%",
        textAlign: "center",
        boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
      }}
    >
      {text}
    </div>
  );
};
