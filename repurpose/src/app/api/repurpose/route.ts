import { NextResponse } from "next/server";
import { repurposeContent } from "@/lib/claude";
import { RepurposeRequest, Platform, Tone, SourceType } from "@/types";

const VALID_PLATFORMS: Platform[] = [
  "twitter",
  "linkedin",
  "instagram",
  "email",
  "video-script",
];
const VALID_TONES: Tone[] = ["professional", "casual", "witty"];
const VALID_SOURCES: SourceType[] = [
  "blog-post",
  "article",
  "video-transcript",
  "other",
];

export async function POST(request: Request) {
  try {
    const body: RepurposeRequest = await request.json();

    if (!body.content || body.content.trim().length < 50) {
      return NextResponse.json(
        { error: "Content must be at least 50 characters." },
        { status: 400 }
      );
    }

    if (
      !body.platforms ||
      !body.platforms.length ||
      !body.platforms.every((p) => VALID_PLATFORMS.includes(p))
    ) {
      return NextResponse.json(
        { error: "Select at least one valid platform." },
        { status: 400 }
      );
    }

    if (!VALID_TONES.includes(body.tone)) {
      return NextResponse.json({ error: "Invalid tone." }, { status: 400 });
    }

    if (!VALID_SOURCES.includes(body.sourceType)) {
      return NextResponse.json(
        { error: "Invalid source type." },
        { status: 400 }
      );
    }

    const outputs = await repurposeContent(
      body.content,
      body.sourceType,
      body.platforms,
      body.tone
    );

    return NextResponse.json({ outputs });
  } catch (error) {
    console.error("Repurpose API error:", error);
    const message =
      error instanceof Error ? error.message : "Something went wrong.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
