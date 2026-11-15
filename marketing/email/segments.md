DRAFT for Ray's review. Nothing here is sent until Ray approves it and a person loads it into HighLevel.

# Segmenting rules

How a contact's HighLevel tags decide which email sequence they get, when they leave it, and when they are flagged as a hot lead.

This file is a specification for a person to build from. An AI does not create, change, publish or pause HighLevel workflows, import contacts, or change consent status.

The tag families seg-*, concern-* and timing-* are already used in HighLevel. The exact tag names below are proposed. [Ray to confirm: exact seg-*, concern-* and timing-* tag names as they exist in HighLevel]

---

## 1. Before anything else: consent

A tag never enrols a contact by itself. Consent is checked first, every time.

| Check | Rule |
|---|---|
| Express consent | The contact asked to hear from Ray (Move Planner opt-in, lead magnet form, investor list). Can be enrolled. |
| Implied consent, inquiry | Valid for 6 months from the inquiry. After that, no sequence without express consent. |
| Implied consent, client | Valid for 2 years from a purchase or contract with Ray. |
| Commented, followed, or found online | Not consent. Never enrolled. |
| Referral | One message only, and only if the referrer knows both sides and is named in it. Not a sequence. |
| Unsubscribed | Never enrolled in anything. Permanent until the person opts in again. |

Proof of consent stays in HighLevel. [Ray to confirm: HighLevel field or tag that records the consent basis and date]

---

## 2. Which seg-* tag puts a contact in which sequence

One contact is in one sequence at a time.

| Tag | Sequence | File | Call to action |
|---|---|---|---|
| seg-first-time-buyer | First-time buyer nurture, 5 emails | sequences-first-time-buyer.md | Free home plan through the Move Planner |
| seg-newcomer | Newcomer family nurture, 5 emails | sequences-newcomer-family.md | Free home plan through the Move Planner |
| seg-move-up-seller | Move-up seller nurture, 5 emails | sequences-move-up-seller.md | Pricing and move plan conversation |
| seg-investor | Investor nurture, 5 emails | sequences-investor.md | Ask for the cash flow sheet |
| seg-agent | Agent nurture, 5 emails | sequences-agent.md | Private conversation with Ray |
| seg-past-client | Past-client check-in, 2 emails | win-back.md, Part B | Reply to Ray |
| Any seg-* tag, silent 90+ days | Win-back, 3 emails | win-back.md, Part A | Reply, then the segment call to action |

Send timing for every nurture sequence: day 0, 2, 5, 9, 14, counted from the day the contact enters.

### If a contact has more than one seg-* tag

Use the first rule that matches:

1. seg-agent wins over everything. Agents get the agent sequence only and never a buyer, seller or investor sequence.
2. seg-past-client plus a new seg-* tag: Ray reviews before any sequence starts. A past client with a new plan gets a call, not a drip.
3. seg-newcomer wins over seg-first-time-buyer, so the family gets the Dari service line and the newcomer explanations.
4. seg-move-up-seller wins over seg-first-time-buyer. Someone who owns a home is not a first-time buyer.
5. seg-investor plus seg-move-up-seller: Ray decides. [Ray to confirm: which sequence an investor who is also selling their own home should get]
6. No seg-* tag: no sequence. The contact waits until the Move Planner answer or a person sets the tag.

---

## 3. What the concern-* tag does

The concern-* tag does not change which sequence a contact is in. It tells the person loading the sequence, and Ray before a call, which email answers the contact's main worry. Optional build: send the matching email in the day 2 slot and move the original day 2 email to the slot it left.

| Proposed tag | Segment | Email that answers it |
|---|---|---|
| concern-affordability | First-time buyer | Email 1 (real number) and email 2 (programs) |
| concern-wrong-time | First-time buyer | Email 3 (is this the wrong time) |
| concern-credit-history | Newcomer family | Email 2 (credit history, newcomer mortgage programs) |
| concern-language | Newcomer family | Email 1 and email 3 (terms explained, Dari service line) |
| concern-trust | Newcomer family | Email 4 (who does what) |
| concern-sell-or-buy-first | Move-up seller | Email 1 (sell first or buy first) |
| concern-two-homes | Move-up seller | Email 3 (carrying two homes) |
| concern-pricing | Move-up seller | Email 2 (how I price a home) |
| concern-cash-flow | Investor | Email 1 and email 2 (cash flow sheet, assumptions) |
| concern-legal-units | Investor | Email 3 (is the unit legal) |
| concern-split | Agent | Email 4 (figures on the call only) |
| concern-support | Agent | Email 3 (coaching from live deals) |
| concern-tools | Agent | Email 2 (ARIA and PROPEL) |
| concern-switching | Agent | Email 4 (switching without losing clients) |

---

## 4. What the timing-* tag does

| Proposed tag | Meaning | What happens |
|---|---|---|
| timing-0-3-months | Timeline under 90 days | Hot lead. Flag for Ray at once. See section 6. |
| timing-3-6-months | 3 to 6 months | Nurture sequence as written. |
| timing-6-12-months | 6 to 12 months | Nurture sequence as written. |
| timing-12-plus-months | More than a year | Nurture sequence as written, then the weekly market email. |
| timing-unsure | Not sure yet | Nurture sequence as written. |

If a timing-* tag changes to timing-0-3-months while a contact is in a sequence, the hot lead rule applies from that moment.

---

## 5. Decision style

Each nurture email has four alternate opening sentences, one per Move Planner decision style: Numbers, Proof, Speed, Ease.

- If the contact has a decision style from the Move Planner, use the matching opening sentence. [Ray to confirm: HighLevel tag or field that stores the decision style]
- If there is no style on file: Ease for newcomer families, Numbers for investors (from audience/decision-styles.md). The first-time buyer, move-up seller and agent sequences are drafted in Ease. [Ray to confirm: default decision style for first-time buyers, move-up sellers and agents]
- Proof openings are not loaded until Ray replaces the placeholder with a real example that has written consent. Until then, contacts with the Proof style get the default opening.
- One style per email. Do not mix.

---

## 6. Hot leads

A contact is a hot lead when any one of these is true:

1. Timeline under 90 days (timing-0-3-months, or they say so in a reply, a form or a message).
2. Pre-approved for a mortgage. [Ray to confirm: tag or field that records pre-approval]
3. They ask for a call, in any channel and in any words.

What happens:

- Flag it at once so Ray calls. In Slack #agent-marketing this is an interrupt: first line starts with "INTERRUPT:", then what happened, then what Ray should do. First name and last initial only. No phone number, email or address.
- The contact leaves or skips the nurture sequence so automated email does not run over a live conversation. [Ray to confirm: hold hot leads out of nurture until Ray has called, or let email 1 send first]
- The hot lead is counted in Airtable "MOS Leads" by source and segment. Counts only.
- After Ray's call, Ray or Diana decides what the contact gets next. Automation does not decide.

Signals that are close but not hot by this rule (for Ray to review, not an interrupt): replied MOVING to a win-back email, has already found their next home, has a specific investment property in mind.

---

## 7. When a contact exits a sequence

A contact leaves their sequence the moment any of these happens. Remaining emails are not sent.

| Trigger | What happens next |
|---|---|
| Books a call (buyer plan call, seller conversation, agent conversation) | Exit. Ray takes over. No more automated email until Ray or Diana says so. |
| Replies to any email | Exit. A person reads the reply. An AI may draft an answer for Ray's approval; nothing is sent automatically. |
| Unsubscribes, or writes "stop" in any form | Exit everything. Never message again. Hand to the CRM owner to confirm removal. Honoured within 10 business days at the latest. |
| Becomes a hot lead (section 6) | Exit. Flag for Ray. |
| Completes the Move Planner or asks for a cash flow sheet | This is the call to action being taken. Exit, and Ray or the team follows up in person. [Ray to confirm: tag that marks Move Planner completion] |
| Asks for a human | Exit. Hand to Ray or Diana the same hour. |
| Sends an angry or upset reply | Exit. Flag with the text and a suggested calm reply. Nothing is sent as final. |
| Email bounces | Exit. A person checks the address. |
| Consent expires (6 months after an inquiry with no express consent) | Exit. No further email without express consent. |
| Tag changes to a different seg-* | Exit the current sequence. The new sequence starts from email 1 only after a person confirms the change. |
| Finishes email 5 with no action | Moves to the weekly market email for their segment, if consent is still valid. |

### Entering win-back

A contact enters the win-back sequence (win-back.md, Part A) when all of these are true:

- They have a seg-* tag other than seg-past-client.
- No open, click, reply or booking for 90 days or more.
- They are not in another sequence.
- Consent is still valid on the day of each send.
- They have not been through win-back before. [Ray to confirm: tag for contacts who finish win-back with no response]

Win-back exits use the same table above. After win-back email 3 with no response, the contact receives no further sequences and stays in HighLevel. Nothing is deleted.

---

## 8. Every email, every sequence

- Sender block at the end, in this order:
  - Ray Ahmadi, Broker | Ray Homes Real Estate | eXp Realty, Brokerage
  - [Ray to confirm: mailing address]
  - Unsubscribe: {{unsubscribe_link}}
- CASL also asks for a contact method. [Ray to confirm: whether a phone number or reply-to email is added to the sender block]
- [Ray to confirm: exact registered brokerage name, for example "eXp Realty, Brokerage"]
- One segment and one call to action per email.
- No em dashes, no banned phrases, no invented figures, no advice on mortgages, tax or law.
- Ray approves each email in Slack #agent-marketing before a person loads it.

## 9. Open questions for Ray

1. Contacts who have already completed the Move Planner should not be asked to take it again. The buyer and newcomer sequences as drafted assume the contact has not completed it. [Ray to confirm: what buyers who already finished the Move Planner should be sent instead]
2. Tracking: each link should carry a UTM so calls booked can be credited to the email. [Ray to confirm: UTM naming for email links]
