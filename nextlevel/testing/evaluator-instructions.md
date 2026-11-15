# Evaluator instructions (offer test)

You simulate customers hearing a pitch. You are given a pitch file, a persona range and an output path.

Read the pitch file (it is ALL the buyer knows) and `personas.json`. Do NOT read any earlier round's results. Evaluate only the personas in your range, one at a time, each in isolation.

For each persona, become that person using every field in their record (role, market, production, tools, budget_sensitivity, scepticism, deal_breakers, must_see_to_continue, the_question_they_want_answered, reason_to_say_no, likely_outcome_prior, tags) and decide honestly.

Rules that keep this honest:
- Real buyers are harsher than simulated ones. Default to "passes" unless the pitch as written clearly overcomes this person's specific objections. An unanswered deal breaker or unanswered must-see question means they do not buy. Do not invent facts the pitch does not state.
- A promise to confirm or test something later is weaker than a stated fact: it can earn a call booking, rarely a purchase.
- A stated "no" (for example "not available in your country", "your language is not promised") is a clear answer: the persona it excludes passes, without resentment, and may still refer someone.
- Personas tagged as an unfixable no stay a no unless the pitch removes their exact reason. Competitors and tyre-kickers never buy. Scepticism 4 or 5 means written policies are doubted until proven.
- "buys" means: they would book the call AND, assuming the call matches the pitch exactly, pay. Use it only when nothing they need is left open.
- A business owner can buy only if the pitch says their industry can buy now; otherwise their choices are "joins waitlist" or "passes".
- Each decision must cite the exact part of the pitch that caused it, or the exact missing piece.

Output: a JSON array, one object per persona, with exactly these fields:
id; segment; decision_founding ("buys", "books call only", "joins waitlist", "passes"); decision_standard (same options, if only the standard price were offered); would_refer (true/false); main_reason (one sentence in the persona's own voice, plain and specific, no profanity); what_almost_changed_their_mind (one sentence); missing_info (array of specific unanswered questions that mattered, empty if none); price_reaction ("cheap", "fair", "expensive", "cannot judge"); max_monthly_they_would_pay_cad (number, 0 if none); trust_in_ray (1 to 5); best_product_for_them ("Answer", "Reviews", "Nurture", "Ads", "Complete", "none"); line_that_helped_most (exact phrase from the pitch, or ""); line_that_hurt_most (exact phrase from the pitch, or "").

Validate with python: valid JSON, exactly 25 objects, the ids in your range each once, every field present with allowed values, quoted lines are exact substrings of the pitch. Fix until it passes. Write only your output file. Do not edit anything else. Do not commit. Report in under 100 words: validation result and the counts for decision_founding and decision_standard.
