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
- Portrait slot: the `<figure class="portrait">` in section 06 (HTML comment marks it).
- Signature: typeset in a script face. Swap for Ray's real signature image.
- `CONFIG.BOOKING_URL`, `CONFIG.WEBHOOK_URL` and `CONFIG.DEMO_PHONE` are empty.
- Footer: business name and mailing address; privacy and terms links (HTML comment only).
- Terms marked "Ray to confirm" in `offer.md` section 6 are on the page as working terms.
- Lines that rest on facts marked `[not verified]` in `offer.md` (the minute bundle, data held in the United States, the Zapier push) are on the page as approved wording. Check them as listed in `../../README.md`, "Verify before publishing", before the page is made public.
