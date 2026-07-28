---
description: Turn your reaction to a render into editing rules that stick
argument-hint: [what you thought of it]
allowed-tools: Read, Write, Bash(python3:*), Task
---

# Learn from: $ARGUMENTS

## 1. Classify

Launch the **critic** agent with what the user said. It returns
`(aspect, direction, quote)` triples from a fixed vocabulary, plus anything it
could not map.

Do not classify in the main thread and do not invent corrections outside the
vocabulary — `reelforge.cli feedback` rejects them, deliberately.

## 2. Record

```bash
python3 -m reelforge.cli feedback \
  --note captions:too-low:"the captions sat too low" \
  --note zooms:too-many:"way too many zooms" \
  [--edl path/to.edl.json]
```

Every note is appended to `memory/decisions.jsonl`, then anything now heard
**twice** is promoted into `memory/playbook.md` with its quote attached as the
reason.

## 3. Report

Say plainly:

- **What changed now** — which rule, from what to what, and in plain language
  ("push-ins will now be spaced 4.5s apart instead of 3.0s")
- **What is waiting** — corrections heard once, which will apply if they say it
  again. This is the part people miss: nothing changes the first time, and
  without being told, they will think it was ignored.
- **What could not be mapped** — and whether that is a gap in the vocabulary or
  something ReelForge does not control

Then offer to re-render an affected EDL so they can see the difference
immediately. `compose` reads the playbook fresh every run, so a re-compose
picks up the new rules with no extra step.

## Notes

The threshold is two on purpose. Every clip has something slightly wrong with
it; a playbook that swings on one reaction never settles. Two is where a
preference has distinguished itself from a mood.

To undo a rule, edit `memory/playbook.md` directly — it is a plain text file and
each line carries the reason it exists. Deleting a line reverts that rule to the
default. Nothing in the system objects to being overruled.
