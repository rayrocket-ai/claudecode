---
description: Lay out a finished edit as a post — showcase ("write this → get this"), explainer, or full — with a "Comment KEYWORD" end card
argument-hint: <edit.edl.json> [assets...] [--keyword WORD] [--offer "what they get"]
allowed-tools: Read, Write, Glob, Bash(reelforge:*), Bash(python3:*), Bash(ffmpeg:*), Bash(ffprobe:*), Task
---

# Post $ARGUMENTS

Launch the **post-designer** agent with the edit, the assets the user gave
(screenshots, diagrams, result clips), and any keyword or offer. It picks the
format, places each top-panel clip on the word that names it, writes the
end card, renders, and looks at the frames before reporting.

The formats, with timings taken from the two reference reels, are in
`docs/REFERENCE-FORMATS.md`.

## Without Claude Code

```bash
# Claude designs the layout from the edit and the assets
reelforge post reel-1.edl.json --assets prompt-result.mp4 diagram.png --keyword EDIT --render

# or lay it out from a spec you wrote
reelforge post reel-1.edl.json --spec reel-1.post.json --render
```

## Report back

Relay the format and why, the end-card keyword, the output path, and any
notes (clips moved or dropped, overlays removed for the split). Then remind
the user that a comment keyword only pays off if something answers the
comments. A comment-to-DM automation has to be set up for that keyword.
