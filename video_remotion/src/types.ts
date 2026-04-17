export interface WordTiming {
  word: string;
  start: number;
  end: number;
}

export interface BRollClip {
  src: string;
  startAtSecond: number;
  durationSeconds: number;
}

export interface ReelProps {
  videoSrc: string;
  words: WordTiming[];
  brolls: BRollClip[];
  title?: string;
  captionStyle?: "bottom" | "center";
}
