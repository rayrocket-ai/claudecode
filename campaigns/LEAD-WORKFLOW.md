# Lead workflow: what happens after a lead comes in

Ray asked for this on 2026-11-15: a workflow after leads come in, and
staying on top of them. This file is what the "Lead desk" scheduled run
follows. It holds rules and templates only.

PRIVACY: this repo is public. Never write a lead's name, phone, email or
message into any tracked file. Lead details live in Gmail and the CRM only.

## Where leads arrive (all land in Ray's Gmail)

| Source | Sender | Subject contains | Notes |
|---|---|---|---|
| Website contact form (the page every YouTube ad links to) | `mg.msgsndr.us` ("Ray Homes Real Estate - Internal Alert") | "New Contact Us form submission" | Sent by GoHighLevel. Has name, email, phone, message. Does NOT say which ad or listing sent them. |
| Lofty CRM (rayahmadi.com home search) | `no-reply@lofty.com` | "New Buyer Lead Alert", "New Seller Lead", "Pending Lead Showing Request" | "A Lead was Assigned to You" is a team hand-off, count it but do not draft. "Saved a Listing" is a signal, not a new lead. |
| REALTOR.ca | `lead@realtor.ca`, `noreply@leads.realtor.ca` | "General inquiry for" | The subject names the listing. |
| Facebook lead forms | Pabbly / Facebook | lead alerts | Pabbly is broken since Nov 9. Until Ray reconnects it, form leads sit in the Page's Leads Center and do not reach Gmail. Remind him. |

Gmail search for new leads (run each time, last 2 days, not yet logged):

    (from:mg.msgsndr.us subject:"Contact Us form submission") OR
    (from:no-reply@lofty.com subject:("Lead Alert" OR "Showing Request")) OR
    (from:(lead@realtor.ca OR noreply@leads.realtor.ca) subject:inquiry)
    newer_than:2d -label:Lead/Logged

## Labels (already created in Gmail)

- `Lead/Logged` (Label_12): the run has seen this lead.
- `Lead/Reply drafted` (Label_13): a reply draft is waiting in Drafts.
- `Lead/Overdue` (Label_14): no human answer within the time limit.
- `Lead` (Label_6): Ray's own label. Add it too, never remove it.

## Steps for each new lead

1. Read the thread in full. Add `Lead` and `Lead/Logged`.
2. Work out the listing: REALTOR.ca subjects name it; for the contact form
   read the message. If it is not clear, treat as "listing unknown".
3. Decide who answers:
   - Contact-form leads, and any inquiry on the four advertised listings
     (34 Buttonleaf, 53 Alpha, 85 Sidney, 97 Jackman): draft a first reply
     for Ray (step 4).
   - Other listings and rentals: Ray forwards these to his team. Do not
     draft. Only check that the thread was forwarded or answered.
4. Draft the first reply as a Gmail draft addressed to the lead's email,
   with Ray's Gmail signature switched on. Add `Lead/Reply drafted`. Never
   send. If the lead gave only a phone number, skip the draft and tell Ray
   to call or text.
5. Tell Ray in the chat, one line per lead: source, listing, what they
   asked, and "reply is in Drafts" or "phone only, call". Names and numbers
   may appear in the chat, never in the repo.

## Time limits ("staying on top")

- Between 8 AM and 9 PM Toronto time a lead should get a human answer
  within 2 hours. An answer means: a sent reply in the thread, a forward to
  a team member, a team reply such as "added to Lofty, called", or the
  draft no longer sitting in Drafts.
- Past 2 hours with none of these: add `Lead/Overdue` and put it first in
  the message to Ray.
- No reply from the lead after 2 days: draft follow-up 1. After 5 days:
  draft follow-up 2. After that, stop and leave it to the CRM drip.
- When an answer is seen, remove nothing; the labels are the history.

## Prices and facts

Take the price from the newest REALTOR.ca "is live" email for that address
at the time of drafting. If there is any doubt (a relist or a signing in
the last few days), leave the number out and write "I will send you the
price sheet". Facts come from campaigns/<slug>/plan.md. Never claim a pool
for 53 Alpha; say "pool-sized yard".

## Reply templates (Ray's voice: short sentences, no "just", no em dashes)

### First reply, listing known

Subject: <street address>: price, address and tour

    Hi <first name>,

    Thanks for reaching out about the <town> home.

    Here is what you asked for.
    Address: <full address>
    Price: <price>
    <two facts from plan.md, one line>

    I can show it to you this week. Which day works, and are evenings or
    the weekend better for you?

    Call or text me any time.

### First reply, listing unknown (came from an ad, no listing named)

Subject: Your home inquiry

    Hi <first name>,

    Thanks for reaching out. Which home caught your eye?

    These are the ones I have on the market right now:
    - Stouffville, over 4,000 sq ft finished, separate-entrance lower level
    - Woodbridge, pool-sized lot, walkout lower level with its own entrance
    - Bowmanville, freehold, no condo fees, 3 bed and 2 full bath
    - West Woodbridge, two kitchens, big backyard and deck

    Tell me which one and I will send the price, the address and a time to
    see it. Or call or text me and we can sort it out in two minutes.

### First reply, general buyer or seller inquiry

    Hi <first name>,

    Thanks for your message about <what they asked, in their words>.

    Three quick questions so I send you the right homes: which area, what
    price range, and when would you like to move?

    Call or text me any time. I can also set up a search that emails you
    new listings the day they come out.

### Follow-up 1 (day 2)

    Hi <first name>,

    Checking in on the <town> home. It is still available today. Would you
    like to see it this week?

### Follow-up 2 (day 5)

    Hi <first name>,

    Last note from me on the <town> home. If the timing is not right, tell
    me what you are looking for and I will watch the market for you.

## Daily numbers

The 7 AM ADMAX run adds one line: new leads yesterday by source, how many
were answered inside 2 hours, how many are overdue now.

## What would make this instant (needs Ray's GoHighLevel, not buildable from here)

The API token saved for this environment is refused for workflows, forms
and pipelines, so the steps below have to be done inside GoHighLevel by Ray
or his team. About 15 minutes.

1. Automation > Workflows > open the workflow that sends "New Contact Us
   form submission".
2. Right after the trigger add: Send SMS to the contact: "Hi {{contact.first_name}},
   Ray Ahmadi here. Got your message. Which home were you asking about? I
   can send the price and address right now."
3. Add: Send Email to the contact with the "listing unknown" template above.
4. Add: Create Task for Ray, "Call new lead", due in 15 minutes.
5. Add: Create Opportunity in the buyer pipeline, first stage.
6. In the internal alert email, add these lines so each lead shows which ad
   sent it: UTM campaign {{contact.attributionSource.utmCampaign}} and UTM
   content {{contact.attributionSource.utmContent}}. The ads already carry
   these tags (for example 85_sidney_inmarket).
7. Add Wait 1 day > If no reply > SMS follow-up; Wait 3 days > email
   follow-up 2.

Also: reconnect the Pabbly Facebook-leads workflow, or replace it with
GoHighLevel's own Facebook Lead Form trigger so form leads enter the same
workflow.

## Paste-ready prompt for GoHighLevel's AI workflow builder

Ray asked on 2026-11-15 for this to be built by logging in. This session
runs in the cloud with no browser signed in to GoHighLevel, and passwords
are never taken in chat, so the build happens on Ray's side: Automation >
Workflows > Create Workflow > build with AI, paste the text below, review,
publish. A Claude session on Ray's own computer (desktop app or the Chrome
extension), where he is already signed in, can also click it through from
this same text.

    Create a workflow named "Website lead: instant reply and follow-up".

    Trigger: Form Submitted, form = the website Contact Us form.

    Step 1. Send SMS to the contact:
    "Hi {{contact.first_name}}, Ray Ahmadi here from Ray Homes Real Estate.
    Got your message. Which home were you asking about? I can send the
    price and address right now. Reply STOP to opt out."

    Step 2. Send email to the contact. Subject: "Your home inquiry". Body:
    "Hi {{contact.first_name}}, thanks for reaching out. Which home caught
    your eye? Tell me which one and I will send the price, the address and
    a time to see it. Or call or text me and we can sort it out in two
    minutes. Ray Ahmadi, Ray Homes Real Estate, eXp Realty, Brokerage."

    Step 3. Send an internal notification email to Ray with the contact's
    name, phone, email, message, UTM campaign
    ({{contact.attributionSource.utmCampaign}}) and UTM content
    ({{contact.attributionSource.utmContent}}).

    Step 4. Add the tag "website-lead".

    Step 5. Create a task assigned to Ray Ahmadi titled "Call new website
    lead", due in 15 minutes.

    Step 6. Create an opportunity in the buyer pipeline, first stage,
    status open, named with the contact's full name.

    Step 7. Wait 1 day. If the contact has not replied, send SMS:
    "Hi {{contact.first_name}}, Ray here. Still happy to send the price and
    address. Which home was it?"

    Step 8. Wait 3 days. If the contact has not replied, send email:
    "Hi {{contact.first_name}}, last note from me. If the timing is not
    right, tell me what you are looking for and I will watch the market
    for you. Ray"

    Stop the workflow for a contact as soon as they reply by SMS or email.
