import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
  Img,
  interpolate,
} from "remotion";
import type { BRollClip } from "./types";

interface Props {
  clips: BRollClip[];
}

export const BRollOverlay: React.FC<Props> = ({ clips }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const activeClip = clips.find(
    (c) =>
      currentTime >= c.startAtSecond &&
      currentTime < c.startAtSecond + c.durationSeconds
  );

  if (!activeClip) return null;

  const clipStartFrame = activeClip.startAtSecond * fps;
  const clipEndFrame = (activeClip.startAtSecond + activeClip.durationSeconds) * fps;

  const fadeIn = interpolate(frame, [clipStartFrame, clipStartFrame + 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(frame, [clipEndFrame - 6, clipEndFrame], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = Math.min(fadeIn, fadeOut);

  const scale = interpolate(
    frame,
    [clipStartFrame, clipEndFrame],
    [1.0, 1.05],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const isVideo = /\.(mp4|webm|mov)$/i.test(activeClip.src);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity,
        overflow: "hidden",
      }}
    >
      {isVideo ? (
        <OffthreadVideo
          src={activeClip.src}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale})`,
          }}
        />
      ) : (
        <Img
          src={activeClip.src}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${scale})`,
          }}
        />
      )}
    </div>
  );
};
