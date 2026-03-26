import Anthropic from "@anthropic-ai/sdk";
import { Platform, Tone, SourceType, PlatformOutput } from "@/types";
import { getPlatformConfig } from "./platforms";
import { buildPrompt } from "./prompts";

const client = new Anthropic();

export async function repurposeContent(
  content: string,
  sourceType: SourceType,
  platforms: Platform[],
  tone: Tone
): Promise<PlatformOutput[]> {
  const { system, user } = buildPrompt(content, sourceType, platforms, tone);

  const message = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 4096,
    system,
    messages: [{ role: "user", content: user }],
  });

  const text =
    message.content[0].type === "text" ? message.content[0].text : "";

  // Parse JSON — strip markdown fences if Claude adds them
  const cleaned = text.replace(/^```json?\s*\n?/, "").replace(/\n?```\s*$/, "");
  const parsed = JSON.parse(cleaned);

  const outputs: PlatformOutput[] = platforms.map((platform) => {
    const platformContent = parsed[platform] || "";
    const config = getPlatformConfig(platform);
    const charCount = platformContent.length;
    const isOverLimit = config?.characterLimit
      ? charCount > config.characterLimit
      : false;

    return {
      platform,
      content: platformContent,
      characterCount: charCount,
      isOverLimit,
    };
  });

  return outputs;
}
