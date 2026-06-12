# Address → Cinematic House Tour Video
### Step plan: Claude (Fable) + Higgsfield, starting from just a listing address

---

## Part 1 — One-time setup (~15 minutes)

**Step 1. Install Claude Code or Claude Desktop**
- Download from claude.com/claude-code (CLI/desktop app) and sign in.
- Make sure you're on a model with tool use (Fable 5 or Opus) — default is fine.

**Step 2. Connect the Higgsfield MCP connector**
- In Claude, open connector settings (Desktop: Settings → Connectors; claude.ai: Settings → Connectors → Browse).
- Add **Higgsfield** and sign in to your Higgsfield account when prompted.
- This gives Claude the `generate_video`, `media_import_url`, `reframe`, and upload tools it needs.

**Step 3. Buy Higgsfield credits**
- A full tour costs roughly **400–800 credits**:
  - 8 video segments × ~45 credits (Seedance 2.0, 1080p, 5s) ≈ 360
  - AI vertical reframe for Reels/TikTok ≈ 365 (optional)
  - A few re-rolls for failed/flagged clips ≈ 50–100 buffer
- The Creator plan allows 8 concurrent render jobs, which is exactly one tour batch.

**Step 4. Install ffmpeg** (for stitching — free, local, no quality loss)
- Mac: `brew install ffmpeg`
- Claude runs all ffmpeg commands itself; you just need it present.

---

## Part 2 — The workflow (what Claude does per address)

**Step 5. Give Claude the address + style brief**
Example prompt:
> "Create a cinematic house tour for **[ADDRESS]**. Find the listing photos online. Make it one continuous drone shot — enter from above, descend, roam room to room. No visible cuts. ~30 seconds. 16:9 and 9:16 versions."

**Step 6. Claude finds the listing photos**
- Web-searches the address → finds the listing (Zolo, HouseSigma, Redfin, broker sites).
- Pulls the photo CDN URLs (many listing sites block scrapers; photo CDNs like
  `shared-s3.property.ca` usually don't — Claude probes for the full photo set).
- Downloads all photos, views them, identifies each room.
- Cleans any burned-in watermarks/text by cropping.

**Step 7. Claude plans the flight path**
Orders the photos into a drone route, e.g.:
aerial → exterior entrance → living room → dining → kitchen (highlight) → bedrooms → exit → twilight hero shot.

**Step 8. Generate the segments — the frame-chaining trick (the key step)**
This is what makes it look like ONE take:
1. Segment 1: `start_image` = aerial photo, `end_image` = exterior photo (Seedance 2.0, 5s, 1080p, 16:9).
2. Extract the **exact final video frame** of segment 1 with ffmpeg (`-sseof -0.15`).
3. Upload that frame → it becomes `start_image` of segment 2; the next listing photo is the `end_image`.
4. Repeat for all ~8 segments. **Photos are benchmarks the drone flies to — never cut points.**
- Every prompt must say: *"the drone is already moving at the first frame and still moving at the last frame, never decelerating."* This kills the pause that reads as a cut.
- This part is sequential: ~5 min per segment ≈ 40 min total. Claude babysits it.

**Step 9. Stitch + smooth (ffmpeg, free)**
- Concatenate all segments — seams are already pixel-identical.
- Add 0.25s micro-crossfades at each join to erase grain/exposure shifts.

**Step 10. Speed ramp (ffmpeg, free)**
- One continuous time curve: brisk on the aerial (~1.2×), **whip through room-to-room transit at ~2.4×** (hides any AI-invented geometry as motion blur — looks like real FPV flying), **slow to 0.85× on the hero room** (usually the kitchen), gentle on the finale.
- Lands the runtime at ~27–30s, Reels/TikTok sweet spot.

**Step 11. Vertical version for IG/TikTok**
- Use Higgsfield's `reframe` tool → 9:16 at 1080×1920.
- It **outpaints** (extends ceiling/floor) instead of cropping, so full rooms stay in frame.
- Long videos process in ~15s chunks; Claude rejoins them with crossfades.

**Step 12. Final delivery**
- 16:9 master (YouTube/website/MLS) + 9:16 vertical (Reels/TikTok), both silent — add trending audio in the app, beat drop synced to the kitchen slowdown.

---

## Known pitfalls (and the fixes)

| Problem | Fix |
|---|---|
| Listing sites return 403 to scrapers | Use the photo CDN directly; probe `_1`, `_2`, … for the full set |
| Seedance flags innocent interiors as NSFW (random) | Re-roll with reworded prompt, or switch that one clip to Kling 3.0 |
| Kling outputs source aspect ratio, not 16:9 | ffmpeg scale + center-crop to 1920×1080 before stitching |
| "Preset recommendation" interrupts generation | Retry with `declined_preset_id` |
| Max 8 concurrent jobs on Creator plan | Queue the 8th after one finishes |
| AI invents geometry between rooms | Whip-speed those transits (Step 10); only photo-anchored moments play slow |
| Clips ease to a stop at segment ends | Prompt "already moving / never decelerating" on every segment |

**Total cost per listing:** ~$5–10 in credits • **Total time:** ~1.5–2 hours, mostly unattended.
