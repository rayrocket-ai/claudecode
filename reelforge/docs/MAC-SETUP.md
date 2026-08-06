# Running ReelForge on your Mac

The shortest path from "nothing" to "an edited video". Your footage is already
on this machine, so there is no upload, no sync, and no server involved.

## Why the Mac is the better edit bay

| | Mac | Hetzner CCX23 |
|---|---|---|
| Your footage | **already there** | must be uploaded first |
| Video encoding | **hardware media engine** | software, CPU only |
| Transcription | fast CPU, unified memory | slower shared vCPUs |
| Always on | no — sleeps, travels with you | **yes** |
| Reachable from your phone | no | **yes** |

Use both, in that order. The Mac is where you edit. The Hetzner box comes
later, as the always-on service that watches a folder so you can drop a clip
from anywhere and find a reel waiting. Nothing has to be chosen once — the
same code runs on both, and the machine profile adapts.

## Install (about ten minutes, mostly downloads)

```bash
# 1. Tools. Homebrew from https://brew.sh first if you do not have it.
brew install ffmpeg python@3.12
brew install --cask chromium          # for animated overlays; Chrome works too

# 2. ReelForge itself
git clone <this repo> ~/reelforge-src
cd ~/reelforge-src/reelforge
python3 -m venv ~/.reelforge/venv
source ~/.reelforge/venv/bin/activate
pip install -e .

# 3. Confirm the machine looks right
reelforge --help
```

Chromium is unsigned when installed by Homebrew, so macOS will refuse to open
it the first time. Right-click the app once and choose Open, or run
`xattr -dr com.apple.quarantine /Applications/Chromium.app`. Until you do,
animated overlays report a backend error — they will not silently disappear.

## First edit

```bash
cd ~/reelforge-src/reelforge
reelforge prepare ~/Movies/your-video.mp4
```

The first run downloads the speech model (about 1.5 GB, once) and transcribes.
After that the transcript is cached and everything is instant.

Then, from Claude Code in this repository:

```
/reels ~/Movies/your-video.mp4 --count 3
```

or for a long-form episode:

```
/vlog ~/Movies/your-video.mp4
```

Finished files land in `outbox/`. Beside each MP4 is the `.edl.json` that
produced it — that file *is* the edit, and every decision in it is readable.
Change a number, re-run `reelforge render`, and nothing has to be re-analysed.

Then tell it what you thought:

```
/reel-feedback the captions sat too low and there were too many zooms
```

Anything you say **twice** becomes a permanent rule. The first time is
recorded and nothing changes — that is deliberate, because every clip has
something slightly wrong with it and a system that swings on one reaction
never settles.

## What the Mac gets you automatically

`reelforge` reads the machine on startup and adapts. On Apple Silicon it
selects the **VideoToolbox hardware encoder** rather than software x264, and
deliberately runs fewer segments in parallel — a fixed-function encoder does
not go faster when you queue more work at it.

Transcription stays on the CPU: CTranslate2, which faster-whisper uses, has no
Metal backend. That is not the limitation it sounds like — an Apple Silicon
core is worth several cloud vCPUs, and with 16 GB or more the full
`distil-large-v3` model runs comfortably.

## Known macOS specifics, all handled

- **Emoji.** Apple Color Emoji is a bitmap font with different strike sizes
  than Noto, so a single hardcoded size disabled emoji entirely on macOS. The
  rasteriser now tries each candidate strike.
- **Browsers.** macOS keeps them in app bundles, never on `PATH`. Chrome,
  Chromium, Brave and Edge are all found by bundle path. Override with
  `REELFORGE_CHROMIUM=/path/to/binary`.
- **Gatekeeper.** See the quarantine note above.

## Later: the Hetzner box as well

When you want a video you drop from your phone to come back edited, deploy the
same code to the server with `docs/SERVER-RUNBOOK.md` and point Syncthing at
its watch folder. The Mac stays your fast edit bay; the box handles the
unattended runs. Neither replaces the other.
