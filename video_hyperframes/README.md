# Video Hyperframes

Independent motion-graphics compositor. Renders HTML + GSAP to MP4 via
[Hyperframes](https://github.com/heygen-com/hyperframes). This folder is
fully self-contained — no imports from `video_remotion/` or
`video_pipeline/`.

## Use this when…

You need **standalone motion-graphics assets**: logo stings, intro bumpers,
animated charts, kinetic typography, shader transitions, pure-graphics
explainers. The output drops back into your main timeline (or is used
on its own).

For anything composited over your base video (captions, B-roll, lower-thirds
over a talking head), use `video_remotion/` instead.

## Setup

```bash
cd video_hyperframes
npm install
```

Requires Node ≥ 22 and FFmpeg on your PATH.

## Preview

```bash
npm run preview
```

Opens a live-reloading browser view.

## Render

```bash
npm run render              # writes ./out/video-hyperframes-scene.mp4
```

## Adding catalog blocks

Hyperframes ships a library of prebuilt blocks (shader transitions,
data-viz, cinematic effects):

```bash
npm run add -- <block-name>
```

## File layout

```
video_hyperframes/
├── index.html      composition stage + clips
├── style.css       visual styles
├── animate.js      GSAP timeline (deterministic — no timers)
├── package.json
└── README.md
```

## Rules (same correctness contract as the main skill)

- **Deterministic only.** No `Date.now()`, no `Math.random()`, no `setTimeout`.
  All motion lives on a `gsap.timeline({ paused: true })` the engine seeks.
- **Alpha exports** for overlays to drop onto a Remotion timeline. Render to
  WebM/VP9 with alpha, or ProRes 4444.
- **Match the target fps.** If you're inserting into a 30fps Remotion reel,
  render this at 30fps.
- **Absolute positioning inside `#stage`.** Don't depend on flow layout.
