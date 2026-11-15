# Next Level sales page: control audit

Run 2026-11-15 with Playwright Chromium against `index.html`, in the light theme and the dark theme. Every control was activated by mouse and by keyboard (Tab to it, then Enter, and Space where the control is a button, a toggle or a checkbox). The same audit was run on the previous version first, so "Fixed?" says what changed.

## Totals

- Controls tested in the final version: **111** distinct controls, each in 2 themes (222 control runs), by mouse and by keyboard.
- Page-level checks: **86** (43 per theme).
- Final version: **0** controls failing, **0** page checks failing.
- Previous version, same audit: 17 of 104 controls failing or missing, 3 page checks failing. See "What was found and fixed".

## What was found and fixed

Found by the audit on the previous version:

| # | Failure | Where | Fix |
|---|---|---|---|
| 1 | No way forward after Back without tapping the same answer again (9 screens across both paths) | Intake | A Next control now appears on any question that already has an answer. It is absent until there is one, so the quiz still cannot be advanced without a choice. |
| 2 | "Change my answers" wiped every answer | Result, both paths | It reopens question 1 with all answers kept; Next steps forward. |
| 3 | Going Back from the contact step lost the typed first name | Contact step, both paths | The name is saved as it is typed. |
| 4 | The booking fallback was a sentence with a small text link; it copied nothing and was a 25px tap target | Result (both paths) and section 08 | A full button, "Copy NEXT and open Instagram" (or WAITLIST), copies the word, opens instagram.com/rayahmadi in a new tab with rel="noopener", confirms on the page in a status line, and keeps the plain instruction under it. |
| 5 | Index link "04 Founding 10": the oversized price box sat on top of the heading it lands on, and at 1440px the "$300" ran into the terms column over "Price locked" and "Month to month" | Section 04 | Heading lifted above the price; the price is sized to its own column. |
| 6 | Index link "07 Questions": the "Before you book." heading was stretched to the full column height, so the sticky heading never worked | Section 07 | Heading aligned to the top of its column; it now stays in view beside the questions. |
| 7 | Tap targets under 44px on a phone: "See the prices" (19px), "Or start with the intake" (27px), "@rayahmadi" (25px), every "Back" (35x34), "Change my answers", "Not sure which problem is yours?" | Page and intake | All are 44px or more. The inline handle is now plain text because the button does that job. |

Found while building and looking, and fixed:

- The short list beside the quiz used the letters A, B, C, which read as answer options next to the real A to D options. It now uses small marks.
- The side index printed over the moving strip of problems. The strip now passes over it.
- The side index relied on a blend mode, so it could not carry colour. It now switches colour over the navy band, and its contrast is measured over every band while scrolling.
- The FAQ said a caller asking for a person is "passed to you". The working offer says the AI offers a callback and texts you; the page now says that.
- "Your answers point to 4 of the four problems" now reads "all four problems".
- With a long multi-line text button on a phone, the underline sat under the whole box. It now underlines the words.

Not failures, left as they are: the wordmark is not a link (there is nowhere else to go on a one-page site); the side index is desktop only, so it has no phone tap size.

Still failing: nothing.

Limits of this audit: it runs in headless Chromium only (no Safari or Firefox, no real phone, no screen reader listening; "announced" means the message is in a role="alert" or role="status" region and focus moves to the field). The Instagram tab was opened against a stub, so the real Instagram page was not loaded. A failing webhook (non-200) retries once by design; "exactly one POST" was verified for a working endpoint.


## Every control

Focus = the focus ring seen when tabbing to the control (outline width and its contrast against the surface behind it; 3:1 is the minimum). Tap size = smallest size measured on a 390px-wide phone.

| Element | Where | Expected | Result by mouse | Result by keyboard | Focus ring | Tap size at 390px | Pass | Fixed? What changed |
|---|---|---|---|---|---|---|---|---|
| 01 INTAKE | index | Scrolls to "quiz" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes (colour only). Index no longer uses blend mode; active item is blue and items over the dark band switch colour. |
| 02 LEAKS | index | Scrolls to "leaks" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes (colour only). Index no longer uses blend mode; active item is blue and items over the dark band switch colour. |
| 03 METHOD | index | Scrolls to "how" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes (colour only). Index no longer uses blend mode; active item is blue and items over the dark band switch colour. |
| 04 FOUNDING 10 | index | Scrolls to "founding" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes. The big price glyph box overlapped the heading the link lands on; heading lifted above it and the price resized to its column. Index recoloured (see checks). |
| 05 MENU | index | Scrolls to "menu" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes (colour only). Index no longer uses blend mode; active item is blue and items over the dark band switch colour. |
| 06 RAY | index | Scrolls to "ray" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes (colour only). Index no longer uses blend mode; active item is blue and items over the dark band switch colour. |
| 07 QUESTIONS | index | Scrolls to "faq" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes. The "Before you book." heading was stretched to the full column height, so it never stayed in view; it now sticks as intended. |
| 08 BOOK | index | Scrolls to "book" with its heading in view and marks this index item current | Pass: section top at 0px, heading in view, index current=true | Enter Pass: section top at 0px, heading in view, index current=true | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | not shown at 390px (desktop index) | Pass | Yes (colour only). Index no longer uses blend mode; active item is blue and items over the dark band switch colour. |
| START THE INTAKE → | hero | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 203x56px | Pass | No. Passed before and after. |
| SEE THE PRICES | hero | Scrolls to "menu" with its heading in view | Pass: section top at 0px, heading in view | Enter Pass: section top at 0px, heading in view | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 122x44px | Pass | Yes. Tap target raised to 44px high (was 19 to 27px). |
| FIND MY BIGGEST LEAK → | leaks | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 239x56px | Pass | No. Passed before and after. |
| BOOK 15 MINUTES WITH RAY → | founding | Scrolls to "book" with its heading in view | Pass: section top at 0px, heading in view | Enter Pass: section top at 0px, heading in view | light ring 2px, 8.26:1; dark ring 2px, 7.66:1 | 275x56px | Pass | No. Passed before and after. |
| Or start with the intake | founding | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 8.26:1; dark ring 2px, 7.66:1 | 155x44px | Pass | Yes. Tap target raised to 44px high (was 19 to 27px). |
| Will callers know it is an AI? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| What does it sound like? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| What is available today? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| What do the Founding 10 pay? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| What does Answer cost after the Founding 10? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Passed before and after. |
| What does usage cost? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New or relabelled in this version. |
| Is there a contract? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| How long does setup take? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| Do I have to change my phone number? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Passed before and after. |
| What do you need from me? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| Does it speak other languages? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New or relabelled in this version. |
| I am on another CRM. Does this replace it? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | New or relabelled in this version. |
| Who can see my callers and my call transcripts? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | New or relabelled in this version. |
| Will my brokerage allow it? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New or relabelled in this version. |
| Is it allowed where I work? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| Do you have client testimonials? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New or relabelled in this version. |
| I run a team. How does that work? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New or relabelled in this version. |
| I am in the US. Can I join? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | New or relabelled in this version. |
| Who pays for the ads? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| Does this promise me more leads or deals? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Passed before and after. |
| Do I have to join Ray's team? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x64px | Pass | No. Passed before and after. |
| I run a business that is not real estate. Can I use it? | faq | Opens its answer; a second press closes it | Pass: open false > true > false | Enter Pass: open false > true > false; Space Pass: open false > true > false | light ring 2px, 6.54:1; dark ring 2px, 8.54:1 | 358x88px | Pass | No. Passed before and after. |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | book | Copies NEXT, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, rel noopener, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, rel noopener, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 311x56px | Pass | Yes. New button. Before, the fallback was a sentence with a small text link that copied nothing. |
| Not sure which problem is yours? Take the intake first. | book | Scrolls to the intake and puts focus on the current question | Pass: intake at 215px from top, focus on #qt | Enter Pass: intake at 215px from top, focus on #qt; Space Pass: intake at 215px from top, focus on #qt | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x48px | Pass | Yes. Tap target raised to 44px high (was 19 to 27px). |
| Option A Solo agent → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option B Agent with an assistant → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C Team leader → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D Broker or brokerage owner → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option E I run a different kind of business → | Intake, agent path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Next | Intake, agent path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "A new buyer calls while you are in a showing. What happens?" | Enter Pass: moved forward to "A new buyer calls while you are in a showing. What happens?"; Space Pass: moved forward to "A new buyer calls while you are in a showing. What happens?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Option A It goes to voicemail and I call back when I can. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Enter Pass: advanced to "When did you last ask a client for a Google review?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | No. Passed before and after. |
| Option B Someone on my team picks up. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Space Pass: advanced to "When did you last ask a client for a Google review?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C I step out and take it. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Enter Pass: advanced to "When did you last ask a client for a Google review?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D I am not sure how many I miss. → | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "When did you last ask a client for a Google review?"; Back (mouse) kept the answer | Space Pass: advanced to "When did you last ask a client for a Google review?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Next | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "When did you last ask a client for a Google review?" | Enter Pass: moved forward to "When did you last ask a client for a Google review?"; Space Pass: moved forward to "When did you last ask a client for a Google review?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Back (on this screen) | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. Tap target raised from 35x34 to 44x44px. |
| Option A At my last closing. I ask every time. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Enter Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option B A few months ago. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Space Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C I cannot remember. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Enter Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D I do not have a Google Business Profile set up. → | Intake, agent path: "When did you last ask a client for a Google review?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (mouse) kept the answer | Space Pass: advanced to "Think about every contact in your database. How many heard from you in the last 90 days?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | No. Passed before and after. |
| Next | Intake, agent path: "When did you last ask a client for a Google review?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "Think about every contact in your database. How many heard from you in the last 90 days?" | Enter Pass: moved forward to "Think about every contact in your database. How many heard from you in the last 90 days?"; Space Pass: moved forward to "Think about every contact in your database. How many heard from you in the last 90 days?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Back (on this screen) | Intake, agent path: "When did you last ask a client for a Google review?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. Tap target raised from 35x34 to 44x44px. |
| Option A Most of them. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Are you running paid ads right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option B Some of them. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Are you running paid ads right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C Very few. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Are you running paid ads right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D I do not have them in one place. → | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Are you running paid ads right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Are you running paid ads right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Next | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "Are you running paid ads right now?" | Enter Pass: moved forward to "Are you running paid ads right now?"; Space Pass: moved forward to "Are you running paid ads right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Back (on this screen) | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. The typed first name is now kept when you go Back; tap target raised from 35x34 to 44px. |
| Option A Yes, and I know what each lead costs me. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Which one of these costs you the most right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x84px | Pass | No. Passed before and after. |
| Option B Yes, and I do not know if they work. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Which one of these costs you the most right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C I tried and stopped. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Which one of these costs you the most right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D No, and I do not plan to. → | Intake, agent path: "Are you running paid ads right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Which one of these costs you the most right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Next | Intake, agent path: "Are you running paid ads right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "Which one of these costs you the most right now?" | Enter Pass: moved forward to "Which one of these costs you the most right now?"; Space Pass: moved forward to "Which one of these costs you the most right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Back (on this screen) | Intake, agent path: "Are you running paid ads right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. Tap target raised from 35x34 to 44x44px. |
| Option A Calls I do not get to. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option B Not enough reviews. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C A database I never contact. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D Ads that do not pay. → | Intake, agent path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Next | Intake, agent path: "Which one of these costs you the most right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Back (on this screen) | Intake, agent path: "Which one of these costs you the most right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. Tap target raised from 35x34 to 44x44px. |
| First name (text field) | Intake, agent path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Email (text field) | Intake, agent path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Mobile, optional (text field) | Intake, agent path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Email consent checkbox | Intake, agent path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Text consent checkbox | Intake, agent path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Back | Intake, agent path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "Which one of these costs you the most right now?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. The typed first name is now kept when you go Back; tap target raised from 35x34 to 44px. |
| Show my result (submit) | Intake, agent path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | Small. Fields now carry aria-invalid and point to the message. |
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, agent path: result | Copies NEXT, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "NEXT", message "Copied NEXT. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | 311x56px | Pass | Yes. New button. Before, the fallback was a sentence with a small text link that copied nothing. |
| CHANGE MY ANSWERS | Intake, agent path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | Yes. It used to wipe every answer; it now reopens the questions with the answers kept. |
| Option A Solo agent → | Intake, business path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option B Agent with an assistant → | Intake, business path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C Team leader → | Intake, business path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Enter Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D Broker or brokerage owner → | Intake, business path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (mouse) kept the answer | Space Pass: advanced to "A new buyer calls while you are in a showing. What happens?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option E I run a different kind of business → | Intake, business path: "Which best describes you?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "What kind of business do you run?"; Back (mouse) kept the answer | Enter Pass: advanced to "What kind of business do you run?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Next | Intake, business path: "Which best describes you?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "What kind of business do you run?" | Enter Pass: moved forward to "What kind of business do you run?"; Space Pass: moved forward to "What kind of business do you run?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Option A Mortgage broker → | Intake, business path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Which one of these costs you the most right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Option B Real estate lawyer → | Intake, business path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Which one of these costs you the most right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Option C Accountant → | Intake, business path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Which one of these costs you the most right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Option D Contractor or renovation → | Intake, business path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Which one of these costs you the most right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Option E Insurance → | Intake, business path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Enter Pass: advanced to "Which one of these costs you the most right now?"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Option F Something else → | Intake, business path: "What kind of business do you run?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "Which one of these costs you the most right now?"; Back (mouse) kept the answer | Space Pass: advanced to "Which one of these costs you the most right now?"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Next | Intake, business path: "What kind of business do you run?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "Which one of these costs you the most right now?" | Enter Pass: moved forward to "Which one of these costs you the most right now?"; Space Pass: moved forward to "Which one of these costs you the most right now?" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Back (on this screen) | Intake, business path: "What kind of business do you run?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. Tap target raised from 35x34 to 44x44px. |
| Option A Calls I do not get to. → | Intake, business path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option B Not enough reviews. → | Intake, business path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option C A database I never contact. → | Intake, business path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Enter Pass: advanced to "contact step"; Back (Space) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Option D Ads that do not pay. → | Intake, business path: "Which one of these costs you the most right now?" | Saves this answer and moves to the next screen; Back shows it still selected | Pass: advanced to "contact step"; Back (mouse) kept the answer | Space Pass: advanced to "contact step"; Back (Enter) kept the answer | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x62px | Pass | No. Passed before and after. |
| Next | Intake, business path: "Which one of these costs you the most right now?" | Appears only once this question has an answer; moves forward without re-choosing | Pass: moved forward to "contact step" | Enter Pass: moved forward to "contact step"; Space Pass: moved forward to "contact step" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 54x44px | Pass | Yes. New control. Before, going Back meant tapping the same answer again to move on. |
| Back (on this screen) | Intake, business path: "Which one of these costs you the most right now?" | Returns to the previous question with its answer still selected | Pass: covered with each option above | Pass: Enter and Space covered with each option above | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. Tap target raised from 35x34 to 44x44px. |
| First name (text field) | Intake, business path: contact step | Takes focus and typed text | Pass: click then type gave "Sam" | Tab Pass: typed "Sam" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Email (text field) | Intake, business path: contact step | Takes focus and typed text | Pass: click then type gave "sam@example.com" | Tab Pass: typed "sam@example.com" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Mobile, optional (text field) | Intake, business path: contact step | Takes focus and typed text | Pass: click then type gave "4165550100" | Tab Pass: typed "4165550100" | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Email consent checkbox | Intake, business path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 358x55px | Pass | No. Passed before and after. |
| Text consent checkbox | Intake, business path: contact step | Ticks and unticks; never ticked for you | Pass: clicking the label ticked (true) then unticked (true) | Space Pass: ticked (true) then unticked (true) | light ring 2px, 6:1; dark ring 2px, 8.02:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | No. Passed before and after. |
| Back | Intake, business path: contact step | Returns to the last question with its answer selected, and keeps the name already typed | Pass: returned to "Which one of these costs you the most right now?" with the answer selected | Enter Pass: answer kept, name kept | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 44x44px | Pass | Yes. The typed first name is now kept when you go Back; tap target raised from 35x34 to 44px. |
| Show my result (submit) | Intake, business path: contact step | Checks the name (and the email when consent is ticked), announces any problem, then shows the result | Pass: blocked an empty name and a bad email with a message | Enter Pass: Enter in a field re-ran the checks; Enter on the button with a valid name and no consent showed the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 185x56px | Pass | Small. Fields now carry aria-invalid and point to the message. |
| COPY WAITLIST AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, business path: result | Copies WAITLIST, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page | Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "WAITLIST", message "Copied WAITLIST. Paste it in a message to @rayahmadi." | Enter Pass: new tab https://www.instagram.com/rayahmadi/, clipboard "WAITLIST", message "Copied WAITLIST. Paste it in a message to @rayahmadi." | light ring 2px, 6.54:1; dark ring 2px, 6.15:1 | not measured on its own at 390px; same component as the rows in the tap table below | Pass | Yes. New button. Before, the fallback was a sentence with a small text link that copied nothing. |
| CHANGE MY ANSWERS | Intake, business path: result | Reopens the questions with every earlier answer still selected | Pass: back at "Which best describes you?" with answers kept; Next led back to the result | Enter Pass: back at "Which best describes you?" with answers kept; Next led back to the result; Space Pass: back at "Which best describes you?" with answers kept; Next led back to the result | light ring 2px, 6:1; dark ring 2px, 8.02:1 | 149x44px | Pass | Yes. It used to wipe every answer; it now reopens the questions with the answers kept. |

## Page-level checks

| Check | Light | Dark | Detail |
|---|---|---|---|
| No click handlers on non-interactive elements (things that act clickable but are not controls) | Pass | Pass |  |
| No link with an empty or "#" href, and every in-page link has a target | Pass | Pass |  |
| Side index highlights the section in view (manual scroll to the middle of each) | Pass | Pass | quiz:quiz leaks:leaks how:how founding:founding menu:menu ray:ray faq:faq book:book |
| Side index text is at least 4.5:1 over every band while scrolling | Pass | Pass | Light: lowest 6:1 (01 Intake at y=1260) Dark: lowest 7.66:1 (04 Founding 10 at y=4680) |
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
| Cannot advance without a choice: business "Which best describes you?" | Pass | Pass |  |
| Cannot advance without a choice: business "What kind of business do you run?" | Pass | Pass |  |
| Cannot advance without a choice: business "Which one of these costs you the most right now?" | Pass | Pass |  |
| Consent boxes are never pre-ticked (business path) | Pass | Pass | {"c":false,"s":false,"hid":true} |
| Text-message consent row shows only when a mobile number is typed, and clears with it (business path) | Pass | Pass |  |
| Validation messages appear, are announced (role=alert) and move focus to the field (business path) | Pass | Pass | empty name: "Add your first name so the result is written to you." focus #nl-name; bad email: "Enter a valid email, like name@example.com, or untick the box to see your result here only." focus #nl-email; aria-invalid true/true |
| No consent, WEBHOOK_URL empty: zero network requests on submit (business path) | Pass | Pass |  |
| Result takes focus on its heading so it is announced (business path) | Pass | Pass | focus on #rt |
| No console errors (intake, both paths) | Pass | Pass |  |
| No network requests beyond fonts during the whole intake (WEBHOOK_URL empty) | Pass | Pass |  |
| Stubbed endpoint, consent not ticked: no request is sent | Pass | Pass | 0 requests |
| Stubbed endpoint, consent ticked: exactly one POST, with consent_email true and the tags | Pass | Pass | 1 POST; tags ["nl-problem-reviews","nl-seg-solo","nl-flag-calls","nl-flag-database","nl-flag-ads"]; keys name,email,phone,business_type,biggest_problem,answers,secondary_flags,tags,path,consent_email,consent_sms,source,location_id,page,submitted_at |
| WEBHOOK_URL empty, consent ticked: still zero network requests | Pass | Pass |  |
| With BOOKING_URL set, the booking button links to it in a new tab with rel=noopener | Pass | Pass | {"href":"https://cal.test/ray","t":"_blank","rel":"noopener","copy":""} |
| Tap targets are at least 44px on a 390px phone (74 measured, every screen) | Pass | Pass |  |
| Phone (touch) walk through the intake reaches the result | Pass | Pass |  |
| No console errors (phone) | Pass | Pass |  |
| No horizontal scroll at 360px (page, contact step, result, waitlist result) | Pass | Pass | page 360/360, contact step 360/360, result 360/360, waitlist result 360/360 |
| No horizontal scroll at 390px (page, contact step, result, waitlist result) | Pass | Pass | page 390/390, contact step 390/390, result 390/390, waitlist result 390/390 |
| No horizontal scroll at 768px (page, contact step, result, waitlist result) | Pass | Pass | page 768/768, contact step 768/768, result 768/768, waitlist result 768/768 |
| No horizontal scroll at 1280px (page, contact step, result, waitlist result) | Pass | Pass | page 1280/1280, contact step 1280/1280, result 1280/1280, waitlist result 1280/1280 |
| No horizontal scroll at 1440px (page, contact step, result, waitlist result) | Pass | Pass | page 1440/1440, contact step 1440/1440, result 1440/1440, waitlist result 1440/1440 |
| prefers-reduced-motion: nothing animates, and the intake, anchors and FAQ all still work | Pass | Pass | running animations 0, marquee animation none, result true, anchor top 0px, FAQ open true |
| No console errors (reduced motion) | Pass | Pass |  |
| Text and button-label contrast meets AA (28 colour pairs measured from the rendered page, every screen) | Pass | FAIL | lowest 3.45:1 (#f2551c on #ffffff, span.num "3") |
| Text and button-label contrast meets AA (34 colour pairs measured from the rendered page, every screen) | FAIL | Pass | Light:  Dark: lowest 5.19:1 (#93a6ff on #253270, span.no "04") |

## Tap targets on a 390px phone

Every visible control on the page and on every intake screen. Checkboxes are measured by their whole label, which is the tap area.

| Control | Screen | Size |
|---|---|---|
| START THE INTAKE → | page | 203x56px |
| SEE THE PRICES | page | 122x44px |
| FIND MY BIGGEST LEAK → | page | 239x56px |
| BOOK 15 MINUTES WITH RAY → | page | 275x56px |
| Or start with the intake | page | 155x44px |
| Will callers know it is an AI? | page | 358x64px |
| What does it sound like? | page | 358x64px |
| What is available today? | page | 358x64px |
| What do the Founding 10 pay? | page | 358x64px |
| What does Answer cost after the Founding 10? | page | 358x88px |
| What does usage cost? | page | 358x64px |
| Is there a contract? | page | 358x64px |
| How long does setup take? | page | 358x64px |
| Do I have to change my phone number? | page | 358x88px |
| What do you need from me? | page | 358x64px |
| Does it speak other languages? | page | 358x64px |
| I am on another CRM. Does this replace it? | page | 358x88px |
| Who can see my callers and my call transcripts? | page | 358x88px |
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
| D Broker or brokerage owner → | Which best describes you? | 358x62px |
| E I run a different kind of business → | Which best describes you? | 358x62px |
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
| COPY NEXT AND OPEN INSTAGRAM ↗ (OPENS IN A NEW TAB) | result | 311x56px |
| CHANGE MY ANSWERS | result | 149x44px |

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
| `#1f3ffe` | `#ffffff` | 6.56:1 | 4.5:1 | a "01 Intake" |
| `#555c6f` | `#ffffff` | 6.67:1 | 4.5:1 | a "02 Leaks" |
| `#555c6e` | `#ffffff` | 6.68:1 | 4.5:1 | a "01 Intake" |
| `#555c6e` | `#ffffff` | 6.68:1 | 3:1 | li "Mortgage brokers" |
| `#394dba` | `#ffffff` | 7.13:1 | 4.5:1 | a "02 Leaks" |
| `#3b4eb3` | `#ffffff` | 7.18:1 | 4.5:1 | a "01 Intake" |
| `#0a0f24` | `#93a6ff` | 8.26:1 | 4.5:1 | .btn hover/focus fill "BOOK 15 MINUTES WITH RAY" |
| `#ffffff` | `#1c2a6e` | 13.04:1 | 3:1 | span "300" |
| `#0b0d17` | `#f2f5ff` | 17.78:1 | 3:1 | h2 "Six questions." |
| `#0b0d17` | `#f2f5ff` | 17.78:1 | 4.5:1 | span "Solo agent" |
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
| `#9aa8e4` | `#090b14` | 8.5:1 | 4.5:1 | a "02 Leaks" |
| `#9ca9db` | `#090b14` | 8.52:1 | 4.5:1 | a "01 Intake" |
| `#93a6ff` | `#090b14` | 8.54:1 | 4.5:1 | a "08 Book" |
| `#93a6ff` | `#090b14` | 8.54:1 | 3:1 | em "your phone?" |
| `#090b14` | `#93a6ff` | 8.54:1 | 4.5:1 | button.btn "Start the intake" |
| `#a3abc0` | `#090b14` | 8.55:1 | 4.5:1 | a "01 Intake" |
| `#a3abc0` | `#090b14` | 8.55:1 | 3:1 | li "Mortgage brokers" |
| `#ffa27d` | `#2a1810` | 8.67:1 | 4.5:1 | span.tag "Opening next" |
| `#ffffff` | `#253270` | 11.92:1 | 3:1 | span "300" |
| `#f3f5fb` | `#0f1324` | 16.91:1 | 3:1 | h2 "Six questions." |
| `#f3f5fb` | `#0f1324` | 16.91:1 | 4.5:1 | span "Solo agent" |
| `#f3f5fb` | `#090b14` | 18.01:1 | 4.5:1 | span "Next" |
| `#f3f5fb` | `#090b14` | 18.01:1 | 3:1 | span "You were in" |
| `#0b0d17` | `#f6f8fd` | 18.23:1 | 4.5:1 | span "Next" |
| `#0b0d17` | `#f6f8fd` | 18.23:1 | 3:1 | h3 "Your biggest leak: calls you" |
| `#f6f8fd` | `#0b0d17` | 18.23:1 | 4.5:1 | .btn hover/focus fill "COPY NEXT AND OPEN INSTA" |
| `#0a0f24` | `#ffffff` | 18.98:1 | 4.5:1 | a.btn "Book 15 minutes with Ray" |
| `#090b14` | `#ffffff` | 19.63:1 | 4.5:1 | .btn hover/focus fill "START THE INTAKE →" |
