import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";

export interface CounterProps {
  from: number;
  to: number;
  startAtSecond: number;
  durationSeconds: number;
  suffix?: string;
  prefix?: string;
  x?: number | string;
  y?: number | string;
  color?: string;
  fontSize?: number;
  decimals?: number;
}

export const Counter: React.FC<CounterProps> = ({
  from,
  to,
  startAtSecond,
  durationSeconds,
  suffix = "",
  prefix = "",
  x = "50%",
  y = "50%",
  color = "#FF5A00",
  fontSize = 180,
  decimals = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  if (t < startAtSecond || t > startAtSecond + durationSeconds) return null;

  const startFrame = startAtSecond * fps;
  const endFrame = (startAtSecond + durationSeconds) * fps;

  const value = interpolate(
    frame,
    [startFrame, endFrame - 4],
    [from, to],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    },
  );

  const opacity = interpolate(
    frame,
    [startFrame, startFrame + 4, endFrame - 6, endFrame],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: "translate(-50%, -50%)",
        opacity,
        fontFamily: "Menlo, 'SF Mono', monospace",
        fontWeight: 900,
        fontSize,
        color,
        textShadow: "0 4px 20px rgba(0,0,0,0.6)",
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {prefix}
      {value.toFixed(decimals)}
      {suffix}
    </div>
  );
};
