import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";

export interface ArrowAnnotationProps {
  text: string;
  fromX: number;  // pixels
  fromY: number;
  toX: number;
  toY: number;
  startAtSecond: number;
  durationSeconds: number;
  color?: string;
  strokeWidth?: number;
  fontSize?: number;
}

/**
 * Draws a hand-drawn style curved arrow with a label.
 * Reveals by tracing the path from `from` to `to`, then pops the label.
 */
export const ArrowAnnotation: React.FC<ArrowAnnotationProps> = ({
  text,
  fromX,
  fromY,
  toX,
  toY,
  startAtSecond,
  durationSeconds,
  color = "#FF5A00",
  strokeWidth = 6,
  fontSize = 36,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  if (t < startAtSecond || t > startAtSecond + durationSeconds) return null;

  const startFrame = startAtSecond * fps;
  const endFrame = (startAtSecond + durationSeconds) * fps;
  const drawDurationFrames = Math.min(18, (endFrame - startFrame) / 3);

  const progress = interpolate(
    frame,
    [startFrame, startFrame + drawDurationFrames],
    [0, 1],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    },
  );

  const labelOpacity = interpolate(
    frame,
    [startFrame + drawDurationFrames - 2, startFrame + drawDurationFrames + 6],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const fadeOut = interpolate(
    frame,
    [endFrame - 8, endFrame],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Control point — perpendicular offset from midpoint for the curve.
  const midX = (fromX + toX) / 2;
  const midY = (fromY + toY) / 2;
  const dx = toX - fromX;
  const dy = toY - fromY;
  const len = Math.sqrt(dx * dx + dy * dy) || 1;
  const perpX = -dy / len;
  const perpY = dx / len;
  const curveAmount = len * 0.25;
  const ctrlX = midX + perpX * curveAmount;
  const ctrlY = midY + perpY * curveAmount;

  const pathLength = 1000; // arbitrary large number for dash
  const dashOffset = pathLength * (1 - progress);

  return (
    <svg
      width={width}
      height={height}
      style={{ position: "absolute", inset: 0, opacity: fadeOut, pointerEvents: "none" }}
    >
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="8"
          refY="5"
          orient="auto"
        >
          <polygon points="0 0, 10 5, 0 10" fill={color} />
        </marker>
      </defs>
      <path
        d={`M ${fromX} ${fromY} Q ${ctrlX} ${ctrlY} ${toX} ${toY}`}
        stroke={color}
        strokeWidth={strokeWidth}
        fill="none"
        strokeLinecap="round"
        markerEnd={progress > 0.95 ? "url(#arrowhead)" : undefined}
        style={{
          strokeDasharray: pathLength,
          strokeDashoffset: dashOffset,
        }}
      />
      <text
        x={fromX}
        y={fromY - 16}
        fontFamily="Menlo, monospace"
        fontSize={fontSize}
        fontWeight="700"
        fill={color}
        opacity={labelOpacity}
      >
        {text}
      </text>
    </svg>
  );
};
