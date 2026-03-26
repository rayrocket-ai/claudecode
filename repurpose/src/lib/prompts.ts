import { Platform, Tone, SourceType } from "@/types";

const TONE_INSTRUCTIONS: Record<Tone, string> = {
  professional:
    "Use a polished, authoritative tone. Be clear, confident, and credible. Avoid slang or overly casual language.",
  casual:
    "Use a friendly, conversational tone. Write like you're talking to a smart friend. Keep it approachable and relatable.",
  witty:
    "Use a clever, engaging tone with personality. Include wordplay, surprising angles, or humor where appropriate. Be memorable.",
};

const PLATFORM_INSTRUCTIONS: Record<Platform, string> = {
  twitter: `Generate a Twitter/X thread of 3-7 tweets.
Rules:
- Each tweet MUST be under 280 characters
- First tweet is the hook — make it irresistible
- Use line breaks within tweets for readability
- Include a transition between tweets (numbered or flowing narrative)
- Final tweet should have a clear CTA (follow, share, bookmark)
- NO hashtags in the thread (Twitter best practice)
- Separate each tweet with "---" on its own line
- Return ONLY the tweet texts separated by "---"`,

  linkedin: `Generate a LinkedIn post.
Rules:
- Start with a strong hook in the first 2 lines (this shows before "see more")
- Use short paragraphs (1-2 sentences each) with line breaks between them
- Include a personal angle or insight
- End with a question or CTA to drive engagement
- Add 3-5 relevant hashtags at the end
- Keep under 3000 characters total
- Use line breaks generously — dense text gets skipped`,

  instagram: `Generate an Instagram caption.
Rules:
- Opening line must hook — it's all people see before "more"
- Break the body into short, scannable sections
- Use emojis sparingly but strategically (2-4 per caption)
- End with a clear CTA (save, share, comment, link in bio)
- Add a block of 20-25 relevant hashtags after a line break
- Keep the caption under 2200 characters`,

  email: `Generate an email newsletter.
Rules:
- Start with "Subject: " followed by a compelling subject line (under 60 chars)
- Then "Preview: " followed by preview text (under 90 chars)
- Then a blank line, followed by the email body
- Open with a personal, engaging intro (2-3 sentences)
- Break content into clear sections with bold headers using **Header**
- Include 2-3 key takeaways or insights
- End with a single, clear CTA
- Keep the tone warm and direct — like writing to a subscriber you respect`,

  "video-script": `Generate a short-form video script (30-60 seconds).
Rules:
- Format with clear sections: [HOOK - first 3 seconds], [BODY], [CTA]
- The hook must stop the scroll — use a bold claim, question, or surprising stat
- Include [visual/action cues] in brackets throughout
- Keep sentences short and punchy — written for speaking, not reading
- End with a memorable CTA
- Target 80-150 words total (speaking pace: ~150 words/minute)
- Include approximate timestamps like [0:00], [0:05], etc.`,
};

export function buildPrompt(
  content: string,
  sourceType: SourceType,
  platforms: Platform[],
  tone: Tone
): { system: string; user: string } {
  const platformInstructions = platforms
    .map(
      (p) => `### ${p.toUpperCase()}
${PLATFORM_INSTRUCTIONS[p]}`
    )
    .join("\n\n");

  const system = `You are an expert content repurposing strategist. You take source content and transform it into platform-optimized formats that maximize engagement.

Your output quality is exceptional — each platform's content should feel native, not like a lazy copy-paste adaptation.

CRITICAL: You MUST return valid JSON and nothing else. No markdown code fences, no explanation, no preamble. Just the JSON object.

The JSON must have this exact structure:
{
${platforms.map((p) => `  "${p}": "the content for this platform"`).join(",\n")}
}

Use \\n for newlines within the content strings. Ensure the JSON is valid.`;

  const user = `## Source Content
Type: ${sourceType}

${content.slice(0, 15000)}

## Instructions

Repurpose this content for the following platforms.

**Tone:** ${tone} — ${TONE_INSTRUCTIONS[tone]}

${platformInstructions}

Return ONLY the JSON object with platform keys and content values. No other text.`;

  return { system, user };
}
