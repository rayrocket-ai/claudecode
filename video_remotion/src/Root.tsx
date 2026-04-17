import React from "react";
import { Composition, staticFile } from "remotion";
import { ReelComposition } from "./ReelComposition";
import { sampleWords, sampleBRolls } from "./sampleData";
import type { ReelProps } from "./types";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Reel = ReelComposition as any;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 9:16 vertical reel — 30 fps, 30 seconds */}
      <Composition
        id="ReelComposition"
        component={Reel}
        durationInFrames={30 * 30}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          videoSrc: staticFile("main.mp4"),
          words: sampleWords,
          brolls: sampleBRolls,
          title: "Stay Consistent",
          captionStyle: "bottom",
        }}
      />

      {/* 16:9 landscape version */}
      <Composition
        id="ReelLandscape"
        component={Reel}
        durationInFrames={30 * 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          videoSrc: staticFile("main.mp4"),
          words: sampleWords,
          brolls: sampleBRolls,
          title: "Stay Consistent",
          captionStyle: "center",
        }}
      />
    </>
  );
};
