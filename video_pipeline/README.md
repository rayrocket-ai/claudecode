# Video prep pipeline

Turns a long-form video into cleanly edited content: silence trimmed, filler
words removed, transcribed with word-level timings, optionally reframed to
9:16, rendered to a final MP4 from an AI-generated EDL.

Two compositors sit alongside this pipeline (both optional, pick per task):

- `../video_remotion/` — React/Remotion. Captions, B-roll, motion-graphics
  overlays baked on top of the base video.
- `../video_hyperframes/` — HTML/GSAP. Standalone motion-graphics inserts.

The editorial contract (cut rules, EDL format, fade durations, etc.) lives in
`../.claude/skills/video-editing/SKILL.md`.

## Setup (one-time)

```bash
cd video_pipeline
pip install -r requirements.txt
# ffmpeg must be on PATH: sudo apt install ffmpeg
```

## Usage

```bash
# from repo root — full prep pipeline
python3 studio.py prep video_pipeline/input/my_long_video.mp4

# with ElevenLabs Scribe (preserves filler words, better timestamps)
python3 studio.py prep video_pipeline/input/my_long_video.mp4 --engine scribe

# render an EDL to final MP4
python3 studio.py render edl.json -o output/final.mp4
```

Or call `./run_pipeline.sh <input> [whisper-model] [engine]` for the legacy
silence -> transcribe -> cut fillers -> reels -> vertical pipeline.

Outputs land in `output/<basename>/`:

```
silenced.mp4             # silence removed
cleaned.mp4              # silence + filler words removed
cleaned.srt              # subtitles (from cleaned cut)
cleaned.words.json       # word-level timings (feeds Remotion, Scribe)
cleaned.segments.json    # phrase-level timings
takes_packed.md          # phrase-level reading artifact for cut selection
reels/                   # reel-length chunks, original aspect
reels_vertical/          # reel-length chunks, 9:16 (blurred background)
```

## Individual scripts

Run any stage standalone:

```bash
python3 cut_silence.py      in.mp4  out.mp4  --threshold -30 --min-silence 0.5
python3 transcribe.py       in.mp4  --engine scribe            # or --engine whisper
python3 cut_fillers.py      in.mp4  out.mp4  --pad 0.05        # needs .words.json
python3 pack_transcripts.py --edit-dir output/myvid/
python3 split_reels.py      in.mp4  reels/   --min 30 --max 60 --target 45
python3 to_vertical.py      in.mp4  out.mp4  --mode blur       # or --mode crop
python3 render.py           edl.json -o final.mp4 [--preview]
```

## Whisper model sizes

| Model     | Speed | Quality | RAM   |
|-----------|-------|---------|-------|
| tiny      | 10x   | rough   | ~1 GB |
| base      | 7x    | good    | ~1 GB |
| small     | 4x    | better  | ~2 GB |
| medium    | 2x    | great   | ~5 GB |
| large-v3  | 1x    | best    | ~10 GB|

Start with `base`. Bump to `small`/`medium` if captions have errors.

## Finish with motion graphics

**Remotion (React, recommended for captions over base video):**

```bash
cd ../video_remotion
npm install                                                      # one-time
node scripts/import-words.js ../video_pipeline/output/myvid/cleaned.words.json
node scripts/import-scene.js  my-scene.json                      # optional
npm run start                                                    # browser studio
npm run render                                                   # out/reel.mp4
```

**Hyperframes (HTML/GSAP, standalone motion-graphics assets):**

```bash
cd ../video_hyperframes
npm install
npm run preview
npm run render                  # out/video-hyperframes-scene.mp4
```

**Render directly from an EDL** (no GUI, agent-friendly):

```bash
python3 studio.py render edl.json -o output/final.mp4
```

See `../.claude/skills/video-editing/SKILL.md` for the EDL schema and the
full editorial contract.
