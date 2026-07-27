---
description: Check that this machine can run ReelForge, and report what to fix
allowed-tools: Bash(python3:*), Bash(ffmpeg:*), Bash(ffprobe:*), Bash(fc-list:*), Bash(nvidia-smi:*), Bash(df:*), Bash(systemctl status *), Read
---

# ReelForge doctor

Verify this machine is ready to edit video, and report precisely what to fix.

## Steps

1. **Hardware and toolchain profile**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/core/hardware.py"
   ```

   This prints detected cores, RAM, free disk, GPU, ffmpeg/ffprobe/node
   versions, plus the derived settings the pipeline will use (whisper model,
   compute type, render parallelism, encoder args) and a `blockers` /
   `warnings` split.

2. **Fonts.** Captions need a bold sans for text and a colour emoji font for
   the emoji PNG pack:

   ```bash
   fc-list | grep -iE 'inter|montserrat|noto color emoji' | head
   ```

   Missing colour emoji is not fatal — ReelForge rasterises emoji to PNG
   overlays rather than relying on libass colour glyph support, precisely
   because that path fails silently on headless Linux. But the pack has to be
   generated from *some* emoji font.

3. **Transcription stack** (only if `blockers` is empty):

   ```bash
   python3 -c "import faster_whisper, ctranslate2; print('faster-whisper ok')"
   ```

4. **Server mode**, if this is the Hetzner box:

   ```bash
   systemctl status reelforge-watch --no-pager 2>&1 | head -20
   ls -la "${REELFORGE_INBOX:-$HOME/reelforge/inbox}" 2>&1 | head
   df -h "${REELFORGE_ROOT:-$HOME/reelforge}"
   ```

## Reporting

Write a short report, in this order:

- **Blockers** — what stops ReelForge working at all, each with the exact
  command that fixes it. Point at `scripts/install.sh` for toolchain gaps and
  `scripts/server-setup.sh` for server-mode gaps.
- **Warnings** — what will work but degrade, and the practical consequence.
  Translate specs into expectations rather than repeating numbers: on a 4-core
  box say "expect roughly real-time transcription — a 60-minute source takes
  about an hour to pre-warm", not "4 cores detected".
- **Derived settings** — the whisper model, encoder, and parallelism chosen,
  and one line on why, so the choice is visible rather than magic.
- **Disk** — free space, and if it is tight, what `server/retention.py --dry-run`
  would reclaim.

Do not fix anything automatically. This command reports; the user decides.
