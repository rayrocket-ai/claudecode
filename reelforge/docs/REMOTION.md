# The Remotion engine

ReelForge renders with [Remotion](https://www.remotion.dev) by default. Every
frame is drawn as a React composition in a headless browser, which buys what
an ffmpeg filter graph does poorly:

- spring physics on graphics
- real typography on captions
- colour emoji drawn natively
- motion you can read and change as code

The ffmpeg engine remains as a fallback. When Remotion isn't installed, the
render still succeeds and its report says it used ffmpeg and why.

## Python decides, Remotion draws

The composition in `remotion/` never makes an editorial decision.
`core/render/remotion_renderer.py` resolves the whole EDL into frame numbers
first, using the **same functions the ffmpeg engine uses**:

| Decision | Made by | Arrives in props as |
|---|---|---|
| Which source frames survive | the EDL's segments | `segments[].trimBefore`, `from`, `duration` |
| Where the crop window sits | `filters.crop_window` | `segments[].crop` (source px, clamped) |
| Push-in curve | the EDL's framing | `zoomFrom`/`zoomTo`, normalised so the small end is 1 |
| Transition dips | the ffmpeg engine's boundary rule | `fadeIn`/`fadeOut` frames |
| Caption cards | `ass.group_words` (word count, characters, pauses, cuts) | `captions.pages[]` |
| Caption position | the playbook's learned `caption_position` | `captions.style.positionY` |
| When music ducks | word timings, short gaps merged | `music.windows[]` |
| When effects land | the catalogue's per-effect lead | `sfx[].from` / `trimBefore` |

This is why the two engines frame a shot identically, and why QC can keep
repairing the EDL rather than the pixels.

After the browser, one ffmpeg pass normalises loudness with the picture copied
untouched. Remotion has no loudness normaliser, and the platform target is
part of the EDL's contract (-16 LUFS for short-form, -14 for YouTube).

## Choosing an engine

```bash
reelforge render edit.edl.json                   # auto: Remotion if installed
reelforge render edit.edl.json --engine ffmpeg   # force ffmpeg
REELFORGE_ENGINE=ffmpeg reelforge edit video.mp4
```

Asking for `--engine remotion` when it isn't installed is an error, not a
silent fallback. Asking for one engine and quietly getting the other would
be the wrong kind of helpful.

## Install

`scripts/mac-setup.sh` and `scripts/hetzner-setup.sh` both do it. By hand:

```bash
cd reelforge/remotion
npm install
npx remotion browser ensure     # fetch Remotion's headless browser once
```

## The browser trap

Remotion drives Chrome in the old headless mode. **Desktop Chrome no longer
has that mode** (it was removed in Chrome 132). Pointed at desktop Chrome,
Remotion's browser dies on launch with nothing better than
`Closed with 1 signal`. That exact failure cost a session before it was
understood.

So ReelForge only ever hands Remotion a *Chrome headless shell*: Playwright's
`chromium_headless_shell-*`, or `REELFORGE_REMOTION_BROWSER`. When neither
exists, it passes no browser and Remotion fetches its own. A test pins that
desktop Chrome is never chosen.

## Speed

A browser screenshotting every frame is slower than a filter graph:

| Machine | 30-second vertical reel |
|---|---|
| Apple Silicon Mac (10 cores) | under a minute |
| Hetzner CCX23 (4 vCPU) | roughly two to four minutes |

Use `--draft` while iterating. It changes encode quality, not the decisions,
so everything you would judge (framing, timing, captions) is visible in it.

## Adding a graphic

1. Write the component in `remotion/src/graphics.tsx` as a pure function of
   `useCurrentFrame()`. Use `spring()` and `interpolate()`; never use timers
   or CSS animations, because frames render out of order, in parallel.
2. Register it in `GRAPHICS` and in `GraphicName` (`remotion/src/types.ts`).
3. Add both spellings to `GRAPHIC_ALIASES` in `core/render/remotion_renderer.py`,
   and a standalone `Composition` in `remotion/src/Root.tsx`. The standalone
   one serves the ffmpeg engine's `remotion` overlay type.
4. `npx tsc --noEmit`, render a short edit, and look at the frames.
   `npm run studio` previews interactively.

## Licence

Remotion is not MIT-licensed. Its licence is free for individuals, for
companies with **up to three employees**, and for non-profits. Larger
companies need a paid company licence from remotion.pro.

If Ray Homes is four or more people, a licence is needed before Remotion
renders are used commercially. The ffmpeg engine has no such condition, and
`REELFORGE_ENGINE=ffmpeg` switches everything to it.
