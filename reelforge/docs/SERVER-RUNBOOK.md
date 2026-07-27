# Server runbook — running ReelForge on Hetzner

How to stand it up, reach it from a phone, and fix it when it misbehaves.

## Why a server rather than a laptop

Three things you cannot get on a desktop:

- **Pre-warming.** The watcher starts transcribing the moment footage lands.
  By the time you sit down, an hour-long source is analysed and planning is
  instant. A laptop is asleep when you need this to have already happened.
- **Session survival.** tmux means a render survives you closing the lid.
  Start it at the office, reattach from your phone on the train.
- **One brain.** `memory/` lives in one place, so taste learned from a reel you
  cut on your phone applies to the next one you cut at your desk.

## First-time setup

```bash
ssh you@your-hetzner-box
git clone https://github.com/rayrocket-ai/claudecode
cd claudecode/reelforge

./scripts/install.sh        # ffmpeg, faster-whisper, fonts, python env
./scripts/server-setup.sh   # dirs, syncthing, tailscale, systemd, tmux
```

Then, in order:

**1. Join the tailnet.** `sudo tailscale up`, follow the URL. This is what makes
"from anywhere" safe — SSH and Syncthing bind to the private mesh, and nothing
is exposed to the public internet.

**2. Pair Syncthing.** Its admin GUI has no authentication by default, so it
stays on localhost. Reach it through a tunnel:

```bash
ssh -L 8384:127.0.0.1:8384 you@your-hetzner-box
# then open http://127.0.0.1:8384
```

Add your phone and laptop as devices, then share `~/reelforge/inbox` and
`~/reelforge/outbox`. Set **inbox** to *Send Only* on the phone and *Receive
Only* on the server if you never want the server writing back to your camera
roll — most people prefer that.

**3. Verify.** From Claude Code on the box: `/reel-doctor`.

## Daily use

**From a laptop:**
```bash
ssh hetzner -t 'tmux attach -t reelforge'
```

**From a phone:** Termius or Blink on iOS, Termux on Android. Same command. With
Tailscale running on the phone, `hetzner` resolves over the mesh from anywhere —
hotel wifi, cellular, an airport lounge.

**The loop:** drop a video into the synced `inbox/` from your camera roll → the
watcher pre-warms it while you do something else → attach to tmux and say
`/reels inbox/talk.mp4 --count 3` → renders appear in `outbox/` and sync back to
your phone.

You never wait on a progress bar, because the slow part already happened.

### Detaching without killing anything

`Ctrl-b d` detaches. The session, and any render in it, keeps running. Closing
the terminal has the same effect. `tmux attach -t reelforge` from anywhere picks
up exactly where you left off — including mid-conversation with Claude.

## Once the LibreChat front end lands (phase 9)

Terminal from a phone works, but typing editorial direction into tmux with a
thumb keyboard is unpleasant. LibreChat, self-hosted on the same box, gives you
a browser tab instead: ReelForge exposes an MCP server, a LibreChat agent
consumes it, and you review renders inline instead of syncing them first.

Same tailnet, same auth story, no bot to build. Until then, tmux is the answer
and it genuinely works.

## Operations

```bash
# Watcher
systemctl --user status reelforge-watch
journalctl --user -u reelforge-watch -f          # follow live
systemctl --user restart reelforge-watch

# Retention
python3 server/retention.py --dry-run            # what would be reclaimed
systemctl --user list-timers reelforge-retention

# Disk
df -h ~/reelforge
du -sh ~/reelforge/{inbox,outbox,.cache}
```

### What gets deleted, and what never does

| | Policy |
|---|---|
| `inbox/` source footage | **Never deleted automatically.** Yours to manage. |
| `memory/` | **Never deleted.** Kilobytes, and the only unrecoverable thing here. |
| `outbox/` renders | Expire after 30 days — regenerable from their EDL. |
| `outbox/` EDLs (`.json`) | Kept forever. They *are* the edit. |
| `.cache/` | LRU eviction above 100 GB, by last access. |

If the disk fills, retention will not solve it by deleting your footage. It
reports and stops. That is deliberate.

## Troubleshooting

**Watcher dies when I log out.** Lingering is not enabled:
`sudo loginctl enable-linger $USER`. Without it, user units stop with your
session, which defeats the whole point.

**Watcher won't start, `ModuleNotFoundError`.** Expected before phase 2 — the
unit is installed but `server/watcher.py` needs the ingest pipeline. Not a
misconfiguration.

**Transcription is much slower than expected.** Check `/reel-doctor` for the
chosen model. On a small CX instance it falls back to `small.en` and runs near
real-time; on a dedicated AX box `distil-large-v3` runs 5–15× real-time. The
watcher is `Nice=15` and `IOSchedulingClass=idle`, so it also yields to anything
else busy on the box — that is working as intended, not a fault.

**Box became unresponsive during a render.** `render_parallelism` leaves one
core free, but a `-preset slow` final render on a small box is still heavy. Drop
`[render] parallelism` in `config.toml`.

**Syncthing conflicts (`*.sync-conflict-*`).** Two devices wrote the same file.
Set inbox to Send Only on the phone.

**Out of space mid-render.** `python3 server/retention.py` then re-run. If that
does not free enough, the sources are the problem — archive them off the box.

## Backup

One thing matters:

```bash
tar czf reelforge-memory-$(date +%F).tar.gz -C ~/reelforge memory/
```

`memory/` is your accumulated taste. Everything else — renders, caches, even the
engine — regenerates from source footage and git. That directory does not.
Back it up somewhere off the box.
