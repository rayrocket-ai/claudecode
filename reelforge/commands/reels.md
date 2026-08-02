---
description: Cut long-form footage into ranked vertical reels
argument-hint: <video> [--count N] [--style karaoke-bold|clean|punch] [--draft]
allowed-tools: Read, Write, Bash(python3:*), Task
---

# Cut $ARGUMENTS into reels

## 1. Check the source is ready

```bash
reelforge prepare "$1"
```

Prints the cache key and whether the transcript and signals are warm. If the
watcher has already pre-warmed it — the normal case on the server — this is
instant. If not, it transcribes now and says how long that will take.

If the source has no speech, stop and say so: reels are cut from what is said,
and there is nothing here to work from.

## 2. Find the moments

Read `memory/style-profile.md` if it exists, then launch the **editor** agent
with the transcript, signals summary, and the highlights schema. Ask it for
about 3x the requested clip count.

Do not do this analysis yourself in the main thread. An hour of transcript is
large, and the point of the subagent is that its context is disposable.

## 3. Compose and render

```bash
reelforge compose "$1" --highlights highlights.json --count 3
reelforge render <edl.json> [--draft]
```

`compose` ranks the candidates, suppresses ones covering the same moment, and
writes one EDL per reel. `render` turns an EDL into an MP4 in `outbox/`.

Render `--draft` first when the user is likely to want changes — it is several
times faster and the framing, timing, and caption decisions are all visible in
it. Save the slow encode for something they have approved.

## 4. Report

For each reel, in rank order:

- The hook line, verbatim — this is what they are actually judging
- Duration, and why it scored where it did
- What was cut from inside it and why (repeats, tangents, filler)
- The output path

Then say what you noticed but did not use — a strong moment that was too long,
one that needed context, a good line that ran into a tangent. That is often
more useful than the clips themselves, because it is what they would have
looked for next.

If a clip scored well but you had reservations, say so plainly rather than
presenting all N as equally good.

## Notes

The EDL beside each MP4 is the edit. To change something, edit that file and
re-render — no need to re-analyse. Every decision in it is inspectable, which
is the point.

After they have watched them, `/reel-feedback` turns their reaction into rules.
Anything said twice becomes part of the playbook, and the next batch reflects it.
