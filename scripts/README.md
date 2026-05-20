# Studio scripts

## Automated video drop

The flow:

```
Drop file in ~/Dropbox/raw_videos/  →  watcher uploads to GitHub release
                                         ↓
              studio.py pull --latest --prep  ←  here, in the sandbox
```

### One-time setup (on your laptop)

```bash
scripts/install_watcher.sh                  # default folder: ~/Dropbox/raw_videos
scripts/install_watcher.sh ~/Videos/raw     # or pick your own
```

The installer:

- Brew-installs `gh` and `fswatch` if missing
- Authenticates `gh` if needed
- Installs a LaunchAgent (`com.claudecode.video-watcher`) that runs the
  watcher at login and restarts it if it dies

Linux: skip the installer, run `scripts/watch_and_upload.sh` under `tmux`
or systemd. Needs `gh` and `inotify-tools`.

### How it works

`scripts/watch_and_upload.sh` watches the folder. For every new
`.mp4 / .mov / .m4v / .webm / .mkv`:

1. Waits 5s for the file size to stabilize (so Dropbox can finish syncing).
2. Slugs the filename and creates a release `raw-YYYYMMDD-HHMMSS-<slug>`.
3. Uploads the file as the release asset.
4. Moves the source file to `<watch-dir>/uploaded/`.
5. Logs the path in `<watch-dir>/.uploaded.log` so reruns skip it.

Upload retries 3× with exponential backoff on transient `gh` failures.

### Pulling into the studio

```bash
python3 studio.py releases                  # list newest raw-* releases
python3 studio.py pull --latest             # download newest into video_pipeline/input/
python3 studio.py pull raw-20260520-104133-clip
python3 studio.py pull --latest --prep      # download + run prep immediately
python3 studio.py pull --latest --prep --engine scribe
```

If the repo is private, set `GITHUB_TOKEN` in `.env` (fine-grained PAT with
`Contents: Read` on this repo is enough).

### Manual / one-shot uploads

```bash
scripts/watch_and_upload.sh --once          # scan + upload everything, then exit
```

Useful if the daemon isn't running and you just want to push a single batch.
