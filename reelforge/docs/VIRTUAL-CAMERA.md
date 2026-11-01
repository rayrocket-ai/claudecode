# Virtual camera: several cameras from one

Reference 3 is a cooking reel captioned "this video was shot from one angle."
Its top half shows close-ups, side angles, an overhead view, an orbit, a
different room, and a shot through flowers. Its bottom half shows the single
locked-off wide shot it all came from. This page splits what that reel does
into what ReelForge does from the pixels, and what needs a generative model.

## What the reference does

| Time | Top half (the result) | How |
|---|---|---|
| 0–5 s | close-up of hands cutting, then a medium | crop: the pixels contain it |
| 5–13 s | camera to the side, overhead, a slow move "that never happened" | generated: no crop makes a new viewpoint |
| 15–22 s | same take relocated to a penthouse with an ocean view | generated (new location) |
| 22–33 s | inside that location: side, close-up, orbit, behind an object | generated, plus foreground depth |
| 33–37 s | extreme close-ups of the face and hands | crop |
| 44–47 s | "Comment КАДР": a lead magnet for the lesson | end card (`reelforge post`) |

A new camera arrives every 1.5–3 s. The voice never cuts. That combination,
a picture cut with no audio cut, is what makes one camera read as several.

## From the pixels: `reelforge camera`

```bash
reelforge camera reel.edl.json --style multicam --render
```

It writes `reel-camera.edl.json`: every segment gets a shot list under
`framing[].shots`. Remotion draws each shot as its own camera, and the
segment's voice plays once underneath (audio across shot cuts measures
identical to no cut).

| Size | Zoom over the base crop | Framed on |
|---|---|---|
| wide | 1.0 | the subject, pulled toward centre |
| medium | 1.3 | the face, eyes on the upper third |
| close | 1.75 | the face |
| extreme | 2.4 | the face, tight |
| detail | 2.0 | wherever the hands are moving (frame differencing, face masked out) |

| Move | What it is |
|---|---|
| static | locked off |
| push / pull | a slow dolly in or out across the shot (~7%) |
| pan / tilt | the frame travels across the subject |
| punch | a fast push in a third of a second, on an emphasised word |
| drift | handheld sway: two slow sines per axis plus a hint of roll, with overscan so edges never show |
| peek | a soft dark edge drifting across one side, as if shot past an object; placed away from the subject |

Rules: cut on word starts (sentence ends and pauses preferred), consecutive
sizes at least 25% apart, never the same move twice in a row, open close on
the hook, punch where the edit already marked emphasis.

Styles: `multicam` (2–3.5 s shots, social), `documentary` (3–5.5 s,
constant sway), `cinematic` (locked-off glides, foreground depth).

**Resolution is the limit.** A close-up is a crop, and a crop of a small
source is soft. The planner caps magnification at `--max-upscale` (default
2.6× of the source's own pixels) and compresses the size ladder to fit,
saying so in its notes:

| Source → 1080×1920 reel | Tightest sharp shot |
|---|---|
| 4K landscape (3840×2160) | the full ladder, extreme close-up included |
| 4K vertical (2160×3840) | the full ladder with room to spare |
| 1080p landscape | about 1.45×: medium and a gentle close-up |
| 1080p vertical | the full ladder, softer at extreme |

Film in 4K. It is the single change that most improves this.

## Beyond the pixels: `reelforge angles`

A side angle, an overhead view, an orbit or a new location is new
information. No crop contains it. Those shots come from a video-to-video
generative model, and ReelForge does the editing around it:

```bash
reelforge angles export reel-camera.edl.json --count 3 --location "a penthouse with an ocean view"
#   -> reel-camera-angles/angle-01.mp4 ... + angles.json with a prompt per clip
#   run each through your video tool, same length, save as reel-camera-angles/results/angle-01.mp4
reelforge angles ingest reel-camera.edl.json
reelforge render reel-camera-angles.edl.json
```

- Export picks the longest shots, spread through the edit (never the hook,
  so it stays on the real face), and cuts each from the source at full
  quality.
- Ingest matches results by source time, so re-planning after export cannot
  send a clip to the wrong shot. It time-stretches each clip by
  generated-length ÷ sent-length so the generated lips stay on the original
  voice. It refuses a clip more than 20% off, because by then it is visibly
  out of sync.
- Generated clips replace picture only. The voice is always the original
  recording.

A generated face is a likeness of the speaker. Use it only on footage of
yourself or with the person's consent, and follow the platform's rules on
labelling AI-generated content.
