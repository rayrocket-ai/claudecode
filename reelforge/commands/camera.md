---
description: Make one-camera footage look multi-camera — close-ups, detail shots and pro camera moves, plus AI-generated angles
argument-hint: <edit.edl.json> [--style multicam|documentary|cinematic] [--angles N] [--location "..."]
allowed-tools: Read, Write, Edit, Glob, Bash(reelforge:*), Bash(python3:*), Bash(ffmpeg:*), Bash(ffprobe:*), Task
---

# Camera $ARGUMENTS

Launch the **camera-director** agent with the edit and any options. It plans
the shot list, renders, checks one frame per shot, and fixes what is off.

If the user asked for angles the camera never saw (side, overhead, orbit, a
different location), the agent also exports the requests for their AI video
tool. Tell the user plainly that those shots come from that tool. Bring them
back with `reelforge angles ingest` once the results are saved.

## Without Claude Code

```bash
reelforge camera reel.edl.json --style multicam --render
reelforge angles export reel-camera.edl.json --count 3 --location "a penthouse with an ocean view"
reelforge angles ingest reel-camera.edl.json && reelforge render reel-camera-angles.edl.json
```

See `docs/VIRTUAL-CAMERA.md`.
