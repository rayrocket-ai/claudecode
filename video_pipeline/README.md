# Video prep pipeline

Turns a long-form video into Reel-ready chunks: silence trimmed, transcribed,
split at sentence breaks, and reframed to 9:16.

Finish in CapCut (or similar) to add B-roll, animated captions, and music.

## Setup (one-time)

```bash
cd video_pipeline
pip install -r requirements.txt
# ffmpeg must be on PATH: sudo apt install ffmpeg
```

## Usage

```bash
# drop your video into video_pipeline/input/ (or anywhere)
./run_pipeline.sh input/my_long_video.mp4

# larger, more accurate model:
./run_pipeline.sh input/my_long_video.mp4 small
```

Outputs land in `output/<basename>/`:

```
cleaned.mp4              # silence removed
cleaned.srt              # subtitles
cleaned.words.json       # word-level timings (for animated captions)
cleaned.segments.json    # sentence-level timings
reels/                   # reel-length chunks, original aspect
reels_vertical/          # reel-length chunks, 9:16 (blurred background)
```

## Individual scripts

Run any stage standalone:

```bash
python3 cut_silence.py  in.mp4 out.mp4 --threshold -30 --min-silence 0.5
python3 transcribe.py   in.mp4 --model base
python3 split_reels.py  in.mp4 reels/ --min 30 --max 60 --target 45
python3 to_vertical.py  in.mp4 out.mp4 --mode blur   # or --mode crop
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

## Finish in CapCut

1. Import `reels_vertical/<file>.mp4`
2. Import `cleaned.srt` for captions (or use CapCut's auto-captions to get animated word-by-word)
3. Drop B-roll on track 2 at the beats you want
4. Add music on the audio track, duck under voiceover
5. Export at 1080x1920, 30fps
