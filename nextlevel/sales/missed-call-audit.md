# The free missed-call audit

**Note, 2026-11-15:** the audit is now a secondary, optional tactic. It is kept as drafted, and its legal flags are unchanged. The primary lead source is inbound content (see `nextlevel/content/`).

Draft for Ray to approve. Builds on Ray's existing audit plan: call 20 GTA agents on weekdays between 7 and 9 PM, log each call, send the audit email within 24 hours.

The audit is the proof step in the sales machine. It shows an agent what happened on their own line. It does not need a claim from us.

## Before the first call: three checks

1. **CASL.** The audit email is a commercial message. Agents who asked for an audit on the sales page have given consent. For agents who did not ask, Ray needs a consent basis before any email or text is sent. [Ray to confirm with counsel: the consent basis for a one-to-one audit email to an agent's published business address]
2. **Calling rules.** These are calls to business lines for a business purpose. [Ray to confirm with counsel: any calling rules that apply to the audit calls and the voice note]
3. **Honesty.** The caller never pretends to be a buyer or seller. If the agent picks up, say who is calling and why.

No one is added to a marketing list because of an audit. One call, one email, one follow-up only if they reply.

## 1. Who to call

- 20 GTA real estate agents per round.
- Start with agents who asked for the audit through the sales page.
- Then agents who advertise a direct business number on their own website, Google Business Profile or listing signs.
- Solo agents and small teams first. They answer their own phones.
- Skip agents on Ray's own team, agents Ray is in an active deal with, and anyone who has asked not to be contacted.

## 2. When

- Weekdays, 7 to 9 PM.
- One call per agent. No repeat dialing.
- Use the Next Level number, not a blocked number.

## 3. How the call goes

1. Dial the published business number.
2. Count the rings.
3. Note what happens: a person, voicemail, full voicemail box, a message service, nothing.
4. If voicemail: leave the voice note in section 6. Note whether the greeting gives another way to reach them.
5. If the agent answers: use the live script in section 6.
6. Start a timer. Log if and when a callback or text comes in, up to the time the audit email is sent.
7. Fill the log before the next call.

## 4. What to log

Keep the log in a private sheet or in HighLevel. Not in Slack. Not in shared channels.

| Column | What goes in it |
|---|---|
| Audit # | 1 to 20 |
| Date | Date of the call |
| Time called | To the minute |
| Agent | First name and last initial |
| Brokerage | As published |
| Number source | Sales page request, own website, Google profile, sign |
| Consent basis | Requested audit, or as confirmed with counsel |
| Rings | Count before answer or voicemail |
| Outcome | Answered live, voicemail, mailbox full, message service, no answer |
| Greeting | Named the agent? Gave another contact? Yes or no for each |
| Voice note left | Yes or no |
| Text back received | Yes or no, and minutes after the call |
| Callback received | Yes or no, and time |
| Audit email sent | Date and time (within 24 hours of the call) |
| Reply | None, replied, booked a call, asked to stop |
| Pipeline stage | Lead, Audit sent, Call booked |
| Notes | One line. Facts only. |

After 20 calls, count: how many answered live, how many went to voicemail, how many called or texted back before the email went out. Those are real numbers Ray can use, described exactly as what they are: "we called 20 GTA agents on weekday evenings."

## 5. The audit email

Send within 24 hours of the call. One version for voicemail, one for a live answer. Fill every field from the log. Do not round or estimate.

### Version A: the call went to voicemail

**Subject:** I called your line at {{audit_time}} yesterday

Hi {{contact.first_name}},

Ray Ahmadi here. I am a broker with Ray Homes Real Estate, eXp Realty, in the GTA.

Yesterday at {{audit_time}} I called your business line, {{audit_number_called}}. Here is what happened:

- Rings before voicemail: {{audit_rings}}
- Outcome: {{audit_outcome}}
- Text back: {{audit_text_back}}
- Callback: {{audit_callback}}

I was not a buyer. If I had been, I would have been free to call the next agent.

I had the same gap in my own business. [Ray to confirm: true for Ray Homes, or reword] I fixed it with an AI receptionist that answers every call, asks the questions I would ask, and books the appointment. [Ray to add: real number from Ray Homes]

I am setting it up for 10 agents at a founding price. I can show you how it handles a call like mine in 15 minutes.

Book a time here: {{custom_values.nl_booking_link}}

Ray

Ray Ahmadi | Next Level
[Ray to confirm: business name and mailing address for Next Level]
Unsubscribe: {{unsubscribe_link}}

### Version B: the agent answered

**Subject:** Thank you for picking up last night

Hi {{contact.first_name}},

Ray Ahmadi here, the broker who called you at {{audit_time}} yesterday. You answered in {{audit_rings}} rings. Most evening calls I make to agents do not go that way. [Ray to add: real number from the audit log, or cut this sentence]

One question: what happens to that same call when you are in a showing?

I use an AI receptionist on my own line for those hours. It answers, qualifies and books. [Ray to add: real number from Ray Homes]

I am setting it up for 10 agents at a founding price. I can show you a live call in 15 minutes.

Book a time here: {{custom_values.nl_booking_link}}

Ray

Ray Ahmadi | Next Level
[Ray to confirm: business name and mailing address for Next Level]
Unsubscribe: {{unsubscribe_link}}

### Rules for the email

- One email per agent. A second message only if they reply.
- The subject line must be true. Use the real time.
- If the agent says stop, mark them do-not-contact that day.
- Ray approves the template once, and reads the first 20 before they send.

## 6. Voice note scripts

### If the call goes to voicemail

Keep it under 30 seconds. Speak slowly. Say the number twice.

"Hi {{first name}}, this is Ray Ahmadi. I am a broker with Ray Homes Real Estate at eXp Realty.

I am not calling about a listing. I am calling agents in the GTA this evening to see what happens when a new caller reaches their line. Yours went to voicemail at {{time}}.

I will send you a short note tomorrow with exactly what I saw. No cost.

You can reach me at [Ray to set: callback number for audits]. Again, [number].

Thank you."

### If the agent answers

"Hi {{first name}}, this is Ray Ahmadi. I am a broker with Ray Homes Real Estate at eXp Realty. Have I caught you at a bad time?

I will be quick. I am calling agents in the GTA this evening to see what happens when a new caller reaches their line. You picked up, which is more than most. [Ray: say this only if the log shows it is true]

I had a problem with missed calls in my own business and built a fix for it. [Ray to confirm: true for Ray Homes, or reword] May I email you a short note on what I found tonight?"

If yes: "What is the best email for you?" Log it. Log the consent, the date and the time.

If no: "Understood. Thank you for your time. Have a good evening." Mark do-not-contact. Send nothing.

### If recorded as a voice message to send with the email

Only for agents who asked for the audit.

"Hi {{first name}}, Ray Ahmadi here. You asked for a missed-call audit. I called your line at {{time}} yesterday. It rang {{rings}} times and went to {{outcome}}. The full note is in this email. If you want to hear how an AI receptionist would have handled that call, book 15 minutes with me using the link below."

## Next step

Ray confirms the three checks at the top with counsel, then approves the email and the scripts. Diana sets up the log.
