# Animated overlays and sound

Phase 7. Three capabilities that turn a tight edit into a produced one:
sound effects, a ducked music bed, and animated graphics.

## Sound effects

Effects are **synthesised at render time**, not shipped as audio files. No
licensing question, nothing to download, and byte-identical every run — which
is what lets the cache key be the effect's name alone.

| Name | Length | Use |
|---|---|---|
| `whoosh` | 0.55s | Air over a cut or a fast push-in |
| `whoosh_down` | 0.55s | Downward sweep for a reveal landing |
| `impact` | 0.70s | Low thump under a hard cut or a title |
| `pop` | 0.16s | An emoji or a caption word appearing |
| `click` | 0.06s | A rapid list, a beat |
| `riser` | 1.60s | Tension building into a reveal |
| `ding` | 0.90s | A point landing |

```python
SoundEffect(at=4.5, name="whoosh", gain_db=-9, why="cover the dissolve")
```

**`at` is where the effect lands, not where its file starts.** Each entry in
the catalogue carries a `lead`, and the renderer starts playback that much
earlier — a whoosh placed exactly on a cut is heard just *after* it, which
reads as a mistake. The riser leads by 1.5s because it has to already be
running to peak on the moment it builds to.

Gains are negative by convention and validation rejects anything above unity:
effects are normalised to a fixed peak, so a positive gain is asking for
clipping rather than for emphasis.

A plain cut gets **no** effect by default (`suggest_for_transition`). A whoosh
on every cut is the fastest way to make an edit sound like a template.

## Music bed

```python
Audio(music="bed.m4a", music_gain_db=-19.0, duck=True)
```

The bed is **looped at the input**, so a two-minute track covers a ten-minute
episode with no preparation, and trimmed to the exact edit length.

Ducking is a compressor keyed off the dialogue, not a volume schedule. A bed
at a fixed level either buries a quiet sentence or vanishes under a loud one;
keying it to the voice makes it move the way a human mixer would. The defaults
(`duck_threshold`, `duck_ratio`, `duck_attack_ms`, `duck_release_ms`) are
tuned to be felt and not heard — a slow release keeps it from pumping between
sentences.

`amix` runs with `normalize=0` and `duration=first`. Normalising would drop the
dialogue several dB the moment music appeared, so a scored video would be
quieter than the same video without music, for no reason the user could see.

*Verification:* against a pure-tone source, adding a bed and four effects
raised non-tone energy 12× (25,250 → 313,058) while the tone itself stayed
flat (220,373 → 220,488). The mix is real and the speech is untouched.

## Animated overlays

Two backends, one output format: a transparent PNG sequence composited by the
finishing pass.

### HyperFrames — the default

A composition is a single HTML page rendered in headless Chromium. The
important constraint is that **a composition is a pure function of time**: the
page draws the instant it is given and nothing animates in the browser.

That inversion buys three things. Capture is exact, because there is no race
between an animation clock and a screenshot. Frames are independent, so they
can be rendered in any order. And a re-render is byte-identical, which is what
makes the frame cache sound.

```python
Overlay(type="hyperframes", at=1.2, dur=2.6, comp="lower-third",
        props={"title": "Ray Rocket", "subtitle": "Toronto Real Estate"})
```

Built in: `lower-third`, `callout`, `kinetic` (word-by-word typography),
`progress`. Compositions are authored full-frame and position themselves in
their own CSS, so layout lives in one place instead of split between the
composition and the filter graph.

Needs only a Chromium binary. Found via `REELFORGE_CHROMIUM`,
`PLAYWRIGHT_BROWSERS_PATH`, or `PATH`.

### Remotion — for spring physics and complex sequencing

React, so it needs a Node project:

```bash
npx create-video@latest ~/.reelforge/remotion
export REELFORGE_REMOTION_PROJECT=~/.reelforge/remotion
```

```python
Overlay(type="remotion", at=2.0, dur=2.0, comp="LowerThird",
        props={"title": "Ray Rocket"})
```

Rendered with `--sequence --image-format=png --pixel-format=yuva420p`.
Rendering to a video and keying it back would lose the soft edges that are the
reason to use Remotion at all.

**Choosing:** HyperFrames for lower-thirds, callouts and kinetic type — no
build step and much lighter on a CPU-only box. Remotion when you want spring
physics or genuinely complex sequencing. Both composite identically, so
switching one overlay does not disturb anything else.

**Verification status.** HyperFrames is proven end to end: real Chromium
captures, real transparency, composited into a finished MP4. Remotion's
command layer is built and unit-tested and its packages install cleanly, but
it has **not** been proven rendering a frame here — Chrome refuses to launch
as root without a sandbox flag that Remotion's CLI does not expose, and this
development container runs as root. On a box where the renderer runs as an
ordinary user that constraint does not apply. Until someone has seen it
produce a frame, treat Remotion as unverified and prefer HyperFrames.

## Two failure modes this guards against

**Silent absence.** A missing backend raises `BackendUnavailable` naming the
exact command that fixes it, and the renderer reports it as a warning. A
finished video that quietly lacks its lower-third is the worst outcome
possible, because nothing in the output suggests anything went wrong.

**Silent opacity.** Chromium happily screenshots its own error page — exit
status 0, valid PNG — when a page fails to load, and that PNG is *opaque*,
so compositing it covers the entire video. This bit during development: a
relative path in a `file://` URL makes Chromium read the first segment as a
hostname. A file-existence check cannot catch it. So the first captured frame
of every sequence is inspected for a real alpha channel, and a capture with no
transparency is an error rather than a layer.
