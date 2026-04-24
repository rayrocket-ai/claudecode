import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";

export interface StatRevealProps {
  value: string;          // e.g. "90%" or "2.4x"
  label: string;          // e.g. "of web-agent work is wasted"
  startAtSecond: number;
  durationSeconds: number;
  x?: number | string;
  y?: number | string;
  accentColor?: string;
  labelColor?: string;
  backgroundColor?: string;
  valueFontSize?: number;
  labelFontSize?: number;
}

export const StatReveal: React.FC<StatRevealProps> = ({
  value,
  label,
  startAtSecond,
  durationSeconds,
  x = "50%",
  y = "50%",
  accentColor = "#FF5A00",
  labelColor = "rgba(255,255,255,0.7)",
  backgroundColor = "rgba(10,10,10,0.92)",
  valueFontSize = 260,
  labelFontSize = 42,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  if (t < startAtSecond || t > startAtSecond + durationSeconds) return null;

  const startFrame = startAtSecond * fps;
  const endFrame = (startAtSecond + durationSeconds) * fps;

  const containerScale = spring({
    frame: frame - startFrame,
    fps,
    from: 0.92,
    to: 1,
    durationInFrames: 14,
    config: { damping: 12 },
  });

  const valueScale = spring({
    frame: frame - startFrame - 2,
    fps,
    from: 0.7,
    to: 1,
    durationInFrames: 18,
    config: { damping: 10, mass: 0.6 },
  });

  const labelOpacity = interpolate(
    frame,
    [startFrame + 10, startFrame + 22],
    [0, 1],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    },
  );

  const fadeOut = interpolate(
    frame,
    [endFrame - 8, endFrame],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${containerScale})`,
        opacity: fadeOut,
        background: backgroundColor,
        padding: "60px 80px",
        borderRadius: 24,
        textAlign: "center",
        boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
      }}
    >
      <div
        style={{
          fontFamily: "Menlo, 'SF Mono', monospace",
          fontWeight: 900,
          fontSize: valueFontSize,
          color: accentColor,
          transform: `scale(${valueScale})`,
          lineHeight: 1,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontFamily: "Arial, sans-serif",
          fontSize: labelFontSize,
          fontWeight: 500,
          color: labelColor,
          marginTop: 24,
          opacity: labelOpacity,
          maxWidth: 900,
        }}
      >
        {label}
      </div>
    </div>
  );
};
