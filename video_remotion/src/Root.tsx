import React from "react";
import { Composition, staticFile } from "remotion";
import { ReelComposition } from "./ReelComposition";
import { JsonComposition, defaultJsonSceneProps } from "./JsonComposition";
import { sampleWords, sampleBRolls } from "./sampleData";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Reel = ReelComposition as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const JsonScene = JsonComposition as any;

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

      {/* 16:9 landscape */}
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

      {/* JSON-driven composition — motion-graphics library, AI-friendly.
         Use node scripts/import-scene.js to populate from a scene.json. */}
      <Composition
        id="JsonScene"
        component={JsonScene}
        durationInFrames={30 * 60}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultJsonSceneProps}
      />

      <Composition
        id="JsonSceneVertical"
        component={JsonScene}
        durationInFrames={30 * 60}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultJsonSceneProps}
      />
    </>
  );
};
