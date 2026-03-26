import { PlatformConfig } from "@/types";

export const PLATFORMS: PlatformConfig[] = [
  {
    id: "twitter",
    name: "Twitter / X",
    icon: "𝕏",
    characterLimit: 280,
    description: "Thread of 3-7 tweets, each under 280 chars",
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    icon: "in",
    characterLimit: 3000,
    description: "Professional post with hooks and hashtags",
  },
  {
    id: "instagram",
    name: "Instagram",
    icon: "📷",
    characterLimit: 2200,
    description: "Engaging caption with hashtags",
  },
  {
    id: "email",
    name: "Email Newsletter",
    icon: "✉️",
    characterLimit: null,
    description: "Subject line + body with sections",
  },
  {
    id: "video-script",
    name: "Video Script",
    icon: "🎬",
    characterLimit: null,
    description: "30-60 second script with hooks and CTA",
  },
];

export function getPlatformConfig(id: string): PlatformConfig | undefined {
  return PLATFORMS.find((p) => p.id === id);
}
