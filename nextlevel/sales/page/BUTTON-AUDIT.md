# Next Level sales page: control audit

Rerun 2026-11-15 after the offer update (round 3 offer, four quiz paths), with Playwright Chromium against `index.html`, in the light theme and the dark theme, at 360, 390, 768, 1280 and 1440px wide. Every control was activated by mouse and by keyboard (Tab to it, then Enter, and Space where the control is a button, a toggle or a checkbox). "Fixed?" compares each control with the audit of the version before this update.

## Totals

| | Before this update | After this update |
|---|---|---|
| Distinct controls tested | 111 | **232** |
| Control runs (each control in 2 themes, by mouse and by keyboard) | 222 | **464** |
| Page-level checks | 86 (43 per theme) | **222** (111 per theme) |
| Quiz paths walked | 2 (agent, waitlist) | **6 walks of 4 paths** (agent; founding-business as a mortgage broker and as a contractor; waitlist with a date and with no date; us-list) |
| Controls failing | 0 | **0** |
| Page checks failing | 0 | **0** |

## What this rerun covered

- The full control audit from the earlier version, unchanged in method, on the updated page.
- Six walks of the intake, each by mouse and by keyboard, with every answer on every screen pressed, Back and Next checked, the contact step validated and every control in the result used:
  1. **agent** (solo agent, missed calls).
  2. **founding-business**, mortgage broker.
  3. **founding-business**, contractor or renovator.
  4. **waitlist with a date** (real estate lawyer): 1 March 2027 and the starting price.
  5. **waitlist with no date** ("Something else").
  6. **us-list** ("I am in the United States"): no price, no booking.
- The wording of each result, checked by rule: the two trade results must not contain "showing", "listing", "buyer" or "seller"; the waitlist and US list results must carry no founding price and no booking step; no result may say "at cost", "no markup" or mention a demo number.
- The webhook payload for each of the six walks against a stubbed endpoint: exactly one POST with consent, none without consent, and no network request at all while `WEBHOOK_URL` is empty. The payloads are printed at the end of this file.
- `CONFIG.DEMO_PHONE`: empty (nothing about a demo number anywhere) and set (a "Call the demo line" block with a `tel:` link under the hero buttons and in the buying results, not in the waitlist or US list results).
- No horizontal scroll, no clipped text and no console error at 360, 390, 768, 1280 and 1440px, on the page, the contact step and seven results, in both themes. Contrast was measured on every one of those screens.
- Tap targets on a 390px phone across all six walks.

## What was found in this rerun

Page failures: **none**. Every control and every page check passed on the first full run of the updated page.

Two faults were in the audit script, not the page, and were corrected before the final run:

| # | What the first run reported | Cause | Fix |
|---|---|---|---|
| 1 | "Result wording" failed on all six walks: "Copy NEXT" not found | The button label is shown in capitals by the stylesheet, and the rule compared case | The wording rules ignore case |
| 2 | "Clipped text" at every width: the "(opens in a new tab)" span | That span is the visually hidden label for screen readers | Visually hidden elements are left out of the clipped-text check |

Small changes to controls and labels made during this update, before the final run:

- The waitlist and US list results signed off "On your call: Ray, every time", although neither offers a call. They now read "Operated by Ray Ahmadi".
- The first quiz screen showed "Question 1 of 6" before the path was known. It now reads "Question 1" until the first answer is in.
- "Broker or brokerage owner" now reads "Real estate broker or brokerage owner", because "Mortgage broker" sits directly under it.
- A `[hidden]` rule was added to the page so the text-consent row stays hidden wherever the page is hosted.

Carried over from the earlier audit, still true: the wordmark is not a link; the side index is desktop only, so it has no phone tap size.

Still failing: nothing.

Limits of this audit: it runs in headless Chromium only (no Safari or Firefox, no real phone, no screen reader listening; "announced" means the message is in a role="alert" or role="status" region and focus moves to the field). The Instagram tab was opened against a stub, so the real Instagram page was not loaded. A failing webhook (non-200) retries once by design; "exactly one POST" was verified for a working endpoint. The `tel:` link was checked for its address, size and focus ring; no call was placed. The audit checks behaviour and wording rules. It does not check that the facts marked `[not verified]` in `offer.md` are true.


## Every control

Focus = the focus ring seen when tabbing to the control (outline width and its contrast against the surface behind it; 3:1 is the minimum). Tap size = smallest size measured on a 390px-wide phone.

| Element | Where | Expected | Result by mouse | Result by keyboard | Focus ring | Tap size at 390px | Pass | Fixed? What changed |
|---|---|---|---|---|---|---|---|---|
| 01 INTAKE | index | Scrolls to "quiz" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| 02 LEAKS | index | Scrolls to "leaks" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| 03 METHOD | index | Scrolls to "how" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| 04 FOUNDING 10 | index | Scrolls to "founding" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| 05 MENU | index | Scrolls to "menu" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| 06 RAY | index | Scrolls to "ray" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| 07 QUESTIONS | index | Scrolls to "faq" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| 08 BOOK | index | Scrolls to "book" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | No. Same control as the earlier version; passed then and passes now. |
| START THE INTAKE → | hero | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 203x56px | Pass | No. Same control as the earlier version; passed then and passes now. |
| SEE THE PRICES | hero | Scrolls to "menu" with its heading in view | Pass: section top at 0px, heading in view | Enter Pass: section top at 0px, heading in view | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 122x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| FIND MY BIGGEST LEAK → | leaks | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 239x56px | Pass | No. Same control as the earlier version; passed then and passes now. |
| BOOK 15 MINUTES WITH RAY → | founding | Scrolls to "book" with its heading in view | Pass: section top at 0px, heading in view | Enter Pass: section top at 0px, heading in view | light ring 2px, 8.26:1; dark ring 2px, 7.66:1 | 275x56px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Or start with the intake | founding | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 8.26:1; dark ring 2px, 7.66:1 | 155x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| I am in the United States | founding | Opens the US list question in the intake, with focus on it | Pass: intake at 215px from top, focus on #qt, question "What kind of business do you run in the United States?" | Enter Pass: intake at 215px from top, focus on #qt, question "What kind of business do you run in the United States?"; Space Pass: intake at 215px from top, focus on #qt, question "What kind of business do you run in the United States?" | light ring 2px, 8.26:1; dark ring 2px, 7.66:1 | 162x44px | Pass | New. Opens the US list question. |
| Will callers know it is an AI? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| What does it sound like? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| What is available today? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| What do the Founding 10 pay? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| What does Answer cost after the Founding 10? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Same control as the earlier version; passed then and passes now. |
| What does usage cost? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Is there a cheaper plan? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New in this update. |
| Is there a contract? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| How long does setup take? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Do I have to change my phone number? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Same control as the earlier version; passed then and passes now. |
| What do you need from me? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Does it speak other languages? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| I am on another CRM. Does this replace it? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Who can see my callers and my call transcripts? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Where is my data held? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New in this update. |
| Will my brokerage allow it? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Is it allowed where I work? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Do you have client testimonials? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| I run a team. How does that work? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| I am in the US. Can I join? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Who pays for the ads? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Does this promise me more leads or deals? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Do I have to join Ray's team? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Same control as the earlier version; passed then and passes now. |
| I run a business that is not real estate. Can I use it? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Same control as the earlier version; passed then and passes now. |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | book | Copies NEXT, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, rel noopener, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, rel noopener, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 311x56px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Not sure which problem is yours? Take the intake first. | book | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x48px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option A Solo agent → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option B Agent with an assistant → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option C Team leader → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option D Real estate broker or brokerage owner → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | Changed. The first screen now has eight answers; the rest of the agent path is as it was. |
| Option E Mortgage broker → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | Changed. The first screen now has eight answers; the rest of the agent path is as it was. |
| Option F Contractor or renovator → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | Changed. The first screen now has eight answers; the rest of the agent path is as it was. |
| Option G I run a different kind of business → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | Changed. The first screen now has eight answers; the rest of the agent path is as it was. |
| Option H I am in the United States → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run in the United States?"; Back (mouse) kept the answer | Space Pass: advanced to "What kind of business do you run in the United States?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | Changed. The first screen now has eight answers; the rest of the agent path is as it was. |
| Next | Intake, agent path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "A new buyer calls while you are in a showing. What happens?" | Enter Pass: moved forward to "A new buyer calls while you are in a showing. What happens?"; Space Pass: moved forward to "A new buyer calls while you are in a showing. What happens?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option A It goes to voicemail and I call back when I can. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Enter Pass: advanced to "When did you last ask a client for a Google review?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option B Someone on my team picks up. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Space Pass: advanced to "When did you last ask a client for a Google review?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option C I step out and take it. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Enter Pass: advanced to "When did you last ask a client for a Google review?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option D I am not sure how many I miss. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Space Pass: advanced to "When did you last ask a client for a Google review?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Next | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "When did you last ask a client for a Google review?" | Enter Pass: moved forward to "When did you last ask a client for a Google review?"; Space Pass: moved forward to "When did you last ask a client for a Google review?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Back (on this screen) | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option A At my last closing. I ask every time. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Enter Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option B A few months ago. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Space Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option C I cannot remember. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Enter Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option D I do not have a Google Business Profile set up. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Space Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Next | Intake, agent path: "When did you last ask a client for a Google review?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "Think about every contact in your database. How many heard from you in the last 90 days?" | Enter Pass: moved forward to "Think about every contact in your database. How many heard from you in the last 90 days?"; Space Pass: moved forward to "Think about every contact in your database. How many heard from you in the last 90 days?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Back (on this screen) | Intake, agent path: "When did you last ask a client for a Google review?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option A Most of them. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Are you running paid ads right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option B Some of them. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Are you running paid ads right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option C Very few. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Are you running paid ads right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option D I do not have them in one place. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Are you running paid ads right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Next | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "Are you running paid ads right now?" | Enter Pass: moved forward to "Are you running paid ads right now?"; Space Pass: moved forward to "Are you running paid ads right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Back (on this screen) | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option A Yes, and I know what each lead costs me. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Which one of these costs you the most right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option B Yes, and I do not know if they work. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Which one of these costs you the most right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option C I tried and stopped. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Which one of these costs you the most right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option D No, and I do not plan to. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Which one of these costs you the most right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Next | Intake, agent path: "Are you running paid ads right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "Which one of these costs you the most right now?" | Enter Pass: moved forward to "Which one of these costs you the most right now?"; Space Pass: moved forward to "Which one of these costs you the most right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Back (on this screen) | Intake, agent path: "Are you running paid ads right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option A Calls I do not get to. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option B Not enough reviews. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option C A database I never contact. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option D Ads that do not pay. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Next | Intake, agent path: "Which one of these costs you the most right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Back (on this screen) | Intake, agent path: "Which one of these costs you the most right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| First name (text field) | Intake, agent path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Email (text field) | Intake, agent path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Mobile, optional (text field) | Intake, agent path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Email consent checkbox | Intake, agent path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Text consent checkbox | Intake, agent path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | see note | Pass | No. Same control as the earlier version; passed then and passes now. |
| Back | Intake, agent path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "Which one of these costs you the most right now?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Show my result (submit) | Intake, agent path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | No. Same control as the earlier version; passed then and passes now. |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, agent path: result | Copies NEXT, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | 311x56px | Pass | No. Same control as the earlier version; passed then and passes now. |
| CHANGE MY ANSWERS | Intake, agent path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | No. Same control as the earlier version; passed then and passes now. |
| Option A Solo agent → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Agent with an assistant → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Team leader → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Real estate broker or brokerage owner → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option E Mortgage broker → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option F Contractor or renovator → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option G I run a different kind of business → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option H I am in the United States → | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run in the United States?"; Back (mouse) kept the answer | Space Pass: advanced to "What kind of business do you run in the United States?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What is your biggest phone problem right now?" | Enter Pass: moved forward to "What is your biggest phone problem right now?"; Space Pass: moved forward to "What is your biggest phone problem right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Option A Calls go to voicemail while I am working. → | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option B Calls in the evening and on weekends go unanswered. → | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option C I call back too late and they have moved on. → | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option D I answer everything myself and it pulls me off my work. → | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new client calls while you are with someone else. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Next | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "A new client calls while you are with someone else. What happens?" | Enter Pass: moved forward to "A new client calls while you are with someone else. What happens?"; Space Pass: moved forward to "A new client calls while you are with someone else. What happens?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Option A It goes to voicemail and I call back when I can. → | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option B Someone in the office picks up during the day. → | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option C An answering service takes a message. → | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option D I am not sure how many calls I miss. → | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| First name (text field) | Intake, founding-business (mortgage broker) path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email (text field) | Intake, founding-business (mortgage broker) path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Mobile, optional (text field) | Intake, founding-business (mortgage broker) path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email consent checkbox | Intake, founding-business (mortgage broker) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Text consent checkbox | Intake, founding-business (mortgage broker) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | see note | Pass | New in this update. |
| Back | Intake, founding-business (mortgage broker) path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "A new client calls while you are with someone else. What happens?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Show my result (submit) | Intake, founding-business (mortgage broker) path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | New in this update. |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, founding-business (mortgage broker) path: result | Copies NEXT, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | 311x56px | Pass | New in this update. |
| CHANGE MY ANSWERS | Intake, founding-business (mortgage broker) path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | New in this update. |
| Option A Solo agent → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Agent with an assistant → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Team leader → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Real estate broker or brokerage owner → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option E Mortgage broker → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option F Contractor or renovator → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option G I run a different kind of business → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option H I am in the United States → | Intake, founding-business (contractor) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run in the United States?"; Back (mouse) kept the answer | Space Pass: advanced to "What kind of business do you run in the United States?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, founding-business (contractor) path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What is your biggest phone problem right now?" | Enter Pass: moved forward to "What is your biggest phone problem right now?"; Space Pass: moved forward to "What is your biggest phone problem right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Option A Calls go to voicemail while I am working. → | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option B Calls in the evening and on weekends go unanswered. → | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option C I call back too late and they have moved on. → | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option D I answer everything myself and it pulls me off my work. → | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new customer calls while you are on a job site. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Next | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "A new customer calls while you are on a job site. What happens?" | Enter Pass: moved forward to "A new customer calls while you are on a job site. What happens?"; Space Pass: moved forward to "A new customer calls while you are on a job site. What happens?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Option A It goes to voicemail and I call back when I can. → | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option B Someone in the office picks up during the day. → | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option C An answering service takes a message. → | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option D I am not sure how many calls I miss. → | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| First name (text field) | Intake, founding-business (contractor) path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email (text field) | Intake, founding-business (contractor) path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Mobile, optional (text field) | Intake, founding-business (contractor) path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email consent checkbox | Intake, founding-business (contractor) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Text consent checkbox | Intake, founding-business (contractor) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | see note | Pass | New in this update. |
| Back | Intake, founding-business (contractor) path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "A new customer calls while you are on a job site. What happens?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Show my result (submit) | Intake, founding-business (contractor) path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | New in this update. |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, founding-business (contractor) path: result | Copies NEXT, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | 311x56px | Pass | New in this update. |
| CHANGE MY ANSWERS | Intake, founding-business (contractor) path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | New in this update. |
| Option A Solo agent → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Agent with an assistant → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Team leader → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Real estate broker or brokerage owner → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option E Mortgage broker → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option F Contractor or renovator → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option G I run a different kind of business → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option H I am in the United States → | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run in the United States?"; Back (mouse) kept the answer | Space Pass: advanced to "What kind of business do you run in the United States?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What kind of business do you run?" | Enter Pass: moved forward to "What kind of business do you run?"; Space Pass: moved forward to "What kind of business do you run?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Option A Real estate lawyer → | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Accountant → | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Insurance → | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Something else → | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What is your biggest phone problem right now?" | Enter Pass: moved forward to "What is your biggest phone problem right now?"; Space Pass: moved forward to "What is your biggest phone problem right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Option A Calls go to voicemail while I am working. → | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option B Calls in the evening and on weekends go unanswered. → | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option C I call back too late and they have moved on. → | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option D I answer everything myself and it pulls me off my work. → | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Next | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| First name (text field) | Intake, waitlist with a date (real estate lawyer) path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email (text field) | Intake, waitlist with a date (real estate lawyer) path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Mobile, optional (text field) | Intake, waitlist with a date (real estate lawyer) path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email consent checkbox | Intake, waitlist with a date (real estate lawyer) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Text consent checkbox | Intake, waitlist with a date (real estate lawyer) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | see note | Pass | New in this update. |
| Back | Intake, waitlist with a date (real estate lawyer) path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "What is your biggest phone problem right now?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Show my result (submit) | Intake, waitlist with a date (real estate lawyer) path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | New in this update. |
| COPY WAITLIST AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, waitlist with a date (real estate lawyer) path: result | Copies WAITLIST, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "WAITLIST", message "Copied WAITLIST. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "WAITLIST", message "Copied WAITLIST. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | 312x72px | Pass | New in this update. |
| CHANGE MY ANSWERS | Intake, waitlist with a date (real estate lawyer) path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | New in this update. |
| Option A Solo agent → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Agent with an assistant → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Team leader → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Real estate broker or brokerage owner → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option E Mortgage broker → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option F Contractor or renovator → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option G I run a different kind of business → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option H I am in the United States → | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run in the United States?"; Back (mouse) kept the answer | Space Pass: advanced to "What kind of business do you run in the United States?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, waitlist with no date (something else) path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What kind of business do you run?" | Enter Pass: moved forward to "What kind of business do you run?"; Space Pass: moved forward to "What kind of business do you run?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Option A Real estate lawyer → | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Accountant → | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Insurance → | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Something else → | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What is your biggest phone problem right now?" | Enter Pass: moved forward to "What is your biggest phone problem right now?"; Space Pass: moved forward to "What is your biggest phone problem right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Option A Calls go to voicemail while I am working. → | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option B Calls in the evening and on weekends go unanswered. → | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option C I call back too late and they have moved on. → | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option D I answer everything myself and it pulls me off my work. → | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Next | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| First name (text field) | Intake, waitlist with no date (something else) path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email (text field) | Intake, waitlist with no date (something else) path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Mobile, optional (text field) | Intake, waitlist with no date (something else) path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email consent checkbox | Intake, waitlist with no date (something else) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Text consent checkbox | Intake, waitlist with no date (something else) path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | see note | Pass | New in this update. |
| Back | Intake, waitlist with no date (something else) path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "What is your biggest phone problem right now?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Show my result (submit) | Intake, waitlist with no date (something else) path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | New in this update. |
| COPY WAITLIST AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, waitlist with no date (something else) path: result | Copies WAITLIST, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "WAITLIST", message "Copied WAITLIST. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "WAITLIST", message "Copied WAITLIST. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | 312x72px | Pass | New in this update. |
| CHANGE MY ANSWERS | Intake, waitlist with no date (something else) path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | New in this update. |
| Option A Solo agent → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Agent with an assistant → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Team leader → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Real estate broker or brokerage owner → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | New in this update. |
| Option E Mortgage broker → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "What is your biggest phone problem right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option F Contractor or renovator → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What is your biggest phone problem right now?"; Back (mouse) kept the answer | Space Pass: advanced to "What is your biggest phone problem right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option G I run a different kind of business → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option H I am in the United States → | Intake, us-list path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run in the United States?"; Back (mouse) kept the answer | Space Pass: advanced to "What kind of business do you run in the United States?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, us-list path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What kind of business do you run in the United States?" | Enter Pass: moved forward to "What kind of business do you run in the United States?"; Space Pass: moved forward to "What kind of business do you run in the United States?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Option A Real estate agent or team → | Intake, us-list path: "What kind of business do you run in the United States?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option B Mortgage broker → | Intake, us-list path: "What kind of business do you run in the United States?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option C Contractor or renovator → | Intake, us-list path: "What kind of business do you run in the United States?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Option D Another kind of business → | Intake, us-list path: "What kind of business do you run in the United States?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | New in this update. |
| Next | Intake, us-list path: "What kind of business do you run in the United States?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | New in this update. |
| Back (on this screen) | Intake, us-list path: "What kind of business do you run in the United States?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| First name (text field) | Intake, us-list path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email (text field) | Intake, us-list path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Mobile, optional (text field) | Intake, us-list path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Email consent checkbox | Intake, us-list path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | New in this update. |
| Text consent checkbox | Intake, us-list path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | see note | Pass | New in this update. |
| Back | Intake, us-list path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "What kind of business do you run in the United States?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | New in this update. |
| Show my result (submit) | Intake, us-list path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | New in this update. |
| COPY USLIST AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, us-list path: result | Copies USLIST, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "USLIST", message "Copied USLIST. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "USLIST", message "Copied USLIST. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | 312x72px | Pass | New in this update. |
| CHANGE MY ANSWERS | Intake, us-list path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | New in this update. |

## Page-level checks

| Check | Light | Dark | Detail |
|---|---|---|---|
| No click handlers on non-interactive elements (things that act clickable but are not controls) | Pass | Pass |  |
| No link with an empty or "#" href, and every in-page link has a target | Pass | Pass |  |
| Side index highlights the section in view (manual scroll to the middle of each) | Pass | Pass | quiz:quiz leaks:leaks how:how founding:founding menu:menu ray:ray faq:faq book:book |
| Side index text is at least 4.5:1 over every band while scrolling | Pass | Pass | Light: lowest 6:1 (01 Intake at y=1260) Dark: lowest 7.66:1 (04 Founding 10 at y=4860) |
| Nothing left invisible after scrolling the whole page | Pass | Pass |  |
| No console errors (page, all controls used) | Pass | Pass |  |
| No network requests beyond fonts while using the page (WEBHOOK_URL empty) | Pass | Pass |  |
| Cannot advance without a choice: agent "Which best describes you?" | Pass | Pass |  |
| Cannot advance without a choice: agent "A new buyer calls while you are in a showing. What happens?" | Pass | Pass |  |
| Cannot advance without a choice: agent "When did you last ask a client for a Google review?" | Pass | Pass |  |
| Cannot advance without a choice: agent "Think about every contact in your database. How many heard from you in the last 90 days?" | Pass | Pass |  |
| Cannot advance without a choice: agent "Are you running paid ads right now?" | Pass | Pass |  |
| Cannot advance without a choice: agent "Which one of these costs you the most right now?" | Pass | Pass |  |
| Consent boxes are never pre-ticked (agent path) | Pass | Pass | {"c":false,"s":false,"hid":true} |
| Text-message consent row shows only when a mobile number is typed, and clears with it (agent path) | Pass | Pass |  |
| Validation messages appear, are announced (role=alert) and move focus to the field (agent path) | Pass | Pass | empty name: "Add your first name so the result is written to you." focus #nl-name; bad email: "Enter a valid email, like name@example.com, or untick the box to see your result here only." focus #nl-email; aria-invalid true/true |
| No consent, WEBHOOK_URL empty: zero network requests on submit (agent path) | Pass | Pass |  |
| Result takes focus on its heading so it is announced (agent path) | Pass | Pass | focus on #rt |
| Result wording is right for the agent path | Pass | Pass | founding price, 250 minutes, $0.30, booking step; no demo line |
| Cannot advance without a choice: founding-business (mortgage broker) "Which best describes you?" | Pass | Pass |  |
| Cannot advance without a choice: founding-business (mortgage broker) "What is your biggest phone problem right now?" | Pass | Pass |  |
| Cannot advance without a choice: founding-business (mortgage broker) "A new client calls while you are with someone else. What happens?" | Pass | Pass |  |
| Consent boxes are never pre-ticked (founding-business (mortgage broker) path) | Pass | Pass | {"c":false,"s":false,"hid":true} |
| Text-message consent row shows only when a mobile number is typed, and clears with it (founding-business (mortgage broker) path) | Pass | Pass |  |
| Validation messages appear, are announced (role=alert) and move focus to the field (founding-business (mortgage broker) path) | Pass | Pass | empty name: "Add your first name so the result is written to you." focus #nl-name; bad email: "Enter a valid email, like name@example.com, or untick the box to see your result here only." focus #nl-email; aria-invalid true/true |
| No consent, WEBHOOK_URL empty: zero network requests on submit (founding-business (mortgage broker) path) | Pass | Pass |  |
| Result takes focus on its heading so it is announced (founding-business (mortgage broker) path) | Pass | Pass | focus on #rt |
| Result wording is right for the founding-business (mortgage broker) path | Pass | Pass | founding price and booking step, worded for a mortgage broker; no showing, listing, buyer or seller |
| Cannot advance without a choice: founding-business (contractor) "Which best describes you?" | Pass | Pass |  |
| Cannot advance without a choice: founding-business (contractor) "What is your biggest phone problem right now?" | Pass | Pass |  |
| Cannot advance without a choice: founding-business (contractor) "A new customer calls while you are on a job site. What happens?" | Pass | Pass |  |
| Consent boxes are never pre-ticked (founding-business (contractor) path) | Pass | Pass | {"c":false,"s":false,"hid":true} |
| Text-message consent row shows only when a mobile number is typed, and clears with it (founding-business (contractor) path) | Pass | Pass |  |
| Validation messages appear, are announced (role=alert) and move focus to the field (founding-business (contractor) path) | Pass | Pass | empty name: "Add your first name so the result is written to you." focus #nl-name; bad email: "Enter a valid email, like name@example.com, or untick the box to see your result here only." focus #nl-email; aria-invalid true/true |
| No consent, WEBHOOK_URL empty: zero network requests on submit (founding-business (contractor) path) | Pass | Pass |  |
| Result takes focus on its heading so it is announced (founding-business (contractor) path) | Pass | Pass | focus on #rt |
| Result wording is right for the founding-business (contractor) path | Pass | Pass | founding price and booking step, worded for a contractor; no showing, listing, buyer or seller |
| Cannot advance without a choice: waitlist with a date (real estate lawyer) "Which best describes you?" | Pass | Pass |  |
| Cannot advance without a choice: waitlist with a date (real estate lawyer) "What kind of business do you run?" | Pass | Pass |  |
| Cannot advance without a choice: waitlist with a date (real estate lawyer) "What is your biggest phone problem right now?" | Pass | Pass |  |
| Consent boxes are never pre-ticked (waitlist with a date (real estate lawyer) path) | Pass | Pass | {"c":false,"s":false,"hid":true} |
| Text-message consent row shows only when a mobile number is typed, and clears with it (waitlist with a date (real estate lawyer) path) | Pass | Pass |  |
| Validation messages appear, are announced (role=alert) and move focus to the field (waitlist with a date (real estate lawyer) path) | Pass | Pass | empty name: "Add your first name so the result is written to you." focus #nl-name; bad email: "Enter a valid email, like name@example.com, or untick the box to see your result here only." focus #nl-email; aria-invalid true/true |
| No consent, WEBHOOK_URL empty: zero network requests on submit (waitlist with a date (real estate lawyer) path) | Pass | Pass |  |
| Result takes focus on its heading so it is announced (waitlist with a date (real estate lawyer) path) | Pass | Pass | focus on #rt |
| Result wording is right for the waitlist with a date (real estate lawyer) path | Pass | Pass | 1 March 2027 and $500 setup plus $400 a month; no founding price, no booking |
| Cannot advance without a choice: waitlist with no date (something else) "Which best describes you?" | Pass | Pass |  |
| Cannot advance without a choice: waitlist with no date (something else) "What kind of business do you run?" | Pass | Pass |  |
| Cannot advance without a choice: waitlist with no date (something else) "What is your biggest phone problem right now?" | Pass | Pass |  |
| Consent boxes are never pre-ticked (waitlist with no date (something else) path) | Pass | Pass | {"c":false,"s":false,"hid":true} |
| Text-message consent row shows only when a mobile number is typed, and clears with it (waitlist with no date (something else) path) | Pass | Pass |  |
| Validation messages appear, are announced (role=alert) and move focus to the field (waitlist with no date (something else) path) | Pass | Pass | empty name: "Add your first name so the result is written to you." focus #nl-name; bad email: "Enter a valid email, like name@example.com, or untick the box to see your result here only." focus #nl-email; aria-invalid true/true |
| No consent, WEBHOOK_URL empty: zero network requests on submit (waitlist with no date (something else) path) | Pass | Pass |  |
| Result takes focus on its heading so it is announced (waitlist with no date (something else) path) | Pass | Pass | focus on #rt |
| Result wording is right for the waitlist with no date (something else) path | Pass | Pass | no date promised; no price for this business, no booking |
| Cannot advance without a choice: us-list "Which best describes you?" | Pass | Pass |  |
| Cannot advance without a choice: us-list "What kind of business do you run in the United States?" | Pass | Pass |  |
| Consent boxes are never pre-ticked (us-list path) | Pass | Pass | {"c":false,"s":false,"hid":true} |
| Text-message consent row shows only when a mobile number is typed, and clears with it (us-list path) | Pass | Pass |  |
| Validation messages appear, are announced (role=alert) and move focus to the field (us-list path) | Pass | Pass | empty name: "Add your first name so the result is written to you." focus #nl-name; bad email: "Enter a valid email, like name@example.com, or untick the box to see your result here only." focus #nl-email; aria-invalid true/true |
| No consent, WEBHOOK_URL empty: zero network requests on submit (us-list path) | Pass | Pass |  |
| Result takes focus on its heading so it is announced (us-list path) | Pass | Pass | focus on #rt |
| Result wording is right for the us-list path | Pass | Pass | Canada only, US list, told by 1 March 2027; no price, no booking |
| No console errors (intake, all six walks) | Pass | Pass |  |
| No network requests beyond fonts during the whole intake (WEBHOOK_URL empty) | Pass | Pass |  |
| Stubbed endpoint, consent not ticked: no request is sent (agent) | Pass | Pass | 0 requests |
| Stubbed endpoint, consent ticked: exactly one POST with the right payload (agent) | Pass | Pass | 1 POST of 1 requests; path agent; industry real-estate; tags ["nl-problem-reviews","nl-seg-solo","nl-flag-calls","nl-flag-database","nl-flag-ads"]; business_type "Solo agent"; biggest_problem "Not enough reviews"; fields name,email,phone,business_type,biggest_problem,answers,secondary_flags,tags,path,industry,consent_email,consent_sms,source,location_id,page,submitted_at |
| WEBHOOK_URL empty, consent ticked: zero network requests (agent) | Pass | Pass |  |
| Stubbed endpoint, consent not ticked: no request is sent (founding-business, mortgage broker) | Pass | Pass | 0 requests |
| Stubbed endpoint, consent ticked: exactly one POST with the right payload (founding-business, mortgage broker) | Pass | Pass | 1 POST of 1 requests; path founding-business; industry mortgage; tags ["nl-founding-business","nl-founding-business-mortgage","nl-phone-voicemail"]; business_type "Mortgage broker"; biggest_problem "Calls go to voicemail while I am working"; fields name,email,phone,business_type,biggest_problem,answers,secondary_flags,tags,path,industry,consent_email,consent_sms,source,location_id,page,submitted_at |
| WEBHOOK_URL empty, consent ticked: zero network requests (founding-business, mortgage broker) | Pass | Pass |  |
| Stubbed endpoint, consent not ticked: no request is sent (founding-business, contractor) | Pass | Pass | 0 requests |
| Stubbed endpoint, consent ticked: exactly one POST with the right payload (founding-business, contractor) | Pass | Pass | 1 POST of 1 requests; path founding-business; industry contractor; tags ["nl-founding-business","nl-founding-business-contractor","nl-phone-afterhours"]; business_type "Contractor or renovator"; biggest_problem "Calls in the evening and on weekends go unanswered"; fields name,email,phone,business_type,biggest_problem,answers,secondary_flags,tags,path,industry,consent_email,consent_sms,source,location_id,page,submitted_at |
| WEBHOOK_URL empty, consent ticked: zero network requests (founding-business, contractor) | Pass | Pass |  |
| Stubbed endpoint, consent not ticked: no request is sent (waitlist with a date) | Pass | Pass | 0 requests |
| Stubbed endpoint, consent ticked: exactly one POST with the right payload (waitlist with a date) | Pass | Pass | 1 POST of 1 requests; path waitlist; industry lawyer; tags ["nl-waitlist","nl-waitlist-lawyer"]; business_type "Real estate lawyer"; biggest_problem "I call back too late and they have moved on"; fields name,email,phone,business_type,biggest_problem,answers,secondary_flags,tags,path,industry,consent_email,consent_sms,source,location_id,page,submitted_at |
| After a sent sign-up the result confirms it and drops the Instagram step (waitlist with a date) | Pass | Pass |  |
| WEBHOOK_URL empty, consent ticked: zero network requests (waitlist with a date) | Pass | Pass |  |
| Stubbed endpoint, consent not ticked: no request is sent (waitlist with no date) | Pass | Pass | 0 requests |
| Stubbed endpoint, consent ticked: exactly one POST with the right payload (waitlist with no date) | Pass | Pass | 1 POST of 1 requests; path waitlist; industry other; tags ["nl-waitlist","nl-waitlist-other"]; business_type "Something else"; biggest_problem "I answer everything myself and it pulls me off my work"; fields name,email,phone,business_type,biggest_problem,answers,secondary_flags,tags,path,industry,consent_email,consent_sms,source,location_id,page,submitted_at |
| After a sent sign-up the result confirms it and drops the Instagram step (waitlist with no date) | Pass | Pass |  |
| WEBHOOK_URL empty, consent ticked: zero network requests (waitlist with no date) | Pass | Pass |  |
| Stubbed endpoint, consent not ticked: no request is sent (us-list) | Pass | Pass | 0 requests |
| Stubbed endpoint, consent ticked: exactly one POST with the right payload (us-list) | Pass | Pass | 1 POST of 1 requests; path us-list; industry real-estate; tags ["nl-us-list","nl-us-list-real-estate"]; business_type "Real estate agent or team"; biggest_problem ""; fields name,email,phone,business_type,biggest_problem,answers,secondary_flags,tags,path,industry,consent_email,consent_sms,source,location_id,page,submitted_at |
| After a sent sign-up the result confirms it and drops the Instagram step (us-list) | Pass | Pass |  |
| WEBHOOK_URL empty, consent ticked: zero network requests (us-list) | Pass | Pass |  |
| Text consent is sent as true only when its box is ticked, with the number | Pass | Pass | consent_sms true, phone 4165550100 |
| With BOOKING_URL set, the booking button links to it in a new tab with rel=noopener | Pass | Pass | {"href":"https://cal.test/ray","t":"_blank","rel":"noopener","copy":""} |
| With BOOKING_URL set, the US list result still has no booking link | Pass | Pass |  |
| DEMO_PHONE empty: nothing about a demo number anywhere (page and result), and the "dial the live system yourself" line is still there | Pass | Pass | [{"n":0,"t":false},{"n":0,"t":false}] |
| DEMO_PHONE set: a "Call the demo line" block with a tel: link shows near the hero and in the agent result (390px, 44px target, focus ring) | Pass | Pass | Light: hero [{"where":"hero","href":"tel:+14165550100","text":"CALL THE DEMO LINE +1 416 555 0100 Dial it before you book anything and hear the AI answer.","w":185,"h":44}]; result [{"where":"result","href":"tel:+14165550100","text":"CALL THE DEMO LINE +1 416 555 0100 Dial it before you book anything and hear the AI answer.","w":185,"h":44}]; ring 2px 6.54:1 Dark: hero [{"where":"hero","href":"tel:+14165550100","text":"CALL THE DEMO LINE +1 416 555 0100 Dial it before you book anything and hear the AI answer.","w":185,"h":44}]; result [{"where":"result","href":"tel:+14165550100","text":"CALL T |
| DEMO_PHONE set: a "Call the demo line" block with a tel: link shows near the hero and in the mortgage result (390px, 44px target, focus ring) | Pass | Pass | Light: hero [{"where":"hero","href":"tel:+14165550100","text":"CALL THE DEMO LINE +1 416 555 0100 Dial it before you book anything and hear the AI answer.","w":185,"h":44}]; result [{"where":"result","href":"tel:+14165550100","text":"CALL THE DEMO LINE +1 416 555 0100 Dial it before you book anything and hear the AI answer.","w":185,"h":44}]; ring 2px 6.54:1 Dark: hero [{"where":"hero","href":"tel:+14165550100","text":"CALL THE DEMO LINE +1 416 555 0100 Dial it before you book anything and hear the AI answer.","w":185,"h":44}]; result [{"where":"result","href":"tel:+14165550100","text":"CALL T |
| DEMO_PHONE set: no demo block in the waitlist result (nothing to buy there) | Pass | Pass |  |
| DEMO_PHONE set: no demo block in the US list result (nothing to buy there) | Pass | Pass |  |
| DEMO_PHONE set: contrast AA, no horizontal scroll at 390px, no console errors | Pass | Pass |   |
| Phone (touch) walk through the intake reaches the result (agent) | Pass | Pass |  |
| Phone (touch) walk through the intake reaches the result (founding-business (mortgage broker)) | Pass | Pass |  |
| Phone (touch) walk through the intake reaches the result (founding-business (contractor)) | Pass | Pass |  |
| Phone (touch) walk through the intake reaches the result (waitlist with a date (real estate lawyer)) | Pass | Pass |  |
| Phone (touch) walk through the intake reaches the result (waitlist with no date (something else)) | Pass | Pass |  |
| Phone (touch) walk through the intake reaches the result (us-list) | Pass | Pass |  |
| Tap targets are at least 44px on a 390px phone (127 measured, every screen) | Pass | Pass |  |
| No console errors (phone) | Pass | Pass |  |
| No horizontal scroll, clipped text or console error at 360px (page, contact step and all seven results) | Pass | Pass | page 360/360, contact step 360/360, agent result 360/360, team result 360/360, mortgage result 360/360, contractor result 360/360, dated waitlist result 360/360, undated waitlist result 360/360, US list result 360/360 |
| No horizontal scroll, clipped text or console error at 390px (page, contact step and all seven results) | Pass | Pass | page 390/390, contact step 390/390, agent result 390/390, team result 390/390, mortgage result 390/390, contractor result 390/390, dated waitlist result 390/390, undated waitlist result 390/390, US list result 390/390 |
| No horizontal scroll, clipped text or console error at 768px (page, contact step and all seven results) | Pass | Pass | page 768/768, contact step 768/768, agent result 768/768, team result 768/768, mortgage result 768/768, contractor result 768/768, dated waitlist result 768/768, undated waitlist result 768/768, US list result 768/768 |
| No horizontal scroll, clipped text or console error at 1280px (page, contact step and all seven results) | Pass | Pass | page 1280/1280, contact step 1280/1280, agent result 1280/1280, team result 1280/1280, mortgage result 1280/1280, contractor result 1280/1280, dated waitlist result 1280/1280, undated waitlist result 1280/1280, US list result 1280/1280 |
| No horizontal scroll, clipped text or console error at 1440px (page, contact step and all seven results) | Pass | Pass | page 1440/1440, contact step 1440/1440, agent result 1440/1440, team result 1440/1440, mortgage result 1440/1440, contractor result 1440/1440, dated waitlist result 1440/1440, undated waitlist result 1440/1440, US list result 1440/1440 |
| prefers-reduced-motion: nothing animates, and the intake, anchors and FAQ all still work | Pass | Pass | running animations 0, marquee animation none, result true, anchor top 0px, FAQ open true |
| No console errors (reduced motion) | Pass | Pass |  |
| Text and button-label contrast meets AA (36 colour pairs measured from the rendered page, every screen and result, at 360 to 1440px) | Pass | FAIL | lowest 3.45:1 (#f2551c on #ffffff, span.num "3") |
| Text and button-label contrast meets AA (46 colour pairs measured from the rendered page, every screen and result, at 360 to 1440px) | FAIL | Pass | Light:  Dark: lowest 5.19:1 (#93a6ff on #253270, span.no "04") |

## Tap targets on a 390px phone

Every visible control on the page and on every intake screen. Checkboxes are measured by their whole label, which is the tap area.

| Control | Screen | Size |
|---|---|---|
| START THE INTAKE → | page | 203x56px |
| SEE THE PRICES | page | 122x44px |
| FIND MY BIGGEST LEAK → | page | 239x56px |
| BOOK 15 MINUTES WITH RAY → | page | 275x56px |
| Or start with the intake | page | 155x44px |
| I am in the United States | page | 162x44px |
| Will callers know it is an AI? | page | 358x64px |
| What does it sound like? | page | 358x64px |
| What is available today? | page | 358x64px |
| What do the Founding 10 pay? | page | 358x64px |
| What does Answer cost after the Founding 10? | page | 358x88px |
| What does usage cost? | page | 358x64px |
| Is there a cheaper plan? | page | 358x64px |
| Is there a contract? | page | 358x64px |
| How long does setup take? | page | 358x64px |
| Do I have to change my phone number? | page | 358x88px |
| What do you need from me? | page | 358x64px |
| Does it speak other languages? | page | 358x64px |
| I am on another CRM. Does this replace it? | page | 358x88px |
| Who can see my callers and my call transcripts? | page | 358x88px |
| Where is my data held? | page | 358x64px |
| Will my brokerage allow it? | page | 358x64px |
| Is it allowed where I work? | page | 358x64px |
| Do you have client testimonials? | page | 358x64px |
| I run a team. How does that work? | page | 358x64px |
| I am in the US. Can I join? | page | 358x64px |
| Who pays for the ads? | page | 358x64px |
| Does this promise me more leads or deals? | page | 358x88px |
| Do I have to join Ray's team? | page | 358x64px |
| I run a business that is not real estate. Can I use it? | page | 358x88px |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | page | 311x56px |
| Not sure which problem is yours? Take the intake first. | page | 358x48px |
| A Solo agent → | Which best describes you? | 358x62px |
| B Agent with an assistant → | Which best describes you? | 358x62px |
| C Team leader → | Which best describes you? | 358x62px |
| D Real estate broker or brokerage owner → | Which best describes you? | 358x84px |
| E Mortgage broker → | Which best describes you? | 358x62px |
| F Contractor or renovator → | Which best describes you? | 358x62px |
| G I run a different kind of business → | Which best describes you? | 358x62px |
| H I am in the United States → | Which best describes you? | 358x62px |
| A It goes to voicemail and I call back when I can. → | A new buyer calls while you are in a showing. What happens? | 358x84px |
| B Someone on my team picks up. → | A new buyer calls while you are in a showing. What happens? | 358x62px |
| C I step out and take it. → | A new buyer calls while you are in a showing. What happens? | 358x62px |
| D I am not sure how many I miss. → | A new buyer calls while you are in a showing. What happens? | 358x62px |
| BACK | A new buyer calls while you are in a showing. What happens? | 44x44px |
| A It goes to voicemail and I call back when I can. → | after Back | 358x84px |
| B Someone on my team picks up. → | after Back | 358x62px |
| C I step out and take it. → | after Back | 358x62px |
| D I am not sure how many I miss. → | after Back | 358x62px |
| BACK | after Back | 44x44px |
| NEXT → | after Back | 54x44px |
| A At my last closing. I ask every time. → | When did you last ask a client for a Google review? | 358x62px |
| B A few months ago. → | When did you last ask a client for a Google review? | 358x62px |
| C I cannot remember. → | When did you last ask a client for a Google review? | 358x62px |
| D I do not have a Google Business Profile set up. → | When did you last ask a client for a Google review? | 358x84px |
| BACK | When did you last ask a client for a Google review? | 44x44px |
| A Most of them. → | Think about every contact in your database. How many heard from you in the last 90 days? | 358x62px |
| B Some of them. → | Think about every contact in your database. How many heard from you in the last 90 days? | 358x62px |
| C Very few. → | Think about every contact in your database. How many heard from you in the last 90 days? | 358x62px |
| D I do not have them in one place. → | Think about every contact in your database. How many heard from you in the last 90 days? | 358x62px |
| BACK | Think about every contact in your database. How many heard from you in the last 90 days? | 44x44px |
| A Yes, and I know what each lead costs me. → | Are you running paid ads right now? | 358x84px |
| B Yes, and I do not know if they work. → | Are you running paid ads right now? | 358x62px |
| C I tried and stopped. → | Are you running paid ads right now? | 358x62px |
| D No, and I do not plan to. → | Are you running paid ads right now? | 358x62px |
| BACK | Are you running paid ads right now? | 44x44px |
| A Calls I do not get to. → | Which one of these costs you the most right now? | 358x62px |
| B Not enough reviews. → | Which one of these costs you the most right now? | 358x62px |
| C A database I never contact. → | Which one of these costs you the most right now? | 358x62px |
| D Ads that do not pay. → | Which one of these costs you the most right now? | 358x62px |
| BACK | Which one of these costs you the most right now? | 44x44px |
| FIRST NAME | contact step | 358x55px |
| EMAIL | contact step | 358x55px |
| MOBILE (OPTIONAL) | contact step | 358x55px |
| Yes, email me my result and follow-up from Next Level. I can unsubscri | contact step | 358x62px |
| SHOW MY RESULT → | contact step | 185x56px |
| BACK | contact step | 44x44px |
| Yes, you may text me at this number about my result. Reply STOP to end | contact step | 358x62px |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | result, agent | 311x56px |
| CHANGE MY ANSWERS | result, agent | 149x44px |
| A Calls go to voicemail while I am working. → | What is your biggest phone problem right now? | 358x84px |
| B Calls in the evening and on weekends go unanswered. → | What is your biggest phone problem right now? | 358x84px |
| C I call back too late and they have moved on. → | What is your biggest phone problem right now? | 358x84px |
| D I answer everything myself and it pulls me off my work. → | What is your biggest phone problem right now? | 358x84px |
| BACK | What is your biggest phone problem right now? | 44x44px |
| A Calls go to voicemail while I am working. → | after Back | 358x84px |
| B Calls in the evening and on weekends go unanswered. → | after Back | 358x84px |
| C I call back too late and they have moved on. → | after Back | 358x84px |
| D I answer everything myself and it pulls me off my work. → | after Back | 358x84px |
| A It goes to voicemail and I call back when I can. → | A new client calls while you are with someone else. What happens? | 358x84px |
| B Someone in the office picks up during the day. → | A new client calls while you are with someone else. What happens? | 358x84px |
| C An answering service takes a message. → | A new client calls while you are with someone else. What happens? | 358x84px |
| D I am not sure how many calls I miss. → | A new client calls while you are with someone else. What happens? | 358x62px |
| BACK | A new client calls while you are with someone else. What happens? | 44x44px |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | result, founding-business (mortgage broker) | 311x56px |
| CHANGE MY ANSWERS | result, founding-business (mortgage broker) | 149x44px |
| A It goes to voicemail and I call back when I can. → | A new customer calls while you are on a job site. What happens? | 358x84px |
| B Someone in the office picks up during the day. → | A new customer calls while you are on a job site. What happens? | 358x84px |
| C An answering service takes a message. → | A new customer calls while you are on a job site. What happens? | 358x84px |
| D I am not sure how many calls I miss. → | A new customer calls while you are on a job site. What happens? | 358x62px |
| BACK | A new customer calls while you are on a job site. What happens? | 44x44px |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | result, founding-business (contractor) | 311x56px |
| CHANGE MY ANSWERS | result, founding-business (contractor) | 149x44px |
| A Real estate lawyer → | What kind of business do you run? | 358x62px |
| B Accountant → | What kind of business do you run? | 358x62px |
| C Insurance → | What kind of business do you run? | 358x62px |
| D Something else → | What kind of business do you run? | 358x62px |
| BACK | What kind of business do you run? | 44x44px |
| A Real estate lawyer → | after Back | 358x62px |
| B Accountant → | after Back | 358x62px |
| C Insurance → | after Back | 358x62px |
| D Something else → | after Back | 358x62px |
| COPY WAITLIST AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | result, waitlist with a date (real estate lawyer) | 312x72px |
| CHANGE MY ANSWERS | result, waitlist with a date (real estate lawyer) | 149x44px |
| COPY WAITLIST AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | result, waitlist with no date (something else) | 312x72px |
| CHANGE MY ANSWERS | result, waitlist with no date (something else) | 149x44px |
| A Real estate agent or team → | What kind of business do you run in the United States? | 358x62px |
| B Mortgage broker → | What kind of business do you run in the United States? | 358x62px |
| C Contractor or renovator → | What kind of business do you run in the United States? | 358x62px |
| D Another kind of business → | What kind of business do you run in the United States? | 358x62px |
| BACK | What kind of business do you run in the United States? | 44x44px |
| A Real estate agent or team → | after Back | 358x62px |
| B Mortgage broker → | after Back | 358x62px |
| C Contractor or renovator → | after Back | 358x62px |
| D Another kind of business → | after Back | 358x62px |
| COPY USLIST AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | result, us-list | 312x72px |
| CHANGE MY ANSWERS | result, us-list | 149x44px |

## Contrast, measured from the rendered page

Each row is a text colour on the surface behind it, as computed by the browser, on the page, every intake screen and the result. AA needs 4.5:1, or 3:1 for large text (24px and up).

### Light theme

| Text | On | Ratio | Needs | Example |
|---|---|---|---|---|
| `#f2551c` | `#ffffff` | 3.45:1 | 3:1 | span.num "3" |
| `#c2410c` | `#fff1ea` | 4.69:1 | 4.5:1 | span.tag "Opening next" |
| `#1f3fff` | `#e9edff` | 5.61:1 | 4.5:1 | span.tag "Available now" |
| `#93a6ff` | `#1c2a6e` | 5.67:1 | 4.5:1 | span.no "04" |
| `#93a6ff` | `#1c2a6e` | 5.67:1 | 3:1 | sup "$" |
| `#1f3fff` | `#f2f5ff` | 6:1 | 4.5:1 | span.no "01" |
| `#1f3fff` | `#f2f5ff` | 6:1 | 3:1 | em "One brief." |
| `#555c6e` | `#f2f5ff` | 6.14:1 | 4.5:1 | span.label "The intake" |
| `#aab2c8` | `#1c2a6e` | 6.15:1 | 4.5:1 | span.label "The Founding 10" |
| `#555c6e` | `#f4f6fc` | 6.18:1 | 4.5:1 | span.tag "When all four are open" |
| `#1f3fff` | `#ffffff` | 6.54:1 | 4.5:1 | a "08 Book" |
| `#1f3fff` | `#ffffff` | 6.54:1 | 3:1 | em "your phone?" |
| `#ffffff` | `#1f3fff` | 6.54:1 | 4.5:1 | button.btn "Start the intake" |
| `#ffffff` | `#1f3fff` | 6.54:1 | 3:1 | span "Answered." |
| `#2040fc` | `#ffffff` | 6.56:1 | 4.5:1 | a "01 Intake" |
| `#555c6e` | `#ffffff` | 6.68:1 | 4.5:1 | a "01 Intake" |
| `#555c6e` | `#ffffff` | 6.68:1 | 3:1 | li "Real estate lawyers" |
| `#2341f4` | `#ffffff` | 6.7:1 | 4.5:1 | a "01 Intake" |
| `#545b71` | `#ffffff` | 6.75:1 | 4.5:1 | a "02 Leaks" |
| `#515a79` | `#ffffff` | 6.8:1 | 4.5:1 | a "02 Leaks" |
| `#2743ea` | `#ffffff` | 6.82:1 | 4.5:1 | a "08 Book" |
| `#2a45e2` | `#ffffff` | 6.89:1 | 4.5:1 | a "08 Book" |
| `#2d47d9` | `#ffffff` | 6.97:1 | 4.5:1 | a "08 Book" |
| `#3048d1` | `#ffffff` | 7.06:1 | 4.5:1 | a "02 Leaks" |
| `#44539c` | `#ffffff` | 7.09:1 | 4.5:1 | a "01 Intake" |
| `#3e50ac` | `#ffffff` | 7.12:1 | 4.5:1 | a "01 Intake" |
| `#364bc1` | `#ffffff` | 7.16:1 | 4.5:1 | a "02 Leaks" |
| `#0a0f24` | `#93a6ff` | 8.26:1 | 4.5:1 | .btn hover/focus fill "BOOK 15 MINUTES WITH RAY" |
| `#ffffff` | `#1c2a6e` | 13.04:1 | 3:1 | span "300" |
| `#ffffff` | `#1c2a6e` | 13.04:1 | 4.5:1 | h3 "No setup fee" |
| `#0b0d17` | `#f2f5ff` | 17.78:1 | 3:1 | h2 "Six questions." |
| `#0b0d17` | `#f2f5ff` | 17.78:1 | 4.5:1 | span "Real estate agent or team" |
| `#0a0f24` | `#ffffff` | 18.98:1 | 4.5:1 | a.btn "Book 15 minutes with Ray" |
| `#0b0d17` | `#ffffff` | 19.37:1 | 4.5:1 | span "Next" |
| `#0b0d17` | `#ffffff` | 19.37:1 | 3:1 | span "You were in" |
| `#ffffff` | `#0b0d17` | 19.37:1 | 4.5:1 | .btn hover/focus fill "START THE INTAKE →" |

### Dark theme

| Text | On | Ratio | Needs | Example |
|---|---|---|---|---|
| `#93a6ff` | `#253270` | 5.19:1 | 4.5:1 | span.no "04" |
| `#93a6ff` | `#253270` | 5.19:1 | 3:1 | sup "$" |
| `#aab2c8` | `#253270` | 5.63:1 | 4.5:1 | span.label "The Founding 10" |
| `#ffffff` | `#2a48ff` | 6.05:1 | 4.5:1 | span "2:14 pm, the same call" |
| `#ffffff` | `#2a48ff` | 6.05:1 | 3:1 | span "Answered." |
| `#1f3fff` | `#f6f8fd` | 6.15:1 | 4.5:1 | span.res-kicker "Available now: the Founding " |
| `#1f3fff` | `#f6f8fd` | 6.15:1 | 3:1 | span.amt "$300 a month" |
| `#f6f8fd` | `#1f3fff` | 6.15:1 | 4.5:1 | a.btn "Copy NEXT and open Instagram" |
| `#555c6e` | `#f6f8fd` | 6.29:1 | 4.5:1 | span.label "Intake brief" |
| `#93a6ff` | `#171d3d` | 7.14:1 | 4.5:1 | span.tag "Available now" |
| `#ff7a4d` | `#090b14` | 7.61:1 | 3:1 | span.num "3" |
| `#a3abc0` | `#11152a` | 7.85:1 | 4.5:1 | span.tag "When all four are open" |
| `#93a6ff` | `#0f1324` | 8.02:1 | 4.5:1 | span.no "01" |
| `#93a6ff` | `#0f1324` | 8.02:1 | 3:1 | em "One brief." |
| `#a3abc0` | `#0f1324` | 8.03:1 | 4.5:1 | span.label "The intake" |
| `#0a0f24` | `#93a6ff` | 8.26:1 | 4.5:1 | .btn hover/focus fill "BOOK 15 MINUTES WITH RAY" |
| `#9aa8e2` | `#090b14` | 8.48:1 | 4.5:1 | a "01 Intake" |
| `#9ba8e1` | `#090b14` | 8.49:1 | 4.5:1 | a "02 Leaks" |
| `#94a6fa` | `#090b14` | 8.5:1 | 4.5:1 | a "01 Intake" |
| `#97a7ef` | `#090b14` | 8.5:1 | 4.5:1 | a "08 Book" |
| `#a1aaca` | `#090b14` | 8.52:1 | 4.5:1 | a "02 Leaks" |
| `#95a7f5` | `#090b14` | 8.53:1 | 4.5:1 | a "01 Intake" |
| `#9ba9de` | `#090b14` | 8.53:1 | 4.5:1 | a "01 Intake" |
| `#93a6fe` | `#090b14` | 8.53:1 | 4.5:1 | a "01 Intake" |
| `#96a7f3` | `#090b14` | 8.53:1 | 4.5:1 | a "08 Book" |
| `#93a6ff` | `#090b14` | 8.54:1 | 4.5:1 | a "08 Book" |
| `#93a6ff` | `#090b14` | 8.54:1 | 3:1 | em "your phone?" |
| `#090b14` | `#93a6ff` | 8.54:1 | 4.5:1 | button.btn "Start the intake" |
| `#9ca9dd` | `#090b14` | 8.54:1 | 4.5:1 | a "02 Leaks" |
| `#95a7f6` | `#090b14` | 8.54:1 | 4.5:1 | a "08 Book" |
| `#a3abc0` | `#090b14` | 8.55:1 | 4.5:1 | a "01 Intake" |
| `#a3abc0` | `#090b14` | 8.55:1 | 3:1 | li "Real estate lawyers" |
| `#a3abc1` | `#090b14` | 8.56:1 | 4.5:1 | a "02 Leaks" |
| `#a2abc5` | `#090b14` | 8.57:1 | 4.5:1 | a "02 Leaks" |
| `#ffa27d` | `#2a1810` | 8.67:1 | 4.5:1 | span.tag "Opening next" |
| `#ffffff` | `#253270` | 11.92:1 | 3:1 | span "300" |
| `#ffffff` | `#253270` | 11.92:1 | 4.5:1 | h3 "No setup fee" |
| `#f3f5fb` | `#0f1324` | 16.91:1 | 3:1 | h2 "Six questions." |
| `#f3f5fb` | `#0f1324` | 16.91:1 | 4.5:1 | span "Real estate agent or team" |
| `#f3f5fb` | `#090b14` | 18.01:1 | 4.5:1 | span "Next" |
| `#f3f5fb` | `#090b14` | 18.01:1 | 3:1 | span "You were in" |
| `#0b0d17` | `#f6f8fd` | 18.23:1 | 4.5:1 | span "Next" |
| `#0b0d17` | `#f6f8fd` | 18.23:1 | 3:1 | h3 "Your biggest leak: calls you" |
| `#f6f8fd` | `#0b0d17` | 18.23:1 | 4.5:1 | .btn hover/focus fill "COPY NEXT AND OPEN INSTA" |
| `#0a0f24` | `#ffffff` | 18.98:1 | 4.5:1 | a.btn "Book 15 minutes with Ray" |
| `#090b14` | `#ffffff` | 19.63:1 | 4.5:1 | .btn hover/focus fill "START THE INTAKE →" |


## Webhook payload for each path

Captured from the single POST the page made to a stubbed endpoint with the email consent box ticked. Name and email are test values.

### agent

```json
{
 "name": "Sam",
 "email": "sam@example.com",
 "phone": "",
 "business_type": "Solo agent",
 "biggest_problem": "Not enough reviews",
 "answers": {
  "who": {
   "question": "Which best describes you?",
   "answer": "Solo agent"
  },
  "q1": {
   "question": "A new buyer calls while you are in a showing. What happens?",
   "answer": "It goes to voicemail and I call back when I can."
  },
  "q2": {
   "question": "When did you last ask a client for a Google review?",
   "answer": "A few months ago."
  },
  "q3": {
   "question": "Think about every contact in your database. How many heard from you in the last 90 days?",
   "answer": "Very few."
  },
  "q4": {
   "question": "Are you running paid ads right now?",
   "answer": "Yes, and I do not know if they work."
  },
  "problem": {
   "question": "Which one of these costs you the most right now?",
   "answer": "Not enough reviews."
  }
 },
 "secondary_flags": [
  "calls",
  "database",
  "ads"
 ],
 "tags": [
  "nl-problem-reviews",
  "nl-seg-solo",
  "nl-flag-calls",
  "nl-flag-database",
  "nl-flag-ads"
 ],
 "path": "agent",
 "industry": "real-estate",
 "consent_email": true,
 "consent_sms": false,
 "source": "nextlevel-sales-page",
 "location_id": "n0qwGpNQ3CShe8AIhyI0",
 "page": "https://nl.test/hook.html",
 "submitted_at": "2026-11-15T05:59:17.355Z"
}
```

### founding-business, mortgage broker

```json
{
 "name": "Sam",
 "email": "sam@example.com",
 "phone": "",
 "business_type": "Mortgage broker",
 "biggest_problem": "Calls go to voicemail while I am working",
 "answers": {
  "who": {
   "question": "Which best describes you?",
   "answer": "Mortgage broker"
  },
  "phone": {
   "question": "What is your biggest phone problem right now?",
   "answer": "Calls go to voicemail while I am working."
  },
  "line": {
   "question": "A new client calls while you are with someone else. What happens?",
   "answer": "It goes to voicemail and I call back when I can."
  }
 },
 "secondary_flags": [],
 "tags": [
  "nl-founding-business",
  "nl-founding-business-mortgage",
  "nl-phone-voicemail"
 ],
 "path": "founding-business",
 "industry": "mortgage",
 "consent_email": true,
 "consent_sms": false,
 "source": "nextlevel-sales-page",
 "location_id": "n0qwGpNQ3CShe8AIhyI0",
 "page": "https://nl.test/hook.html",
 "submitted_at": "2026-11-15T05:59:25.221Z"
}
```

### founding-business, contractor

```json
{
 "name": "Sam",
 "email": "sam@example.com",
 "phone": "",
 "business_type": "Contractor or renovator",
 "biggest_problem": "Calls in the evening and on weekends go unanswered",
 "answers": {
  "who": {
   "question": "Which best describes you?",
   "answer": "Contractor or renovator"
  },
  "phone": {
   "question": "What is your biggest phone problem right now?",
   "answer": "Calls in the evening and on weekends go unanswered."
  },
  "line": {
   "question": "A new customer calls while you are on a job site. What happens?",
   "answer": "I am not sure how many calls I miss."
  }
 },
 "secondary_flags": [],
 "tags": [
  "nl-founding-business",
  "nl-founding-business-contractor",
  "nl-phone-afterhours"
 ],
 "path": "founding-business",
 "industry": "contractor",
 "consent_email": true,
 "consent_sms": false,
 "source": "nextlevel-sales-page",
 "location_id": "n0qwGpNQ3CShe8AIhyI0",
 "page": "https://nl.test/hook.html",
 "submitted_at": "2026-11-15T05:59:33.288Z"
}
```

### waitlist with a date

```json
{
 "name": "Sam",
 "email": "sam@example.com",
 "phone": "",
 "business_type": "Real estate lawyer",
 "biggest_problem": "I call back too late and they have moved on",
 "answers": {
  "who": {
   "question": "Which best describes you?",
   "answer": "I run a different kind of business"
  },
  "industry": {
   "question": "What kind of business do you run?",
   "answer": "Real estate lawyer"
  },
  "phone": {
   "question": "What is your biggest phone problem right now?",
   "answer": "I call back too late and they have moved on."
  }
 },
 "secondary_flags": [],
 "tags": [
  "nl-waitlist",
  "nl-waitlist-lawyer"
 ],
 "path": "waitlist",
 "industry": "lawyer",
 "consent_email": true,
 "consent_sms": false,
 "source": "nextlevel-sales-page",
 "location_id": "n0qwGpNQ3CShe8AIhyI0",
 "page": "https://nl.test/hook.html",
 "submitted_at": "2026-11-15T05:59:42.676Z"
}
```

### waitlist with no date

```json
{
 "name": "Sam",
 "email": "sam@example.com",
 "phone": "",
 "business_type": "Something else",
 "biggest_problem": "I answer everything myself and it pulls me off my work",
 "answers": {
  "who": {
   "question": "Which best describes you?",
   "answer": "I run a different kind of business"
  },
  "industry": {
   "question": "What kind of business do you run?",
   "answer": "Something else"
  },
  "phone": {
   "question": "What is your biggest phone problem right now?",
   "answer": "I answer everything myself and it pulls me off my work."
  }
 },
 "secondary_flags": [],
 "tags": [
  "nl-waitlist",
  "nl-waitlist-other"
 ],
 "path": "waitlist",
 "industry": "other",
 "consent_email": true,
 "consent_sms": false,
 "source": "nextlevel-sales-page",
 "location_id": "n0qwGpNQ3CShe8AIhyI0",
 "page": "https://nl.test/hook.html",
 "submitted_at": "2026-11-15T05:59:49.106Z"
}
```

### us-list

```json
{
 "name": "Sam",
 "email": "sam@example.com",
 "phone": "",
 "business_type": "Real estate agent or team",
 "biggest_problem": "",
 "answers": {
  "who": {
   "question": "Which best describes you?",
   "answer": "I am in the United States"
  },
  "usbiz": {
   "question": "What kind of business do you run in the United States?",
   "answer": "Real estate agent or team"
  }
 },
 "secondary_flags": [],
 "tags": [
  "nl-us-list",
  "nl-us-list-real-estate"
 ],
 "path": "us-list",
 "industry": "real-estate",
 "consent_email": true,
 "consent_sms": false,
 "source": "nextlevel-sales-page",
 "location_id": "n0qwGpNQ3CShe8AIhyI0",
 "page": "https://nl.test/hook.html",
 "submitted_at": "2026-11-15T05:59:55.240Z"
}
```
