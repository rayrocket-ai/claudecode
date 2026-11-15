# Smart sales page: copy

Draft for Ray to approve. Agent edition. Nothing is published until every `[Ray to ...]` is filled and Ray says yes.

**Working offer.** The round 2 offer (`../testing/offer-pitch-v2.md`) is the working offer. Lines marked "Set 2026-11-15 after the persona test; Ray to confirm" were set by the assistant after the persona test, under Ray's instruction to fix the offer. Ray has not approved them yet. The markers are notes for Ray and the builder and do not appear on the page. Full list: `../offer.md` section 6.

Flow: headline > quiz (6 questions) > contact step > personalized result > offer > FAQ > book the 15-minute call.

## 1. Headline options

Pick one. Test a second later.

1. **Every call answered, qualified and booked. Live in 7 days.**
2. **You were in a showing. Who answered your phone?**
3. **Your next client called while you were with your last one.**
4. **An AI receptionist for agents, built by a broker who runs it on his own business.**
5. **Find the biggest leak in your business in 6 questions.**

Subheadline (works with any of the five):
Answer 6 questions. See where your business leaks first and what fixes it.

Button: **Start the quiz**

Under the button: Built and used by Ray Ahmadi. GTA real estate broker, Ray Homes Real Estate under eXp Realty. 12+ years. About 50 deals a year. Multi-year eXp Icon agent. English and Dari. [Ray to confirm: what can be said about eXp on a Next Level page]

## 2. The quiz

One question per screen. One tap per answer.

Each answer that points to a problem is marked with its route.

**Q1. A new buyer calls while you are in a showing. What happens?**
- A. It goes to voicemail and I call back when I can. → **missed calls**
- B. Someone on my team picks up.
- C. I step out and take it.
- D. I am not sure how many I miss. → **missed calls**

**Q2. When did you last ask a client for a Google review?**
- A. At my last closing. I ask every time.
- B. A few months ago. → **reviews**
- C. I cannot remember. → **reviews**
- D. I do not have a Google Business Profile set up. → **reviews**

**Q3. Think about every contact in your database. How many heard from you in the last 90 days?**
- A. Most of them.
- B. Some of them. → **dead database**
- C. Very few. → **dead database**
- D. I do not have them in one place. → **dead database**

**Q4. Are you running paid ads right now?**
- A. Yes, and I know what each lead costs me.
- B. Yes, and I do not know if they work. → **ads**
- C. I tried and stopped. → **ads**
- D. No, and I do not plan to.

**Q5. Which one of these costs you the most right now?**
- A. Calls I do not get to. → **missed calls**
- B. Not enough reviews. → **reviews**
- C. A database I never contact. → **dead database**
- D. Ads that do not pay. → **ads**

**Q6. Which best describes you?**
- A. Solo agent.
- B. Agent with an assistant.
- C. Team leader.
- D. Broker or brokerage owner.

Q6 does not route. It tells Ray, who takes every call for now, who is on the call. Team leaders and brokers are tagged for the later team offers.

### Routing rule

1. The answer to Q5 decides the result.
2. Q1 to Q4 are saved as secondary flags and used later in follow-up.
3. Each result writes one tag: `nl-problem-missed-calls`, `nl-problem-reviews`, `nl-problem-dead-database` or `nl-problem-ads`.
4. Each tag starts the matching follow-up sequence, only for contacts who ticked the consent box.

### Contact step

Heading: **Where should we send your result?**

- First name
- Email
- Mobile (optional)

Checkbox, not pre-ticked:
"Yes, send me my result and follow-up emails from Ray Ahmadi at Next Level. I can unsubscribe at any time."

Second checkbox, not pre-ticked, shown only if a mobile number is entered:
"Yes, you may text me at this number about my result. Reply STOP to end."

Below the button:
Ray Ahmadi | Next Level
[Ray to confirm: business name and mailing address for Next Level]
We do not sell or share your details.

If the first box is not ticked: show the result on screen and send nothing.

Button: **Show my result**

## 3. Result blocks

Each block: what we saw, what it means, what fixes it, next step.

**Shown under every result, above the button.** Set 2026-11-15 after the persona test; Ray to confirm.

- $300 a month for the first 10 agents. Phone, text and AI minutes are billed at cost with no markup, up to a monthly cap you set.
- You dial the live system yourself on the call, before you pay.
- English at launch. Any other language is tested on your own line. No charge if it is not good enough for you.
- Your callers stay yours. Audio recording is off unless you turn it on.
- Canada first. US agents where setup is confirmed for their state on the call.

### Result: missed calls

**Your biggest leak: calls you do not get to.**

{{contact.first_name}}, you told us calls go to voicemail when you are with a client. A caller who reaches voicemail can hang up and call the next agent.

You cannot be in a showing and on the phone. Something else has to pick up.

**What fixes it:** Next Level Answer. An AI receptionist answers every call you miss, says it is an AI, asks the questions you choose, and books the appointment on your calendar. You get a summary of each call by text and by email. If a caller asks for a person, or it is urgent, it offers a callback and texts you straight away. You keep your number, and calls forward only when you do not answer. It is live in 7 days.

Ray is a GTA real estate broker with 12+ years in the business and about 50 deals a year. He runs this on his own line at Ray Homes.

**Your next step:** book a 15-minute call. You dial the live system yourself and hear it answer. Ray shows you his own numbers and the real usage bill for his own line before you pay. [Ray to add: real number from Ray Homes]

Button: **Book my 15-minute call**

Second option: **Send me a free missed-call audit.** We call your business line once in the evening and send you exactly what happened.

### Result: reviews

**Your biggest leak: happy clients who were never asked.**

{{contact.first_name}}, you told us review requests happen when you remember. Meanwhile buyers and sellers can compare agents on Google before they call anyone.

**What fixes it:** a review request that goes out at closing and again at day 30, every time, with replies drafted for you to approve. This is Next Level Reviews. It opens after Ray finishes proving it on his own business.

**What is ready today:** Next Level Answer, the AI receptionist. More reviews bring more calls. Those calls need answering.

**Your next step:** book a 15-minute call. Ray will show you his own review system and his own review numbers live, and put you first in line for Reviews. You can also dial the live receptionist yourself on the call. [Ray to add: real number from Ray Homes]

Button: **Book my 15-minute call**

### Result: dead database

**Your biggest leak: a database nobody is talking to.**

{{contact.first_name}}, you told us most of your contacts have not heard from you in the last 90 days. Some of them will move. The agent who stayed in touch is the one they think of.

**What fixes it:** a reactivation campaign to the people you have permission to contact, follow-up with everyone who raises a hand, and regular past-client touches. This is Next Level Nurture. It opens after Ray finishes proving it on his own database.

**What is ready today:** Next Level Answer, the AI receptionist. When your database starts calling back, every call is answered and booked.

**Your next step:** book a 15-minute call. Ray will walk you through what he is running on his own list and show you his own numbers live. You can also dial the live receptionist yourself on the call. [Ray to add: real number from Ray Homes]

Button: **Book my 15-minute call**

### Result: ads

**Your biggest leak: ad money with nobody watching it.**

{{contact.first_name}}, you told us you run ads, or tried to, and cannot say what they did. Ads fail in two places: nobody watches them daily, and nobody calls the lead fast.

**What fixes it:** listing and buyer ads run and watched daily. This is Next Level Ads. It opens after Ray finishes proving it on his own business.

**What is ready today:** the second half of the fix. Next Level Answer picks up every call your ads create and books it.

**Your next step:** book a 15-minute call. Bring your last ad report. Ray will go through it with you and show you his own ad numbers live. You can also dial the live receptionist yourself on the call. [Ray to add: real number from Ray Homes]

Button: **Book my 15-minute call**

## 4. The offer section

**The Founding 10**

We are opening Next Level to 10 agents first. It is open now.

**What you get: Next Level Answer**
- Every call answered by an AI receptionist set up for your business.
- Callers qualified with your questions.
- Appointments booked on your calendar.
- A text back to anyone who hangs up.
- A summary of every call, by text and by email.
- A callback offer and a text alert to you when a caller asks for a person or it is urgent.
- Set up for you. Live in 7 days from the day we have your details.
- A check-in at day 3 and day 14.
- A results report every month.

**The founding price: $300 a month.**

**Usage, in plain terms.** Phone, text and AI minutes are billed at cost with no markup for founding clients, on top of the $300. You set a monthly spending cap before go-live, and the system stops and alerts you if it is reached. On the call Ray shows you the real usage bill for his own line before you pay. (Set 2026-11-15 after the persona test; Ray to confirm. The rate per minute as a number: [Ray to add: usage rate per minute])

**Founding terms** (Approved by Ray, 2026-11-15)
- No setup fee for the Founding 10.
- Your $300 a month stays locked while your subscription is active.
- Month to month. Cancel before your next billing date. Your contacts are exported for you when you leave.
- Live within 7 days of the day we have everything we need from you, or your first month is not charged. This applies once per client, to the first month only, and not when the delay is a carrier or registration approval outside our control.
- In return: a short feedback call at day 14 and at day 30. Your numbers are shared only with your written permission.

**More founding terms** (Set 2026-11-15 after the persona test; Ray to confirm)
- Try before you pay. On the call you dial the live system yourself.
- English at launch. Any other language is tested on your own line with you during setup. If it does not handle your callers' language to your standard, you do not go live and you are not charged.
- Your callers stay yours. No one at Next Level or Ray Homes contacts your callers or uses your contacts, and that is written in the agreement.
- Each call is transcribed so you get the summary. The transcript stays in your own account. The people who can read it are you, and the set-up team only while they are setting up or fixing your account.
- Audio recording is off unless you turn it on. When it is on, the AI says so at the start of the call.
- When you leave, your contacts and transcripts are exported to you and deleted from the account, and call forwarding is switched off that day.
- Every call arrives as a text and an email summary, so it works beside any CRM. A direct push into your CRM is confirmed for your specific CRM on the call, before you pay.
- You get a one-page summary to show your broker of record before you sign. If your brokerage says no within 14 days, you get your first month back.
- One subscription covers one business line. A team routing calls to several agents is quoted on the call.
- Canada first. US agents can join only where setup is confirmed for their state on the call. Prices are in Canadian dollars.

**Why there is a founding price:** Next Level is new. The first 10 agents are its founding clients, and there are no client testimonials yet. That is the reason the founding price and the founding terms exist. Founders pay $300 a month with no setup fee and a locked price. Everyone after them pays $500 setup plus $400 a month. (Set 2026-11-15 after the persona test; Ray to confirm.)

**Why 10:** [Ray to confirm: the real reason for the cap of 10. PROPOSED wording, Ray to approve: "Ray is involved in every founding setup and reviews the early calls himself. That only works with a small group."]

**Why trust it:** Ray is a working GTA real estate broker. Ray Homes Real Estate under eXp Realty. 12+ years. About 50 deals a year. Multi-year eXp Icon agent. He built this for his own business first and runs it there today. On the call you dial it yourself, and he shows you his own numbers and his own usage bill. [Ray to add: real number from Ray Homes]

**What it is not:** it is not a promise of leads or deals. It makes sure the calls you already get are answered and booked.

Button: **Book my 15-minute call**

## 5. FAQ

**Will callers know it is an AI?**
Yes. It says so at the start of the call. If a caller asks for a person, or it is urgent, it offers a callback and alerts you by text straight away. (Set 2026-11-15 after the persona test; Ray to confirm.)

**What does it sound like?**
Book the call and dial the live system yourself. You hear it answer before you pay anything. (Set 2026-11-15 after the persona test; Ray to confirm.) [Ray to add: demo line number, if Ray wants it public]

**How long does setup take?**
Live in 7 days from the day you send us your details.

**What do you need from me?**
Your business details, your hours and areas, the questions you want asked, calendar access, the number to forward, and the monthly spending cap you choose.

**Do I have to change my phone number?**
No. You keep your number. Calls forward only when you do not answer, including when your phone is off. Forwarding is switched off the day you cancel. (Set 2026-11-15 after the persona test; Ray to confirm.)

**Is there a contract?**
It is month to month. You can cancel before your next billing date, and we export your contacts for you. (Approved by Ray, 2026-11-15.) Your transcripts are exported with them, and both are deleted from the account when you leave. (Set 2026-11-15 after the persona test; Ray to confirm.)

**What does usage cost?** (Set 2026-11-15 after the persona test; Ray to confirm.)
Phone, text and AI minutes are billed at cost with no markup for founding clients, on top of the $300. You set a monthly spending cap before go-live. If it is reached, the system stops and alerts you. On the call Ray shows you the real usage bill for his own line before you pay. [Ray to add: usage rate per minute]

**What does it cost after the Founding 10?**
Founders pay $300 a month. After the Founding 10, Next Level Answer is $500 for setup plus $400 a month, in Canadian dollars. (Approved by Ray, 2026-11-15.)

**Is it allowed where I work?**
Rules on call recording and on telling callers they are speaking with an AI differ by province and state. We confirm them for your location before you go live. Audio recording is off unless you turn it on, and when it is on the AI says so at the start of the call. (Set 2026-11-15 after the persona test; Ray to confirm.)

**Will my brokerage allow it?** (Set 2026-11-15 after the persona test; Ray to confirm.)
You get a one-page summary to show your broker of record before you sign. If your brokerage says no within 14 days, you get your first month back.

**Does it speak other languages?** (Set 2026-11-15 after the persona test; Ray to confirm.)
English at launch. Any other language is tested on your own line with you during setup. If it does not handle your callers' language to your standard, you do not go live and you are not charged. [Ray to confirm: which languages the voice agent handles today]

**Can it tell a caller if a listing is still available?**
[Ray to confirm: is the listing lookup live for the Founding 10]

**I am on another CRM. Does this replace it?** (Set 2026-11-15 after the persona test; Ray to confirm.)
No. It works beside it. You get every call as a text and an email summary from day one. A direct push into your CRM is confirmed for your specific CRM on the call, before you pay. If it cannot be done, you are told then. [Ray to confirm: which CRMs get a direct push]

**Who can see my callers and my call transcripts?** (Set 2026-11-15 after the persona test; Ray to confirm.)
Your callers stay yours. No one at Next Level or Ray Homes contacts your callers or uses your contacts, and that is written in the agreement. Each call is transcribed so you get the summary. The transcript stays in your own account. The people who can read it are you, and the set-up team only while they are setting up or fixing your account. [Ray to add: where client data is hosted]

**I run a team. How does that work?** (Set 2026-11-15 after the persona test; Ray to confirm.)
One subscription covers one business line. A team routing calls to several agents is quoted on the call. [Ray to set: team pricing]

**I am in the US. Can I join?** (Set 2026-11-15 after the persona test; Ray to confirm.)
Canada first. US agents can join the Founding 10 only where setup is confirmed for their state on the call. The price is in Canadian dollars. [Ray to confirm: which US states]

**Do you have client testimonials?** (Set 2026-11-15 after the persona test; Ray to confirm.)
Not yet. Next Level is new and the first 10 agents are its founding clients. That is the reason the founding price and the founding terms exist. What you can check today is Ray's own track record and the live system, which you dial yourself on the call.

**Who is behind this?**
Ray Ahmadi, a GTA real estate broker with Ray Homes Real Estate under eXp Realty. 12+ years in the business, about 50 deals a year, and a multi-year eXp Icon agent. He works with clients in English and Dari. Next Level is operated by Ray Ahmadi. The registered business name and address are on the agreement you sign before paying. (Set 2026-11-15 after the persona test; Ray to confirm.) [Ray to confirm: business name and mailing address for Next Level]

**Do I have to join Ray's team?**
No. Next Level is open to agents at any brokerage.

**I run a business that is not real estate. Can I use it?**
Not yet. Answer opens to other businesses once the first 10 agents are live, in this order: mortgage brokers, real estate lawyers, accountants, contractors and renovators, insurance. The starting price is $500 setup plus $400 a month. Join the waitlist and you get first notice. We ask one question now: your industry and your biggest phone problem. Outside those five industries you can still join, and no date is promised. (Set 2026-11-15 after the persona test; Ray to confirm.)

## 6. Call to action

**Hear it answer a call.**

Book 15 minutes with Ray. He will ask about your business, have you dial the AI receptionist yourself, and tell you plainly if it fits. If it does, you can be live in 7 days.

Button: **Book my 15-minute call**

Under the button: 15 minutes. By phone or video. With Ray.

Footer on every page:
Ray Ahmadi | Next Level
[Ray to confirm: business name and mailing address for Next Level]
Privacy policy | Terms [Ray to confirm with counsel]

## Notes for the builder

- No countdown timers. No "only 2 spots left" unless it is true on that day and Ray updates it by hand.
- No testimonials until there are real ones with written permission. Where the page says there are none yet, it says so as the reason the founding price and founding terms exist.
- Every "(Set 2026-11-15 after the persona test; Ray to confirm.)" marker is a note for Ray and the builder. It is removed from the published page once Ray confirms the term.
- Every `[Ray to add: real number from Ray Homes]` is replaced with a real number or the bracket is removed. The sentence around it is written to stand without it: the page leads with Ray's track record and the live demo, and the system numbers are shown live on the call.
- The only track-record facts on the page: GTA real estate broker, Ray Homes Real Estate under eXp Realty, 12+ years, about 50 deals a year, multi-year eXp Icon agent, English and Dari. No other number.
- Traffic is inbound, from content on every platform. The free missed-call audit is an optional second step, not the main path.
- The page must read well on a phone first.
