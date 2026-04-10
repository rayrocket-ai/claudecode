"""AI prompts for video script generation."""

SCRIPT_SYSTEM_PROMPT = """You are a world-class short-form video scriptwriter specializing in personal \
brand content for real estate and mortgage professionals. You create scripts that feel authentic, \
not scripted — like the creator is talking to a friend over coffee.

CORE PRINCIPLES:
- Every script starts with a PATTERN INTERRUPT hook (the first 3 seconds decide if someone stays or scrolls)
- Stories > Statistics (but use shocking stats to support stories)
- Vulnerability builds trust — show the human side, the struggles, the real moments
- Each script should feel like a different "episode" — varied energy, varied hooks, varied pacing
- The creator should NEVER sound like they're selling — they're sharing, teaching, helping
- Weave personal stories NATURALLY — don't force them. A mortgage tip can connect to "when I bought my first home..."
- Write in spoken language, not written language. Use contractions, pauses (...), emphasis (ALL CAPS for key words)
- Include specific numbers, dates, and examples — vague advice doesn't go viral
- Every script should make the viewer feel something: surprise, motivation, relatability, urgency, or hope

PLATFORM AWARENESS:
- TikTok: Fast-paced, trend-aware, younger audience, under 60 seconds ideal
- Instagram Reels: Slightly more polished, aspirational, strong visual hooks
- YouTube Shorts: Can be more educational, slightly longer (up to 60s), searchable
- Facebook Reels: Broader audience, family-friendly, relatable content works best

HOOK STYLES (rotate these — never use the same style twice in a batch):
1. "Stop scrolling" question: "Did you know 73% of Canadians can't afford a home in their own city?"
2. Controversial take: "Everyone says buy a house ASAP, but here's why that's terrible advice in 2024..."
3. Shocking stat: "The average mortgage payment went up $800/month this year. Let that sink in."
4. Story opener: "Last week, my client called me crying. Here's what happened..."
5. Pattern interrupt: Start mid-action, unexpected visual, breaking the fourth wall
6. Direct challenge: "If you're renting right now and think you can't buy — you NEED to hear this."
7. Confession: "I've been in real estate for years and I STILL made this mistake last month..."

OUTPUT FORMAT:
You must respond with a valid JSON array containing exactly the number of script objects requested.
Each script object must have these fields:
- category: string (real_estate, mortgage, politics_economy, sports, personal)
- title: string (short, catchy title for internal reference)
- hook: string (the first 3-5 seconds — the most critical part)
- body: string (the main content, 30-60 seconds when spoken aloud)
- cta: string (call to action — what should the viewer do next?)
- personal_tie_in: string (how this connects to the creator's personal story)
- hashtags: object with keys "tiktok", "instagram", "youtube", "facebook" — each an array of strings
- visual_suggestions: string (what to show on screen, b-roll ideas, text overlays)
- platform_notes: object with keys "tiktok", "instagram", "youtube", "facebook" — platform-specific tips
- hook_style: string (which hook style from the list above)
- estimated_duration: integer (seconds, typically 30-60)

IMPORTANT: Return ONLY the JSON array. No markdown, no explanation, no code fences. Just pure JSON."""


def build_generation_prompt(
    creator_profile: dict,
    trending_data: dict,
    num_scripts: int = 7,
) -> str:
    """Build the user prompt for generating a daily batch of scripts."""

    name = creator_profile.get("name", "the creator")
    location = creator_profile.get("location", "Ontario, Canada")
    profession = creator_profile.get("profession", "Real Estate & Mortgage Professional")
    bio = creator_profile.get("bio", "")
    story_elements = creator_profile.get("story_elements", {})
    brand_values = creator_profile.get("brand_values", [])

    # Format story elements
    story_section = ""
    if story_elements:
        parts = []
        if story_elements.get("family"):
            parts.append(f"- Family: {story_elements['family']}")
        if story_elements.get("challenges"):
            parts.append(f"- Challenges overcome: {story_elements['challenges']}")
        if story_elements.get("victories"):
            parts.append(f"- Victories & wins: {story_elements['victories']}")
        if story_elements.get("travels"):
            parts.append(f"- Travel experiences: {story_elements['travels']}")
        if story_elements.get("background"):
            parts.append(f"- Background story: {story_elements['background']}")
        if parts:
            story_section = "\n".join(parts)

    # Format trending data by category
    def format_trends(category: str, limit: int = 5) -> str:
        items = trending_data.get(category, [])[:limit]
        if not items:
            return "  No trending data available — use evergreen content ideas."
        lines = []
        for item in items:
            source = item.get("source", "unknown")
            title = item.get("title", "")
            summary = item.get("summary", "")[:150]
            lines.append(f"  - [{source}] {title}")
            if summary:
                lines.append(f"    {summary}")
        return "\n".join(lines)

    re_trends = format_trends("real_estate")
    mortgage_trends = format_trends("mortgage")
    politics_trends = format_trends("politics")
    sports_trends = format_trends("sports")
    general_trends = format_trends("general", limit=8)

    brand_values_str = ", ".join(brand_values) if brand_values else "authenticity, education, family, hard work"

    prompt = f"""Generate {num_scripts} short-form video scripts for today.

CREATOR PROFILE:
- Name: {name}
- Location: {location}
- Profession: {profession}
- Bio: {bio or "A passionate real estate and mortgage professional who helps families achieve their dream of home ownership."}
- Brand values: {brand_values_str}
- Tone: Motivational & Educational — "let me show you" energy, inspiring but grounded

PERSONAL STORY ELEMENTS (weave these in naturally — don't force every one into every script):
{story_section or "- Family-driven motivation: works hard every day for family"}

TODAY'S TRENDING DATA:

Real Estate:
{re_trends}

Mortgage:
{mortgage_trends}

Politics & Economy:
{politics_trends}

Sports:
{sports_trends}

General Trending:
{general_trends}

REQUIRED CONTENT MIX ({num_scripts} scripts total):
1. Real Estate Script #1 — Connect to a trending real estate topic. Tips, market insights, buyer/seller advice.
2. Real Estate Script #2 — Different angle from #1. Could be a story, myth-busting, or local market update.
3. Mortgage Script #1 — Connect to trending mortgage/rate data. Make complex topics simple and actionable.
4. Mortgage Script #2 — Different angle. First-time buyer tips, rate strategy, qualification myths, etc.
5. Politics/Economy Script — How a current political or economic event affects housing or personal finance. Take a take but stay respectful.
6. Sports Script — Take a trending sports moment and extract a life or business lesson. Show personality.
7. Personal/Lifestyle Script — A personal story, family moment, travel memory, or motivational message. Pure relatability and brand building.

RULES:
- Use a DIFFERENT hook style for each script (never repeat in the same batch)
- Each script should be 30-60 seconds when spoken aloud
- Write in first person as {name or "the creator"}
- Reference specific trending topics from the data above when relevant
- Make the personal tie-ins feel natural, not forced
- Include Canada/Ontario-specific references where appropriate
- Hashtags should be platform-specific and include a mix of broad + niche tags
- Visual suggestions should be practical and achievable with a smartphone

Generate all {num_scripts} scripts now as a JSON array."""

    return prompt


def build_regenerate_prompt(
    creator_profile: dict,
    trending_data: dict,
    category: str,
    existing_script: dict | None = None,
) -> str:
    """Build a prompt to regenerate a single script."""

    name = creator_profile.get("name", "the creator")
    bio = creator_profile.get("bio", "")
    story_elements = creator_profile.get("story_elements", {})

    category_labels = {
        "real_estate": "Real Estate",
        "mortgage": "Mortgage",
        "politics_economy": "Politics & Economy",
        "sports": "Sports",
        "personal": "Personal/Lifestyle",
    }

    cat_label = category_labels.get(category, category)
    relevant_trends = trending_data.get(category.replace("_economy", ""), [])[:5]

    trends_text = ""
    for item in relevant_trends:
        trends_text += f"- [{item.get('source')}] {item.get('title')}\n"

    avoid_text = ""
    if existing_script:
        avoid_text = f"""
The previous version of this script used:
- Hook style: {existing_script.get('hook_style', 'unknown')}
- Title: {existing_script.get('title', '')}

Please generate a COMPLETELY DIFFERENT script — different hook style, different angle, different story."""

    prompt = f"""Generate exactly 1 {cat_label} video script for {name or 'the creator'}.

Bio: {bio or 'Real estate & mortgage professional in Ontario, Canada.'}

Story elements to potentially weave in:
- Family: {story_elements.get('family', 'Family-driven motivation')}
- Background: {story_elements.get('background', '')}

Trending data for this category:
{trends_text or 'Use evergreen content ideas for this category.'}
{avoid_text}

Return a JSON array containing exactly 1 script object with category "{category}"."""

    return prompt
