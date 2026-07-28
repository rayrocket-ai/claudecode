# memory/

Your taste, persisted. This is the only directory here that cannot be
regenerated from source footage and git — back it up (see
`docs/SERVER-RUNBOOK.md`).

Nothing in it is tracked except this file and the `.example.md` templates. The
live files are yours and differ per machine.

## What lives here

**`playbook.md`** — the rules the composer reads at render time. Generated, but
plain text and safe to edit by hand. Every learned line carries the quote it
came from and how many times you said it:

```
min_punch_gap: 6.0  # from feedback 2026-07-28: space the push-ins further apart -- "seriously, fewer zooms" (2x)
```

To overrule something, delete the line. It reverts to the default. Nothing in
the system objects to being overruled.

**`decisions.jsonl`** — append-only log of every correction you have made. The
raw history; `playbook.md` is what is distilled from it.

**`applied.json`** — how many occurrences of each correction have already been
folded into the playbook. Without it, re-running would compound every past
correction on every run and the numbers would drift to their limits.

**`provenance.json`** — the reason attached to each rule, kept separately so it
survives the playbook being regenerated.

**`style-profile.md`** — free-form notes for the *agents* rather than the
composer. The editor and producer read this before choosing anything. Use it for
things that are not numbers: what your channel is about, who watches it, hooks
that work, subjects you avoid. Copy `style-profile.example.md` to start.

## How learning works

Nothing becomes a rule the first time you say it.

One reaction to one clip is a mood — every clip has something slightly wrong
with it, and a playbook that swings on a single remark never settles. Say the
same thing about a **second** render and it becomes a rule.

`/reel-feedback` always reports what is still waiting on a second mention, so a
correction never silently disappears.

The vocabulary of corrections is fixed and lives in `core/feedback.py`. The
model classifies what you said into it; the arithmetic is code. A model allowed
to rewrite its own rules freely produces a system that changes unpredictably and
cannot explain itself, which is the thing this directory exists to prevent.
