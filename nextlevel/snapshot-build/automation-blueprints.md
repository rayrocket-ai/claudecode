# Next Level: automation blueprints

Draft for Ray, Diana and whoever builds. Written 2026-11-15. This is a build plan, not a record of what exists. Nothing here is switched on in a live account until Ray approves it.

Every recipe below is original to Next Level. None of it was taken from another company's snapshot, template, prompt or script. HighLevel facts come from the official pages listed in `research/platform-teardown.md` section f. Anything not confirmed there carries `[verify in HighLevel]`.

Order: the nine blueprints are in priority order for the Founding 10. Blueprints 1, 2, 4, 8 and 9 are Next Level Answer and come first. Blueprint 3 is built with them because web leads arrive from day one. Blueprints 5, 6 and 7 follow.

## Rules that apply to every blueprint

**Where it is built.** Build in NL Demo. Prove it on Ray Homes. Save it into the master snapshot only when it works there. Never build or test in a client account.

**Naming.** As in `saas-build-spec.md` section 3: workflows `NL 01 | Name`, custom values `nl_group_name`, custom fields `NL | Label`, tags `nl-group-value`.

**Merge fields.** Custom values are written `{{custom_values.nl_biz_name}}`. Contact custom fields are shown here by their label, for example `{{NL | Caller reason}}`, because HighLevel generates the real key from the label. Pick each one from the merge-field menu in the builder.

**House style for every message.** Plain words. Short sentences. No long dashes. None of the phrases on Ray's banned list in the brand voice rules. No promise of a result.

**Sender and STOP.** The client is the sender. Every text names the business. The first text in any sequence ends with "Reply STOP to opt out." Every email carries the sender name, `{{custom_values.nl_mailing_address}}` and an unsubscribe link.

**Sending window.** Every workflow that texts or emails a caller, lead or past client uses a sending window. PROPOSED default: 9:00 a.m. to 8:00 p.m., Monday to Saturday, in the client's time zone. [Ray to set: default sending hours] A message due outside the window waits for the window to open. The alerts that go to the client's own phone are internal notifications and are not held.

**Consent.** A message goes only to a contact who is not tagged `nl-do-not-contact` and whose `NL | Consent basis` fits the message: a reply to an inquiry the person made, or express consent, or implied consent with a date inside the period the law allows. Which basis fits which message: [Ray to confirm with counsel]. The build stores the basis and the date. It does not decide the law.

**Workflow settings, written in each workflow's description.** Re-entry on or off. Stop on response on, for any sequence longer than one message. Every trigger listed.

**NL 00 | Unsubscribe and STOP handling runs under everything.** Trigger: a contact replies STOP, UNSUBSCRIBE, ARRET or similar, or clicks unsubscribe, or the platform marks them do-not-disturb. Steps: add `nl-do-not-contact`, set `NL | Consent basis` to none, remove the contact from every NL workflow, create no task, send nothing more. HighLevel's own STOP handling stays on as well. [verify in HighLevel: that a STOP reply also sets the platform's do-not-disturb for SMS]

### New custom values, fields and tags these blueprints add

All PROPOSED, Ray to approve. They follow the existing convention and add to the lists in the spec.

| Kind | Name | Holds |
|---|---|---|
| Custom value | `nl_q1` to `nl_q5` | The client's own qualifying questions, in the order asked |
| Custom value | `nl_urgent_definition` | What counts as urgent for this client, in one sentence |
| Custom value | `nl_callback_promise` | The words the AI may use about a callback. Default: "as soon as they are free" |
| Custom value | `nl_send_window` | The sending window, as text, for the client's reference |
| Custom value | `nl_forward_off_code` | The code the client dials on their carrier to switch forwarding off |
| Custom value | `nl_report_calls`, `nl_report_answered`, `nl_report_booked`, `nl_report_textbacks`, `nl_report_reviews_asked`, `nl_report_reviews_in`, `nl_report_changed`, `nl_report_next`, `nl_report_month` | The numbers and two sentences for the monthly report |
| Custom value | `nl_usage_included`, `nl_usage_extra_rate` | Minutes included and the price of an extra minute, as agreed with the client |
| Custom field | NL \| Urgent (yes, no) | Set by the voice agent |
| Custom field | NL \| Callback number | The number the caller wants to be reached on |
| Custom field | NL \| Appointment confirmed (yes, no, asked) | Set by the reminder workflow |
| Custom field | NL \| Closed date | Date the deal closed. Drives the review and past-client workflows |
| Custom field | NL \| Last reactivation date | Stops a contact being messaged twice in one campaign period |
| Tag | `nl-urgent` | The call was handled on the urgent path |
| Tag | `nl-textback-sent` | A missed-call text went out today |
| Tag | `nl-appt-confirmed`, `nl-appt-unconfirmed` | Outcome of the reminder |
| Tag | `nl-reactivation-queue` | Cleared for the reactivation campaign |
| Tag | `nl-report-ready` | Added to the client's own contact record to send the monthly report |
| Tag | `nl-usage-80`, `nl-usage-cap-reached` | Applied to the client's own contact record to send the usage messages |
| Tag | `nl-cancel-requested`, `nl-export-sent`, `nl-export-confirmed` | Offboarding steps |

Already in the spec and used below: `nl_biz_name`, `nl_owner_name`, `nl_brokerage_name`, `nl_service_area`, `nl_hours`, `nl_phone_main`, `nl_transfer_number`, `nl_booking_link`, `nl_review_link`, `nl_mailing_address`, `nl_ai_name`, `nl_ai_disclosure_line`, `nl_recording_line`, `nl_languages`, `nl_faq_1` to `nl_faq_5`, `nl_not_allowed`, `nl_appointment_name`, `nl_usage_cap`, `nl_recording_on`, `nl_summary_email`, `nl_summary_mobile`, `nl_crm_name`.

### What can be created through the API and what is built by hand

From the official API reference, read 2026-11-15.

| Piece | Through the API | By hand in the builder |
|---|---|---|
| Custom values, custom fields, tags | Yes | |
| Pipeline and stages | Yes | |
| Calendar | Yes. Connecting the client's Google or Outlook is done by the client | Connection |
| Test contacts | Yes | |
| Voice agent: name, welcome message, prompt, language, maximum call length | Yes | Voice choice by ear, advanced settings, the Deploy tab, the phone number |
| Voice agent actions (booking, update field, trigger workflow, transfer) | Yes, on paper. Treat the first one as a test | Check each action on a real call |
| Workflows | Only if HighLevel has enabled the workflow API for the sub-account. Otherwise the call is refused. Created as drafts when it works | Assume by hand until one test call to the API proves otherwise. A person always publishes |
| Forms, email and text templates, dashboards, review settings | No | Yes |
| Phone number, forwarding, text registration, recording setting | No | Yes |
| Snapshot creation and loading | No | Yes, in the agency view |
| Usage limits, rebilling, SaaS plan | Not planned through the API | Yes, in the agency view |

---

## Blueprint 1. The AI receptionist (NL 01 | Voice agent, with "AI call finished" and "Needs a human")

**Purpose.** Answer a call the client did not pick up. Say it is an AI. Find out who is calling and why. Book a time or take a message. Tell the client at once. Never give advice.

**Product.** Next Level Answer. Inbound only.

### How a call reaches it

1. The client keeps their number. At their carrier they set conditional forwarding (no answer, busy, unreachable) to the Next Level number. Never "forward all calls". [verify with the client's carrier]
2. The Next Level number is a HighLevel phone-system number that is not the sub-account's default number, with no call forwarding set on it, so the agent always answers. (Confirmed on the official page.)
3. Inbound timeout on that number is set low so no voicemail picks up first. (Confirmed: a call that reaches a voicemail is marked completed and the agent never answers.)

### Agent settings

| Setting | Value | Status |
|---|---|---|
| Agent name | `NL Receptionist (agent edition)` | |
| Language | English (US) at launch. Any other language is added only after it passes a test call on the client's own line and is written into `nl_languages` | The language picker is confirmed. Each language: [verify in HighLevel] |
| Voice and model | One of the lower-cost voices. Never ElevenLabs V3 or V4 ($0.17 a minute). Whether to use a speech-to-speech model at $0.10 to $0.20 a minute all in, or the Voice Engine plus a $0.015 voice: [Ray to decide after hearing both on the demo line] | Prices confirmed |
| Maximum call length | PROPOSED 600 seconds. The API allows 180 to 900 and defaults to 300 | Confirmed range. [Ray to set] |
| Working hours | All hours. The carrier forwarding decides which calls arrive | |
| Recording | Off. `nl_recording_on` = no and `nl_recording_line` empty. Set on the number's configuration (Call Recording: disable) | The setting is confirmed. That a summary is still produced with recording off: [verify in HighLevel], test before the first client |
| Welcome message | Greeting plus the disclosure line (below). The welcome message is limited to 190 characters in the API | Confirmed limit |
| Knowledge base | None in version 1. Approved answers come from `nl_faq_1` to `nl_faq_5` | |
| Response speed, interruption handling, pronunciation list for the business name, owner name and local street and town names | Set by ear on test calls and written down per client | Setting names: [verify in HighLevel] |

### AI disclosure line and recording line

- PROPOSED default for `nl_ai_disclosure_line`: "Thanks for calling {{custom_values.nl_biz_name}}. I am {{custom_values.nl_ai_name}}, an AI assistant for {{custom_values.nl_owner_name}}."
- PROPOSED default for `nl_recording_line`, used only when the client has asked in writing for recording: "This call is recorded so {{custom_values.nl_owner_name}} can review it. If you would rather it was not, tell me and I will take a message instead."
- Both are filled only after the rules are confirmed for the client's province. [Ray to confirm with counsel]
- The disclosure is in the welcome message, so it is said on every call before anything else. If asked later "am I talking to a real person", the agent says again that it is an AI.

### Call flow

1. **Greet and disclose.** Welcome message. Recording line if recording is on.
2. **Open question.** "How can I help you today?"
3. **Urgent check, at any point in the call.** The caller asks for a person, says it is urgent, sounds distressed, or says something that matches `nl_urgent_definition`. Go to the urgent path.
4. **Name and number.** Ask the caller's name. Read back the number they are calling from and ask if it is the best one. Store a different number in NL | Callback number.
5. **Question slots.** Ask `nl_q1` to `nl_q5`, one at a time, skipping any already answered. Agent-edition defaults the client can edit:
   - `nl_q1`: "Are you looking to buy, sell or rent?" writes NL | Caller reason.
   - `nl_q2`: "Which area or address is this about?" writes NL | Area of interest.
   - `nl_q3`: "When are you hoping to move?" writes NL | Timeline.
   - `nl_q4`: "Are you already working with a real estate agent?" If yes, the agent takes a message only and does not offer a booking. [Ray to confirm: the wording Ontario rules require here]
   - `nl_q5`: "Is there anything {{custom_values.nl_owner_name}} should know before calling you?"
6. **Questions from the caller.** Answer only from `nl_faq_1` to `nl_faq_5`, `nl_hours` and `nl_service_area`. Anything else: "I do not have that information. I will pass your question to {{custom_values.nl_owner_name}}."
7. **Offer a booking.** "Would you like to book a {{custom_values.nl_appointment_name}} with {{custom_values.nl_owner_name}}?" Use the booking action on the calendar. Offer two times. Say the chosen day and time back. Say a confirmation text will follow. If nothing fits or the caller declines, take a message.
8. **Close.** Recap in one sentence. "{{custom_values.nl_owner_name}} will have this in a moment. Thanks for calling."
9. **After the call.** The agent's actions write the fields and fire `NL 01 | AI call finished`.

**Urgent path.** Confirm name and callback number. Ask for the reason in one sentence. Say: "I am sending this to {{custom_values.nl_owner_name}} right now and asking them to call you back {{custom_values.nl_callback_promise}}." Do not promise a time. Do not attempt a live transfer unless `nl_transfer_number` is filled and a transfer has been tested on a real phone call for this client. Set NL | Urgent to yes. Fire `NL 01 | Needs a human`. End the call.

### The prompt, as slots

The prompt is assembled from these blocks, in this order. The words are ours and stay short so the agent does not ramble.

| Block | Content |
|---|---|
| Role | You answer the phone for `nl_biz_name`, a `nl_industry` business serving `nl_service_area`, with `nl_brokerage_name`. You are an AI assistant named `nl_ai_name`. You are not a licensed professional. |
| Job | Find out who is calling and why, book a `nl_appointment_name` or take a message, and end the call politely. Keep every reply to one or two sentences. Ask one question at a time. |
| Honesty | You have already said you are an AI. Say so again whenever asked. Never claim to be a person. |
| Questions | Ask `nl_q1` to `nl_q5` in order. Skip any the caller has answered. |
| Approved answers | `nl_faq_1` to `nl_faq_5`, `nl_hours`, `nl_service_area`. If the answer is not here, say you do not have it and will pass the question on. Never guess. |
| Never | `nl_not_allowed`, plus the fixed list below. |
| Urgent | `nl_urgent_definition`, plus any request for a person. Follow the urgent path. |
| Booking | Use the calendar action. Offer two times. Repeat the day and time. |
| Language | Speak `nl_languages` only. If the caller speaks another language, say in English that a person will call back, take the number, and follow the urgent path without the urgent tag. |
| Close | Recap, thank the caller, end the call. Then write the summary. |

Whether the prompt can read `{{custom_values.nl_...}}` directly: the official page confirms a Custom Value menu in the prompt editor and shows location, contact, appointment and user fields. Our own custom values: [verify in HighLevel]. If they do not appear, the prompt is filled per client from the intake form by paste, or through the API.

### What it must never say

Fixed for every client. `nl_not_allowed` adds to this list and cannot shorten it.

1. An opinion on what a property is worth, what to offer, or whether a price is fair.
2. Legal, mortgage, tax, insurance or investment advice.
3. Whether a listing is still available, its price or its details. It takes a message. (Until a listing lookup is confirmed and tested, spec section 5.)
4. Anything about another client, another caller or another deal.
5. That it is a person, or that a person is listening when none is.
6. A promise of a callback time, a result, a commission rate or a fee.
7. A comment on a neighbourhood's people, safety or schools.
8. Anything to a caller who says they are represented by another agent, beyond taking a message.
9. The client's personal mobile number, home address or schedule.
10. Anything it is not sure of. "I do not have that information" is always allowed.

### NL 01 | AI call finished

| Part | Detail |
|---|---|
| Trigger | The voice agent's "trigger a workflow" action at the end of the call. Agent actions that trigger workflows are confirmed. The exact action and trigger names: [verify in HighLevel] |
| Conditions | NL \| Urgent is not yes (the urgent workflow handles those) |
| Step 1 | Add `nl-source-ai-call`. Set NL \| Last AI call date to today |
| Step 2 | If an appointment was booked: add `nl-status-booked`, move the opportunity to Appointment booked. Else if NL \| Caller reason is filled: add `nl-status-qualified`, stage Qualified. Else: stage New caller |
| Step 3 | Internal notification by text to `nl_summary_mobile` (copy below). Not held by the sending window |
| Step 4 | Internal notification by email to `nl_summary_email` (copy below) |
| Step 5 | If `nl_crm_name` has a confirmed push: send the contact to the CRM through the tested Zapier connection. One way. [verify in HighLevel: the connection for each CRM, in the client's own account] |
| Settings | Re-entry on. Stop on response off |

Summary text to the client:

> New call for {{custom_values.nl_biz_name}}. {{contact.name}}, {{contact.phone}}. Reason: {{NL | Caller reason}}. Area: {{NL | Area of interest}}. Timeline: {{NL | Timeline}}. Booked: {{appointment.start_time}}. Note: {{NL | Call summary}}

Summary email to the client. Subject: `New call: {{contact.name}}, {{NL | Caller reason}}`

> {{contact.name}} called {{custom_values.nl_biz_name}} and the AI answered.
>
> Number: {{contact.phone}}
> Best number to call back: {{NL | Callback number}}
> Reason: {{NL | Caller reason}}
> Area: {{NL | Area of interest}}
> Timeline: {{NL | Timeline}}
> Working with another agent: as noted in the summary
> Booked: {{appointment.start_time}}
>
> Summary: {{NL | Call summary}}
>
> The full transcript is in your account under this contact. Sent by Next Level Answer for {{custom_values.nl_biz_name}}.

The summary text to the client counts toward the 500 text segments in the offer. Keep `NL | Call summary` to two sentences in the prompt so the text stays within about three segments.

### NL 01 | Needs a human

| Part | Detail |
|---|---|
| Trigger | The voice agent's "trigger a workflow" action on the urgent path. Second trigger: tag `nl-status-needs-human` added |
| Step 1 | Add `nl-urgent` and `nl-status-needs-human` |
| Step 2 | Internal notification by text to `nl_summary_mobile`, at once, any hour |
| Step 3 | Internal notification by email to `nl_summary_email` |
| Step 4 | Create a task for the client: "Call back {{contact.name}}", due now |
| Step 5 | Wait 15 minutes. If the task is still open and it is inside `nl_hours`: one more text to `nl_summary_mobile`. PROPOSED, [Ray to set: whether and when to remind] |
| Settings | Re-entry on |

Urgent alert text to the client:

> URGENT call for {{custom_values.nl_biz_name}}. {{contact.name}} at {{NL | Callback number}} asked for a person. Reason: {{NL | Call summary}}. They were told you will call back.

### What the client sees

A text and an email after every call. The contact in their app with the fields filled and the transcript. The appointment on their own calendar. An urgent text at once when a caller asks for a person.

### Test script: 10 calls

Run from an outside phone, in NL Demo first, then on the client's own line before go-live. Pass mark: all 10 pass in one run. Any fail: fix, then run all 10 again.

| # | The tester says | Pass when |
|---|---|---|
| 1 | "Hi, I am thinking of buying in [area] in the spring." Accepts a time | AI says it is an AI in the first sentence. Asks the questions one at a time. Books. Confirmation text arrives. Summary text and email arrive. Stage is Appointment booked |
| 2 | "I want to sell my house." Refuses every time offered | Takes a message. No booking. Summary arrives. Stage is Qualified |
| 3 | "What do you think my house is worth?" then "Is 12 Main Street still for sale?" | Gives no value and no listing detail. Says it will pass the question on. Offers a booking or a message |
| 4 | "Can I get out of my lease?" and "What rate can I get on a mortgage?" | Gives no legal or mortgage answer |
| 5 | "I need to speak to [owner] right now, it is urgent." | Offers a callback, promises no time, ends. Urgent text reaches the client's phone in under a minute. Task exists |
| 6 | "Are you a real person?" in the middle of a call | Says it is an AI assistant and carries on |
| 7 | "I already have an agent, I have a question about a listing." | Takes a message only. Offers no booking |
| 8 | Says nothing and hangs up after five seconds | No empty summary is sent to the client. Missed-call text-back (blueprint 2) sends one text |
| 9 | A sales pitch: "I am calling about your website ranking." | Polite end. Not marked urgent. Stage Not a fit or New caller |
| 10 | Speaks a language not in `nl_languages`, or with a television loud in the background | Says in English that a person will call back, takes the number, alerts the client. Does not invent answers |

After the 10: reply STOP to the confirmation text from call 1 and confirm every workflow ends for that contact. With recording off, confirm no audio file exists and the summary still arrived. With recording on in NL Demo, confirm the recording line is said first.

### Build: by hand or through the API

| Step | Who and how |
|---|---|
| Custom values, fields, tags, pipeline, calendar | API |
| Agent created with name, welcome message, prompt, language, maximum length | API, then checked by a person |
| Agent actions: booking, field updates, the two workflow triggers | API where it works, otherwise by hand. Each tested on a real call |
| Voice, advanced settings, pronunciation list | By hand, by ear |
| Number purchase, Deploy tab, timeout, recording off | By hand |
| The two workflows | By hand, unless the workflow API is enabled for the sub-account |
| Carrier forwarding | The client, with us on the phone |

---

## Blueprint 2. Missed-call text-back (NL 01 | Missed-call text-back)

**Purpose.** A caller who reached the Next Level line and got no conversation receives one text, so they can reply or book.

**When it fires in practice.** The caller hung up before speaking. The call dropped. The AI was paused by the usage cap. It is not for calls the AI handled.

| Part | Detail |
|---|---|
| Trigger | Call status on an inbound call to the Next Level number: missed, no answer, busy, or a call shorter than 10 seconds. Trigger and filter names: [verify in HighLevel] |
| Conditions | Not tagged `nl-do-not-contact`. Not tagged `nl-textback-sent`. No AI call summary written in the last 10 minutes. The number can receive texts |
| Step 1 | Wait 1 minute. This lets the AI-call workflow finish first if there was a conversation |
| Step 2 | Check the conditions again. If the caller has since been handled, stop |
| Step 3 | If inside the sending window: send the text now. If outside: wait for the window to open, then send. [Ray to decide: whether a reply to a call made a minute ago may go out after hours] |
| Step 4 | Add `nl-source-missed-call` and `nl-textback-sent`. Create the opportunity in New caller if none exists |
| Step 5 | Wait until the caller replies, up to 24 hours. On a reply: create a task for the client, notify `nl_summary_mobile`, stop |
| Step 6 | After 24 hours remove `nl-textback-sent` so a call on another day can be texted again |
| Settings | Re-entry on. Stop on response on. HighLevel's built-in Missed Call Text Back setting is switched off, because it texts on every missed call including repeats (confirmed) |

Text to the caller:

> This is {{custom_values.nl_biz_name}}. Sorry we missed your call. Reply here with what you need and {{custom_values.nl_owner_name}} will get back to you, or book a time: {{custom_values.nl_booking_link}} Reply STOP to opt out.

Notification to the client when the caller replies:

> {{contact.phone}} replied to the missed-call text for {{custom_values.nl_biz_name}}: "{{message.body}}". Reply from your app.

**Consent note.** The caller phoned the business a minute earlier and the text answers that call. Whether that is enough under the anti-spam rules for a text: [Ray to confirm with counsel]. The text names the sender, offers nothing for sale and carries STOP.

**What the client sees.** The text in the conversation thread. A notification only when the caller replies. A count of text-backs on the dashboard.

**Tests.** (1) Call and hang up at five seconds: one text arrives. (2) Call three times in two minutes: still one text. (3) Hold a full AI conversation: no text. (4) Call at 10 p.m.: the text follows the after-hours rule Ray chose. (5) Reply STOP: nothing further, tag applied. (6) Call from a landline: no error, no task spam.

**Build.** Workflow by hand. Tags through the API. The registration that lets a number send texts is filed by hand per client. What a Canadian number must file: [verify in HighLevel].

---

## Blueprint 3. Speed to lead for web and ad forms (NL 01 | Speed-to-lead)

**Purpose.** Someone who fills in a form hears back at once, and the client is told to call them.

**Inbound only.** The AI does not place a call. The workflow sends a text and an email and gives the client a call task.

| Part | Detail |
|---|---|
| Trigger | Form submitted (website contact form, buyer inquiry, seller inquiry). Second trigger: a lead-ad form submitted, when the client is on Next Level Ads. Trigger names for each ad platform: [verify in HighLevel] |
| Conditions | Not tagged `nl-do-not-contact`. Has a phone number or an email |
| Step 1 | Add `nl-source-form` or `nl-source-ad`. Set NL \| Consent basis: express if the consent box was ticked, otherwise "inquiry". Set NL \| Consent date |
| Step 2 | Create the opportunity in New caller |
| Step 3 | Email to the lead, at once, any hour. It answers their inquiry |
| Step 4 | Text to the lead. Inside the sending window: at once. Outside: when the window opens. [Ray to decide: same question as blueprint 2] |
| Step 5 | Internal notification by text to `nl_summary_mobile`, and a task "Call {{contact.name}}", due in 15 minutes inside `nl_hours`, otherwise at the start of the next working day |
| Step 6 | Wait for a reply or a booking, up to 1 day. On either: stop, notify the client |
| Step 7 | No reply and consent is express: one follow-up text the next day inside the window. Consent is "inquiry" only: no second message |
| Step 8 | Stop. Nothing further is sent by this workflow |
| Settings | Re-entry off for the same form within 7 days. Stop on response on |

First text to the lead:

> Hi {{contact.first_name}}, this is {{custom_values.nl_biz_name}}. We got your message. {{custom_values.nl_owner_name}} will call you shortly. If you would rather pick a time, here is the calendar: {{custom_values.nl_booking_link}} Reply STOP to opt out.

Email to the lead. Subject: `We got your message, {{contact.first_name}}`

> Hi {{contact.first_name}},
>
> Thanks for getting in touch with {{custom_values.nl_biz_name}}. Your message is with {{custom_values.nl_owner_name}} now.
>
> If you would like to choose a time to talk, you can book here: {{custom_values.nl_booking_link}}
>
> {{custom_values.nl_owner_name}}
> {{custom_values.nl_biz_name}}, {{custom_values.nl_brokerage_name}}
> {{custom_values.nl_mailing_address}}
> Unsubscribe: {{unsubscribe link from the builder}}

Follow-up text, express consent only:

> Hi {{contact.first_name}}, {{custom_values.nl_owner_name}} at {{custom_values.nl_biz_name}} here. Still happy to help with your question. Reply here or book a time: {{custom_values.nl_booking_link}}

Notification to the client:

> New web lead for {{custom_values.nl_biz_name}}: {{contact.name}}, {{contact.phone}}. They have been sent a reply. Please call within 15 minutes.

**What the client sees.** A text within a minute of the form. A task. The lead in the pipeline with its source.

**Tests.** (1) Submit the form at 2 p.m. with the box ticked: email and text within a minute, task created. (2) Submit at 10 p.m. on a Friday: email at once, text per the rule, task due the next working morning. (3) Submit with the box unticked: no follow-up text on day 2. (4) Book through the link after the first text: the workflow stops. (5) Submit twice in an hour: one sequence. (6) STOP ends it.

**Build.** Forms by hand (the API cannot create forms). Workflow by hand. Fields and tags through the API.

---

## Blueprint 4. Appointment confirmation and reminders (NL 01 | Appointment reminders)

**Purpose.** Every booking is confirmed, reminded once, and either confirmed by the person or flagged to the client.

| Part | Detail |
|---|---|
| Trigger | Appointment booked on the calendar "Call with {{custom_values.nl_owner_name}}", by the AI, the booking link or the client. Second trigger: appointment rescheduled. Trigger names: [verify in HighLevel] |
| Conditions | Appointment is in the future. Contact not tagged `nl-do-not-contact` |
| Step 1 | Confirmation text and email. Inside the window: at once. Outside: email at once, text when the window opens |
| Step 2 | Set NL \| Appointment confirmed to asked. Add `nl-status-booked` |
| Step 3 | Wait until 24 hours before the start. If the booking was made less than 24 hours ahead, skip to step 6 |
| Step 4 | Reminder text asking for a reply |
| Step 5 | Wait for a reply, up to 4 hours inside the window. Reply C, yes or confirm: set the field to yes, add `nl-appt-confirmed`, mark the appointment confirmed, go to step 7. Reply R, no or reschedule: send the reschedule text, create a task for the client, add `nl-appt-unconfirmed`, stop. Anything else: create a task for the client to read the reply |
| Step 6 | No reply: one reschedule text with the booking link, add `nl-appt-unconfirmed`, task for the client "No confirmation from {{contact.name}}" |
| Step 7 | Two hours before the start, inside the window, only if confirmed: a short reminder with the time. PROPOSED, [Ray to decide: keep or drop this step] |
| Step 8 | Appointment cancelled at any point: remove from the workflow, notify the client |
| Settings | Re-entry on (a new booking starts a new run). Stop on response off, because the reply is handled in step 5 |

Confirmation text:

> Hi {{contact.first_name}}, this is {{custom_values.nl_biz_name}}. Your {{custom_values.nl_appointment_name}} with {{custom_values.nl_owner_name}} is booked for {{appointment.start_time}}. Need to change it? {{custom_values.nl_booking_link}} Reply STOP to opt out.

Confirmation email. Subject: `Booked: {{custom_values.nl_appointment_name}} on {{appointment.start_time}}`

> Hi {{contact.first_name}},
>
> Your {{custom_values.nl_appointment_name}} with {{custom_values.nl_owner_name}} is booked for {{appointment.start_time}}.
>
> To change the time: {{custom_values.nl_booking_link}}
>
> {{custom_values.nl_biz_name}}, {{custom_values.nl_brokerage_name}}
> {{custom_values.nl_mailing_address}}

Reminder text, 24 hours before:

> Reminder from {{custom_values.nl_biz_name}}: your {{custom_values.nl_appointment_name}} with {{custom_values.nl_owner_name}} is tomorrow, {{appointment.start_time}}. Reply C to confirm or R to reschedule.

Reschedule text:

> No problem. Pick a new time here: {{custom_values.nl_booking_link}} {{custom_values.nl_biz_name}}

No-reply text:

> {{custom_values.nl_biz_name}} here. We have not heard back about tomorrow, {{appointment.start_time}}. If the time no longer works, choose another here: {{custom_values.nl_booking_link}}

Two-hour reminder:

> See you at {{appointment.start_time}}. {{custom_values.nl_owner_name}}, {{custom_values.nl_biz_name}}

**What the client sees.** The appointment's status on their calendar. A task only when someone has not confirmed or wants to move.

**Tests.** (1) Book for three days out: confirmation now, reminder at 24 hours. (2) Reply C: confirmed, two-hour reminder sends. (3) Reply R: reschedule link, task. (4) Say nothing: no-reply text and task. (5) Book for two hours out: no 24-hour reminder. (6) Cancel: nothing more is sent. (7) Reschedule: the old run ends and a new one starts. (8) Book at 11 p.m.: email now, text in the morning. (9) STOP.

**Build.** Calendar through the API. Workflow by hand.

---

## Blueprint 5. Review requests (NL 02 | Review request at closing, at day 30, and Review reply draft)

**The one rule.** Everyone who is asked gets the same public link. Nobody is asked for a rating first. Nobody is steered away from the public page. The same message offers everyone a private way to say something went wrong.

**Product.** Next Level Reviews. Built now, released when Ray opens that rung.

### NL 02 | Review request at closing

| Part | Detail |
|---|---|
| Trigger | Opportunity stage changed to Closed |
| Conditions | NL \| Review requested date is empty. Consent basis is express or implied with a valid date. Not `nl-do-not-contact`. `nl_review_link` is filled |
| Step 1 | Set NL \| Closed date to today |
| Step 2 | Wait 2 days, then until the sending window opens. [Ray to set: the delay after closing] |
| Step 3 | Text with the review link |
| Step 4 | Email with the review link |
| Step 5 | Set NL \| Review requested date. Add `nl-review-requested` |
| Step 6 | Any reply: task for the client, notify `nl_summary_mobile`. A reply is never answered automatically |
| Settings | Re-entry off. Stop on response on |

Text:

> Hi {{contact.first_name}}, {{custom_values.nl_owner_name}} here from {{custom_values.nl_biz_name}}. Thank you for trusting me with your move. If you have two minutes, a Google review helps other people find me: {{custom_values.nl_review_link}} If anything was not right, reply here and it comes straight to me. Reply STOP to opt out.

Email. Subject: `Thank you, {{contact.first_name}}`

> Hi {{contact.first_name}},
>
> Thank you for trusting me with your move.
>
> If you have two minutes, a Google review helps other people find me: {{custom_values.nl_review_link}}
>
> If anything was not right, reply to this email. It comes straight to me.
>
> {{custom_values.nl_owner_name}}
> {{custom_values.nl_biz_name}}, {{custom_values.nl_brokerage_name}}
> {{custom_values.nl_mailing_address}}
> Unsubscribe: {{unsubscribe link from the builder}}

### NL 02 | Review request at day 30

| Part | Detail |
|---|---|
| Trigger | 30 days after NL \| Closed date |
| Conditions | NL \| Review received is not yes. `nl-review-requested` is present. Consent still valid. Not `nl-do-not-contact`. The contact has not replied to the first request |
| Step 1 | One text inside the window |
| Step 2 | Stop. There is no third request |
| Settings | Re-entry off |

Text:

> Hi {{contact.first_name}}, {{custom_values.nl_owner_name}} from {{custom_values.nl_biz_name}}. I hope the new place is treating you well. If you meant to leave a review and it slipped by, here is the link: {{custom_values.nl_review_link}} Either way, thank you.

How NL | Review received gets set: the client ticks it when the review appears, or Diana does at the monthly report. Whether HighLevel can match a new Google review to a contact by itself: [verify in HighLevel].

### NL 02 | Review reply draft

| Part | Detail |
|---|---|
| Trigger | A new review arrives on the connected Google Business Profile. Trigger name: [verify in HighLevel] |
| Step 1 | In Reputation, the AI reply suggestion is generated for the client to read. Up to four suggestions per review cost nothing (confirmed). Auto-reply modes stay off |
| Step 2 | Internal notification to the client |
| Step 3 | The client edits and posts, or posts as written. A reply posted from an AI suggestion costs $0.01 (confirmed) |
| Rule | Nothing is posted without the client pressing the button. For a review of three stars or fewer, the notification says "please write this one yourself" and no draft is suggested in the message |

Notification to the client:

> New Google review for {{custom_values.nl_biz_name}}. A draft reply is waiting in your account under Reputation. Nothing is posted until you approve it.

**What the client sees.** Requests going out after each closing without their effort. A notification and a draft when a review lands. Counts on the dashboard and in the monthly report.

**Tests.** (1) Move a sample contact to Closed: text and email after the delay, inside the window. (2) Move the same contact out and back: no second request. (3) Contact with no consent basis: nothing sends. (4) Day 30 with NL | Review received set to yes: nothing sends. (5) Reply "the closing was a mess": task and alert, no automatic answer. (6) A sample review arrives: notification only, nothing posted. (7) Check the review link opens the client's own Google review box. (8) STOP.

**Policy and law flags.** One link for everyone: [verify against Google's current review policy]. Messaging a past client after closing rests on consent: [Ray to confirm with counsel].

**Build.** Workflows and review settings by hand. Fields and tags through the API. The client connects their own Google Business Profile while logged in as themselves.

---

## Blueprint 6. Database reactivation and past-client nurture (NL 03)

**Product.** Next Level Nurture. Built now, released when Ray opens that rung.

**Before anything sends.** The client's list is checked for consent, contact by contact or by import column. Only contacts with a recorded basis and date get the tag `nl-reactivation-queue`. No consent record, no tag, no message. Next Level staff do not contact these people and do not copy the list anywhere (promise 6).

### NL 03 | Reactivation campaign

| Part | Detail |
|---|---|
| Trigger | Tag `nl-reactivation-queue` added |
| Conditions | Consent basis express, or implied with a date inside the allowed period [Ray to confirm with counsel]. Not `nl-do-not-contact`. No appointment in the next 30 days. NL \| Last reactivation date is empty or more than 180 days ago. [Ray to set: the gap] |
| Step 1 | Drip: release at most 25 contacts a day, inside the sending window, so replies arrive at a pace the client can answer. [Ray to set: daily number] |
| Step 2 | Text 1 |
| Step 3 | Set NL \| Last reactivation date. Add `nl-reactivation-sent` |
| Step 4 | Wait for a reply, up to 4 days |
| Step 5 | No reply and the contact has an email: one email. No reply and no email: stop |
| Step 6 | Wait for a reply, up to 7 days. Then remove `nl-reactivation-queue` and stop. Two touches at most |
| Settings | Re-entry off. Stop on response on |

Text 1:

> Hi {{contact.first_name}}, it is {{custom_values.nl_owner_name}} at {{custom_values.nl_biz_name}}. It has been a while since we spoke about your move. Are you still thinking about it, or has the plan changed? Either answer is helpful. Reply STOP to opt out.

Email. Subject: `Still thinking about a move, {{contact.first_name}}?`

> Hi {{contact.first_name}},
>
> We spoke a while ago about your plans to move. I am checking in to see whether that is still on your mind.
>
> If it is, reply to this email or book a time here: {{custom_values.nl_booking_link}}
>
> If the plan has changed, tell me and I will stop asking.
>
> {{custom_values.nl_owner_name}}
> {{custom_values.nl_biz_name}}, {{custom_values.nl_brokerage_name}}
> {{custom_values.nl_mailing_address}}
> Unsubscribe: {{unsubscribe link from the builder}}

### NL 03 | Hand-raiser follow-up

| Part | Detail |
|---|---|
| Trigger | A contact tagged `nl-reactivation-sent` replies with anything other than STOP |
| Step 1 | Add `nl-hand-raiser`. Remove from the campaign |
| Step 2 | Task for the client: "Reply to {{contact.name}}", due today |
| Step 3 | Internal notification to `nl_summary_mobile` with the reply |
| Step 4 | No automatic answer. The client replies in their own words. A booking link is one tap away in the app |

Notification:

> {{contact.name}} replied to your check-in: "{{message.body}}". Reply from your app. Their number: {{contact.phone}}

### NL 03 | Past-client touches

| Part | Detail |
|---|---|
| Trigger | NL \| Closed date anniversary. Second trigger, PROPOSED: six months after NL \| Closed date |
| Conditions | Consent basis valid. Not `nl-do-not-contact`. No message from any NL workflow in the last 30 days |
| Step 1 | One text inside the window. No offer, no link |
| Step 2 | Any reply: task and notification, as above |
| Settings | Re-entry on, once per trigger date |

Anniversary text:

> Hi {{contact.first_name}}, {{custom_values.nl_owner_name}} from {{custom_values.nl_biz_name}}. It is a year this week since you got the keys. I hope the place still feels right. If you ever want to know what is happening with prices on your street, I am happy to look.

**What the client sees.** A daily trickle of replies, each as a task. A count of messages sent and replies in the report.

**Tests.** (1) Tag five sample contacts, one with no consent, one with do-not-contact: three receive text 1. (2) Tag 60 samples: 25 go on day one. (3) Reply "yes still looking": hand-raiser task, campaign stops for that contact. (4) Reply STOP: do-not-contact, no task. (5) Tag the same contact again inside the gap: nothing sends. (6) Anniversary date tomorrow on a sample: one text, inside the window.

**Build.** Workflows by hand. The consent check is a person's job with the client, never automated guesswork.

---

## Blueprint 7. The client's monthly report (NL 00 | Monthly report)

**Purpose.** One page, same day each month, real counts only. No estimate of money earned or saved.

**Version 1 is filled by a person.** Whether HighLevel can schedule and email a dashboard or custom report to a client: [verify in HighLevel]. Dashboards and custom reports do travel in a snapshot (confirmed), so the dashboard is built once.

| Part | Detail |
|---|---|
| Trigger | Tag `nl-report-ready` added to the client's own contact record in their sub-account. Diana adds it after filling the numbers. PROPOSED day: the 3rd of each month |
| Before the trigger | Diana opens the dashboard and types the counts into the `nl_report_` custom values: calls received, calls answered by the AI, appointments booked by the AI, text-backs sent, reviews requested and received. She writes `nl_report_changed` and `nl_report_next`, one sentence each. About 10 minutes per client |
| Step 1 | Email to `nl_summary_email` |
| Step 2 | Text to `nl_summary_mobile`: "Your {{custom_values.nl_report_month}} report is in your inbox." |
| Step 3 | Remove `nl-report-ready`. Log the send date |
| Churn check | If the report email is not opened within 7 days, create a task for Ray in the Next Level sales account. Email-open tracking: [verify in HighLevel] |

Report email. Subject: `{{custom_values.nl_biz_name}}: your {{custom_values.nl_report_month}} numbers`

> Hi {{custom_values.nl_owner_name}},
>
> Here is what your Next Level line did in {{custom_values.nl_report_month}}.
>
> Calls that reached the AI: {{custom_values.nl_report_calls}}
> Calls the AI answered: {{custom_values.nl_report_answered}}
> Appointments the AI booked: {{custom_values.nl_report_booked}}
> Missed calls that got a text back: {{custom_values.nl_report_textbacks}}
> Reviews requested and received: {{custom_values.nl_report_reviews_asked}} and {{custom_values.nl_report_reviews_in}}
>
> One thing we changed this month: {{custom_values.nl_report_changed}}
> One thing we suggest next: {{custom_values.nl_report_next}}
>
> These are counts from your own account. Your minutes used are on your invoice.
>
> Ray Ahmadi, Next Level

Leave the reviews line out for clients who are not on Next Level Reviews.

**Later option, Ray to decide.** The counts could be read and written through the API (call logs read, custom values write) so Diana only writes the two sentences. The call-log endpoint returns call details, so this touches promise 7 (who can read a transcript). It needs Ray's decision and a line in the agreement before it is built.

**Tests.** (1) Fill sample numbers in NL Demo, add the tag: email and text arrive, numbers match the dashboard. (2) Leave one value empty: the email is held and Diana is told. Build this check as an if/else on empty values. (3) The email shows no caller names or numbers.

**Build.** Dashboard by hand. Custom values through the API. Workflow by hand.

---

## Blueprint 8. Usage cap and alert (NL 00 | Usage)

**The promise (offer.md, round 3).** 250 AI call minutes included. Extra minutes at $0.30 CAD. The client sets a monthly cap on extra minutes, which can be zero. At the cap the system stops and alerts the client.

**What the platform offers, confirmed on official pages.**

- **SaaS Usage Limits** (HighLevel Labs, beta, "Pro agencies"): a SaaS plan can include a monthly Voice AI minute allowance, with a markup and an overage rule of Bill or Block. The client sees a Usage tab. Automatic threshold alerts are not available yet.
- **AI Usage Limits**: a monthly dollar limit per sub-account, up to $1,000, counting billable usage only. Set to "Block AI at the limit", AI pauses at the limit and resumes when the limit is raised or the month turns. Alerts at 70, 80, 90 and 100 percent. The default is notify only, so the block must be chosen for each client.
- **Fixed-rate rebilling**: Voice AI can be rebilled at a flat rate per minute. It needs the $497 plan.

### Set-up per client

| Step | Detail | Status |
|---|---|---|
| 1 | In the SaaS Configurator, on the NL Answer Founding plan: bundled pricing, Voice AI included, allowance 250 minutes | [verify in HighLevel: that SaaS Usage Limits is available on Ray's plan in Labs] |
| 2 | Overage rule. Cap of zero: Block. Cap above zero: Bill, with the fixed rate set to the price of an extra minute | [verify in HighLevel: the currency of the fixed rate. $0.30 CAD has to be entered as its US dollar equivalent if the field is in US dollars] |
| 3 | AI Usage Limit on the sub-account: the dollar amount that equals the client's cap in extra minutes, with "Block AI at the limit" | [verify in HighLevel: whether the limit counts HighLevel's cost or the rebilled price. Set a low limit in NL Demo, use it up, read the result] |
| 4 | Write the cap into `nl_usage_cap`, the allowance into `nl_usage_included`, the rate into `nl_usage_extra_rate` | API |
| 5 | Agency default for every new sub-account: a limit with Block, so no client is ever uncapped by accident | By hand, agency view |
| 6 | Number fallback. Decide what a caller hears while AI is blocked. PROPOSED: the Next Level number goes to a voicemail greeting recorded by the client, and blueprint 2 texts the caller | [verify in HighLevel: what happens to a call when AI is blocked. This is the single most important test before the first client] |

If SaaS Usage Limits is not available: keep step 3 as the hard stop, set at the dollar value of 250 minutes plus the cap, and check minutes by hand each Monday in the Voice AI dashboard.

### The alerts

HighLevel's threshold alerts reach the agency, not the client. [verify in HighLevel: who receives them] So the client-facing alert is ours.

| Part | Detail |
|---|---|
| Trigger A | Tag `nl-usage-80` added to the client's own contact record. Diana adds it when the 80 percent alert arrives |
| Step | Text and email to the client, at once |
| Trigger B | Tag `nl-usage-cap-reached` added. Diana adds it when the 100 percent alert arrives, or when the block is seen |
| Step 1 | Text and email to the client, at once |
| Step 2 | Task for Ray: call the client the same day |
| Step 3 | On the first day of the next month: remove both tags |

80 percent text:

> Next Level: {{custom_values.nl_biz_name}} has used about 80% of this month's {{custom_values.nl_usage_included}} included minutes. Nothing changes yet. Your cap on extra minutes is {{custom_values.nl_usage_cap}}. Reply here if you want to change it.

Cap-reached text:

> Next Level: {{custom_values.nl_biz_name}} has reached the monthly cap you set. The AI has stopped answering until the 1st, or until you raise the cap. Callers now reach your voicemail greeting and get a text back. To have calls ring only your own phone, dial {{custom_values.nl_forward_off_code}}. Reply RAISE and we will call you.

Cap-reached email. Subject: `Your AI line has reached its monthly cap`

> Hi {{custom_values.nl_owner_name}},
>
> Your line has used its {{custom_values.nl_usage_included}} included minutes and the extra minutes you allowed ({{custom_values.nl_usage_cap}}). As agreed, the AI has stopped answering so you are not billed past your cap.
>
> What happens to calls now: callers reach your voicemail greeting on the Next Level line and receive a text back.
>
> Your choices:
> 1. Do nothing. The AI starts again on the 1st.
> 2. Raise the cap. Reply to this email with the number of extra minutes you want.
> 3. Switch forwarding off so calls ring only your own phone. Dial {{custom_values.nl_forward_off_code}} from your mobile.
>
> Ray Ahmadi, Next Level

The offer says calls "ring through to the client's own phone or voicemail as they did before". With conditional forwarding still on at the carrier, an unanswered call still travels to the Next Level number. So the wording is kept only if the voicemail fallback works or the client switches forwarding off. If the test in step 6 fails, the offer wording changes before anyone is sold on it.

**What the client sees.** Minutes on every invoice. A Usage tab in their account if SaaS Usage Limits is on. A text at 80 percent and at the cap.

**Tests.** Run in NL Demo. (1) Set the allowance to 3 minutes and the cap to zero. Make calls until it is used. Record what the next caller hears. (2) Confirm the text-back fires for that caller. (3) Add each tag: the right message arrives. (4) Raise the limit: the AI answers again within a minute. (5) Read the test invoice: minutes shown, extra minutes at the agreed rate, and note the 5 percent HighLevel adds to carrier and registration fees when rebilling is on. (6) Confirm a brand-new sub-account inherits a blocking limit.

**Build.** All by hand in the agency view. Custom values through the API.

---

## Blueprint 9. Cancellation, export and deletion (NL 00 | Offboarding)

**The promise.** Forwarding is off on the day the client cancels. Their contacts and transcripts are exported to them and deleted from the account within 30 days of the day they leave.

This is a procedure with one small workflow. It runs in the Next Level sales sub-account, on the client's record there.

| Day | Step | Who | Proof kept |
|---|---|---|---|
| 0 | Client asks to cancel. Add `nl-cancel-requested`. Stage moves to At risk, then to a Cancelling stage. PROPOSED new stage | Ray | Note with the date and the client's words |
| 0 | The workflow sends the confirmation email (below) with the cancel date | Workflow | Email in the thread |
| Cancel date | Client dials `nl_forward_off_code`. We call their number with them on the line: their own phone rings and their own voicemail picks up | Diana, client | Test call noted |
| Cancel date | Every workflow in the client's sub-account switched off. Voice agent removed from the number | Diana | Screenshot |
| Cancel date | Subscription cancelled in billing so no further charge is made | Ray | Billing record |
| +1 to +7 | Export: contacts as CSV. Voice AI call logs with summaries and transcripts as CSV. Recordings, if the client had recording on | Diana | File list |
| +1 to +7 | Check the call-log export is complete. The official page says a bulk export holds up to the 50 most recent calls matching the filters. Export by date range, month by month, and count the rows against the dashboard | Diana | Row counts |
| +1 to +7 | Send the files to the client by a link that expires. Add `nl-export-sent` | Diana | Email in the thread |
| +7 to +21 | Client replies that they have the files. Add `nl-export-confirmed`. No reply after two reminders: Ray phones | Ray | Reply or call note |
| By +30 | If the client wants to keep the Next Level phone number, move it out first. Deleting the sub-account deletes its numbers for good (confirmed) | Diana | Port record |
| By +30 | Delete the sub-account. It can be undone for 24 hours, then it is permanent (confirmed). Delete our copy of the export files | Ray | Date logged |
| By +30 | Email the client that the data is deleted | Workflow | Email in the thread |

Confirmation email. Subject: `Your Next Level cancellation`

> Hi {{contact.first_name}},
>
> This confirms your Next Level service ends on {{cancel date}}.
>
> On that day we will switch call forwarding off with you and check that your phone rings as it did before. No charge is made after that date.
>
> Within 7 days you will get a file of your contacts and your call summaries and transcripts. Once you tell us you have it, we delete them from the account. Everything is deleted within 30 days of {{cancel date}}.
>
> If you want to keep the phone number we set up for you, tell us this week.
>
> Ray Ahmadi, Next Level
> {{Next Level mailing address}}

Deletion email. Subject: `Your Next Level data has been deleted`

> Hi {{contact.first_name}},
>
> Your contacts, call summaries and transcripts were deleted from the Next Level account on {{date}}. We kept no copy.
>
> Thank you for being a founding client.
>
> Ray Ahmadi, Next Level

**Limits to state honestly.** HighLevel says customer data is retained while the agency is an active customer and that deletion requests are handled on written request. Deleting the sub-account removes it from the account Ray controls. What HighLevel keeps in backups and logs, and for how long: [verify in HighLevel: ask support in writing before the agreement promises "deleted"]. [Ray to confirm with counsel: the deletion wording in the agreement]

**Tests.** Run the whole procedure on a test sub-account. (1) The export opens and holds every sample contact and every sample call. (2) After deletion the sub-account cannot be opened. (3) A call to the old forwarding target does not reach an AI. (4) A sample contact that existed only in the test account is not found in the agency or the Ray Homes account.

**Build.** One workflow by hand in the sales sub-account. The rest is a checklist.

---

## Open checks, in the order they block the first client

1. What a caller hears when AI is blocked at the limit (blueprint 8, step 6).
2. Recording off with the summary still produced (blueprint 1).
3. Whether SaaS Usage Limits is available in Labs on Ray's plan, and which currency the fixed rate uses (blueprint 8).
4. Whether the voice prompt reads our own `nl_` custom values (blueprint 1).
5. The exact trigger and filter names for call status, appointment status and new review (blueprints 2, 4, 5).
6. Whether the workflow API is enabled for the Next Level sub-account. One read-only call answers it.
7. What a Canadian number must file before it can text (blueprint 2).
8. The call-log export limit (blueprint 9).
9. Counsel: the disclosure line, the recording line, consent for the missed-call text and for review and reactivation messages, the deletion wording.
