#!/usr/bin/env node
/**
 * Builds src/generatedScene.ts from a scene.json file, which Remotion can
 * import to render a JsonComposition without editing TypeScript.
 *
 * scene.json shape matches JsonSceneProps in src/JsonComposition.tsx:
 *
 *   {
 *     "videoSrc": "main.mp4",        // path under public/
 *     "words":   [ ...words.json contents... ],
 *     "brolls":  [ { "src": "...", "startAtSecond": 0, "durationSeconds": 3 } ],
 *     "overlays": [
 *       { "type": "stat-reveal", "value": "90%", "label": "of ...",
 *         "startAtSecond": 2, "durationSeconds": 4 }
 *     ],
 *     "captionStyle": "bottom"
 *   }
 *
 * Usage:
 *   node scripts/import-scene.js path/to/scene.json
 */
const fs = require("fs");
const path = require("path");

const input = process.argv[2];
if (!input) {
  console.error("Usage: node import-scene.js <scene.json>");
  process.exit(1);
}

const scene = JSON.parse(fs.readFileSync(input, "utf8"));

const ts = `import type { JsonSceneProps } from "./JsonComposition";
import { staticFile } from "remotion";

export const scene: JsonSceneProps = ${JSON.stringify(scene, null, 2)
  // Swap string paths into staticFile() calls for anything in public/.
  .replace(/"videoSrc":\s*"([^"]+)"/g, '"videoSrc": staticFile("$1")')
  .replace(/"src":\s*"(?!https?:)([^"]+)"/g, '"src": staticFile("$1")')};
`;

const out = path.join(__dirname, "..", "src", "generatedScene.ts");
fs.writeFileSync(out, ts);
console.log(`Wrote scene to ${out}`);
console.log(`Overlays: ${scene.overlays?.length ?? 0}`);
console.log(`B-rolls:  ${scene.brolls?.length ?? 0}`);
console.log(`Words:    ${scene.words?.length ?? 0}`);
