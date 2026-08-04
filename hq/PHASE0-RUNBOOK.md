# Phase 0 runbook — Stabilize (run on the Hetzner box)

Companion to `hq/PLAN.md` §6 Phase 0. This is the box-side checklist: every
step here runs on the CCX23 (87.99.139.222), not in a cloud container —
the container cannot reach api.lofty.com, port 22, or the engine's Postgres.
Best loop: open Claude Code directly on the box inside `tmux` and work
through this file top to bottom. Steps are ordered so that nothing
destructive happens before evidence is captured.

**Exit gate (verbatim from the plan):** ≥95% clean test conversations, zero
unhandled job types, Lofty baseline captured. Until this gate passes,
inbound-auto stays off.

---

## 0. Before anything: evidence capture (read-only)

- [ ] `tmux new -s phase0` — everything below runs in this session.
- [ ] Snapshot the box state into a dated evidence directory:
  ```bash
  mkdir -p ~/phase0-evidence/$(date +%F)
  cd ~/phase0-evidence/$(date +%F)
  docker ps -a > docker-ps.txt
  docker stats --no-stream > docker-stats.txt
  systemctl list-units --type=service --state=running > services.txt
  crontab -l > crontab-root.txt 2>&1
  ls -la /opt/ > opt-listing.txt
  df -h > disk.txt; free -h > memory.txt
  ss -tlnp > listening-ports.txt
  ```
- [ ] Postgres backup BEFORE touching anything:
  ```bash
  docker exec <postgres-container> pg_dumpall -U postgres | gzip > pre-phase0-$(date +%F).sql.gz
  ```
  (Find the container name in `docker-ps.txt`. If Postgres runs bare, use
  `pg_dumpall` directly.)
- [ ] Copy that backup OFF the box (laptop or object storage). A backup that
  lives only on the machine it protects is not a backup.

## 1. Security sweep

Order matters: rotate credentials first, then close open doors.

- [ ] **Rotate the root password** — it was pasted into a chat session on
  2026-08-02 and must be treated as compromised. While you're there:
  ```bash
  passwd
  # then, if not already the case:
  #   - create a non-root user with sudo for daily work
  #   - switch SSH to key-only:  PasswordAuthentication no  in /etc/ssh/sshd_config
  #   - systemctl restart sshd   (keep your current session open until a new
  #     login is verified!)
  ```
- [ ] **Portainer**: check how it is exposed (`listening-ports.txt`). If it is
  reachable on a public port, bind it to localhost or put it behind
  Tailscale; verify it has a strong admin password either way.
- [ ] **`/voice/calls` PII leak**: the receptionist dashboard
  (`dashboard/receptionist.py`, content-engine lineage) serves call
  transcripts on an **unauthenticated GET**. Until the endpoint gets auth,
  block it at the proxy/firewall level. The ElevenLabs webhook POST already
  verifies HMAC — only the GET is the hole.
- [ ] **Purge `content.db` from git history** (it contains real data and is
  committed in the content-engine lineage):
  ```bash
  git filter-repo --invert-paths --path content.db   # or BFG
  ```
  then add it to `.gitignore` and force-push only after confirming every
  clone/remote is accounted for.
- [ ] **Lofty API key audit** (Settings → Integrations → API in
  crm.lofty.com). The screenshot audit found 7/10 keys active, including
  keys from earlier agent projects that may STILL be writing:
  | Key | Action |
  |---|---|
  | `rex` | Identify what it feeds (check its last-used timestamp; grep box configs/`.env` files for the key). Revoke unless a live, wanted integration depends on it. |
  | `new claw` | Same — labeled from an earlier agent build. |
  | `openclaw` ("telegram open claw nurture") | Same — this one is labeled as a nurture bot. **No prior agent may keep writing to Lofty unaudited** (plan §6 Phase 0). |
  | "Legacy Token" (no expiry) | Revoke or re-mint with expiry. No-expiry credentials don't survive a security review. |
  | 2× "Lovable API" (duplicates) | Revoke at least the duplicate; likely both. |
  - [ ] Mint ONE new key named **`growth-os`**, with an expiry, and place it
    in the engine's `.env` on the box. It never appears in chat, git, or
    Telegram.
  - [ ] Grep the box for the old key values before revoking, so nothing
    silently breaks: `grep -rn "token " /opt/*/.env /opt/*/config* 2>/dev/null`
- [ ] **ElevenLabs agent prompt → version control**: copy the full agent
  prompt/config from the ElevenLabs dashboard into
  `hq/receptionist/elevenlabs-agent.md` in this repo, and add the AI
  disclosure line while you're in there.
- [ ] **VOW agreement docs onto the box**: locate the signed board/PropTx VOW
  agreement PDFs and drop them into the engine's document storage. (The
  portal-vs-agreement display-rules audit itself is a Phase 3A pre-launch
  task; Phase 0 only ensures the documents are findable.)

## 2. `/opt/realtor-agent` audit (read-only)

Goal: explain the failure metrics before changing a line. Numbers to explain:
**7 of last 9 AI runs failed · 368 "exhausted model iterations" errors ·
132 failed jobs · 106 failed agent turns**.

- [ ] Map the architecture: containers, entry points, queue tables, worker
  loop, which model/provider each agent call uses.
- [ ] Failed jobs by type:
  ```sql
  SELECT job_type, count(*), max(created_at)
  FROM jobs WHERE status = 'failed'
  GROUP BY job_type ORDER BY count(*) DESC;
  ```
  (Adjust table/column names to what the schema actually says.)
- [ ] The "exhausted model iterations" loop: find the iteration cap (likely a
  hardcoded 5), pull 3–5 full failing transcripts, and determine WHY the
  loop never converges (bad tool results? impossible instruction? missing
  context? model too small?). The fix is designed from these transcripts,
  not guessed.
- [ ] Channel identity failures: which channel (Gmail/Boosend/Twilio) fails
  to resolve sender → lead, and how often.
- [ ] Inventory every process that POLLS an external system (BrokerBay,
  Gmail, Lofty/GHL, Telegram). Rule: exactly one poller per system. List
  the duplicates for retirement in step 4.
- [ ] Write findings to `hq/phase0-audit.md` (architecture, root causes,
  fix-in-place vs rewrite verdict per component — evidence first).

## 3. Lofty snapshot (read-only baseline)

Run with the new `growth-os` key from the box. Endpoint paths below are the
shapes from the screenshot/docs audit — **verify each against
developer.lofty.com before running** (it's Cloudflare-blocked from cloud
containers but reachable from the box; base is
`https://api.lofty.com/v1.0/`, header `Authorization: token $LOFTY_KEY`).

```bash
mkdir -p ~/phase0-evidence/lofty-snapshot-$(date +%F) && cd $_
export LOFTY_KEY=$(grep LOFTY_API_KEY /opt/realtor-agent/.env | cut -d= -f2)
H="Authorization: token $LOFTY_KEY"

curl -sS -H "$H" https://api.lofty.com/v1.0/me > me.json          # identity/account sanity check
# Full lead export WITH paging — loop until an empty page, save each page:
#   /v1.0/leads?offset=N&limit=100   (verify param names in docs)
# Then: pipelines + stages, tasks, smart-plan inventory, custom fields,
# webhook subscriptions currently registered (who else is listening?).
```

- [ ] All responses saved raw (JSON) into the dated snapshot directory, then
  committed to a private location (NOT this repo if it contains PII —
  the engine's document storage or an encrypted archive).
- [ ] **Reconcile the count**: Lofty lead total vs the engine's "120 leads" vs
  the Telegram bot's SQLite. Decide which system has the real book of
  record and record the verdict in `hq/phase0-audit.md`.
- [ ] Record which pipelines/stages/custom fields exist natively — this
  feeds directly into freezing `hq/CRM-DATA-DICTIONARY.md` (§6.1).

## 4. Fixes (only after 1–3 are captured)

- [ ] Agent loop fix per the transcript evidence; add unsupported-job-type
  handling (unknown type → `blocked` + Telegram alert, never a silent
  retry loop).
- [ ] Healthchecks on every container (`HEALTHCHECK` or systemd watchdog).
- [ ] Structured error alerts → Telegram via the **outbox pattern** (one
  polling process owns the token; everyone else inserts rows).
- [ ] **DB restore test**: restore the step-0 backup into a scratch database
  and verify row counts. An untested backup is a hope, not a backup.
- [ ] Staging vs prod split (separate compose project + DB, staging bot
  token).
- [ ] Retire double-acting automations found in step 2 (one BrokerBay
  poller only; old Lofty-writing agents disabled once their keys are
  revoked).
- [ ] **Mortgage-calculator lead leak** (two-line fix, week 1 per plan §5):
  `web/js/config.js` `FORM_ENDPOINT` is empty so leads fall back to
  `mailto:` — point it at the engine's intake endpoint once that endpoint
  exists; until then at minimum change the mailto to a monitored address.

## 5. Exit-gate measurement

- [ ] Define "clean run": a test conversation that completes with no failed
  jobs, no exhausted-iteration errors, no unhandled types, correct lead
  attribution.
- [ ] Run ≥20 scripted test conversations across channels (Gmail, SMS,
  WhatsApp, voice webhook). Gate: **≥19/20 clean (≥95%)**.
- [ ] Zero unhandled job types over a 72h observation window.
- [ ] Lofty baseline snapshot committed + reconciliation verdict written.
- [ ] Only then: flip the plan's inbound-auto decision to armed for Phase 2.

## Inputs needed from Ray during this phase

From plan §9.1 — the ones Phase 0/1 actually block on:
1. Mint the `growth-os` Lofty key (Settings → Integrations → API) → box `.env`.
2. Team roster: names, roles (buyer's agent / showing partner / admin-TC),
   Telegram IDs, what each may receive.
3. Location of the signed VOW/PropTx agreement documents.
4. Answers to the key-audit question: which of `rex` / `new claw` /
   `openclaw` / "Lovable" integrations, if any, are still wanted.
