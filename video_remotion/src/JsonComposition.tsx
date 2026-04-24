import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { AnimatedCaptions } from "./AnimatedCaptions";
import { BRollOverlay } from "./BRollOverlay";
import {
  Callout,
  Counter,
  LowerThird,
  StatReveal,
  ArrowAnnotation,
} from "./components";
import type { WordTiming, BRollClip } from "./types";

/**
 * A JSON-driven composition. An AI agent can emit a JSON object with
 * `videoSrc`, `words`, `brolls`, and a list of `overlays` — no TypeScript
 * edits needed.
 *
 * Overlay items follow a discriminated union by `type`. See `OverlayItem`
 * below for the supported shapes.
 */
export type OverlayItem =
  | ({ type: "callout" } & import("./components").CalloutProps)
  | ({ type: "counter" } & import("./components").CounterProps)
  | ({ type: "lower-third" } & import("./components").LowerThirdProps)
  | ({ type: "stat-reveal" } & import("./components").StatRevealProps)
  | ({ type: "arrow" } & import("./components").ArrowAnnotationProps);

export interface JsonSceneProps {
  videoSrc: string;
  words: WordTiming[];
  brolls: BRollClip[];
  overlays: OverlayItem[];
  captionStyle?: "bottom" | "center" | "none";
}

export const JsonComposition: React.FC<JsonSceneProps> = ({
  videoSrc,
  words,
  brolls,
  overlays,
  captionStyle = "bottom",
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <OffthreadVideo
        src={videoSrc}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />

      <BRollOverlay clips={brolls} />

      {/* Motion graphics layer (before captions per the rule: captions last) */}
      {overlays.map((ov, i) => {
        switch (ov.type) {
          case "callout":
            return <Callout key={i} {...ov} />;
          case "counter":
            return <Counter key={i} {...ov} />;
          case "lower-third":
            return <LowerThird key={i} {...ov} />;
          case "stat-reveal":
            return <StatReveal key={i} {...ov} />;
          case "arrow":
            return <ArrowAnnotation key={i} {...ov} />;
          default:
            return null;
        }
      })}

      {captionStyle !== "none" && (
        <>
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: "30%",
              background: "linear-gradient(transparent, rgba(0,0,0,0.6))",
              pointerEvents: "none",
            }}
          />
          <AnimatedCaptions words={words} position={captionStyle} />
        </>
      )}
    </AbsoluteFill>
  );
};

/**
 * Default props used when Remotion Studio opens the JsonComposition.
 * Replace with real data via props or `node scripts/import-scene.js`.
 */
export const defaultJsonSceneProps: JsonSceneProps = {
  videoSrc: staticFile("main.mp4"),
  words: [],
  brolls: [],
  overlays: [],
  captionStyle: "bottom",
};
