# Next Level sales page: design notes

Redesign of 2026-11-15. One file: `index.html` (a body fragment; the host adds the document skeleton).

## Identity
- **Type**: Bodoni Moda (display, with its italic for the one accented phrase per heading), Hanken Grotesk (text), DM Mono (labels, times, buttons), Mrs Saint Delafield (typeset signature only). Optical size is pinned to 28 so the hairlines hold at very large sizes.
- **Palette**: warm paper `#f2efe8`, ink `#141311`, one accent (brass, `#8a5a17` on paper and `#d8b06c` on dark). Dark theme inverts paper and ink and keeps the same accent. All colours are tokens on `:root`.
- **Wordmark**: "Next *Level*" with a two-bar step mark. Original, drawn in CSS.
- **Grid**: full-bleed bands, one content column, hairline rules, numbered sections 01 to 08, small uppercase mono labels.

## Motifs
- Hero: oversized headline, then the "phone line" illustration (a day line drawn to scale from 8 am to 10 pm, three missed calls, and the same call answered). It is labelled "Illustration".
- Marquee of the four problems.
- Fixed side index on desktop (1180px and up). White text with `mix-blend-mode: difference` so it reads on paper and on the dark bands.
- The intake (quiz) on a dark band. The result is a paper "intake brief" with a meta row, the finding, the reader's own answers, prices and a signature.
- Founding 10 on a dark band with the price as the figure.
- Price table set like a menu: name, dotted leader, setup, a month.
- Ray: portrait frame captioned "Portrait to come", facts list, one line and signature.

## Motion
- Load: headline lines rise in sequence; the day line draws, call marks and rows arrive, the missed-call tally counts to 3; the answered call then plays on a loop (clock, three stages, waveform).
- Scroll: reveals, rule draws, the $300 count-up, the portrait and signature wipes.
- Hover: button fill sweep, arrow nudge and a small magnetic pull; underline draw on links; quiz rows indent and draw an accent rule.
- Quiz: screens crossfade, options stagger in, the progress line eases to its new value, the brief unrolls.
- Safety: nothing is hidden by CSS waiting for script. Load animations are CSS with `both` fill. Scroll reveals use the Web Animations API with `fill: backwards`, so content rests visible if script fails. With `prefers-reduced-motion` nothing moves, transitions are off and the marquee wraps as static text. No animation library is loaded.

## To replace before launch
- Portrait slot: the `<figure class="portrait">` in section 06 (HTML comment marks it).
- Signature: typeset in a script face. Swap for Ray's real signature image.
- `CONFIG.BOOKING_URL` and `CONFIG.WEBHOOK_URL` are empty.
- Footer: business name and mailing address; privacy and terms links (HTML comment only).
