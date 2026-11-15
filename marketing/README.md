# Ray's Marketing OS

One orchestrator, seven teams, a loop instead of a funnel, and nothing goes live until Ray approves it.

## How it runs

```
Mon 5:32   rayrocket weekly content brief   reads last week's loop feed, picks 6 topics
Mon/Wed/Fri 7:39  rayrocket content pack    long-form outline, carousel, posts
Daily 6:47 Daily Video Coach                today's 3 hooks and scripts
Mon/Wed/Fri 8:27  Marketing Approval Desk   compliance check, Canva design, approval request in Slack
        Ray reacts in Slack #agent-marketing: check mark, x, or a reply with changes
Daily 12:12, 17:12, 20:12  Marketing Publisher   schedules approved pieces in Metricool
Daily 7:05 Viktor                           LEADS lines from HighLevel in #agent-marketing
Sun 18:41  Marketing Analytics Loop         Metricool + leads + deals -> loop feed -> Monday's brief
Weekdays 7:52  Morning brief                one page: what worked, what's booked, what's waiting on Ray
```

## Where things live

| Thing | Place |
|---|---|
| Knowledge base (24 files) | `marketing/knowledge/`, mirrored in Airtable table MOS Knowledge |
| Team roster (36 roles) | `marketing/agents/` |
| Runbooks for the scheduled tasks | `marketing/routines/` |
| Email sequences, win-back, lead magnets (drafts) | `marketing/email/` |
| Posts, leads, deals | Airtable base "Real Estate Marketing Platform": MOS Posts, MOS Leads, MOS Deals |
| Approvals and interrupts | Slack #agent-marketing |
| Scheduling and post analytics | Metricool brand "rayahmadi" |
| Leads, email sending, consent | HighLevel, through Viktor |
| Meta lead ads | Ad Advisor, read only |
| Calls held and what people asked | Zoom for Claude recaps, read only |
| Lead counts when Viktor has not reported | Gmail lead notifications, read only |

## Changing how it behaves

- Voice, offers, rules, compliance: edit the file in `marketing/knowledge/` and the matching MOS Knowledge row.
- What a scheduled task does: edit its runbook in `marketing/routines/` and push. The task reads the runbook on every run.
- The three Marketing tasks fire into one long-running Claude Code session, because that session holds the Slack, Metricool and Airtable connections. If that session is archived, re-create the three tasks from a session that has those connectors.

## Not live yet

See the open items in the hand-off message of 2026-11-15: Ad Advisor's Meta reconnect, Viktor's HighLevel connection, an inbox connection for comments and DMs, Google Drive linked inside Metricool for video files, and the `[Ray to confirm]` items listed in MOS Knowledge ("Needs Ray" column).
