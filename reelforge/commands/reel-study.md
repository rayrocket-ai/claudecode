---
description: Learn the editing style of a reference video and fold it into the playbook
argument-hint: <video-or-url> [--apply]
allowed-tools: Read, Write, Bash(python3:*), Bash(reelforge:*), Bash(yt-dlp:*), Task
---

# Study $ARGUMENTS as a style reference

Someone sends a video and says "make ours like this". This turns that into
numbers the composer can act on, and hands the parts that are not numbers to
the editor agent with the reference's frames in front of it.

## 1. Get the file

If `$1` is a link (TikTok, YouTube, Instagram, Drive), pull it in first:

```bash
reelforge fetch "$1"        # or /reel-fetch
```

Use the downloaded path from here on.

## 2. Measure it

```bash
reelforge study <path> [--name short-name]
```

This measures what a reference can actually tell you: cut cadence, reframe
cadence (the zoom rhythm), pause tightness, energy dynamics, loudness,
caption presence and position, and length. It saves the reading under
`memory/references/` and prints a report with the playbook values the
references imply so far.

**One reference is a direction, not a style.** The suggestions are medians
across every reference studied, so the first one sets a direction and the
third settles it. Do not apply after one unless the user says this single
video *is* the target -- in which case they have, and `--apply` is right.

## 3. Look at what numbers cannot see

Launch the **editor** agent with the report and a filmstrip of the reference
(`reelforge` leaves sampled frames in the work directory; six to ten frames
across the video are enough). Ask it for exactly these, as short observations:

- Caption *style*: font weight, colour, karaoke fill or static, one word at a
  time or phrases, upper case or sentence case
- Emoji and graphics: how often, where, and whether they punctuate or decorate
- B-roll and cutaways: present or not, and roughly how much of the runtime
- Transitions: cuts only, or dips, whips, zooms
- Music and sound effects: is there a bed, are cuts marked with sound
- The hook: quote the first line and say what kind of opening it is

Write these into `memory/style-profile.md` under a `## Reference: <name>`
heading. That file is what the editor reads before every job; the playbook
holds the numbers, the profile holds the taste.

## 4. Apply, if told to

```bash
reelforge study <path> --apply
```

Writes the suggested values into `memory/playbook.md` with provenance naming
the reference, in the same format `/reel-feedback` uses. A rule the user later
disagrees with can be traced to the video that caused it and deleted.

## 5. Report

Say plainly:

- What was measured, in one line per number that moved a playbook value, with
  the value it moved to ("median shot 1.4s -> `min_shot: 0.56`")
- What the editor agent observed that numbers cannot capture
- How many references are in the set now, and whether the style has settled
  (three or more) or is still a single data point
- **What was not measured** -- emoji density, b-roll, transitions, music. If
  the user cares about those, they are in the style profile, not the
  playbook, and they were observed, not counted.

Then offer to cut something in the new style so they can judge it against the
reference side by side. That comparison is worth more than any report.

## Notes

The caption detector finds *where text recurs and changes*, not what it
says. Lettering that never changes -- a poster on the wall behind the
speaker, a channel logo -- is deliberately excluded, because captions move
on to the next words and furniture does not. It is reliable on burned-in
captions and will miss captions rendered as a small sticker in a corner.
Say so if the report shows captions absent but the editor agent can see
them.

Everything in `memory/references/` is a measurement and can be re-derived by
re-running `study`. `memory/style-profile.md` is judgement and cannot; back
it up with the rest of `memory/`.
