# Next Level sales page: text snapshot

Taken 2026-11-15 from `nextlevel/sales/page/index.html` as rendered in a browser, after the page was changed in answer to visitor test round 1 (`../page-round1/RESULTS.md`). For the next visitor test. Example name used in results: Sam.

The page is published with no webhook and no booking link set. So the quiz screens and results below are what a visitor sees today: the last step asks only for an optional first name, nothing is sent, and the booking step is "Ask Ray for a time". The screens that appear once the webhook is switched on are written out separately near the end.

## How the page looks and moves

1. The page is a clean, bright true white with near-black text, thin cool-grey rules between sections and a lot of empty space.
2. One vivid colour, an electric blue, does the pointing: the italic phrase in each headline, the buttons, the section numbers, the quiz progress line, the active item in the side index, key prices, the "$300 a month" in the hero price line and the "Available now" tags.
3. One warm colour, a coral orange, is used sparingly: the dot and the words "Missed call" in the hero illustration, the small diamonds in the moving strip, and the "Opening next" tags.
4. Headlines are set large in a high-contrast serif (Bodoni), body text in a plain sans serif, and small labels, buttons and times in spaced-out capitals in a monospace face. Ray's name appears as a blue handwritten-style signature in the About Ray strip.
5. The first screen now carries the whole pitch: the label naming the three trades, the four-line headline, one plain line saying what it is, one line with the price, the main blue button and the "See the prices" link. On desktop the illustration sits to the right of that copy; on a phone it follows below.
6. The illustration shows one call from start to finish, top to bottom: a 2:14 pm missed call in coral, a blue panel where the same call is answered by the AI ("Answered. Qualified. Booked." light up in turn while a clock counts and a small waveform moves), a 2:16 pm "Appointment booked" row, and a rounded grey text bubble with the summary sent to the agent. It is labelled "Illustration". Under it an outlined button, "See a sample call", opens a white panel over the page with a written sample exchange.
7. Directly under the hero is a compact About Ray strip: a small empty portrait frame with the initials "RA" captioned "Portrait to come", the line "Built by a working broker.", Ray's one-sentence quote and signature, six short facts and three short assurances.
8. Bands alternate: white sections, a pale blue band for the quiz, one deep navy band with a soft blue glow for the Founding 10 price (a large white "$300" that stays in view on desktop beside six short terms and an "All 21 terms" expander), and a pale blue band for the final call to action.
9. As you scroll, sections fade up, rules draw across, the $300 counts up once, a strip of the four problems slides sideways, and on desktop a small numbered index fixed in the left margin marks the section you are in.
10. Buttons fill from the bottom with near-black on hover and lean slightly toward the pointer; quiz answers indent and draw a blue line; quiz screens crossfade and the result unrolls as a white sheet with a blue top edge. The two expanders ("All 21 terms", "All 22 questions") show a plus that turns to a minus.
11. Nothing waits on animation to be readable, and with reduced motion switched on nothing moves and the sliding strip becomes plain wrapped text. In a dark-mode browser the same design runs on near-black with lighter blue and coral; the result sheet and the sample call panel stay light.
12. On a phone everything is one column and noticeably shorter than before: the side index is hidden, the quiz shows one question per screen with full-width answers (eight on the first screen), the price table turns into stacked cards, and every button and link is at least 44px tall.

## Page height, before and after

Measured in Chromium with the web fonts loaded and both expanders closed (their default).

| Width | Before (round 1 version) | After | Change | After, with both expanders open |
|---|---|---|---|---|
| 390px | 16,246px | 11,016px | -32% | 14,794px |
| 1440px | 15,061px | 9,260px | -39% | 13,036px |

## What a visitor sees without scrolling

Exactly the text and controls inside the first viewport, read from the rendered page after the load animation has finished. "Cut off" means the item crosses the bottom edge of the screen.

### 390px phone (390 x 844)

One column. Labels and buttons are shown in capitals on the page.

| # | Kind | Text | Fully visible |
|---|---|---|---|
| 1 | Text | Next Level | Yes |
| 2 | Text | BY RAY AHMADI | Yes |
| 3 | Text | FOR REAL ESTATE AGENTS, MORTGAGE BROKERS AND CONTRACTORS | Yes |
| 4 | Text | You were in a showing. Who answered your phone? | Yes |
| 5 | Text | An AI receptionist answers every call you miss, qualifies the caller and books the appointment. | Yes |
| 6 | Text | $300 a month for the first 10 clients. No setup fee. Month to month. | Yes |
| 7 | Button | SEE WHAT IT WOULD DO FOR YOU (60 SECONDS) → | Yes |
| 8 | Link | SEE THE PRICES | Yes |
| 9 | Text | Also open now to mortgage brokers and to contractors and renovators: 3 founding spots, on the same terms. | Yes |
| 10 | Text | Canada only for now. In the United States? Join the US list | Yes |
| 11 | Button | Join the US list | Yes |
| 12 | Text | ONE CALL, START TO FINISH ILLUSTRATION | Yes |
| 13 | Text | 2:14 pm Missed call You could not pick up | Yes |

Measured positions (px from the top of a 390x844 viewport): headline 106 to 268; what-it-is line 284 to 358; price line 370 to 416; main button 432 to 504; "See the prices" 508 to 552.

### 1440px desktop (1440 x 900)

Two columns: the copy on the left, the illustration on the right, the side index fixed in the left margin. The illustration panel is animated; the clock value and which of "Answered. Qualified. Booked." are lit change second by second.

| # | Kind | Text | Fully visible |
|---|---|---|---|
| 1 | Link (side index) | 01 RAY | Yes |
| 2 | Link (side index) | 02 INTAKE | Yes |
| 3 | Link (side index) | 03 LEAKS | Yes |
| 4 | Link (side index) | 04 METHOD | Yes |
| 5 | Link (side index) | 05 FOUNDING 10 | Yes |
| 6 | Link (side index) | 06 MENU | Yes |
| 7 | Link (side index) | 07 QUESTIONS | Yes |
| 8 | Link (side index) | 08 BOOK | Yes |
| 9 | Text | Next Level | Yes |
| 10 | Text | BY RAY AHMADI, GTA REAL ESTATE BROKER | Yes |
| 11 | Text | FOR REAL ESTATE AGENTS, MORTGAGE BROKERS AND CONTRACTORS | Yes |
| 12 | Text | You were in a showing. Who answered your phone? | Yes |
| 13 | Text | An AI receptionist answers every call you miss, qualifies the caller and books the appointment. | Yes |
| 14 | Text | $300 a month for the first 10 clients. No setup fee. Month to month. | Yes |
| 15 | Button | SEE WHAT IT WOULD DO FOR YOU (60 SECONDS) → | Yes |
| 16 | Link | SEE THE PRICES | Yes |
| 17 | Text | Also open now to mortgage brokers and to contractors and renovators: 3 founding spots, on the same terms. | Yes |
| 18 | Text | Canada only for now. In the United States? Join the US list | Yes |
| 19 | Button | Join the US list | Yes |
| 20 | Text | ONE CALL, START TO FINISH ILLUSTRATION | Yes |
| 21 | Text | 2:14 pm Missed call You could not pick up | Yes |
| 22 | Text | 2:14 PM, THE SAME CALL 0:02 | Yes |
| 23 | Text | Answered. Qualified. Booked. | Yes |
| 24 | Text | Answered by the AI, with Next Level Answer | Yes |
| 25 | Text | 2:16 pm Appointment booked Thursday, 4 pm, on your calendar | Yes |
| 26 | Text | 2:16 PM, TEXT TO YOU | Yes |
| 27 | Text | New caller: Daniel. Ready within three months. Booked Thursday, 4 pm. Full summary in your email. | Yes |
| 28 | Button | SEE A SAMPLE CALL → | Yes |

Measured positions (px from the top of a 1440x900 viewport): headline 130 to 407; what-it-is line 429 to 524; price line 542 to 593; main button 615 to 671; "See the prices" 675 to 719.

On a smaller 360 x 740 phone the same five items are also inside the first screen: the "See the prices" link ends at 540px of 740px.

## The page, top to bottom

Both expanders are shown opened here so every word is in this file. On the page they start closed.

### Side index (desktop only, fixed in the left margin)

01 Ray
02 Intake
03 Leaks
04 Method
05 Founding 10
06 Menu
07 Questions
08 Book

### Top bar

Next Level
By Ray Ahmadi, GTA real estate broker

### Hero

For real estate agents, mortgage brokers and contractors
You were in
a showing.
Who answered
your phone?

An AI receptionist answers every call you miss, qualifies the caller and books the appointment.

$300 a month for the first 10 clients. No setup fee. Month to month.

See what it would do for you (60 seconds)
→
See the prices

Also open now to mortgage brokers and to contractors and renovators: 3 founding spots, on the same terms.

Canada only for now. In the United States?
Join the US list

One call, start to finish
Illustration
2:14 pm
Missed call
You could not pick up
2:14 pm, the same call
On the line
Answered.
Qualified.
Booked.
Answered by the AI, with Next Level Answer
2:16 pm
Appointment booked
Thursday, 4 pm, on your calendar
2:16 pm, text to you

New caller: Daniel. Ready within three months. Booked Thursday, 4 pm. Full summary in your email.

See a sample call
→

[Illustration, described for screen readers as: Illustration of one call, start to finish. At 2:14 pm a call is missed because you could not pick up. With Next Level Answer the same call is answered by the AI, the caller is qualified and an appointment is booked for Thursday at 4 pm. At 2:16 pm a text summary of the call is sent to you.]

### Sample call panel (opens from "See a sample call" in the hero)

Sample script for illustration, not a recording
Close
A sample call.

A new caller rings an agent's line while the agent is with a client. The names are invented.

AI

Thank you for calling Maya's office. I am an AI assistant, and I can help while Maya is with a client. Who am I speaking with?

Caller

Hi, this is Daniel. I saw one of Maya's listings online and I would like to see it.

AI

Thanks, Daniel. Two quick questions so Maya is ready for you. Are you hoping to buy in the next three months, or later?

Caller

In the next three months.

AI

And are you already working with another agent?

Caller

No, not yet.

AI

Maya has an opening on Thursday at 4 pm. Shall I book it for you?

Caller

Yes, Thursday works.

AI

You are booked for Thursday at 4 pm. Maya will have a summary of this call in a moment.

The text Maya receives

New caller: Daniel. Wants to see a listing. Buying within three months. Not working with another agent. Booked Thursday, 4 pm.

This is a written sample, not a recording. On the 15-minute call with Ray you dial the live system yourself and hear it answer.

### Section 01: About Ray (compact strip, directly under the hero)

01
About Ray
RA
Portrait to come
Built by a working broker.
I run this system on my own business. On your call, you dial it yourself.
Ray Ahmadi
Ray Ahmadi, broker
Role
Real estate broker in the GTA
Brokerage
Ray Homes Real Estate, under eXp Realty
Experience
12+ years, about 50 deals a year
Recognition
Multi-year eXp Icon agent
Languages
English and Dari
On your call
Ray himself, every time
You get a one-page summary to show your broker of record before you sign.
Audio recording is off unless you turn it on.
You get a written agreement before any payment.

### Marquee (a moving strip of the four problems, decorative)

Missed calls / Reviews nobody asked for / A database gone quiet / Ads nobody watches

### Section 02: The intake (quiz)

02
The intake
60 seconds, six questions.

Tell us how your business runs today. You see your biggest leak and what fixes it, with the price. Mortgage brokers and contractors answer three questions.

One tap per answer
Your biggest leak, named
What fixes it, with the price

[The quiz itself appears here. Every screen is written out below.]

### Section 03: The four leaks

03
The four leaks
Four places a business leaks.
i
Missed calls

You could not pick up. By the time you called back, they had booked with someone else.

Next Level Answer. An AI receptionist answers every call you miss, qualifies the caller and books the appointment. You get a summary by text and email.

Available now
ii
Reviews

Your clients are happy. Nobody asked them for a Google review.

Next Level Reviews. A review request goes out at closing and again at day 30, every time.

Opening next
iii
Dead database

Years of contacts are sitting there. Most have not heard from you in months.

Next Level Nurture. Reactivation, follow-up with everyone who raises a hand, and regular past-client touches.

Opening next
iv
Ads

You paid for an ad and have no idea what it did.

Next Level Ads. Built for real estate agents first: listing and buyer ads, run and watched daily.

Opening next
Find my biggest leak
→

### Section 04: The method

04
The method
Three steps. We set it up.
Step one
Take the intake

60 seconds. You see your biggest leak and what fixes it, with the price.

Step two
15 minutes with Ray

Ray asks about your business. You dial the live system yourself and hear it answer, before you pay.

Step three
We set it up for you

You send your details. We build it and test it with you before it goes live.

Open now: 7 founding spots
Real estate agents

You are in a showing. A new buyer calls, reaches voicemail and calls the next agent.

Solo agents, agents with an assistant, team leaders, brokers and brokerage owners, at any brokerage. Next Level never recruits a client to Ray's brokerage or team, and joining anything of Ray's is not a condition of the price, the service or the support.

Also open now: 3 founding spots
Mortgage brokers

You are with a client. A new client calls, reaches voicemail and calls the next broker.

Contractors and renovators

You are on a job site. A new customer calls, reaches voicemail and calls the next contractor.

The same founding terms as agents: $300 a month, no setup fee, price locked, 250 minutes included. Same intake, same 15-minute call.

Opening 1 March 2027
Real estate lawyers, accountants and insurance

From $500 setup plus $400 a month. Join the waitlist through the intake and you get first notice before that date. Any other business can join the waitlist too, and no date is promised.

### Section 05: The Founding 10

05
The Founding 10
Next Level Answer, for the first 10 clients

$300

a month. No setup fee.

10 founding spots. 7 for real estate agents. 3 open now to mortgage brokers and to contractors and renovators. Canada only.

Ask Ray for a time
→
Or start with the intake
$300 a month, no setup fee

For the first 10 clients. After them, Answer is $500 setup + $400 a month.

What is included

250 AI call minutes a month, your phone number, and the summary and alert texts, up to 500 text segments a month.

Month to month

Cancel before the next billing date. When you leave, your contacts and transcripts are exported to you and deleted from the account within 30 days.

Live within 7 days

Live within 7 days of you supplying everything needed, or the first month is not charged. Once per client, first month only, and not for carrier or registration delays.

Your callers stay yours

No one at Next Level or Ray Homes contacts your callers or uses your contacts, and that is written in the agreement.

You dial it yourself

On the call you dial the live system yourself and hear it answer, before you pay.

[Expander button, closed by default] All 21 terms / 15 more

[The 15 rows from here to the end of this section are folded until the button is pressed. They stay in the page, so find-in-page reaches them and they print.]
Price locked

The $300 price stays locked while your subscription is active.

Extra minutes

Extra minutes are $0.30 each, at the founding price and at the standard price. A part minute counts as a minute, and unused minutes do not carry over. Minutes used are shown on every invoice, and Ray shows you his own line's real usage on the call.

A cap you set

Before go-live you set a monthly cap on extra minutes, and it can be zero. With the cap at zero, the most you can be billed is $300. With a cap of 100 extra minutes, the most is $330. The system stops and alerts you if the cap is reached.

10 founding spots

7 are for real estate agents. 3 are open now to mortgage brokers and to contractors and renovators, on the same founding terms.

Teams

One subscription covers one business line. Each additional agent line on the same account is half the monthly price: $150 a month at the founding price, $200 at the standard price. Each one adds 125 minutes, and all lines on the account share one pool of minutes.

Canada only

Founding clients are in Canada only, and the price is in Canadian dollars. US agents can join the US list, and are told the US opening date and the US dollar price by 1 March 2027. Nothing is sold to US clients before then.

I am in the United States
Languages

English is live today. Other languages are tested on your own line before you go live, and if one does not meet your standard you are not charged.

Other languages that HighLevel lists can be switched on at your request. Not promised today: Dari, Farsi, Punjabi, Mandarin, Cantonese, Urdu and Arabic. If you need one of these, it is checked against the platform's current list and tested with you during set-up. Ask Ray on the call which languages are available for your line.

Your transcripts and data

Only you can read your call transcripts, and the set-up team only while they are setting up your account or fixing something you asked them to fix. Each call is transcribed so you get the summary. Audio recording is off unless you turn it on, and when it is on the AI says so at the start of the call.

Your account runs on HighLevel, a US software company. Your data is stored in the United States, not in Canada.

Summaries and your CRM

Every call arrives as a text and an email summary, so it works beside any CRM. For Follow Up Boss and BoldTrail there is also a one-way push into your CRM through Zapier. Lofty and Sierra Interactive are tested in your account during set-up.

Urgent callers

If a caller asks for a person, or the call is urgent, the AI offers a callback and you get a text alert straight away.

Your brokerage

You get a one-page summary to show your broker of record before you sign. If your brokerage says no within 14 days, you get your first month back.

Written agreement

You get a written agreement before any payment. It names the registered business and its address.

No recruiting

Next Level never recruits a client to Ray's brokerage or team. Joining anything of Ray's is not a condition of the price, the service or the support.

No cheaper plan

There is no cheaper plan today. If $300 a month is more than your phone problem is worth, this is not the right service for you yet.

Why a founding price

Next Level is new and there are no client testimonials yet. That is the reason for the founding terms: a lower price, no setup fee and a locked price, in return for being first.

### Section 06: Products and prices

06
Products and prices
The menu.

Answer is available now. Reviews, Nurture and Ads are opening next, in this order. Complete follows when all four are open.

Product	Setup	A month

Answer, Founding 10
Available now
AI receptionist. Every call answered, qualified and booked. First 10 clients: 7 real estate agents, and 3 mortgage brokers or contractors. 250 minutes a month included.
None	$300

Answer
Available now
The standard price, after the Founding 10. The same 250 minutes a month included.
$500	$400

Reviews
Opening next
Review requests at closing and at day 30.
$250	$150

Nurture
Opening next
Database reactivation, follow-up and past-client touches.
$500	$250

Ads
Opening next
Listing and buyer ads, run and watched daily. Ad spend goes on your own card.
$500	$750

Complete
When all four are open
All four as one system.
$1,500	$1,500

All prices in Canadian dollars. Answer includes 250 AI call minutes a month, your phone number and up to 500 text segments a month, at the founding price and at the standard price. Extra minutes are $0.30 each, up to a monthly cap you set, and the cap can be zero. A part minute counts as a minute, and unused minutes do not carry over. Each additional agent line on the same account is half the monthly price, $150 founding or $200 standard, and adds 125 minutes to a shared pool. There is no cheaper plan today. Next Level does not promise leads, deals or income. It makes sure the business you already have is answered and followed up.

### Section 07: Questions

07
Questions
Before you book.
What does it cost, and what does usage cost?

The Founding 10 pay $300 a month for Next Level Answer, with no setup fee, and the $300 price stays locked while your subscription is active. Usage costs nothing extra up to 250 AI call minutes a month. The $300 includes those minutes, your phone number, and the summary and alert texts, up to 500 text segments a month. Extra minutes are $0.30 each. A part minute counts as a minute, and unused minutes do not carry over. You set a monthly cap on extra minutes before go-live, and it can be zero. With the cap at zero, the most you can be billed is $300. Minutes used are shown on every invoice, and on the call Ray shows you the real usage on his own line before you pay.

Does it speak other languages?

English is live today. Other languages are tested on your own line before you go live, and if one does not meet your standard you are not charged. Other languages that HighLevel lists can be switched on at your request. Not promised today: Dari, Farsi, Punjabi, Mandarin, Cantonese, Urdu and Arabic. If you need one of these, it is checked against the platform's current list and tested with you during set-up. Ask Ray on the call which languages are available for your line.

Who can read my transcripts, and where is my data held?

Only you can read your call transcripts, and the set-up team only while they are setting up your account or fixing something you asked them to fix. Audio recording is off unless you turn it on. Your callers stay yours: no one at Next Level or Ray Homes contacts your callers or uses your contacts, and that is written in the agreement. Your account runs on HighLevel, a US software company. Your data is stored in the United States, not in Canada. When you leave, your contacts and transcripts are exported to you and deleted from the account within 30 days.

Does it work with my CRM?

Yes, beside it. It does not replace it. Every call reaches you as a text and an email summary from day one. For Follow Up Boss and BoldTrail there is also a push into your CRM through Zapier. It is one way, from Next Level Answer into your CRM. Lofty and Sierra Interactive are tested in your account during set-up. If the push for one of those four does not work in your account during set-up, you can cancel and you are not charged. Any other CRM gets the text and email summary.

Is there a contract?

You get a written agreement before any payment. It names the registered business and its address. It is month to month. Cancel before the next billing date. When you leave, your contacts and transcripts are exported to you and deleted from the account within 30 days.

Can I hear it first?

Yes. On the 15-minute call you dial the live system yourself and hear it answer, before you pay anything. Until then, "See a sample call" near the top of this page shows how a call goes. It is a sample script for illustration, not a recording.

[Expander button, closed by default] All 22 questions / 16 more

[The 16 questions from here to the end of this section are folded until the button is pressed. Every question on the page is itself a closed row that opens when tapped; the answers are written out here.]
Will callers know it is an AI?

Yes. It says so at the start of the call. If a caller asks for a person, or it is urgent, it offers a callback and alerts you by text straight away.

What is available today?

Next Level Answer is available now. Reviews, Nurture and Ads are opening next, in that order. Complete follows when all four are open.

What does Answer cost after the Founding 10?

$500 setup and $400 a month, in Canadian dollars, with the same 250 minutes and the same $0.30 for extra minutes.

Is there a cheaper plan?

There is no cheaper plan today. If $300 a month is more than your phone problem is worth, this is not the right service for you yet.

How long does setup take?

For the Founding 10: live within 7 days of you supplying everything needed, or the first month is not charged. This applies once per client, to the first month only, and not to carrier or registration delays.

Do I have to change my phone number?

No. You keep your number. Calls forward only when you do not answer, including when your phone is off. Forwarding is switched off the day you cancel.

What do you need from me?

Your business details, your hours and areas, the questions you want asked, calendar access, the number to forward, the name of your CRM, the languages your callers use, and the monthly cap on extra minutes you choose.

Will my brokerage allow it?

You get a one-page summary to show your broker of record before you sign. If your brokerage says no within 14 days, you get your first month back.

Is it allowed where I work?

Rules on call recording and on telling callers they are speaking with an AI differ by province and state. We confirm them for your location before you go live. Audio recording is off unless you turn it on, and when it is on the AI says so at the start of the call. Check with your brokerage as well.

Do you have client testimonials?

Not yet. Next Level is new and the first 10 clients are its founding clients. That is the reason for the founding terms: a lower price, no setup fee and a locked price, in return for being first. What you can check today is Ray's own track record and the live system, which you dial yourself on the call.

I run a team. How does that work?

One subscription covers one business line. Each additional agent line on the same account is half the monthly price: $150 a month at the founding price, $200 at the standard price. Each one adds 125 minutes, and all lines on the account share one pool of minutes.

I am in the US. Can I join?

Not yet. Founding clients are in Canada only. You can join the US list: in the intake, pick "I am in the United States". By 1 March 2027 everyone on the US list is told the US opening date and the price in US dollars. Nothing is sold to US clients before then.

Who pays for the ads?

You do, on your own card, straight to the ad platform. The Next Level Ads fee covers running and watching them.

Does this promise me more leads or deals?

No. It makes sure the calls, clients and contacts you already have are answered and followed up.

Do I have to join Ray's team?

No. Next Level never recruits a client to Ray's brokerage or team. Joining anything of Ray's is not a condition of the price, the service or the support. Next Level is open to agents at any brokerage.

I run a business that is not real estate. Can I use it?

It depends on your business. Mortgage brokers, and contractors and renovators: 3 of the 10 founding spots are open to you now, on the same founding terms as agents. That is $300 a month, no setup fee, price locked and 250 minutes included, with the same intake and the same 15-minute call. Real estate lawyers, accountants and insurance: Answer opens to you on 1 March 2027, from $500 setup plus $400 a month. Join the waitlist through the intake and you get first notice before that date. Any other business can join the waitlist, and no date is promised.

### Section 08: Your next step

08
Your next step
Hear it answer a call.

15 minutes with Ray. He asks about your business, has you dial the AI receptionist yourself, and tells you plainly if it fits.

Ask Ray for a time
Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

Not sure which problem is yours? Take the 60-second intake first.

### Footer

Next Level

Operated by Ray Ahmadi. The registered business name and address are on the agreement you sign before any payment.

Software and set-up service. Not real estate brokerage services.

## How the quiz routes

The first screen ("Which best describes you?") has eight answers and decides the path.

| First answer | Path | Screens | Ends in |
|---|---|---|---|
| Solo agent, Agent with an assistant, Team leader, Real estate broker or brokerage owner | agent | 6 questions, then the last step | An intake brief on their biggest leak, with Next Level Answer at the founding terms and "Ask Ray for a time" |
| Mortgage broker, Contractor or renovator | founding-business | 3 questions, then the last step | An intake brief worded for their trade, with Next Level Answer at the founding terms and "Ask Ray for a time" |
| I run a different kind of business | waitlist | 3 questions (the second asks the industry), then the last step | A waitlist brief: 1 March 2027 and the starting price for real estate lawyers, accountants and insurance; no date for "Something else". No price to pay today, no booking |
| I am in the United States | us-list | 2 questions, then the last step | A US list brief. No price, no booking |

The hero link "Join the US list" and the "I am in the United States" control in the founding terms both jump straight to the second screen of the US list path.

On every question: tapping an answer saves it and moves on. Back returns with the earlier answer still selected (shown with a blue line and arrow), and a Next control appears on any question that already has an answer. Before the first answer the progress label reads "Question 1"; after it, "Question 2 of 6" and so on.

The last step has two forms, and which one shows depends on a setting, not on the visitor:

- **Webhook not set (the page as published today).** One field, "First name (optional)", and the button "Show my brief". No email, no mobile, no consent boxes. Leaving the name empty is allowed. The result carries the line "This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser."
- **Webhook set.** The earlier form, unchanged: first name (required), email, mobile (optional), an unticked email consent box, and, only if a mobile number is typed, a second unticked box "Yes, you may text me at this number about my result. Reply STOP to end." The button reads "Show my result". Without the email box ticked the result is shown and nothing is sent. Error messages: "Add your first name so the result is written to you." and "Enter a valid email, like name@example.com, or untick the box to see your result here only."

## Quiz screens: agent path (first answer "Solo agent")

### Screen 1 of 7

Question 1
01
Which best describes you?
A
Solo agent
→
B
Agent with an assistant
→
C
Team leader
→
D
Real estate broker or brokerage owner
→
E
Mortgage broker
→
F
Contractor or renovator
→
G
I run a different kind of business
→
H
I am in the United States
→

One tap per answer. Six questions for real estate agents, three for mortgage brokers and contractors. No email is asked for, and nothing is sent anywhere.

### Screen 2 of 7

Question 2 of 6
02 / 06
A new buyer calls while you are in a showing. What happens?
A
It goes to voicemail and I call back when I can.
→
B
Someone on my team picks up.
→
C
I step out and take it.
→
D
I am not sure how many I miss.
→
Back

### Screen 3 of 7

Question 3 of 6
03 / 06
When did you last ask a client for a Google review?
A
At my last closing. I ask every time.
→
B
A few months ago.
→
C
I cannot remember.
→
D
I do not have a Google Business Profile set up.
→
Back

### Screen 4 of 7

Question 4 of 6
04 / 06
Think about every contact in your database. How many heard from you in the last 90 days?
A
Most of them.
→
B
Some of them.
→
C
Very few.
→
D
I do not have them in one place.
→
Back

### Screen 5 of 7

Question 5 of 6
05 / 06
Are you running paid ads right now?
A
Yes, and I know what each lead costs me.
→
B
Yes, and I do not know if they work.
→
C
I tried and stopped.
→
D
No, and I do not plan to.
→
Back

### Screen 6 of 7

Question 6 of 6
06 / 06
Which one of these costs you the most right now?
A
Calls I do not get to.
→
B
Not enough reviews.
→
C
A database I never contact.
→
D
Ads that do not pay.
→
Back

### Screen 7 of 7: last step

Last step
Your first name
What first name should go on your brief?
First name (optional)
Show my brief
→

No email is asked for. Your brief is shown here only, and nothing is sent or stored.

Back

## Quiz screens: founding-business path, mortgage broker

### Screen 1 of 4

Question 1
01
Which best describes you?
A
Solo agent
→
B
Agent with an assistant
→
C
Team leader
→
D
Real estate broker or brokerage owner
→
E
Mortgage broker
→
F
Contractor or renovator
→
G
I run a different kind of business
→
H
I am in the United States
→

One tap per answer. Six questions for real estate agents, three for mortgage brokers and contractors. No email is asked for, and nothing is sent anywhere.

### Screen 2 of 4

Question 2 of 3
02 / 03
What is your biggest phone problem right now?
A
Calls go to voicemail while I am working.
→
B
Calls in the evening and on weekends go unanswered.
→
C
I call back too late and they have moved on.
→
D
I answer everything myself and it pulls me off my work.
→
Back

### Screen 3 of 4

Question 3 of 3
03 / 03
A new client calls while you are with someone else. What happens?
A
It goes to voicemail and I call back when I can.
→
B
Someone in the office picks up during the day.
→
C
An answering service takes a message.
→
D
I am not sure how many calls I miss.
→
Back

### Screen 4 of 4: last step

Last step
Your first name
What first name should go on your brief?
First name (optional)
Show my brief
→

No email is asked for. Your brief is shown here only, and nothing is sent or stored.

Back

## Quiz screens: founding-business path, contractor or renovator

The same screens as the mortgage broker, except that the third question is worded for a job site.

### Screen 1 of 4

Question 1
01
Which best describes you?
A
Solo agent
→
B
Agent with an assistant
→
C
Team leader
→
D
Real estate broker or brokerage owner
→
E
Mortgage broker
→
F
Contractor or renovator
→
G
I run a different kind of business
→
H
I am in the United States
→

One tap per answer. Six questions for real estate agents, three for mortgage brokers and contractors. No email is asked for, and nothing is sent anywhere.

### Screen 2 of 4

Question 2 of 3
02 / 03
What is your biggest phone problem right now?
A
Calls go to voicemail while I am working.
→
B
Calls in the evening and on weekends go unanswered.
→
C
I call back too late and they have moved on.
→
D
I answer everything myself and it pulls me off my work.
→
Back

### Screen 3 of 4

Question 3 of 3
03 / 03
A new customer calls while you are on a job site. What happens?
A
It goes to voicemail and I call back when I can.
→
B
Someone in the office picks up during the day.
→
C
An answering service takes a message.
→
D
I am not sure how many calls I miss.
→
Back

### Screen 4 of 4: last step

Last step
Your first name
What first name should go on your brief?
First name (optional)
Show my brief
→

No email is asked for. Your brief is shown here only, and nothing is sent or stored.

Back

## Quiz screens: waitlist path (first answer "I run a different kind of business")

### Screen 1 of 4

Question 1
01
Which best describes you?
A
Solo agent
→
B
Agent with an assistant
→
C
Team leader
→
D
Real estate broker or brokerage owner
→
E
Mortgage broker
→
F
Contractor or renovator
→
G
I run a different kind of business
→
H
I am in the United States
→

One tap per answer. Six questions for real estate agents, three for mortgage brokers and contractors. No email is asked for, and nothing is sent anywhere.

### Screen 2 of 4

Question 2 of 3
02 / 03
What kind of business do you run?
A
Real estate lawyer
→
B
Accountant
→
C
Insurance
→
D
Something else
→
Back

### Screen 3 of 4

Question 3 of 3
03 / 03
What is your biggest phone problem right now?
A
Calls go to voicemail while I am working.
→
B
Calls in the evening and on weekends go unanswered.
→
C
I call back too late and they have moved on.
→
D
I answer everything myself and it pulls me off my work.
→
Back

### Screen 4 of 4: last step

Last step
Your first name
What first name should go on your brief?
First name (optional)
Show my brief
→

No email is asked for. Your brief is shown here only, and nothing is sent or stored.

Back

## Quiz screens: US list path (first answer "I am in the United States")

### Screen 1 of 3

Question 1
01
Which best describes you?
A
Solo agent
→
B
Agent with an assistant
→
C
Team leader
→
D
Real estate broker or brokerage owner
→
E
Mortgage broker
→
F
Contractor or renovator
→
G
I run a different kind of business
→
H
I am in the United States
→

One tap per answer. Six questions for real estate agents, three for mortgage brokers and contractors. No email is asked for, and nothing is sent anywhere.

### Screen 2 of 3

Question 2 of 2
02 / 02
What kind of business do you run in the United States?
A
Real estate agent or team
→
B
Mortgage broker
→
C
Contractor or renovator
→
D
Another kind of business
→
Back

### Screen 3 of 3: last step

Last step
Your first name
What first name should go on your brief?
First name (optional)
Show my brief
→

No email is asked for. Your brief is shown here only, and nothing is sent or stored.

Back

## Example results

Agent examples use these answers: solo agent; calls go to voicemail; last asked for a review a few months ago; very few contacts heard from me; running ads and not sure they work. Only the "costs you the most" answer changes between the four. Every example in this section is the result as a visitor sees it today, with no webhook and no booking link set.

### Agent result when the biggest problem is missed calls

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Profile
Solo agent
Costing you most
Calls I do not get to

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Your biggest leak: calls you do not get to.

Sam, you told us the thing costing you most is missed calls. You cannot be in a showing and on the phone. A caller who reaches voicemail can hang up and call the next agent. Something else has to pick up.

In your words
It goes to voicemail and I call back when I can.
A few months ago.
Very few.
Yes, and I do not know if they work.
What fixes it
Available now: the Founding 10
Next Level Answer
$300 a month
An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. No setup fee for the first 10 clients. 250 AI call minutes a month are included. The $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Your answers point to all four problems. Next Level Complete runs all four as one system, when all four are open: $1,500 setup + $1,500 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. You dial the live system yourself and hear it answer. Ray shows you the real usage on his own line before you pay.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Agent result when the biggest problem is reviews

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Profile
Solo agent
Costing you most
Not enough reviews

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Your biggest leak: happy clients who were never asked.

Sam, you told us the thing costing you most is reviews. Buyers and sellers can compare agents on Google before they call anyone. When the request only goes out if you remember, most clients are never asked.

In your words
It goes to voicemail and I call back when I can.
A few months ago.
Very few.
Yes, and I do not know if they work.
What fixes it
Opening next
Next Level Reviews
$250 setup + $150 a month
A review request goes out at closing and again at day 30, every time, with replies drafted for you to approve. Not open yet. Ray puts you in line on the call.
Available now: the Founding 10
Next Level Answer
$300 a month
You also said calls get missed. An AI receptionist answers every call, qualifies the caller and books the appointment. No setup fee for the first 10 clients. 250 AI call minutes a month are included. The $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Your answers point to all four problems. Next Level Complete runs all four as one system, when all four are open: $1,500 setup + $1,500 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. Ray will show you the review system he runs on his own business. You can also dial the live receptionist yourself on the call.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Agent result when the biggest problem is a dead database

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Profile
Solo agent
Costing you most
A database I never contact

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Your biggest leak: a database nobody is talking to.

Sam, you told us the thing costing you most is a quiet database. Some of your contacts will move. The agent who stayed in touch is the one they think of.

In your words
It goes to voicemail and I call back when I can.
A few months ago.
Very few.
Yes, and I do not know if they work.
What fixes it
Opening next
Next Level Nurture
$500 setup + $250 a month
A reactivation campaign to the people you have permission to contact, follow-up with everyone who raises a hand, and regular past-client touches. Not open yet. Ray puts you in line on the call.
Available now: the Founding 10
Next Level Answer
$300 a month
You also said calls get missed. An AI receptionist answers every call, qualifies the caller and books the appointment. No setup fee for the first 10 clients. 250 AI call minutes a month are included. The $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Your answers point to all four problems. Next Level Complete runs all four as one system, when all four are open: $1,500 setup + $1,500 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. Ray will walk you through what he runs on his own list. You can also dial the live receptionist yourself on the call.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Agent result when the biggest problem is ads

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Profile
Solo agent
Costing you most
Ads that do not pay

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Your biggest leak: ad money with nobody watching it.

Sam, you told us the thing costing you most is ads. Ads fail in two places. Nobody watches them daily, and nobody calls the lead fast.

In your words
It goes to voicemail and I call back when I can.
A few months ago.
Very few.
Yes, and I do not know if they work.
What fixes it
Opening next
Next Level Ads
$500 setup + $750 a month
Listing and buyer ads, run and watched daily. Ad spend goes on your own card. Not open yet. Ray puts you in line on the call.
Available now: the Founding 10
Next Level Answer
$300 a month
You also said calls get missed. An AI receptionist answers every call, qualifies the caller and books the appointment. No setup fee for the first 10 clients. 250 AI call minutes a month are included. The $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Your answers point to all four problems. Next Level Complete runs all four as one system, when all four are open: $1,500 setup + $1,500 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. Bring your last ad report. Ray will go through it with you. You can also dial the live receptionist yourself on the call.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Agent result for a team leader (missed calls, no other problem flagged): adds the team line

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Profile
Team leader
Costing you most
Calls I do not get to

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Your biggest leak: calls you do not get to.

Sam, you told us the thing costing you most is missed calls. You cannot be in a showing and on the phone. A caller who reaches voicemail can hang up and call the next agent. Something else has to pick up.

What fixes it
Available now: the Founding 10
Next Level Answer
$300 a month
An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. No setup fee for the first 10 clients. 250 AI call minutes a month are included. The $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
Running a team: each additional agent line on the same account is $150 a month at the founding price, and adds 125 minutes to a shared pool.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. You dial the live system yourself and hear it answer. Ray shows you the real usage on his own line before you pay.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Mortgage broker result (founding-business path)

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Business
Mortgage broker
Biggest phone problem
Calls go to voicemail while I am working

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Your biggest phone problem: calls that reach voicemail.

Sam, you cannot be with a client and on the phone. A client who reaches voicemail can hang up and call the next broker. Something else has to pick up.

In your words
Calls go to voicemail while I am working.
It goes to voicemail and I call back when I can.
What fixes it
Open now to mortgage brokers: 3 founding spots
Next Level Answer
$300 a month
An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. You keep your number, and calls forward only when you do not answer. The same founding terms as real estate agents: no setup fee, 250 AI call minutes a month included, and the $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
3 of the 10 founding spots are open to mortgage brokers and to contractors and renovators. The other 7 are for real estate agents.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. Ray asks about your business. You dial the live system yourself and hear it answer, and Ray shows you the real usage on his own line before you pay.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Contractor result (founding-business path)

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Business
Contractor or renovator
Biggest phone problem
Calls in the evening and on weekends go unanswered

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Your biggest phone problem: calls after hours.

Sam, you cannot be on a job site and on the phone. A customer who reaches voicemail can hang up and call the next contractor. Something else has to pick up.

In your words
Calls in the evening and on weekends go unanswered.
I am not sure how many calls I miss.
What fixes it
Open now to contractors and renovators: 3 founding spots
Next Level Answer
$300 a month
An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. You keep your number, and calls forward only when you do not answer. The same founding terms as real estate agents: no setup fee, 250 AI call minutes a month included, and the $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
3 of the 10 founding spots are open to mortgage brokers and to contractors and renovators. The other 7 are for real estate agents.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. Ray asks about your business. You dial the live system yourself and hear it answer, and Ray shows you the real usage on his own line before you pay.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Waitlist result with a date (real estate lawyer; accountants and insurance read the same)

Next Level
Waitlist brief
Prepared for
Sam
Date
November 15, 2026
Business
Real estate lawyer
Biggest phone problem
I call back too late and they have moved on

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Next Level Answer opens to your industry on 1 March 2027.

Next Level Answer opens to real estate lawyers, accountants and insurance on 1 March 2027, from $500 setup plus $400 a month, in Canadian dollars. People on the waitlist get first notice before that date. There is nothing to buy today.

In your words
I call back too late and they have moved on.
Your next step

Join the waitlist with one message.

Message WAITLIST on Instagram
↗
(opens in a new tab)

The button copies WAITLIST and opens @rayahmadi. Send it as a message and Ray will add you to the list.

Operated by Ray Ahmadi
Ray Ahmadi
Change my answers

### Waitlist result with no date ("Something else")

Next Level
Waitlist brief
Prepared for
Sam
Date
November 15, 2026
Business
Something else
Biggest phone problem
I answer everything myself and it pulls me off my work

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
You can join the waitlist. No date is promised.

Today Next Level Answer is open to real estate agents, mortgage brokers, and contractors and renovators. Real estate lawyers, accountants and insurance open on 1 March 2027. For any other business no date is promised, and there is nothing to buy today.

In your words
I answer everything myself and it pulls me off my work.
Your next step

Join the waitlist with one message.

Message WAITLIST on Instagram
↗
(opens in a new tab)

The button copies WAITLIST and opens @rayahmadi. Send it as a message and Ray will add you to the list.

Operated by Ray Ahmadi
Ray Ahmadi
Change my answers

### US list result

Next Level
US list brief
Prepared for
Sam
Date
November 15, 2026
Business
Real estate agent or team
Country
United States

This brief is shown here only. Nothing was sent or stored. Your answers stay in this browser.

Your result, Sam
Founding clients are in Canada only. You can join the US list.

Next Level Answer is not sold to US clients yet. By 1 March 2027 everyone on the US list is told the US opening date and the price in US dollars. Nothing is sold to US clients before then, so there is nothing to buy or book today.

Your next step

Join the US list with one message.

Message USLIST on Instagram
↗
(opens in a new tab)

The button copies USLIST and opens @rayahmadi. Send it as a message and Ray will add you to the US list.

Operated by Ray Ahmadi
Ray Ahmadi
Change my answers

## Screens that appear only when the webhook is switched on

Not visible on the page as published. Included so the next test can judge them.

### First screen hint (the only difference on the question screens)

One tap per answer. Six questions for real estate agents, three for mortgage brokers and contractors. Your name and email are only asked at the end.

### Last step, agent path

Last step
Your details
Where should we send your result?
First name
Email
Mobile (optional)
Yes, email me my result and follow-up from Next Level. I can unsubscribe at any time.

Show my result
→

Without the tick you still see your result here, and nothing is sent. We do not sell or share your details.

Back

### Last step, the other paths

The same form. Only the heading changes:

- Mortgage broker and contractor: "Where should we send your result?"
- Waitlist: "Where should Ray reach you when your industry opens?"
- US list: "Where should Ray send the US opening date?"

### Last step once a mobile number is typed (the text consent box appears)

Last step
Your details
Where should Ray send the US opening date?
First name
Email
Mobile (optional)
Yes, email me my result and follow-up from Next Level. I can unsubscribe at any time.
Yes, you may text me at this number about my result. Reply STOP to end.

Show my result
→

Without the tick you still see your result here, and nothing is sent. We do not sell or share your details.

Back

### Agent result, missed calls, email box not ticked (nothing sent)

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Profile
Solo agent
Costing you most
Calls I do not get to
Your result, Sam
Your biggest leak: calls you do not get to.

Sam, you told us the thing costing you most is missed calls. You cannot be in a showing and on the phone. A caller who reaches voicemail can hang up and call the next agent. Something else has to pick up.

In your words
It goes to voicemail and I call back when I can.
A few months ago.
Very few.
Yes, and I do not know if they work.
What fixes it
Available now: the Founding 10
Next Level Answer
$300 a month
An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. No setup fee for the first 10 clients. 250 AI call minutes a month are included. The $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Your answers point to all four problems. Next Level Complete runs all four as one system, when all four are open: $1,500 setup + $1,500 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. You dial the live system yourself and hear it answer. Ray shows you the real usage on his own line before you pay.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Agent result, missed calls, sent with consent: adds "Ray will contact you at the details you gave" beside the Instagram option

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Profile
Solo agent
Costing you most
Calls I do not get to
Your result, Sam
Your biggest leak: calls you do not get to.

Sam, you told us the thing costing you most is missed calls. You cannot be in a showing and on the phone. A caller who reaches voicemail can hang up and call the next agent. Something else has to pick up.

In your words
It goes to voicemail and I call back when I can.
A few months ago.
Very few.
Yes, and I do not know if they work.
What fixes it
Available now: the Founding 10
Next Level Answer
$300 a month
An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. No setup fee for the first 10 clients. 250 AI call minutes a month are included. The $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Your answers point to all four problems. Next Level Complete runs all four as one system, when all four are open: $1,500 setup + $1,500 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. You dial the live system yourself and hear it answer. Ray shows you the real usage on his own line before you pay.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

Or wait for Ray

Ray will contact you at the details you gave.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Contractor result, sent with consent

Next Level
Intake brief
Prepared for
Sam
Date
November 15, 2026
Business
Contractor or renovator
Biggest phone problem
Calls in the evening and on weekends go unanswered
Your result, Sam
Your biggest phone problem: calls after hours.

Sam, you cannot be on a job site and on the phone. A customer who reaches voicemail can hang up and call the next contractor. Something else has to pick up.

In your words
Calls in the evening and on weekends go unanswered.
I am not sure how many calls I miss.
What fixes it
Open now to contractors and renovators: 3 founding spots
Next Level Answer
$300 a month
An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. You keep your number, and calls forward only when you do not answer. The same founding terms as real estate agents: no setup fee, 250 AI call minutes a month included, and the $300 price stays locked while your subscription is active. After the Founding 10: $500 setup + $400 a month.

Prices in Canadian dollars.

Before you pay
$300 a month for the first 10 clients. That includes 250 AI call minutes a month, your phone number and up to 500 text segments. Extra minutes are $0.30 each, up to a cap you set. The cap can be zero.
A part minute counts as a minute, and unused minutes do not carry over.
3 of the 10 founding spots are open to mortgage brokers and to contractors and renovators. The other 7 are for real estate agents.
You get a written agreement before any payment. It names the registered business.
You dial the live system yourself on the call, before you pay.
English is live today. Any other language is tested on your own line first. No charge if it does not handle your callers to your standard.
Your callers stay yours. Audio recording is off unless you turn it on. Your data is stored in the United States, not in Canada.
Founding clients are in Canada only. In the United States? Change your first answer to join the US list.
Ask Ray for a time

The call is 15 minutes. Ray asks about your business. You dial the live system yourself and hear it answer, and Ray shows you the real usage on his own line before you pay.

Message NEXT on Instagram
↗
(opens in a new tab)

The button copies NEXT and opens @rayahmadi. Send it as a message and Ray will send you a time.

Or wait for Ray

Ray will contact you at the details you gave.

The online calendar opens shortly.

On your call: Ray, every time
Ray Ahmadi
Change my answers

### Waitlist result with a date, sent with consent

Next Level
Waitlist brief
Prepared for
Sam
Date
November 15, 2026
Business
Real estate lawyer
Biggest phone problem
I call back too late and they have moved on
Your result, Sam
Next Level Answer opens to your industry on 1 March 2027.

Next Level Answer opens to real estate lawyers, accountants and insurance on 1 March 2027, from $500 setup plus $400 a month, in Canadian dollars. People on the waitlist get first notice before that date. There is nothing to buy today.

In your words
I call back too late and they have moved on.
Your next step

You are on the waitlist. You get first notice before 1 March 2027.

Operated by Ray Ahmadi
Ray Ahmadi
Change my answers

### Waitlist result with no date, sent with consent

Next Level
Waitlist brief
Prepared for
Sam
Date
November 15, 2026
Business
Something else
Biggest phone problem
I answer everything myself and it pulls me off my work
Your result, Sam
You can join the waitlist. No date is promised.

Today Next Level Answer is open to real estate agents, mortgage brokers, and contractors and renovators. Real estate lawyers, accountants and insurance open on 1 March 2027. For any other business no date is promised, and there is nothing to buy today.

In your words
I answer everything myself and it pulls me off my work.
Your next step

You are on the waitlist. No date is promised. If your kind of business opens, you get first notice.

Operated by Ray Ahmadi
Ray Ahmadi
Change my answers

### US list result, sent with consent

Next Level
US list brief
Prepared for
Sam
Date
November 15, 2026
Business
Real estate agent or team
Country
United States
Your result, Sam
Founding clients are in Canada only. You can join the US list.

Next Level Answer is not sold to US clients yet. By 1 March 2027 everyone on the US list is told the US opening date and the price in US dollars. Nothing is sold to US clients before then, so there is nothing to buy or book today.

Your next step

You are on the US list. Ray tells you the US opening date and the US dollar price by 1 March 2027.

Operated by Ray Ahmadi
Ray Ahmadi
Change my answers

## Every button and link, and what it does

| Label | Where | What it does |
|---|---|---|
| 01 RAY | index | Scrolls to "ray" with its heading in view and marks this index item current |
| 02 INTAKE | index | Scrolls to "quiz" with its heading in view and marks this index item current |
| 03 LEAKS | index | Scrolls to "leaks" with its heading in view and marks this index item current |
| 04 METHOD | index | Scrolls to "how" with its heading in view and marks this index item current |
| 05 FOUNDING 10 | index | Scrolls to "founding" with its heading in view and marks this index item current |
| 06 MENU | index | Scrolls to "menu" with its heading in view and marks this index item current |
| 07 QUESTIONS | index | Scrolls to "faq" with its heading in view and marks this index item current |
| 08 BOOK | index | Scrolls to "book" with its heading in view and marks this index item current |
| SEE WHAT IT WOULD DO FOR YOU (60 SECONDS) → | hero | Scrolls to the intake and puts focus on the current question |
| SEE THE PRICES | hero | Scrolls to "menu" with its heading in view |
| Join the US list | hero | Opens the US list question in the intake, with focus on it |
| SEE A SAMPLE CALL → | hero | Opens the sample call as a modal dialog with focus inside; Tab stays inside; Esc closes and focus returns here |
| FIND MY BIGGEST LEAK → | leaks | Scrolls to the intake and puts focus on the current question |
| ASK RAY FOR A TIME → | founding | Scrolls to "book" with its heading in view |
| Or start with the intake | founding | Scrolls to the intake and puts focus on the current question |
| ALL 21 TERMS | founding | Opens the folded list (aria-expanded true, content visible); a second press closes it (content stays in the DOM) |
| I am in the United States | founding | Opens the US list question in the intake, with focus on it |
| What does it cost, and what does usage cost? | faq | Opens its answer; a second press closes it |
| Does it speak other languages? | faq | Opens its answer; a second press closes it |
| Who can read my transcripts, and where is my data held? | faq | Opens its answer; a second press closes it |
| Does it work with my CRM? | faq | Opens its answer; a second press closes it |
| Is there a contract? | faq | Opens its answer; a second press closes it |
| Can I hear it first? | faq | Opens its answer; a second press closes it |
| ALL 22 QUESTIONS | faq | Opens the folded list (aria-expanded true, content visible); a second press closes it (content stays in the DOM) |
| Will callers know it is an AI? | faq | Opens its answer; a second press closes it |
| What is available today? | faq | Opens its answer; a second press closes it |
| What does Answer cost after the Founding 10? | faq | Opens its answer; a second press closes it |
| Is there a cheaper plan? | faq | Opens its answer; a second press closes it |
| How long does setup take? | faq | Opens its answer; a second press closes it |
| Do I have to change my phone number? | faq | Opens its answer; a second press closes it |
| What do you need from me? | faq | Opens its answer; a second press closes it |
| Will my brokerage allow it? | faq | Opens its answer; a second press closes it |
| Is it allowed where I work? | faq | Opens its answer; a second press closes it |
| Do you have client testimonials? | faq | Opens its answer; a second press closes it |
| I run a team. How does that work? | faq | Opens its answer; a second press closes it |
| I am in the US. Can I join? | faq | Opens its answer; a second press closes it |
| Who pays for the ads? | faq | Opens its answer; a second press closes it |
| Does this promise me more leads or deals? | faq | Opens its answer; a second press closes it |
| Do I have to join Ray's team? | faq | Opens its answer; a second press closes it |
| I run a business that is not real estate. Can I use it? | faq | Opens its answer; a second press closes it |
| MESSAGE NEXT ON INSTAGRAM ↗ (OPENS IN A NEW TAB) | book | Copies NEXT, opens https://www.instagram.com/rayahmadi/ in a new tab (rel noopener) and confirms on the page |
| Not sure which problem is yours? Take the 60-second intake first. | book | Scrolls to the intake and puts focus on the current question |
| Close | sample | Closes the sample call and returns focus to "See a sample call" |
| Each answer option (A, B, C ...) | Intake, agent path: "Which best describes you?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, agent path: "Which best describes you?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, agent path: "A new buyer calls while you are in a showing. What happens?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, agent path: "When did you last ask a client for a Google review?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, agent path: "When did you last ask a client for a Google review?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, agent path: "Think about every contact in your database. How many heard from you in the last 90 days?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, agent path: "Are you running paid ads right now?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, agent path: "Are you running paid ads right now?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, agent path: "Which one of these costs you the most right now?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, agent path: "Which one of these costs you the most right now?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Back | Intake, agent path: last step | Returns to the last question with its answer marked |
| First name (optional) field | Intake, agent path: last step | Takes text by mouse focus and keyboard typing; may be left empty |
| Show my brief | Intake, agent path: last step | Shows the brief on the page; nothing is sent |
| MESSAGE NEXT ON INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, agent path: result | Copies NEXT, opens instagram.com/rayahmadi in a new tab (rel noopener) and confirms on the page |
| CHANGE MY ANSWERS | Intake, agent path: result | Returns to the first question with every answer kept |
| Each answer option (A, B, C ...) | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, founding-business (mortgage broker) path: "Which best describes you?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, founding-business (mortgage broker) path: "What is your biggest phone problem right now?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, founding-business (mortgage broker) path: "A new client calls while you are with someone else. What happens?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Back | Intake, founding-business (mortgage broker) path: last step | Returns to the last question with its answer marked |
| First name (optional) field | Intake, founding-business (mortgage broker) path: last step | Takes text by mouse focus and keyboard typing; may be left empty |
| Show my brief | Intake, founding-business (mortgage broker) path: last step | Shows the brief on the page; nothing is sent |
| MESSAGE NEXT ON INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, founding-business (mortgage broker) path: result | Copies NEXT, opens instagram.com/rayahmadi in a new tab (rel noopener) and confirms on the page |
| CHANGE MY ANSWERS | Intake, founding-business (mortgage broker) path: result | Returns to the first question with every answer kept |
| Each answer option (A, B, C ...) | Intake, founding-business (contractor) path: "Which best describes you?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, founding-business (contractor) path: "Which best describes you?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, founding-business (contractor) path: "What is your biggest phone problem right now?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, founding-business (contractor) path: "A new customer calls while you are on a job site. What happens?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Back | Intake, founding-business (contractor) path: last step | Returns to the last question with its answer marked |
| First name (optional) field | Intake, founding-business (contractor) path: last step | Takes text by mouse focus and keyboard typing; may be left empty |
| Show my brief | Intake, founding-business (contractor) path: last step | Shows the brief on the page; nothing is sent |
| MESSAGE NEXT ON INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, founding-business (contractor) path: result | Copies NEXT, opens instagram.com/rayahmadi in a new tab (rel noopener) and confirms on the page |
| CHANGE MY ANSWERS | Intake, founding-business (contractor) path: result | Returns to the first question with every answer kept |
| Each answer option (A, B, C ...) | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, waitlist with a date (real estate lawyer) path: "Which best describes you?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, waitlist with a date (real estate lawyer) path: "What kind of business do you run?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, waitlist with a date (real estate lawyer) path: "What is your biggest phone problem right now?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Back | Intake, waitlist with a date (real estate lawyer) path: last step | Returns to the last question with its answer marked |
| First name (optional) field | Intake, waitlist with a date (real estate lawyer) path: last step | Takes text by mouse focus and keyboard typing; may be left empty |
| Show my brief | Intake, waitlist with a date (real estate lawyer) path: last step | Shows the brief on the page; nothing is sent |
| MESSAGE WAITLIST ON INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, waitlist with a date (real estate lawyer) path: result | Copies WAITLIST, opens instagram.com/rayahmadi in a new tab (rel noopener) and confirms on the page |
| CHANGE MY ANSWERS | Intake, waitlist with a date (real estate lawyer) path: result | Returns to the first question with every answer kept |
| Each answer option (A, B, C ...) | Intake, waitlist with no date (something else) path: "Which best describes you?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, waitlist with no date (something else) path: "Which best describes you?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, waitlist with no date (something else) path: "What kind of business do you run?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, waitlist with no date (something else) path: "What is your biggest phone problem right now?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Back | Intake, waitlist with no date (something else) path: last step | Returns to the last question with its answer marked |
| First name (optional) field | Intake, waitlist with no date (something else) path: last step | Takes text by mouse focus and keyboard typing; may be left empty |
| Show my brief | Intake, waitlist with no date (something else) path: last step | Shows the brief on the page; nothing is sent |
| MESSAGE WAITLIST ON INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, waitlist with no date (something else) path: result | Copies WAITLIST, opens instagram.com/rayahmadi in a new tab (rel noopener) and confirms on the page |
| CHANGE MY ANSWERS | Intake, waitlist with no date (something else) path: result | Returns to the first question with every answer kept |
| Each answer option (A, B, C ...) | Intake, us-list path: "Which best describes you?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, us-list path: "Which best describes you?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Each answer option (A, B, C ...) | Intake, us-list path: "What kind of business do you run in the United States?" | Saves the answer and moves to the next screen with focus on its heading; Back returns with this answer marked and a Next control |
| Next and Back | Intake, us-list path: "What kind of business do you run in the United States?" | Space on an answer chooses it; Back returns; Next moves forward without changing the answer |
| Back | Intake, us-list path: last step | Returns to the last question with its answer marked |
| First name (optional) field | Intake, us-list path: last step | Takes text by mouse focus and keyboard typing; may be left empty |
| Show my brief | Intake, us-list path: last step | Shows the brief on the page; nothing is sent |
| MESSAGE USLIST ON INSTAGRAM ↗ (OPENS IN A NEW TAB) | Intake, us-list path: result | Copies USLIST, opens instagram.com/rayahmadi in a new tab (rel noopener) and confirms on the page |
| CHANGE MY ANSWERS | Intake, us-list path: result | Returns to the first question with every answer kept |
| Back | Intake, agent path: last step (webhook set) | Returns to the last question with its answer marked |
| First name field | Intake, agent path: last step (webhook set) | Required; error names it |
| Email field | Intake, agent path: last step (webhook set) | Checked only when the consent box is ticked |
| Mobile (optional) field | Intake, agent path: last step (webhook set) | Typing a number reveals the text-consent box |
| Email consent checkbox | Intake, agent path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Text consent checkbox | Intake, agent path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Show my result | Intake, agent path: last step (webhook set) | Without consent: result only, no request. With consent: one POST, then the result |
| Back | Intake, founding-business (mortgage broker) path: last step (webhook set) | Returns to the last question with its answer marked |
| First name field | Intake, founding-business (mortgage broker) path: last step (webhook set) | Required; error names it |
| Email field | Intake, founding-business (mortgage broker) path: last step (webhook set) | Checked only when the consent box is ticked |
| Mobile (optional) field | Intake, founding-business (mortgage broker) path: last step (webhook set) | Typing a number reveals the text-consent box |
| Email consent checkbox | Intake, founding-business (mortgage broker) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Text consent checkbox | Intake, founding-business (mortgage broker) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Show my result | Intake, founding-business (mortgage broker) path: last step (webhook set) | Without consent: result only, no request. With consent: one POST, then the result |
| Back | Intake, founding-business (contractor) path: last step (webhook set) | Returns to the last question with its answer marked |
| First name field | Intake, founding-business (contractor) path: last step (webhook set) | Required; error names it |
| Email field | Intake, founding-business (contractor) path: last step (webhook set) | Checked only when the consent box is ticked |
| Mobile (optional) field | Intake, founding-business (contractor) path: last step (webhook set) | Typing a number reveals the text-consent box |
| Email consent checkbox | Intake, founding-business (contractor) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Text consent checkbox | Intake, founding-business (contractor) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Show my result | Intake, founding-business (contractor) path: last step (webhook set) | Without consent: result only, no request. With consent: one POST, then the result |
| Back | Intake, waitlist with a date (real estate lawyer) path: last step (webhook set) | Returns to the last question with its answer marked |
| First name field | Intake, waitlist with a date (real estate lawyer) path: last step (webhook set) | Required; error names it |
| Email field | Intake, waitlist with a date (real estate lawyer) path: last step (webhook set) | Checked only when the consent box is ticked |
| Mobile (optional) field | Intake, waitlist with a date (real estate lawyer) path: last step (webhook set) | Typing a number reveals the text-consent box |
| Email consent checkbox | Intake, waitlist with a date (real estate lawyer) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Text consent checkbox | Intake, waitlist with a date (real estate lawyer) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Show my result | Intake, waitlist with a date (real estate lawyer) path: last step (webhook set) | Without consent: result only, no request. With consent: one POST, then the result |
| Back | Intake, waitlist with no date (something else) path: last step (webhook set) | Returns to the last question with its answer marked |
| First name field | Intake, waitlist with no date (something else) path: last step (webhook set) | Required; error names it |
| Email field | Intake, waitlist with no date (something else) path: last step (webhook set) | Checked only when the consent box is ticked |
| Mobile (optional) field | Intake, waitlist with no date (something else) path: last step (webhook set) | Typing a number reveals the text-consent box |
| Email consent checkbox | Intake, waitlist with no date (something else) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Text consent checkbox | Intake, waitlist with no date (something else) path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Show my result | Intake, waitlist with no date (something else) path: last step (webhook set) | Without consent: result only, no request. With consent: one POST, then the result |
| Back | Intake, us-list path: last step (webhook set) | Returns to the last question with its answer marked |
| First name field | Intake, us-list path: last step (webhook set) | Required; error names it |
| Email field | Intake, us-list path: last step (webhook set) | Checked only when the consent box is ticked |
| Mobile (optional) field | Intake, us-list path: last step (webhook set) | Typing a number reveals the text-consent box |
| Email consent checkbox | Intake, us-list path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Text consent checkbox | Intake, us-list path: last step (webhook set) | Mouse ticks it, Space unticks it; never pre-ticked |
| Show my result | Intake, us-list path: last step (webhook set) | Without consent: result only, no request. With consent: one POST, then the result |

Not controls (they look like labels and do nothing when tapped): the wordmark, the "Available now", "Opening next" and "When all four are open" tags, the moving strip, the portrait frame, the illustration.

While no booking link is set, every buying result ends at "Ask Ray for a time": one blue button, "Message NEXT on Instagram" (copies the word NEXT, opens instagram.com/rayahmadi in a new tab, and shows "Copied NEXT. Paste it in a message to @rayahmadi."), the plain instruction under it, and the line "The online calendar opens shortly." There is no button that looks like a calendar. When the webhook is set and the visitor ticked consent, a second option sits beside the button: "Ray will contact you at the details you gave." The waitlist result uses the word WAITLIST and the US list result uses USLIST in the same way. The founding section button reads "Ask Ray for a time" and scrolls to the last section, which shows the same block.

## What is NOT on the page

- **No portrait yet.** The About Ray strip shows a small empty 4:5 frame with the initials "RA" and the caption "Portrait to come". The signature is typeset in a script face, not Ray's real signature.
- **No recording to play.** "See a sample call" opens a written script labelled "Sample script for illustration, not a recording". There is no audio anywhere on the page.
- **No testimonials.** The page says so and gives it as the reason for the founding price and terms. There are no client names, logos, reviews, star ratings or results figures anywhere.
- **No demo number.** Nothing on the page mentions a demo line or a number to dial. The page says "you dial the live system yourself on the call". (A "Call the demo line" block appears under the hero buttons and in the buying results only once a number is set.)
- **No booking calendar.** Every booking step is "Ask Ray for a time" as described above, and it says "The online calendar opens shortly."
- **No business name or address.** The footer reads "Operated by Ray Ahmadi. The registered business name and address are on the agreement you sign before any payment." The old bracketed placeholder is no longer visible. There are no privacy policy or terms links.
- **No list of supported languages.** The page says English is live today and that other languages are tested on the visitor's own line before go-live with no charge if one does not meet their standard, then names seven languages that are not promised and says to ask Ray on the call.
- **No US price or US opening date, and no way for a US visitor to buy or book.**
- **No HST statement.** Prices are stated in Canadian dollars with no line on tax.
- **No names for the set-up team, no countdown timer, no "spots left" counter, no numbers from Ray's own line, no promise of leads, deals or income.**
- **No email, mobile or consent fields, and nothing sent anywhere.** No webhook is set, so the last quiz step asks only for an optional first name, the result says it is shown here only, and waitlist and US list visitors are asked to message Ray on Instagram.
