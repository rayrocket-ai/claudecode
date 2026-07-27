---
description: Pull a video into the inbox from a link (YouTube, Drive, Zoom, direct URL)
argument-hint: <url> [url ...]
allowed-tools: Bash(python3:*), Bash(yt-dlp:*), Bash(rclone:*), Read, Write
---

# Fetch $ARGUMENTS into the inbox

Resolve each URL to a file in `inbox/`, then let the watcher pre-warm it.

## Steps

1. **Classify and fetch.** For each URL:

   ```bash
   python3 -c "
   import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/..')
   from pathlib import Path
   from reelforge.core import fetch
   import os
   inbox = Path(os.environ.get('REELFORGE_ROOT', '~/reelforge')).expanduser() / 'inbox'
   print(fetch.fetch('$1', inbox))
   "
   ```

   Backends are chosen automatically: `yt-dlp` for YouTube and ~1800 other
   sites, `rclone` for Drive/Dropbox/OneDrive, plain `curl` for direct media
   URLs.

2. **Zoom recordings** are the exception — they do not go through `fetch.py`.
   Use the Zoom connector tools to locate the recording and download it into
   `inbox/` directly. Search by meeting topic or date rather than asking the
   user for a recording ID.

3. **Google Drive share links** need a configured rclone remote rather than a
   share URL. If `fetch` raises with that message, relay it — do not attempt to
   scrape the share link, which breaks on anything non-public and on large
   files.

4. **Report** each result as `<name> — <duration>, <resolution>` by probing the
   downloaded file, and note that the watcher will transcribe it in the
   background. Say roughly how long that will take based on the duration and
   what `/reel-doctor` reports for this machine, so the user knows whether to
   wait or come back.

## Notes

For a batch, writing a link file is better than repeated invocations — the
watcher picks it up and fetches unattended:

```
inbox/_links/monday.txt
```

One URL per line, `#` for comments. That folder is synced, so links dropped
from a phone are fetched by the server without a session open at all.

Fetch only content the user has the right to use — their own uploads, licensed
material, or content they have permission for.
