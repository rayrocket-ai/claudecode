DRAFT for Ray's review. Nothing here is sent until Ray approves it and a person loads it into HighLevel.

# Win-back sequence and past-client check-in

Two separate sequences live in this file:

- Part A: a 3-email win-back for leads who have been silent for 90 days or more.
- Part B: a 2-email past-client check-in (home anniversary, market update).

Merge fields: {{contact.first_name}} and {{unsubscribe_link}} are HighLevel fields. [Ray to confirm: exact HighLevel merge field names]

---

# Part A: win-back (silent 90+ days)

- Who gets it: a contact with a seg-* tag who has not opened, clicked, replied or booked in 90 days or more, and who has finished or left their nurture sequence. See segments.md.
- Consent basis: check it before every enrolment. Implied consent from an inquiry lasts 6 months from the inquiry. A contact who is silent past that point with no express consent on file does not get this sequence. The person loading this confirms the consent proof in HighLevel. An AI never changes consent status.
- Segment: each send goes to one segment at a time. The emails below use two segment fields that a person sets per segment in HighLevel:
  - [segment topic]: "your first home", "your family's home in Canada", "your move", "your next investment property", "your real estate business"
  - [segment call to action], from the matching offer/ file:
    - First-time buyer and newcomer family: Start your free home plan here: [Ray to confirm: Move Planner link]
    - Move-up seller: Book your pricing and move plan conversation: [Ray to confirm: seller booking link]
    - Investor: Ask for your cash flow sheet here: [Ray to confirm: investor cash flow sheet link or keyword]
    - Agent: Book a private conversation here: [Ray to confirm: agent booking link]
- Exit: any reply, any booking or any unsubscribe ends the sequence at once. A reply is read by Ray or Diana, not answered by automation.
- After email 3 with no response: the contact stays in HighLevel and receives no further sequences. Nobody is deleted. [Ray to confirm: tag for contacts who finish win-back with no response]
- Compliance check: PASS on rules 1 to 3, 5 to 8, 11 and 12. No figures are quoted.

## Win-back email 1

- Send timing: Day 0 (first day the contact qualifies as silent for 90 days)
- Subject line: Where did you land on [segment topic]?
- Preview text: One word back is enough.
- Call to action: Reply with one word

```text
Hi {{contact.first_name}},

A while back you asked me about [segment topic]. Plans change, and I would like to send you what fits where you are now.

Which one is closest today?

MOVING: you are still planning to go ahead.
LATER: it is on hold for now.
DONE: you have already made your move.

Reply with one word and I will take it from there. If it is MOVING, we will talk and get your plan up to date. If it is LATER, I will send you less and keep it useful. If it is DONE, congratulations, and I will stop the planning emails.

Reply to this email with MOVING, LATER or DONE.

Ray Ahmadi, Broker | Ray Homes Real Estate | eXp Realty, Brokerage
[Ray to confirm: mailing address]
Unsubscribe: {{unsubscribe_link}}
```

Handling replies (for the person in HighLevel): MOVING is a hot lead signal, flag it for Ray to call. LATER moves the contact to the weekly market email only. DONE ends all buyer or seller sequences; if they bought or sold with Ray, they move to the past-client list.

## Win-back email 2

- Send timing: Day 4
- Subject line: The one thing to settle first
- Preview text: It takes the guessing out of the rest.
- Call to action: The segment call to action

```text
Hi {{contact.first_name}},

When a plan stalls, it is usually because one question never got a clear answer.

[segment line]

Once that one question is settled, the rest of the plan falls into place. Until it is, every listing and every headline feels like a reason to wait.

We can settle yours in one step.

[segment call to action]

Ray Ahmadi, Broker | Ray Homes Real Estate | eXp Realty, Brokerage
[Ray to confirm: mailing address]
Unsubscribe: {{unsubscribe_link}}
```

[segment line], one per segment, set by the person in HighLevel so each email names one segment:
- First-time buyer and newcomer family: For most buyers it is the real number: what you can comfortably afford each month.
- Move-up seller: For most sellers moving up it is the order: sell first or buy first.
- Investor: For most investors it is the math: will the rent cover the costs.
- Agent: For most agents it is the leak: missed calls and slow follow-up.

## Win-back email 3

- Send timing: Day 10
- Subject line: Should I keep sending these?
- Preview text: Your call. One word keeps you on the list.
- Call to action: Reply KEEP

```text
Hi {{contact.first_name}},

I have not heard back, and I respect your inbox.

This is the last email in this series. After today I will stop sending you planning emails about [segment topic].

If you would like to keep hearing from me, reply KEEP. You will get my weekly market email: one topic, one sourced number and one next step.

If your plans are active again, reply MOVING and we will talk and get your plan up to date.

If you would rather not hear from me at all, the unsubscribe link below takes care of it, and it is permanent until you opt in again.

Reply KEEP to stay on the list.

Ray Ahmadi, Broker | Ray Homes Real Estate | eXp Realty, Brokerage
[Ray to confirm: mailing address]
Unsubscribe: {{unsubscribe_link}}
```

---

# Part B: past-client check-in

- Who gets it: contacts tagged seg-past-client, people who bought or sold with Ray.
- Consent basis: implied consent lasts 2 years from the purchase or contract. After that, express consent is needed. The person loading this confirms the consent proof and the closing date in HighLevel.
- Privacy: no address, price or deal detail appears in either email.
- Segment: past client. One call to action per email.
- Exit: any reply or unsubscribe ends the automation. Replies go to Ray.
- Compliance check: email 1 is PASS. Email 2 is open on rule 4 until Ray adds the figure, its source link and the month it covers.

## Past-client email 1: home anniversary

- Send timing: on the anniversary of the closing date, each year. [Ray to confirm: HighLevel field that holds the closing date]
- Subject line: Happy home anniversary, {{contact.first_name}}
- Preview text: A quick check-in on your home and your plans.
- Call to action: Reply with your answer

```text
Hi {{contact.first_name}},

Happy home anniversary. It has been {{years_in_home}} since your closing day, and I hope the home has been good to you and your family.

An anniversary is a good day for one question: is the home still the right fit for the next few years?

If yes, enjoy it. I am here when you need a contractor name, a property tax question pointed to the right person, or a second opinion on a renovation.

If something is changing, a growing family, a new job, a parent moving in, tell me and we will map out your options early. No decision needed.

Reply with one line: staying put, or something is changing.

Ray Ahmadi, Broker | Ray Homes Real Estate | eXp Realty, Brokerage
[Ray to confirm: mailing address]
Unsubscribe: {{unsubscribe_link}}
```

Notes: {{years_in_home}} is a placeholder for a calculated field, for example "one year" or "three years". [Ray to confirm: how the anniversary year is filled in HighLevel, or remove the phrase]. [Ray to add: one personal line per client, optional]

## Past-client email 2: market update

- Send timing: [Ray to confirm: how often past clients get the market update, for example twice a year]
- Subject line: What changed in [Ray to add: city or neighbourhood] this [Ray to add: month or season]
- Preview text: One number, where it comes from, and what it means for owners.
- Call to action: Ask for an updated value review of your home

```text
Hi {{contact.first_name}},

Here is one number worth knowing as a homeowner in [Ray to add: city or neighbourhood].

[Ray to add: one market figure with its source link and the month it covers, from TRREB, the Bank of Canada, CMHC, Statistics Canada or the municipality]

What it means for you as an owner: [Ray to add: one or two sentences of perspective, not advice]

One figure for a whole city does not tell you what your own home is worth today. That comes from recent sales of homes like yours, close to yours.

If you would like to know where your home stands, I will review the recent sales in your pocket of the market and walk you through them.

Reply with VALUE and I will prepare your review.

Ray Ahmadi, Broker | Ray Homes Real Estate | eXp Realty, Brokerage
[Ray to confirm: mailing address]
Unsubscribe: {{unsubscribe_link}}
```

Note: this email is not ready to load until all three [Ray to add] items in the body are filled. No figure is drafted here because every number needs a real source and the period it covers.
