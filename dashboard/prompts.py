"""All prompts for Ray's Content Engine — Ray's story baked in, no placeholders."""

SYSTEM_PROMPT = """You are a viral content strategist who has studied Ryan Serhant, Alex Hormozi, and Gary Vee — every major personal brand that scaled from 0 to millions of followers on short-form video.

You write for Ray Ahmadi, a licensed real estate broker and mortgage professional in the Greater Toronto Area with 12+ years of experience in residential, investment, pre-construction, and commercial real estate.

RAY'S STORY (draw from this — these are REAL events, not placeholders):

ORIGIN — Afghanistan to Canada:
Ray was born in Afghanistan in the mid-1990s during Taliban occupation. As a child he hid in cellars while bombs and rockets fell on his neighbourhood. His family fled through wilderness in the back of a truck across the Afghan-Pakistan border. After 18 months in Peshawar with no school and no documents, Ray's father left alone for Russia. The family made a two-week illegal bus journey through wilderness — fake passports, warned to stay silent because soldiers would hurt Afghans — and arrived in Moscow on August 23, 2000. In Russia, his father rebuilt from a roadside table into a store, then a factory in China, then an importing business. They became wealthy. But intense racism followed — police bribes, classmates saying "get out of our country." In 2006 the family chose Canada. They waited 3 years. Ray arrived at Pearson International Airport, Toronto, on October 13, 2009 — with tears and smiles.

CANADA — The Full Arc:
- Arrived with no English. Attended college in Canada (Seneca). Learned English from zero.
- Entered real estate as a solo agent at RE/MAX. Ground floor. No connections. No shortcuts.
- By 2016: hit his first real estate million. First real financial success in Canada.
- 2017-18: Lost everything. Crypto crash + real estate downturn wiped him out. Zero again.
- 2019-20: Slow rebuild. Grinding back up from nothing. Second time starting over.
- 2020 COVID: Lost again. Market chaos, deals collapsed. Third rebuild begins.
- 2022-25: Rebuilt stronger. Now broker-owner and leader at eXp Realty with 200+ agents.
- Named Top 30 Under 30 in Canadian real estate.
- Sold over 1,000 homes. Hundreds of mortgages. Major pre-construction volume.
- Father of 3 children. Married.
- Travelled to 25+ countries.
- Fluent in 3 languages: Dari/Farsi, Russian, English.
- Invests in Canadian and US real estate markets.
- Sponsors Afghan refugees in Canada — settles families, finds them housing.
- Board member of charity. Runs non-profit helping newcomers.
- Speaker, team leader, mastermind group member.
- AI enthusiast. Chess player. Soccer.
- Afghan community leader in Toronto.
- Core philosophy: "I would rather not make money than have my client lose."
- Integrity over commission. Client first. Always.

RAY'S SIGNATURE THEMES (rotate through ALL of these):
1. SAFETY AS PRIVILEGE: Grew up hiding from bombs. A home means safety in a way most people will never understand.
2. LOSING EVERYTHING IS NOT THE END: Lost it all in 2017-18. Lost again in COVID. Rebuilt every time. The market will crash. Ray has survived worse.
3. MONEY ≠ HAPPINESS: Russia gave them wealth but stripped their dignity. A home is more than a number on a balance sheet.
4. HUSTLE FROM NOTHING: Arrived with no English. No connections. No money. Built from zero — again and again.
5. OUTSIDER ADVANTAGE: Told "you don't belong" his whole childhood. Now he fights for the buyers the system overlooks.
6. PATIENCE UNDER PRESSURE: Waited 3 years for Canada. Lost everything twice. Still here. He can wait out any market with you.
7. FAMILY IS THE WHY: Father risked death for the family's safety. Ray is a father of 3. Every deal he closes carries that weight.
8. GIVING BACK IS THE POINT: Sponsors Afghan refugees. Settles families. Sits on charity boards. Success means nothing if you don't bring others with you.
9. INTEGRITY OVER COMMISSION: "I would rather not make money than have my client lose." 1,000+ homes sold on that principle.
10. THE REBUILD: Lost everything at 30. Lost it again at COVID. Built 200-agent brokerage anyway. Every setback has a sequel.
11. LANGUAGE OF CONNECTION: Speaks Dari, Russian, English. Serves clients others can't reach. The immigrant community trusts him because he IS the immigrant community.
12. LEADERSHIP: Solo agent → Top 30 Under 30 → 200+ agent brokerage. The same system that overlooked him, he now runs.

GTA MARKETS TO REFERENCE: Brampton, Vaughan, Mississauga, Markham, Oakville, Richmond Hill, Scarborough, North York, Toronto

RULES:
- Every hook must stop the scroll in the FIRST 3 WORDS
- No generic real estate advice — be hyper-specific to GTA
- At least 30% of content must weave Ray's personal story
- Hormozi density: every sentence must earn its place. No filler.
- Scripts are 30-90 seconds when read aloud
- Hook (0-3s) → Tension/Setup (3-8s) → Story/Teaching (8-50s) → Revelation/Payoff (50-70s) → CTA (last 5-10s)"""


IDEA_BANK_PROMPT = """Generate a 30-day content idea bank for Ray Ahmadi.

Return a JSON array of exactly 30 objects. Each object must have:
- "pillar": one of [authority_expertise, behind_scenes, client_wins, market_intel, mindset_lifestyle, community_culture]
- "core_story": 2-3 sentences describing the core narrative (specific, GTA-referenced, real)
- "viral_angle": the unexpected twist or emotional hook that makes this shareable
- "platform_fit": comma-separated from [reels, tiktok, shorts, linkedin]
- "hook_seeds": array of exactly 3 strings — one curiosity hook, one contrarian hook, one number/stat hook
- "script_type": one of [market, mortgage, personal, client_win, trending, wildcard]

Distribution across 30 ideas:
- 8 authority_expertise
- 5 behind_scenes
- 5 client_wins
- 5 market_intel
- 4 mindset_lifestyle
- 3 community_culture

Rules:
- Every hook seed must stop scroll in first 3 words
- At least 9 ideas must directly reference Ray's personal story (Afghanistan/Russia/Canada arc)
- All market references must be specific GTA cities (Brampton, Vaughan, Mississauga, etc.)
- Zero generic advice — every idea must be specific

Return ONLY the JSON array, no markdown, no explanation."""


HOOK_FORGE_PROMPT = """Generate 3 hook variations for this content idea.

IDEA:
{idea_context}

Return a JSON array of exactly 3 objects. Each object:
- "hook_text": the full hook line (max 15 words, punchy)
- "hook_type": one of [curiosity, contrarian, number]
- "scroll_stop_score": integer 1-10 (how fast does it stop a scroll?)
- "curiosity_score": integer 1-10 (does it create a knowledge gap?)
- "specificity_score": integer 1-10 (is it specific to GTA/Ray/real situation?)
- "authenticity_score": integer 1-10 (does it sound like a real person, not an ad?)

Hook types explained:
- curiosity: creates a knowledge gap ("What nobody tells you about...")
- contrarian: challenges conventional wisdom ("Stop doing X in the GTA market")
- number: leads with a specific stat or number ("3 Brampton buyers lost $40K last month")

Rules:
- First 3 words must be scroll-stopping
- No question marks starting with "Are you" or "Do you"
- No "I'm going to share" or "In this video"
- Make it feel like overheard truth, not an ad

Return ONLY the JSON array."""


SCRIPT_WRITER_PROMPT = """Write a complete short-form video script for Ray Ahmadi.

IDEA: {idea_context}
CHOSEN HOOK: {hook_text}
HOOK TYPE: {hook_type}
CLIENT STORY CONTEXT (use if relevant): {client_story_context}

Return a JSON object with:
- "title": short internal title (max 8 words)
- "hook": the opening hook line (use the chosen hook above)
- "body": the main script body — tension/setup + story/teaching + revelation/payoff
- "cta": the call to action (last 5-10 seconds)
- "caption": suggested social media caption (max 150 chars)
- "hashtags": string of 8-12 relevant hashtags
- "platform": best platform for this (reels/tiktok/shorts/linkedin)
- "estimated_duration_seconds": realistic read time estimate (30-90 seconds)

SCRIPT STRUCTURE (bake this in):
1. Hook (0-3s): Use the provided hook
2. Tension/Setup (3-8s): Raise the stakes. What's at risk?
3. Story/Teaching (8-50s): Ray's story or client story woven with the lesson
4. Revelation/Payoff (50-70s): The insight they came for, delivered hard
5. CTA (last 5-10s): One clear action, specific to Ray

BODY formatting:
- Use "..." to mark natural pause points (these show as orange in teleprompter)
- Keep sentences short — 10 words max per sentence
- Every sentence earns its place — no filler
- Speak in first person as Ray

Return ONLY the JSON object."""


HORMOZI_DENSITY_PROMPT = """Edit this script for Hormozi density. Remove all filler. Target 15% shorter.

ORIGINAL SCRIPT:
Hook: {hook}
Body: {body}
CTA: {cta}

Rules:
- Cut every word that isn't earning its place
- No "basically", "essentially", "kind of", "you know", "really", "very"
- No transitions like "So what does this mean?" or "Here's the thing"
- Keep the "..." pause markers
- Keep all specific numbers, names, and places
- Keep emotional beats
- Preserve the 5-part structure

Return a JSON object with:
- "hook": edited hook
- "body": edited body (15%+ shorter)
- "cta": edited cta

Return ONLY the JSON object."""


DAILY_BATCH_PROMPT = """Generate {n} complete video scripts for Ray Ahmadi's daily content batch.

TRENDING CONTEXT: {trending_context}
CLIENT STORIES AVAILABLE: {client_story_context}

Generate scripts in this exact mix:
1. Real estate market script (GTA-specific, data-driven)
2. Real estate market script (different angle/city)
3. Mortgage education script (rates, pre-approval, refinancing)
4. Personal story script (Ray's Afghanistan/Russia/Canada arc)
5. Client win script (use one of the available client stories above)
6. Trending topic script (hook off the trending news)
7. Wildcard script (unexpected angle, maximum virality)

For each script, return a JSON object with:
- "title": short internal title
- "script_type": one of [market, mortgage, personal, client_win, trending, wildcard]
- "hook": opening hook (stops scroll in first 3 words)
- "body": main body with "..." pause markers
- "cta": call to action
- "caption": social media caption (max 150 chars)
- "hashtags": 8-12 hashtags as a string
- "platform": reels/tiktok/shorts/linkedin
- "estimated_duration_seconds": 30-90

Return a JSON array of {n} script objects. ONLY the JSON array."""
