import type { WordTiming, BRollClip } from "./types";

/**
 * Sample word timings — replace with output from video_pipeline/transcribe.py
 * (the .words.json file). Times are in seconds.
 */
export const sampleWords: WordTiming[] = [
  { word: "The", start: 0.5, end: 0.6 },
  { word: "key", start: 0.6, end: 0.8 },
  { word: "to", start: 0.8, end: 0.9 },
  { word: "success", start: 0.9, end: 1.3 },
  { word: "is", start: 1.5, end: 1.6 },
  { word: "staying", start: 1.6, end: 1.9 },
  { word: "consistent", start: 1.9, end: 2.5 },
  { word: "every", start: 2.5, end: 2.7 },
  { word: "single", start: 2.8, end: 3.1 },
  { word: "day", start: 3.1, end: 3.5 },
  { word: "no", start: 3.8, end: 3.9 },
  { word: "matter", start: 3.9, end: 4.2 },
  { word: "what", start: 4.2, end: 4.5 },
  { word: "happens", start: 4.5, end: 5.0 },
  { word: "you", start: 5.2, end: 5.3 },
  { word: "just", start: 5.3, end: 5.5 },
  { word: "keep", start: 5.5, end: 5.7 },
  { word: "going", start: 5.7, end: 6.1 },
];

/**
 * Sample B-roll clips — point these at actual video/image files.
 * Place files in the public/ folder and reference as staticFile("name.mp4").
 */
export const sampleBRolls: BRollClip[] = [
  // { src: staticFile("broll-city.mp4"), startAtSecond: 2, durationSeconds: 3 },
  // { src: staticFile("broll-gym.mp4"), startAtSecond: 5, durationSeconds: 2 },
];
