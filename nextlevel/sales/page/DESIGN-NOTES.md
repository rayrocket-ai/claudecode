# Next Level sales page: design notes

Restyled 2026-11-15 after Ray asked for "nicer white colours, bright colours". Structure, type scale, motion and quiz logic are unchanged from the redesign of the same day. One file: `index.html` (a body fragment; the host adds the document skeleton).

## Identity
- **Type**: Bodoni Moda (display, with its italic for the one accented phrase per heading), Hanken Grotesk (text), DM Mono (labels, times, buttons), Mrs Saint Delafield (typeset signature only). Optical size is pinned to 28 so the hairlines hold at very large sizes.
- **Palette (light)**: true white `#ffffff`, near-black `#0b0d17`, cool-grey text `#555c6e` and rules `#dde2ee`. Primary: electric blue `#1f3fff`. Secondary: coral `#f2551c` for marks, `#c2410c` where it is text. Tint band `#f2f5ff`. One dark band, deep navy `#0a0f24`, where the blue lightens to `#93a6ff`.
- **Why blue**: it reads as trust for a real estate audience and as technology without the violet that most AI brands use; emerald was rejected because green next to prices reads as a money promise, and the page promises no income.
- **Palette (dark)**: page `#090b14`, text `#f3f5fb`, primary `#93a6ff`, coral `#ff7a4d` / `#ffa27d`. The result sheet stays a light sheet.
- All colours are tokens on `:root`. Contrast is measured from the rendered page in `BUTTON-AUDIT.md`.
- **Wordmark**: "Next *Level*" with a two-bar step mark; the upper bar is blue.
- **Grid**: full-bleed bands, one content column, hairline rules, numbered sections 01 to 08, small uppercase mono labels.

The sections describing motifs, motion and the round 3 offer update below are kept as history. Where they differ from "Visitor test round 1 changes" at the end of this file, that last section is the current state.

## Where colour is used
- Blue: the italic headline phrase, buttons, section numbers, quiz progress line, active side-index item, founding price in the menu, FAQ plus signs, step rules, signature, "Available now" tags (with a slow pulse on the dot).
- Coral: the three missed-call dots and the missed-call count, marquee diamonds, "Opening next" tags. Nowhere else.
- One gradient: the blue "same call, answered" panel in the hero (blue to a deeper blue, with a soft shadow). One glow: behind the $300 on the navy band.

## Motifs
- Hero: oversized headline, then the "phone line" illustration (a day line drawn to scale from 8 am to 10 pm, three missed calls, and the same call answered). It is labelled "Illustration".
- Marquee of the four problems.
- Fixed side index on desktop (1180px and up). Script marks each link that sits over the navy band so it takes the band colours.
- The intake (quiz) on the pale blue band. The result is a white "intake brief" sheet with a blue top edge: meta row, the finding, the reader's own answers, prices, the five "before you pay" lines and a signature.
- Founding 10 on the navy band with the price as the figure; the price stays in view on desktop while the terms scroll.
- Price table set like a menu: name, dotted leader, setup, a month.
- Ray: portrait frame captioned "Portrait to come", facts list, one line and signature.
- Final call to action on a pale blue band.

## Motion
- Load: headline lines rise in sequence; the day line draws, call marks and rows arrive, the missed-call tally counts to 3; the answered call then plays on a loop (clock, three stages, waveform).
- Scroll: reveals, rule draws, the $300 count-up, the portrait and signature wipes.
- Hover: button fill sweep, arrow nudge and a small magnetic pull; underline draw on links; quiz rows indent and draw an accent rule.
- Quiz: screens crossfade, options stagger in, the progress line eases to its new value, the brief unrolls.
- Safety: nothing is hidden by CSS waiting for script. Load animations are CSS with `both` fill. Scroll reveals use the Web Animations API with `fill: backwards`, so content rests visible if script fails. With `prefers-reduced-motion` nothing moves, transitions are off and the marquee wraps as static text. No animation library is loaded.

## Behaviour added in this pass
- Booking fallback (while `CONFIG.BOOKING_URL` is empty): a button that copies NEXT (or WAITLIST) and opens instagram.com/rayahmadi in a new tab with `rel="noopener"`, a confirmation line, and the plain instruction.
- Quiz: a Next control on any question that already has an answer; "Change my answers" keeps the answers; the typed first name survives Back.
- All standalone text controls are at least 44px tall.

## Offer update, 2026-11-15 (round 3 offer)
Design, motion, the booking fallback and the consent logic are unchanged. What was added:
- **Four quiz paths**, chosen by the first answer. Agents: six questions (unchanged). Mortgage brokers and contractors: three questions and a result that offers Answer on the founding terms, worded for the trade. "I run a different kind of business": industry, one phone question, then a waitlist result (1 March 2027 and the starting price for real estate lawyers, accountants and insurance; no date for anything else). "I am in the United States": one question, then a US list result with no price and no booking.
- **Webhook payload**: same fields plus `industry`; `path` is `agent`, `founding-business`, `waitlist` or `us-list`. New tags follow the old style: `nl-founding-business`, `nl-founding-business-<trade>`, `nl-phone-<problem>`, `nl-us-list`, `nl-us-list-<business>`.
- **`CONFIG.DEMO_PHONE`** (empty). When set, script adds a "Call the demo line" block with a `tel:` link under the hero buttons and in every result that offers Answer. When empty nothing about a demo number is on the page.
- **Hero**: one line under the buttons, with a blue rule on its left, welcomes mortgage brokers and contractors. The headline and the label are as they were.
- **Who it is for**: three columns (agents, 7 spots; mortgage brokers and contractors, 3 spots; opening 1 March 2027).
- **Founding terms**: 21 rows. One row holds a text button, "I am in the United States", that opens the US list question in the intake.
- The saved-answers key is now `nlQuizV2`, so answers saved by the earlier version are not read into the new paths.
- A `[hidden]{display:none!important}` rule was added so the text-consent row stays hidden wherever the page is hosted.

## To replace before launch
- Portrait slot: the `<figure class="portrait">` in the About Ray strip, section 01 (HTML comment marks it).
- Signature: typeset in a script face. Swap for Ray's real signature image.
- `CONFIG.BOOKING_URL`, `CONFIG.WEBHOOK_URL` and `CONFIG.DEMO_PHONE` are empty.
- Footer: business name and mailing address (the placeholder is now an HTML comment only; the visible line says they are on the agreement); privacy and terms links (HTML comment only).
- Terms marked "Ray to confirm" in `offer.md` section 6 are on the page as working terms.
- Lines that rest on facts marked `[not verified]` in `offer.md` (the minute bundle, data held in the United States, the Zapier push) are on the page as approved wording. Check them as listed in `../../README.md`, "Verify before publishing", before the page is made public.

## Visitor test round 1 changes, 2026-11-15
Palette, type faces, tokens, CONFIG, payload fields, the four quiz paths and the consent rules are unchanged. What changed, against `../../testing/page-round1/RESULTS.md`:

- **Hero**: two columns on desktop (copy left, illustration right), one column on a phone. Order: label "For real estate agents, mortgage brokers and contractors", the same four-line headline at a smaller size, the what-it-is line, the price line, the main button "See what it would do for you (60 seconds)", "See the prices", the "3 founding spots" line, then "Canada only for now. In the United States? Join the US list" (a text button that opens the US path). All of the first five fit a 360 x 740 phone screen without scrolling.
- **Illustration**: one call from start to finish (missed call, the same call answered by the AI, appointment booked, the text summary). The day line and the count of three missed calls are gone. Still `role="img"` with a written description and the visible label "Illustration". The looped "Answered. Qualified. Booked." panel is unchanged.
- **Sample call**: an outlined button under the illustration opens a native `<dialog>` (modal, Esc, backdrop click, Close; focus returns to the button). It holds a nine-line written exchange and the text the agent receives, labelled "Sample script for illustration, not a recording". Invented first names, no numbers, no addresses. It uses the light sheet tokens in both themes, like the result brief.
- **About Ray**: now a compact strip directly under the hero (section 01) with a small portrait slot, the six approved facts, the quote and signature, and three short assurances. The old section 06 is removed. Side index order: Ray, Intake, Leaks, Method, Founding 10, Menu, Questions, Book.
- **Founding terms**: six rows first, then an "All 21 terms" expander for the other 15. FAQ: six questions first, then "All 22 questions" for the other 16 (two pairs of overlapping questions were merged, so 22 where there were 23). The expander is a `<button>` with `aria-expanded` and `aria-controls`. The folded block carries `hidden="until-found"` and is laid out with `content-visibility: hidden`, so it stays in the DOM, find-in-page opens it (`beforematch`), and a print rule shows it.
- **Languages and data rows** lead with what is offered; the not-promised list follows in smaller text. The data row leads with who can read a transcript and recording off, then says plainly that data is stored in the United States.
- **Booking fallback** (`BOOKING_URL` empty): "Ask Ray for a time", one button "Message NEXT on Instagram", and "The online calendar opens shortly." When the webhook is set and consent was ticked, "Ray will contact you at the details you gave." sits beside the button. The founding section button reads "Ask Ray for a time" in this mode. With `BOOKING_URL` set everything is as before.
- **Last quiz step** (`WEBHOOK_URL` empty): only "First name (optional)" and "Show my brief"; the result says "This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser." With `WEBHOOK_URL` set the earlier form and consent logic are untouched.
- **Trade wording**: "who it is for" is three compact columns, each group with a one-line missed-call example in its own trade. The leaks heading and the missed-call quote no longer assume an agent.
- **Length**: band padding and the section headline scale were reduced, the footer placeholder was replaced, and the About Ray section was merged into the strip. Heights are in `../../testing/page-snapshot/page-text.md`.
- **Footer**: "Operated by Ray Ahmadi. The registered business name and address are on the agreement you sign before any payment."
