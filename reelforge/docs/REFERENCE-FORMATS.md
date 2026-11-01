# Reference formats

Two reels were studied frame by frame and transcribed. Both are short-form
lead magnets: show the thing, then "comment KEYWORD" to get it by DM. This
page records what they do and how ReelForge reproduces each part, so the
next reference can be compared against the same list.

## Shared shape

| | Reference 1, "write this → get this" | Reference 2, carousel skill explainer |
|---|---|---|
| Length | ~19 s (12 s of panels, 3 s end card, 4 s outro) | ~50 s |
| Layout | split: panel on top, speaker below | split: panel on top, speaker below |
| Top panel | a chat prompt types, then the result appears beside it | one wide diagram, the camera panning and pushing in across it |
| Panel changes | a new prompt → result pair every ~2 s; the pill flips every ~1 s | every 2–3 s (the pan moves on, or a new zoom) |
| Captions | none on the speaker; the seam pill carries the message | white text on a black bar sitting on the seam, 2–4 words |
| Silence | n/a (music-led) | **0 %**: every breath cut |
| Loudness | −13 LUFS | −14 LUFS |
| Ending | "Comment Edit" card, speaker live in a phone frame with captions, then a ~4 s dim Instagram outro | "Comment Carrusel" over the diagram's last node |

The script is the same in both. The hook promises the result ("with this
skill we publish 100+ carousels a month"). Three or more beats then show
how it works. The close names the keyword and what commenters get ("comment
CARRUSEL and I'll send you the same skill").

## How ReelForge does each part

| Part | Where | Notes |
|---|---|---|
| Split layout | `EDL.layout` (`kind: split`, `ratio`) | The speaker's crop is recomputed for the lower region's shape, so the face is framed rather than squashed. Remotion only: the ffmpeg engine warns and renders full frame. |
| Prompt → result panel | `TopClip(kind="prompt")` | Typing finishes at 85 % of the reveal point. The result springs in. The pill flips WRITE THIS → TO GET THIS. |
| Diagram pan | `TopClip(kind="image", pan_from, pan_to)` | `[x, y, zoom]`, eased in-out. Explainers drift left to right by default. |
| Seam captions | caption style `seam` | Centred on the split line, white on a full-width black bar. |
| End card | `EDL.end_card` | Keyword in the brand accent, subtitle pill, speaker kept live in a muted phone frame with its captions, then the outro with the handle (default 1 s; the reference holds ~4 s, so set `outro` for a slower close). |
| Loudness | `post.SOCIAL_LOUDNESS` = −14 | Applied by `reelforge post` for split formats and end cards. |
| Breath-tight cutting | the playbook's silence rules | Reference 2's 0 % silence is a pacing target for talking-head reels. `reelforge study` measures it. |

The cut detector under-counts cuts in split-screen references, because only
the top half changes. Count panel changes by eye or from the top half.

## Making one

```bash
reelforge edit take.mov --count 1          # cut the reel
reelforge post ~/reelforge/outbox/take-1.edl.json \
    --assets result.mp4 diagram.png --keyword EDIT --render
```

Or in Claude Code: `/edit take.mov`, then `/post <edl> <assets…>`.

## The ability Reference 2 sells: carousels

The carousel skill it describes takes three inputs (the audience's problem,
the context, and a carousel idea that already worked) or a reel that already
performed, and returns the design, hook, body and call to action ready to
post. ReelForge's version is `reelforge carousel` / `/carousel` with the
carousel-writer agent. It writes the copy, then Remotion draws 1080×1350
slides in the brand from `~/reelforge/memory/brand.json`. Several variants
per run, each a different angle, is what turns one idea into a month of
posts.
