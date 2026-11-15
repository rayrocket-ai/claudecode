# Routine: Marketing Analytics Loop

Team 7: Post Analyst, Call Tracker, Revenue Tracker, Email Analyst, Loop Feeder.
Schedule: Sundays 6:41 PM Toronto, before Monday's content brief. Time limit 20 minutes.
Read only everywhere except Airtable. Never post in Slack.

## Step 1. Post Analyst
Last 7 days, for instagram (posts, reels), tiktok (posts), youtube (videos), linkedin (posts), facebook (posts, reels): getAnalyticsAvailableMetrics for the network and connector, then getAnalyticsDataByMetrics for views, reach, likes, comments, shares, saves per post. Match each post to its MOS Posts row by caption and date; update the metric fields, Post URL and "Metrics updated". A post with no row (Ray posted by hand): create a row with Status "Published" and Notes "posted outside the desk". At most 40 posts.

## Step 2. Call Tracker
Read #agent-marketing for the last 8 days. Viktor reports HighLevel leads in lines starting "LEADS <YYYY-MM-DD> |". For each line not yet in MOS Leads (match on Entry) create rows: Entry "<date> <source>", Date, Source, Segment, New leads, Hot leads, Calls booked, Post or ad credited, Reported by "Viktor (HighLevel)". 
Gmail fallback, used for any day with no LEADS line: search Ray's Gmail (newer_than:8d) for lead notification emails (HighLevel or LeadConnector new lead and form submission notices, Meta lead form notices, Move Planner submissions, website form emails, booked appointment confirmations). Count them per day and per source, and create MOS Leads rows with Reported by "Claude" and Notes "counted from Gmail notifications". Read only: never send, reply, label, archive or delete. Copy no names, phone numbers, emails or message text into Airtable; counts only. If neither Viktor nor Gmail shows anything, record "Leads and calls: not tracked yet" with the reason.

## Step 3. Meta lead ads (Ad Advisor)
At most ONE read call: campaign performance for account 732663023528570, last 7 days (result count, cost per result, spend). If the response says Meta needs reconnecting or the data is a stale snapshot, do not use the numbers; write "Meta ads: not tracked, Ad Advisor needs Meta reconnected". Never a write call.

## Step 4. Revenue Tracker
From MOS Deals: signed clients and closings in the last 30 days by Source and by "Post or ad credited". Where a lead or deal credits a post, add to that post's "Leads attributed" and "Calls attributed". Follow the crediting order in reporting/metrics-and-attribution. Never guess a source.

## Step 5. Loop Feeder
Rewrite the Content of the MOS Knowledge row "reporting/loop-feed" (keep the title and the Format section; replace Status and body), set Updated to today, and mirror the same text into marketing/knowledge/reporting/loop-feed.md, commit and push to the session branch:
- Week covered.
- Make more of: up to 3 topics, formats or hooks, with the numbers that earned it.
- Make less of: up to 3, with the numbers.
- What brought calls and clients: by source and by post or ad, or "not tracked yet" with the reason.
- Questions the audience asked this week (themes only).
- One test for next week.
- Approval flow health: pieces sent, approved, rejected, expired this week.

## Final message
Three lines: the top "make more of" item with its numbers, calls booked this week or "not tracked yet", and any connection that needs fixing.
