---
description: Write and draw Instagram carousels — from the audience's problem, your context and a winning idea, or from a reel that performed
argument-hint: [--from-reel <video|edl|txt>] [--variants N] [--keyword WORD]
allowed-tools: Read, Write, Glob, Bash(reelforge:*), Bash(python3:*), Task
---

# Carousel $ARGUMENTS

Launch the **carousel-writer** agent. It needs one of two things. Ask for
whichever is missing, in one message:

1. **Three inputs**: the audience's problem, the context (who is posting,
   what they sell), and a carousel idea that already worked for someone else.
   `~/reelforge/memory/context.md` is used as the context when it exists, so
   the user only has to say it once.
2. **A reel that performed**: a video, its EDL, or a transcript.

The agent writes the copy (hook, body slides, call to action, caption), and
renders each carousel to `slide-01.png …` at 1080×1350 in the account's
brand (`~/reelforge/memory/brand.json`). It then opens a few slides to check
them before reporting.

## Without Claude Code

```bash
reelforge carousel --problem "buyers think they need 20% down" \
                   --context @~/reelforge/memory/context.md \
                   --idea "5 myths that keep you renting" --variants 3 --keyword GUIDE

reelforge carousel --from-reel ~/reelforge/outbox/best-reel.edl.json --keyword CAROUSEL

# re-render after editing the copy by hand, no API call
reelforge carousel --decision ~/reelforge/outbox/carousels/01-.../carousel.json
```

## Report back

List each carousel's folder, angle and hook, and paste the caption. If a
keyword was used, remind the user to point their comment-to-DM automation
at it.
