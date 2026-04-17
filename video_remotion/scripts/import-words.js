#!/usr/bin/env node
/**
 * Converts video_pipeline's .words.json into a TypeScript file
 * that Remotion can import directly.
 *
 * Usage:
 *   node scripts/import-words.js ../video_pipeline/output/myvid/cleaned.words.json
 *
 * Writes: src/generatedWords.ts
 */
const fs = require("fs");
const path = require("path");

const input = process.argv[2];
if (!input) {
  console.error("Usage: node import-words.js <path-to-words.json>");
  process.exit(1);
}

const raw = JSON.parse(fs.readFileSync(input, "utf8"));
const words = raw.map((w) => ({
  word: w.word.trim(),
  start: Math.round(w.start * 1000) / 1000,
  end: Math.round(w.end * 1000) / 1000,
}));

const ts = `import type { WordTiming } from "./types";

export const words: WordTiming[] = ${JSON.stringify(words, null, 2)};
`;

const outPath = path.join(__dirname, "..", "src", "generatedWords.ts");
fs.writeFileSync(outPath, ts);
console.log(`Wrote ${words.length} words to ${outPath}`);
