export type Platform = "twitter" | "linkedin" | "instagram" | "email" | "video-script";
export type Tone = "professional" | "casual" | "witty";
export type SourceType = "blog-post" | "article" | "video-transcript" | "other";

export interface PlatformConfig {
  id: Platform;
  name: string;
  icon: string;
  characterLimit: number | null;
  description: string;
}

export interface RepurposeRequest {
  content: string;
  sourceType: SourceType;
  platforms: Platform[];
  tone: Tone;
}

export interface PlatformOutput {
  platform: Platform;
  content: string;
  characterCount: number;
  isOverLimit: boolean;
}

export interface RepurposeResponse {
  outputs: PlatformOutput[];
}

export interface HistoryEntry {
  id: string;
  timestamp: number;
  sourceSnippet: string;
  sourceType: SourceType;
  tone: Tone;
  platforms: Platform[];
  outputs: PlatformOutput[];
}
