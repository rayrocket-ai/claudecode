# Three tests before the first client

For Ray and Diana. Written 2026-11-15. A runbook, not a record. Nothing below has been run yet.

These are the first three open checks in `automation-blueprints.md`. Each one decides whether a line in `offer.md` can stay as written. No founding client goes live until all three have a dated result in the table at the bottom.

**Where.** NL Demo only. Never Ray Homes, never a client account.

**What you need first.** The demo number bought and pointed at the receptionist (backlog items 5 and 6). `NL 01 | AI call finished` built and published in NL Demo (item 8). An outside phone that is not a user on the account. For test 1, a second phone to stand in for "the client's own phone".

**Menu names.** Marked [verify menu name] where the official pages did not give the exact label. Write the real label into this file when you see it.

**Write down what happens, not what you expected.** Time of each call, what you heard, in the caller's words.

---

## Test 1. What a caller hears when the AI is blocked at the usage limit

**The promise it protects.** `offer.md` section 6, Usage, and spec promise 3: at the cap the system stops, alerts the client, and calls "ring through to the client's own phone or voicemail as they did before".

**Who.** Diana in the account, Ray on the outside phone. About one hour.

### Steps in the account

1. Agency view. Open Settings, then the AI usage limits page. [verify menu name: "AI Usage Limits"]
2. Find NL Demo. Set its monthly limit to the lowest amount the field accepts (try $1). [verify menu name: the limit field]
3. Choose "Block AI at the limit". The default is notify only, so check it twice. [verify menu name]
4. Save. Note the time and the amount.
5. Set the "client's own phone" stand-in: on the second phone, set conditional forwarding (no answer, busy, unreachable) to the demo number, the way a client would. [verify with the carrier]
6. Leave NL Demo's voicemail and missed-call settings as the blueprint has them. Do not add a fallback yet. The first run records what HighLevel does by default.

### What to dial

1. From the outside phone, call the demo number and talk to the AI until the limit is used up. Keep a tally of minutes. Watch for the 70, 80, 90 and 100 percent alerts and note who receives each one (agency email, sub-account user, nobody).
2. When the account shows AI as blocked, hang up. Wait two minutes.
3. **Call A.** Call the demo number directly. Stay on the line for 60 seconds. Write down exactly what you hear, second by second: ringing, a voice, a greeting, silence, a tone, a hang-up.
4. **Call B.** Call the second phone and do not answer it, so the call forwards to the demo number. Write down the same.
5. Check the outside phone for a text (the missed-call text-back).
6. In NL Demo, open the conversation for the outside phone's number. Note what was logged: missed call, voicemail, nothing.
7. Raise the limit. Call the demo number again. Note how long until the AI answers.

### Pass or fail

| Result | Means |
|---|---|
| Pass | On call A and call B the caller reaches the client's own phone or voicemail, or hears a clear spoken message, and can leave a message or gets a text back. The call is logged in the account |
| Fail | Dead air, endless ringing, an error tone, a carrier error message, or a hang-up with nothing logged |
| Partial | A clear outcome on one call and not the other. Treat as fail until fixed |

Also record, pass or not: whether the dollar limit counted HighLevel's cost or the rebilled price (compare the minutes you used with the limit you set), and who received the alerts.

### If it fails

1. Build the fallback from blueprint 8, step 6: a voicemail greeting on the demo number recorded in the client's voice, and the missed-call text-back workflow. [verify menu name: the number's voicemail setting]
2. Run calls A and B again while AI is still blocked.
3. If the caller still gets dead air or an error: the only safe stop is the client switching forwarding off. Test that: dial the carrier's forwarding-off code on the second phone, call it, and confirm it rings and reaches its own voicemail.
4. Ask HighLevel support in writing what a caller is meant to hear when AI is blocked. Save the reply.

### What the offer wording changes to if it fails

Current words (`offer.md` section 6, spec promise 3): calls "ring through to the client's own phone or voicemail as they did before".

- If the voicemail fallback works: "When your cap is reached the AI stops answering. Callers reach a voicemail greeting in your voice and get a text back. You get a text and an email at once."
- If only switching forwarding off works: "When your cap is reached we text and email you at once. You switch forwarding off with one code and calls ring only your own phone. Until you do, callers reach a voicemail greeting."
- If neither works: the cap is not sold as a hard stop. The wording becomes "We alert you at 80 percent and at your cap. Minutes past the cap are billed at $0.30 CAD until you tell us to pause the line." Ray decides whether the offer still stands on those terms before any sale.

The cap-reached text and email in blueprint 8 change to match whichever line is true.

---

## Test 2. Recording off: is there still a transcript, a summary text and a summary email

**The promise it protects.** `offer.md` section 6, Recording, and spec promises 14 and 17: audio recording is off unless the client turns it on, and the client still gets the summary by text and by email.

**Who.** Diana. About 30 minutes.

### Steps in the account

1. NL Demo. Open Settings, then Phone Numbers, then the demo number's configuration. [verify menu name]
2. Set Call Recording to disabled. Save. [verify menu name: "Call Recording"]
3. Confirm the custom value `nl_recording_on` is "no" and `nl_recording_line` is empty.
4. Confirm `nl_summary_mobile` and `nl_summary_email` hold a phone and an inbox you can read.
5. Confirm `NL 01 | AI call finished` is published.

### What to dial

1. From the outside phone, call the demo number. Hold a normal two-minute call: give a name, say you want to buy, name an area and a timeline. Decline the booking.
2. Hang up. Start a timer.

### What to look at

1. The contact in NL Demo: is there a transcript on the call? Is `NL | Call summary` filled? Are `NL | Caller reason`, `NL | Area of interest` and `NL | Timeline` filled?
2. The Voice AI call log for the call: summary present, transcript present. [verify menu name: Voice AI dashboard or call logs]
3. The conversation thread and the call log entry: is there an audio file or a play button? There should be none.
4. The phone in `nl_summary_mobile`: did the summary text arrive, and how many seconds after the hang-up?
5. The inbox in `nl_summary_email`: did the summary email arrive?
6. Did the AI say anything about recording at the start? It should not.

### Pass or fail

| Result | Means |
|---|---|
| Pass | No audio file anywhere. Transcript present. Summary field filled. Summary text and summary email both arrived |
| Fail A | No transcript or no summary with recording off |
| Fail B | Transcript and summary exist but the text or the email did not arrive. This is a workflow fault, not a recording fault. Fix the workflow and run again |
| Fail C | An audio file exists even though recording was disabled |

### If it fails

- Fail A: switch recording on, repeat the call, and confirm the transcript and summary appear. That proves the transcript depends on the recording. Then look for a setting that deletes recordings automatically, and how soon. [verify menu name]
- Fail C: look for a second recording setting on the agent or at the agency level. Ask HighLevel support in writing. Do not go live while audio is kept against the stated wording. [verify menu name]

### What the offer wording changes to if it fails

Current words (`offer.md` section 6): "Audio recording is off unless the client turns it on, and when it is on the AI says so at the start of the call."

- Fail A, as the spec already sets out (promise 14): "Calls are recorded so the summary can be written. The recording is deleted within a day. The AI says the call is recorded at the start of every call." Then `nl_recording_on` becomes "yes" for every client, `nl_recording_line` is filled for every client, the deletion must itself be tested, and the recording line goes to counsel before any sale. [Ray to confirm with counsel]
- If recordings cannot be deleted within a day either: "Calls are recorded and the AI says so at the start of every call. You can delete any recording from your account." Ray decides whether to sell on that.
- The answer to "Is this legal? Recording calls, AI on the phone?" in the objections section changes to match.

---

## Test 3. SaaS usage limits: is the feature on Ray's plan, which currency, and does the client see a usage tab

**The promise it protects.** `offer.md` section 6, Usage, and spec promises 1, 2 and 6: 250 minutes included, extra minutes at $0.30 CAD, minutes shown to the client.

**Who.** Ray, logged in as the agency owner, with Diana. About 45 minutes. No phone call is needed for the first three parts.

### Part 1. Is the feature there

1. Agency view. Open Settings, then Labs. [verify menu name]
2. Look for "SaaS Usage Limits". Note: present or not, on or off, and any plan label beside it (the official page says beta, "Pro agencies").
3. If present, switch it on.
4. Agency view. Note the plan name shown under billing. [verify menu name]

### Part 2. Can a plan carry a Voice AI minute allowance

1. Open the SaaS Configurator. Open a test plan, or create one named "NL test plan, not for sale". [verify menu name]
2. Look for the usage or bundled pricing section. Is Voice AI listed? Can you type a monthly allowance in minutes? Type 3. [verify menu name]
3. Look for the overage rule. Are both "Bill" and "Block" offered? Choose Block for now.

### Part 3. Which currency is the per-minute rate in

1. In the same plan, change the overage rule to Bill and find the fixed rate per Voice AI minute. [verify menu name]
2. Write down the currency symbol or code shown beside the field, and any help text.
3. Type 0.30 and save. Open the plan again and read back what was stored.
4. Open the rebilling settings for NL Demo and read the Voice AI line: is the rate shown there in the same currency? [verify menu name]
5. If nothing on screen names the currency, check which currency the agency's Stripe account charges SaaS subscriptions in, and ask HighLevel support in writing. Do not guess.

### Part 4. Does the client see a usage tab

1. Attach the test plan to NL Demo. [verify menu name]
2. Create a user in NL Demo with the role a client would have, or use the client-view switch if there is one. [verify menu name]
3. Log in as that user in a private browser window. Look for a Usage tab, in Settings or under billing. [verify menu name]
4. Make one two-minute call to the demo number. After ten minutes, look at the tab again: are minutes used shown, against the allowance of 3? Is a part minute rounded up?
5. Take a screenshot with no caller details in view.
6. Set the plan back, or remove the test plan from NL Demo.

### Pass or fail

| Part | Pass | Fail |
|---|---|---|
| 1 | "SaaS Usage Limits" is in Labs on Ray's plan and switches on | Not listed, or greyed out with a plan upgrade message |
| 2 | A plan accepts a Voice AI allowance in minutes and offers Bill and Block | No minute allowance, or no Block |
| 3 | The currency of the rate is stated on screen or confirmed in writing by support | Unknown after both |
| 4 | A client-role user sees minutes used against the allowance | No tab, or a tab without Voice AI minutes |

### If it fails

- Part 1 or 2: use the fallback already in blueprint 8. The AI Usage Limit on the sub-account becomes the hard stop, set at the dollar value of 250 minutes plus the client's cap, with Block. Diana checks minutes by hand each Monday in the Voice AI dashboard and adds the `nl-usage-80` and `nl-usage-cap-reached` tags. Test 1 must pass for this fallback to hold.
- Part 3, US dollars: enter the US dollar amount that equals $0.30 CAD on the day, write the date and the exchange rate in the spec, and set a reminder to review it each quarter. [Ray to set: who reviews it]
- Part 4: the client gets their minutes in the monthly report and on the invoice instead. Check that the invoice does show minutes (spec promise 6). If it does not, a one-line usage statement is sent by hand with each invoice.

### What the offer wording changes to if it fails

Current words (`offer.md` section 6): "250 AI call minutes a month ... Extra minutes are $0.30 CAD each ... Minutes used are shown on each invoice."

- Parts 1 or 2 fail: the price and allowance wording can stay, because the fallback keeps the stop. Remove any line that says the client can watch usage live in their account. Add: "We check your minutes every week and tell you at 80 percent."
- Part 3, rate is in US dollars: either keep "$0.30 CAD" and accept that Ray absorbs the exchange difference, or change to "Extra minutes are billed at [US dollar figure] USD each, about $0.30 CAD", using the real figure of the day. [Ray to decide]
- Part 4 fails: replace any "see your usage in your account" line with "Your minutes used are on every invoice and in your monthly report." If the invoice cannot show minutes either: "We send your minutes used with every invoice."

---

## Results

Fill in one row per run. A test that was run twice gets two rows.

| Test | Date | Run by | Result (pass, fail, partial) | What happened, in one or two sentences | Offer wording changed? (no, or the new words and the date Ray approved them) |
|---|---|---|---|---|---|
| 1. Caller experience when AI is blocked: call A (direct) | | | | | |
| 1. Caller experience when AI is blocked: call B (forwarded) | | | | | |
| 1. Does the dollar limit count cost or rebilled price; who got the alerts | | | | | |
| 2. Recording off: transcript and summary field | | | | | |
| 2. Recording off: summary text and summary email | | | | | |
| 2. Recording off: no audio file | | | | | |
| 3. SaaS Usage Limits in Labs on Ray's plan | | | | | |
| 3. Minute allowance with Bill and Block | | | | | |
| 3. Currency of the per-minute rate | | | | | |
| 3. Client sees a usage tab | | | | | |

When every row has a pass, or a fail with new wording approved by Ray, replace the matching `[verify in HighLevel]` marks in `saas-build-spec.md` section 13 and `automation-blueprints.md` with the result and the date.
