# Visitor instructions (page test)

You simulate people visiting a web page. You are given a persona range and an output path.

Read `page-snapshot/page-text.md` in full (the page's look, all visible text in order, every quiz screen for every path, example result briefs, every button and what it does, and what is NOT on the page). Look at the screenshots in `page-snapshot/` with the Read tool: preview-hero.png, preview-mobile-hero.png, preview-quiz.png, preview-founding.png, preview-menu.png, preview-result.png, preview-business-result.png. Then read `personas.json`. Do NOT read any offer-round or earlier page-round results. Evaluate only the personas in your range, one at a time, each in isolation.

For each persona, walk the page as that person would, using their device, attention, arrived_from, scepticism, deal_breakers, must_see_to_continue and the_question_they_want_answered:
- "skims 20 seconds" on a phone sees the first screen and perhaps one scroll. They decide from the headline, the sub-line, the button and what they glimpse. They do not read the FAQ or the 21 founding terms.
- "reads half" reaches roughly the method and founding sections before deciding.
- "reads everything" reads it all, including the FAQ.
- The page is long. Information a persona needs only counts if it sits where that persona would actually reach it.
- The booking button does not open a calendar today: it copies a word and opens Instagram. The form's submit shows a result on screen; nothing is emailed yet. Judge that experience honestly as the visitor would feel it.

Rules that keep this honest:
- Real visitors are harsher and less patient than simulated ones. Most cold visitors leave. Default to leaving unless something specific on the page, in a place they would see, earns the next step.
- Do not invent content that is not in the snapshot. Unfixable-no personas stay no unless the page removes their exact reason. Competitors and tyre-kickers may complete the quiz to look around but never book in good faith.
- A persona excluded by a clear statement (not available in their country, their language not promised) leaves or joins the relevant list, without resentment.
- Cite the exact words or element that caused each decision.

Output: a JSON array, one object per persona, with exactly these fields:
id; device; furthest_point ("first screen", "who it is for", "problems", "method", "founding", "menu", "ray", "faq", "final cta", "quiz started", "quiz finished", "result"); started_quiz (true/false); finished_quiz (true/false); quiz_path ("agent", "founding-business", "waitlist", "us-list", "none"); gave_contact_details (true/false); ticked_email_consent (true/false); outcome ("left", "quiz only", "joined a list", "tried to book", "would buy after call"); seconds_on_page (number); first_impression (one sentence in their voice about the look and headline); main_reason (one sentence in their voice, specific, no profanity); element_that_helped_most (exact words or element name, or ""); element_that_hurt_most (exact words or element name, or ""); confusion (array of specific things that confused or annoyed them, empty if none); missing (array of specific things they looked for and did not find where they looked, empty if none); booking_fallback_reaction (one of "fine", "annoyed", "gave up", "did not reach it"); design_score (1 to 5: how premium and trustworthy the page looked to them); clarity_score (1 to 5: how quickly they understood what is offered and what it costs).

Validate with python: valid JSON, exactly 25 objects, the ids in your range each once, every field present with allowed values. Fix until it passes. Write only your output file. Do not edit anything else. Do not commit. Report in under 100 words: validation result and the counts for outcome and started_quiz.
