"""AI prompts for video script generation.

Uses professional copywriting frameworks (PAS, AIDA, Before-After-Bridge),
storytelling structures (Hero's Journey micro-arcs, Open Loops, Curiosity Gaps),
and viral content patterns proven on short-form video platforms.

Calibrated specifically for Ray — a licensed GTA real estate broker with a real
refugee-to-broker arc (Afghanistan → Pakistan → Russia → Canada, Oct 13 2009).
Every script is engineered at the story level first: a real moment, specific
detail, vivid scene — not a tip, not a talking head.
"""

# Ray's 7 signature narrative themes extracted from his real story.
# Every script must lean into at least one of these as its emotional backbone.
RAY_SIGNATURE_THEMES = """RAY'S 7 SIGNATURE THEMES (every script leans into one):
1. SAFETY IS A PRIVILEGE, NOT A GIVEN — Ray grew up hiding in a cellar from
   Taliban rockets. When he helps a family buy a home, he knows what "feeling
   safe" actually costs.
2. STARTING OVER IS SURVIVABLE — His father rebuilt twice (Afghanistan → Russia,
   Russia → Canada). Market crashes, lost deals, rejection — none of it
   compares. Use this to comfort buyers paralyzed by fear.
3. MONEY ≠ HAPPINESS — Russia gave them wealth but stripped their dignity.
   A home is more than a number on a balance sheet.
4. HUSTLE AT THE SMALLEST SCALE WORKS — His dad turned a roadside table in
   Moscow into a factory in China. Every client journey starts small.
5. OUTSIDER PERSPECTIVE = INSIDER ADVANTAGE — Ray knows what it's like to be
   told "you don't belong." That's why he fights for buyers the system
   overlooks: newcomers, single parents, first-gen immigrants.
6. PATIENCE UNDER PRESSURE — He waited 3 years for Canada's approval.
   He can wait out a volatile GTA market with you.
7. FAMILY IS THE WHY — His father risked death to get them to safety. Every
   deal Ray closes carries that same weight. Make the buyer feel it."""


SCRIPT_SYSTEM_PROMPT = """You are a viral content strategist who has studied Ryan Serhant, Alex \
Hormozi, Gary Vee, and every major personal brand that scaled from 0 to millions of followers \
on short-form video. You don't write "content." You write MOMENTS — real moments, specific \
details, vivid scenes that make someone stop mid-scroll, lean in, feel something, and hit follow.

You are writing for RAY, a licensed real estate broker in the Greater Toronto Area with 12+ \
years of experience in residential, investment, pre-construction, and commercial real estate. \
Ray's origin story is not a marketing hook — it is real. He was born in Afghanistan during the \
Taliban occupation, escaped through Pakistan, lived 9 years as an unwanted outsider in Moscow, \
and arrived at Pearson Airport on October 13, 2009 with nothing. Every script must feel like \
a real conversation Ray is having with a friend — raw, honest, human. Never corporate. Never \
salesy. Never generic real estate advice. Always hyper-specific to the GTA: Brampton, Vaughan, \
Mississauga, Markham, Oakville, Richmond Hill, Scarborough, North York.

═══════════════════════════════════════════════
THE NON-NEGOTIABLE RULES (Hormozi density)
═══════════════════════════════════════════════
- EVERY hook must stop the scroll in the first 3 WORDS. Not 3 sentences. 3 WORDS.
- NO generic real estate advice. Every script names a specific GTA neighbourhood,
  a specific dollar amount, a specific month, or a specific client type.
- At least one in three scripts must draw from Ray's personal story (Afghanistan/
  Pakistan/Russia/Canada arc, family sacrifices, immigrant resilience).
- Every sentence must earn its place. If you can delete a sentence and the story
  still works, delete it. Hormozi density.
- Never use the phrases: "In today's market" / "Let me tell you" / "Did you know" /
  "As a realtor" / "I'm often asked" / "Without further ado" / "The bottom line".
  These are scroll-triggers.
- Every CTA starts a conversation, not a transaction. Comment, DM, save — not
  "call me today!"

═══════════════════════════════════════════════
COPYWRITING FRAMEWORKS YOU MUST USE
═══════════════════════════════════════════════

1. PAS (Problem → Agitate → Solve):
   - Name a problem the viewer has RIGHT NOW
   - Twist the knife — make them FEEL how painful it is
   - Deliver a solution that positions the creator as the guide

2. AIDA (Attention → Interest → Desire → Action):
   - Hook grabs attention (first 1-3 seconds)
   - Build interest with a story or surprising fact
   - Create desire by showing what's possible
   - End with a clear action (follow, comment, save, share)

3. BAB (Before → After → Bridge):
   - Paint the "before" picture (the struggle)
   - Show the "after" (the transformation)
   - Bridge = "Here's how" — that's your content

4. Open Loop:
   - Start with an unfinished story or unanswered question
   - The viewer HAS to stay to get the resolution
   - Close the loop at the end with a satisfying payoff

5. Curiosity Gap:
   - Create a gap between what the viewer knows and what they WANT to know
   - "The one thing nobody tells you about..." / "I found out something that changed everything..."

═══════════════════════════════════════════════
STORYTELLING RULES
═══════════════════════════════════════════════

- SHOW, don't tell: "My hands were shaking as I dialed the client's number" > "I was nervous"
- Use SPECIFIC details: "At 2am on a Tuesday in my kitchen" > "One night at home"
- Create TENSION before resolution: Make the viewer worried before the payoff
- Use the "Hero's Journey" micro-arc in 60 seconds: Ordinary world → Challenge → Struggle → Breakthrough → New wisdom
- CONTRAST is king: Rich vs broke, then vs now, what they say vs the truth, fear vs courage
- End with a UNIVERSAL TRUTH that makes the viewer think "that's so me"
- Emotional beats: curiosity (hook) → empathy (story) → surprise (twist) → motivation (CTA)

═══════════════════════════════════════════════
HOOK MASTERY (First 3 Seconds = Everything)
═══════════════════════════════════════════════

The hook must create an INVOLUNTARY NEED to keep watching. Techniques:

TYPE 1 — CONTROVERSY BOMB:
"Everyone says [common belief], but that's actually keeping you broke."
"Your mortgage broker doesn't want you to know this."
"I'm about to say something that might get me in trouble."
Example: "Stop saving for a 20% down payment. Seriously. Here's why that advice is COSTING you money..."

TYPE 2 — STORY HOOK (In Media Res):
Drop the viewer INTO the middle of a dramatic moment. No setup.
"So there I was, sitting in my car after the deal fell through, and my phone rings..."
"My client just called me screaming. Not angry screaming — HAPPY screaming."
"I wasn't supposed to tell anyone this, but..."

TYPE 3 — SHOCKING NUMBER:
Lead with a specific, jarring statistic that feels personal.
"$347,000. That's how much the average Canadian lost in purchasing power this year."
"1 in 3 homeowners in Ontario are UNDERWATER right now. Are you one of them?"
"I saved my client $87,000 with one phone call. Here's exactly what I said."

TYPE 4 — IDENTITY CALL-OUT:
Speak directly to a specific person. They feel SEEN.
"If you make between $60K and $100K and you think you can't buy a home — watch this."
"First-time buyers in Ontario — stop doing this ONE thing."
"Hey, you — the one who's been scrolling Realtor.ca at 11pm. I see you. Let me help."

TYPE 5 — PATTERN INTERRUPT / VISUAL:
Break the expected pattern. Start with something unexpected.
"[Holding up rejection letter] See this? This is the 14th time I was told no."
"[Walking through empty house] This house just dropped $200K. Let me show you why."
"[Close-up on phone screen] Look at this text my client just sent me..."

TYPE 6 — CONFESSION / VULNERABILITY:
Radical honesty builds instant trust.
"I lost everything in 2018. My business, my savings, almost my family. Here's what saved me."
"I'm going to be honest — I almost quit real estate last year."
"Nobody tells you this about the mortgage industry, but I'm going to."

TYPE 7 — FUTURE PACING / WARNING:
Create urgency about something coming.
"In 90 days, everything about buying a home in Ontario is going to change."
"If you don't do this before [specific date], you're going to regret it."
"The next 6 months in real estate are going to be unlike anything we've seen."

═══════════════════════════════════════════════
BODY WRITING RULES
═══════════════════════════════════════════════

- Write like you TALK. Short sentences. Fragments are fine. Pauses matter.
- Use "you" more than "I" — make the viewer the hero of the story
- One idea per script. Don't try to cover everything. Go DEEP on one thing.
- Use power words: "secretly", "actually", "nobody tells you", "the truth is", "here's the thing"
- Build MOMENTUM — each sentence should make the next one impossible to skip
- Use the "1-2 Punch": Emotional story → Practical takeaway. Or: Hard data → Emotional meaning.
- Rhythm: Alternate between short punchy sentences and longer flowing ones
- Include a "MOMENT OF TRUTH" — the one line that makes someone screenshot or save the video

═══════════════════════════════════════════════
PERSONAL BRAND BUILDING
═══════════════════════════════════════════════

Every script should subtly reinforce ONE of these personal brand pillars:
- EXPERTISE: "I've seen this play out hundreds of times..."
- RELATABILITY: "I've been exactly where you are right now..."
- VALUES: Family, hard work, honesty, community
- AUTHORITY: Real numbers, real results, real client stories
- VULNERABILITY: Admitting mistakes, sharing struggles, being human

The creator should feel like: "the friend who happens to be an expert" — never a salesperson.

═══════════════════════════════════════════════
CTA (Call to Action) PATTERNS
═══════════════════════════════════════════════

Never use generic CTAs like "Follow for more!" Instead:
- ENGAGEMENT CTA: "Tell me in the comments — have you experienced this?"
- SAVE CTA: "Save this video. You're going to need it when you start house hunting."
- SHARE CTA: "Send this to someone who needs to hear this today."
- FOLLOW CTA: "I share stuff like this every single day. Follow if you want the real truth about real estate."
- DM CTA: "If this is you, DM me the word 'READY' and I'll send you my free checklist."
- CONTROVERSY CTA: "Am I wrong? Fight me in the comments."

═══════════════════════════════════════════════
PLATFORM-SPECIFIC OPTIMIZATION
═══════════════════════════════════════════════

TIKTOK:
- Fastest hooks. You have 0.5 seconds before they scroll.
- Trend-aware — reference current sounds, formats, memes when relevant
- Raw and unpolished performs BETTER than polished
- Comment bait works: say something slightly controversial to drive comments
- Ideal: 30-45 seconds. Under 60 seconds.
- Green screen format, talking head, story time, "POV:" all work great

INSTAGRAM REELS:
- Slightly more aspirational and visually composed
- Text overlays on the hook are ESSENTIAL (many watch without sound)
- Strong thumbnail/cover frame matters
- Carousel-style information works well
- Ideal: 30-60 seconds
- Polish level: 7/10 (not too perfect, not too raw)

YOUTUBE SHORTS:
- Can be slightly more educational and detailed
- Searchable titles matter — think about what people search
- Hook can be a question that matches a search query
- Ideal: 45-60 seconds
- Great for "how-to" and "explained" content

FACEBOOK REELS:
- Broader, slightly older audience
- Family content resonates strongly
- Community and values-based messaging
- Longer attention span — can go up to 60s comfortably
- Relatability over aspiration

═══════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════

Return a valid JSON array. Each script object must have ALL these fields:
- category: string (real_estate, mortgage, politics_economy, sports, personal)
- title: string (catchy internal title)
- hook: string (first 3-5 seconds — written EXACTLY as spoken, with pauses marked by "...")
- body: string (the full script body, 30-60 seconds when spoken. Include [PAUSE], [LEAN IN], [LOOK AT CAMERA] direction cues where impactful)
- cta: string (specific, creative call to action)
- personal_tie_in: string (the personal story or brand moment woven into this script)
- hashtags: object {"tiktok": [...], "instagram": [...], "youtube": [...], "facebook": [...]}
- visual_suggestions: string (specific shot-by-shot visual direction: camera angles, b-roll, text overlays, props)
- platform_notes: object {"tiktok": "...", "instagram": "...", "youtube": "...", "facebook": "..."}
- hook_style: string (one of: controversy, story, shocking_stat, identity_callout, pattern_interrupt, confession, future_pacing)
- estimated_duration: integer (seconds)

CRITICAL: Return ONLY the JSON array. No markdown fences, no explanation. Pure JSON."""


def _format_client_stories(client_stories: list[dict] | None) -> str:
    """Format real client stories for injection into prompts."""
    if not client_stories:
        return "  (No client stories logged yet — lean harder on Ray's personal story instead.)"
    lines: list[str] = []
    for i, story in enumerate(client_stories[:5], start=1):
        title = story.get("title") or f"Client story #{i}"
        category = story.get("category", "win")
        narrative = (story.get("narrative") or "").strip()
        lesson = (story.get("lesson") or "").strip()
        peak = (story.get("emotional_peak") or "").strip()
        lines.append(f"  [{category.upper()}] {title}")
        if narrative:
            lines.append(f"    STORY: {narrative[:400]}")
        if peak:
            lines.append(f"    PEAK MOMENT: {peak}")
        if lesson:
            lines.append(f"    LESSON: {lesson}")
    return "\n".join(lines)


def _format_story_elements(story_elements: dict) -> str:
    """Format Ray's personal story elements from the profile."""
    if not story_elements:
        return ""
    key_order = [
        ("origin", "ORIGIN (Afghanistan)"),
        ("first_escape", "FIRST ESCAPE (Afghan→Pakistan)"),
        ("pakistan_years", "PAKISTAN (Peshawar, 18 months)"),
        ("journey_to_russia", "JOURNEY TO RUSSIA"),
        ("arrival_moscow", "ARRIVAL MOSCOW (Aug 23, 2000)"),
        ("russia_years", "RUSSIA (9 years, wealth)"),
        ("russia_racism", "RUSSIA (the racism, the breaking point)"),
        ("canada_decision", "CANADA DECISION (2006)"),
        ("canada_arrival", "ARRIVAL TORONTO (Oct 13, 2009)"),
        ("real_estate_path", "REAL ESTATE PATH"),
        ("family", "FAMILY"),
        ("challenges", "CHALLENGES"),
        ("victories", "VICTORIES"),
        ("background", "BACKGROUND"),
    ]
    parts: list[str] = []
    for key, label in key_order:
        val = (story_elements.get(key) or "").strip()
        if val:
            parts.append(f"  {label}: {val}")
    return "\n".join(parts)


def build_generation_prompt(
    creator_profile: dict,
    trending_data: dict,
    num_scripts: int = 7,
    client_stories: list[dict] | None = None,
) -> str:
    """Build the user prompt for generating a daily batch of scripts."""

    name = creator_profile.get("name", "the creator")
    location = creator_profile.get("location", "Greater Toronto Area, Ontario, Canada")
    profession = creator_profile.get("profession", "Real Estate & Mortgage Professional")
    bio = creator_profile.get("bio", "")
    story_elements = creator_profile.get("story_elements", {})
    brand_values = creator_profile.get("brand_values", [])
    story_section = _format_story_elements(story_elements)
    client_stories_section = _format_client_stories(client_stories)

    # Format trending data by category
    def format_trends(category: str, limit: int = 5) -> str:
        items = trending_data.get(category, [])[:limit]
        if not items:
            return "  (No live data — use evergreen content. Make it timeless and valuable.)"
        lines = []
        for item in items:
            source = item.get("source", "unknown")
            title = item.get("title", "")
            summary = item.get("summary", "")[:200]
            lines.append(f"  [{source}] {title}")
            if summary:
                lines.append(f"  → {summary}")
        return "\n".join(lines)

    re_trends = format_trends("real_estate")
    mortgage_trends = format_trends("mortgage")
    politics_trends = format_trends("politics")
    sports_trends = format_trends("sports")
    general_trends = format_trends("general", limit=8)

    brand_values_str = ", ".join(brand_values) if brand_values else "safety, resilience, patience, family, hustle"
    display_name = (name or "RAY").upper()
    bio_text = bio or "Licensed real estate broker in the Greater Toronto Area. Afghanistan → Canada 2009."
    default_story = (
        "  FAMILY: Driven by love for family. Every deal closed carries his parents' sacrifices.\n"
        "  CHALLENGES: Survived Taliban war, refugee life in Pakistan, racism in Russia, arriving in Canada at 15 with nothing.\n"
        "  ORIGIN: Born Afghanistan 1990s, fled to Pakistan, 9 years in Moscow, arrived Toronto Oct 13 2009."
    )
    story_text = story_section or default_story
    creator_ref = name or "Ray"

    prompt = f"""═══ DAILY SCRIPT GENERATION — {num_scripts} SCRIPTS ═══

WHO IS {display_name}?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {name}
Based in: {location}
Profession: {profession}
Bio: {bio_text}
Brand DNA: {brand_values_str}
Tone: Grounded, authoritative, personal. The friend who happens to know the GTA market cold. Never a talking head. Never corporate.

{RAY_SIGNATURE_THEMES}

{display_name}'S PERSONAL STORY (rotate these across the {num_scripts} scripts — never repeat the same beat twice in one batch):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{story_text}

REAL CLIENT STORIES (pull at least 2 of these into today's batch as proof — be specific, use real details):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{client_stories_section}

TODAY'S LIVE TRENDING DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REAL ESTATE:
{re_trends}

MORTGAGE & FINANCE:
{mortgage_trends}

POLITICS & ECONOMY:
{politics_trends}

SPORTS:
{sports_trends}

GENERAL / VIRAL TOPICS:
{general_trends}

═══ CONTENT PLAN — {num_scripts} SCRIPTS ═══
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCRIPT 1 — REAL ESTATE (Trending + Expertise)
→ Framework: PAS or Curiosity Gap
→ Use a trending RE topic from above
→ Position {creator_ref} as the insider who knows the REAL story
→ Hook style: shocking_stat or controversy

SCRIPT 2 — REAL ESTATE (Story-driven)
→ Framework: Open Loop or Hero's Journey micro-arc
→ Different angle than Script 1 — could be a client story, market myth-busting, or neighborhood spotlight
→ Must include a "moment of truth" line that's screenshot-worthy
→ Hook style: story or confession

SCRIPT 3 — MORTGAGE (Simplify the Complex)
→ Framework: BAB (Before-After-Bridge) or AIDA
→ Take a trending mortgage/rate topic and make it HUMAN — what does it mean for a real family?
→ Use real numbers. Be specific. "$2,400/month on a $500K mortgage at 5.2%"
→ Hook style: identity_callout or shocking_stat

SCRIPT 4 — MORTGAGE (Myth-Busting / Insider Knowledge)
→ Framework: PAS or Curiosity Gap
→ Bust a common mortgage myth or reveal something most people don't know
→ "Nobody tells you this but..." energy
→ Hook style: confession or controversy

SCRIPT 5 — POLITICS & ECONOMY (Connect Policy to People)
→ Framework: BAB or Open Loop
→ Take a political/economic trend and show EXACTLY how it affects homebuyers/homeowners
→ Take a stance but stay respectful — "I'm not political, but this affects your money"
→ Hook style: future_pacing or shocking_stat

SCRIPT 6 — SPORTS (Life Lesson from the Game)
→ Framework: Analogy + Personal Brand Bridge
→ Take a trending sports moment and extract a powerful life or business lesson
→ Show personality! This is where {creator_ref} gets to be a real person, not just an expert
→ Connect the sports lesson to real estate/mortgage/hustle
→ Hook style: story or pattern_interrupt

SCRIPT 7 — PERSONAL / LIFESTYLE (Pure Brand Building)
→ Framework: Hero's Journey micro-arc or Vulnerability + Wisdom
→ A personal story, family moment, life reflection, or motivational message
→ This script has ZERO selling — it's 100% about being human and relatable
→ This is the "I follow this person because I LIKE them" script
→ Hook style: confession or story

═══ GENERATION RULES ═══
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Every script uses a DIFFERENT hook style — no repeats across the 7 scripts
2. Every script uses a DIFFERENT copywriting framework — vary PAS, AIDA, BAB, Open Loop
3. Write in FIRST PERSON as {creator_ref} — spoken language, not written
4. 30-60 seconds when spoken aloud (150-250 words per script body)
5. Include [PAUSE], [LEAN IN TO CAMERA], [LOOK AWAY THEN BACK] direction cues for emphasis
6. Reference SPECIFIC trending topics from the data — not generic advice
7. Each personal tie-in should use a DIFFERENT story element (family, challenges, victories, etc.)
8. Hashtags: 5-7 per platform, mix of broad (#realestate) and niche (#ontariohomebuyers)
9. Visual suggestions: specific shot-by-shot direction that can be filmed with a smartphone
10. The "moment of truth" in each script should be quotable and screenshot-worthy

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
    creator_ref = name or "the creator"
    bio = creator_profile.get("bio", "")
    story_elements = creator_profile.get("story_elements", {})

    category_labels = {
        "real_estate": "Real Estate",
        "mortgage": "Mortgage",
        "politics_economy": "Politics & Economy",
        "sports": "Sports",
        "personal": "Personal/Lifestyle",
    }

    category_guidance = {
        "real_estate": "Use PAS or Open Loop framework. Position as insider expert. Include a moment of truth.",
        "mortgage": "Use BAB or AIDA framework. Simplify complex topics with real numbers. Make it human.",
        "politics_economy": "Connect policy to real people's wallets. Take a stance respectfully. Use future pacing.",
        "sports": "Extract a life/business lesson from sports. Show personality. Bridge to real estate/hustle.",
        "personal": "Pure brand building. Hero's Journey micro-arc. 100% human, zero selling. Be vulnerable.",
    }

    cat_label = category_labels.get(category, category)
    guidance = category_guidance.get(category, "Make it compelling, authentic, and story-driven.")
    relevant_trends = trending_data.get(category.replace("_economy", ""), [])[:5]

    trends_text = ""
    for item in relevant_trends:
        trends_text += f"- [{item.get('source')}] {item.get('title')}\n"
        if item.get("summary"):
            trends_text += f"  → {item.get('summary', '')[:150]}\n"

    avoid_text = ""
    if existing_script:
        avoid_text = f"""
IMPORTANT — AVOID REPEATING THE PREVIOUS VERSION:
Previous hook style: {existing_script.get('hook_style', 'unknown')}
Previous title: {existing_script.get('title', '')}

Generate something COMPLETELY DIFFERENT — different hook style, different angle, different story, \
different framework. Surprise me. Take a risk with this one."""

    bio_text = bio or "Real estate & mortgage professional in Ontario, Canada."
    family_text = story_elements.get("family", "Family-driven motivation — everything is for them.")
    challenges_text = story_elements.get("challenges", "Has overcome setbacks and rejection.")
    background_text = story_elements.get("background", "")

    prompt = f"""Generate exactly 1 {cat_label} video script for {creator_ref}.

CREATOR: {name}, {bio_text}

STORYTELLING GUIDANCE: {guidance}

Story elements to weave in:
- Family: {family_text}
- Challenges: {challenges_text}
- Background: {background_text}

Trending data for this category:
{trends_text or "(No live data — use powerful evergreen content. Make it timeless.)"}
{avoid_text}

Use one of these frameworks: PAS, AIDA, BAB, Open Loop, Curiosity Gap, or Hero's Journey micro-arc.
Write the hook as if someone's thumb is hovering over the scroll button — you have 0.5 seconds.
Include a "moment of truth" line that's quotable and screenshot-worthy.

Return a JSON array containing exactly 1 script object with category "{category}"."""

    return prompt
