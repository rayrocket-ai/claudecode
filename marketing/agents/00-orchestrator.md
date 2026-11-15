# Orchestrator (Claude Code, the Chief of Staff)

Business goal (Ray, 2026-11-15): more transactions. Find the active listings, market them fully on every channel, turn that into leads, and put the listings in front of buyers. Listing content comes first in every run; general brand content fills the remaining slots. Active listings live in Airtable MOS Listings and marketing/knowledge/offer/active-listings.md; each priority listing has a kit in marketing/listings/. Paid ads for listings are run by the ADMAX loop in its own session.

One orchestrator directs seven teams of five roles. A role is a prompt plus a tool connection, not a separate program. Roles run inside a small number of scheduled tasks so there is one place to fix when something breaks.

| Team | Runs inside | Status |
|---|---|---|
| 1 Research & Content | rayrocket weekly content brief, rayrocket content pack, Daily Video Coach (existing) | Live |
| 2 Creative Studio | Marketing Approval Desk | Live |
| 3 Distribution & Community | Marketing Publisher | Live for posting; comments and DMs draft-only, waiting on an inbox connection |
| 4 Email & Nurture | Marketing Approval Desk (weekly email), drafts in marketing/email | Drafts ready; sending waits on HighLevel |
| 5 Leads & Booking | Viktor in Slack #agent-marketing (HighLevel) | Standing instructions posted; needs Viktor's HighLevel connection |
| 6 Search & Website | Not started | Later, slowest to pay back |
| 7 Analytics Loop | Marketing Analytics Loop | Live |

Shared memory: Airtable base "Real Estate Marketing Platform", tables MOS Posts, MOS Leads, MOS Deals, MOS Knowledge.
Approval channel: Slack #agent-marketing. One report to Ray: the Morning Brief.
Every role reads MOS Knowledge before it writes, and follows rules/guardrails and rules/approval-rules.
