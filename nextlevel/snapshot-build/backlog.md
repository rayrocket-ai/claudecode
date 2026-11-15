# Next Level: build backlog

Draft for Ray. Written 2026-11-15. A plan, not a record of work done. Nothing in a live account changes until Ray approves it.

Sources: `research/platform-teardown.md` (what the official pages confirm), `snapshot-build/automation-blueprints.md` (the recipes), `saas-build-spec.md` section 13 (the promises).

**Who builds.**
- **Ray**: decisions, counsel, billing, anything that creates a credential.
- **Diana**: work inside the HighLevel builder and the agency view.
- **Claude through the API**: the pieces the official API can create, in a sub-account where Ray has added a private integration. Claude publishes nothing and switches nothing on.
- **Viktor, as a proposal**: Viktor already holds a HighLevel connection in Slack and proposes and reports. Items marked this way are suggestions for his standing instructions. Ray approves each one before it starts.

**Effort.** S is under two hours. M is half a day to a day. L is more than a day.

## Access Claude needs

**Today.** The environment holds one HighLevel private integration token. It can only read conversations in the Ray Homes sub-account. It cannot read or write anything in the Next Level sub-account (location ID `n0qwGpNQ3CShe8AIhyI0`) or in NL Demo. So Claude cannot build anything yet.

**What Ray would do, himself.**

1. Open the Next Level sub-account. Go to Settings, then Private Integrations. Create one named "Claude build (Next Level)". Menu names: [verify in HighLevel].
2. Tick only the scopes in the table below. Leave everything else unticked.
3. Copy the token once and add it to this environment's secrets under its own name, for example `GHL_PIT_NEXTLEVEL`. Never paste it into a chat, a file in the repo, a Slack message or an email.
4. Do the same inside NL Demo with a second token, `GHL_PIT_NLDEMO`, because a sub-account token works only in its own sub-account and the master snapshot is built in NL Demo, not in the sales account.
5. Do not create an agency-level token for this work. Nothing in this backlog needs one.
6. Rotate or delete each token when the build is finished. A private integration token does not expire by itself (confirmed on the official page).

**Scopes, by exact name, from the official API reference read on 2026-11-15.** Whether the tick-box list in the account uses the same names: [verify in HighLevel].

| Scope | Read or write | What it allows | Needed for |
|---|---|---|---|
| `locations.readonly` | Read | Read the sub-account's own details | Confirming the token points at the right account |
| `locations/customValues.readonly` | Read | List custom values | Checking what exists before creating |
| `locations/customFields.readonly` | Read | List custom fields | Same |
| `locations/tags.readonly` | Read | List tags | Same |
| `locations/templates.readonly` | Read | List email and text templates | Checking message copy matches the approved text |
| `opportunities.readonly` | Read | List pipelines and stages | Checking the pipeline |
| `calendars.readonly` | Read | List calendars | Checking the calendar |
| `contacts.readonly` | Read | Read contacts | Finding the sample contacts Claude created, to remove them |
| `forms.readonly` | Read | List forms | Checking form names for workflow triggers |
| `workflows.readonly` | Read | Search workflows and read a definition | Also the test of whether HighLevel has enabled the workflow API for this sub-account |
| `voice-ai-agents.readonly` | Read | List voice agents and their settings | Checking the agent after creating it |
| `phonenumbers.read` | Read | List the sub-account's numbers | Confirming which number is the default, which must not go to the agent |
| `locations/customValues.write` | Write | Create and edit custom values | The `nl_` values |
| `locations/customFields.write` | Write | Create and edit custom fields | The `NL \| ` fields |
| `locations/tags.write` | Write | Create tags | The `nl-` tags |
| `pipelines.create` | Write | Create a pipeline with stages | NL \| Client pipeline, and the sales pipeline |
| `calendars.write` | Write | Create and edit calendars | The call calendar |
| `contacts.write` | Write | Create and delete contacts | Sample contacts labelled "sample" in NL Demo only. Not ticked on the sales account unless Ray wants test leads there |
| `voice-ai-agents.write` | Write | Create and edit a voice agent | The receptionist, in NL Demo only |
| `voice-ai-agent-goals.write` | Write | Create and edit a voice agent's actions | Booking, field updates, workflow triggers, in NL Demo only |
| `workflows.write` | Write | Create and edit workflows as drafts | Ticked only if the read test shows the workflow API is enabled |

**Deliberately left out.**

| Scope | Why it is not requested |
|---|---|
| `workflows.publish` | A person publishes every workflow, after reading it |
| `workflows.logs` | Logs can hold contact details. Diana reads them in the builder |
| `voice-ai-dashboard.readonly` | Call logs hold transcripts. Not needed to build. It would be needed only for the automated monthly report, which waits for Ray's decision on promise 7 |
| `conversation-ai.write`, `knowledge-bases.write` | Nothing in the first release uses them |
| `wallet.readonly` | Billing is checked by Ray in the agency view |
| `saas/company.write` and every agency scope | Rebilling, plans and snapshots are set by hand by Ray or Diana |
| Conversations and messages | Claude sends no messages. The existing Ray Homes token already reads conversations there; its scope name was not re-read today |

**Rules Claude follows with these tokens.** Read before writing. Create, never overwrite: if a name already exists, stop and report. Write to NL Demo first, to the sales account second, to a client account never. List every object created, with its ID, in the report back to Ray. Remove sample contacts at the end.

## This week: ready for the first founding client

| # | Item | Why | Who builds | Effort | Depends on | Done when |
|---|---|---|---|---|---|---|
| 1 | Confirm the plan, SaaS mode and Labs | SaaS mode and markup rebilling need the $497 plan. SaaS Usage Limits is a Labs beta | Ray | S | Nothing | Ray has seen on screen: the plan name, SaaS Configurator open, and whether "SaaS Usage Limits" appears in Labs |
| 2 | Create the two private integrations and add the tokens to the environment's secrets | Claude cannot build without them | Ray | S | 1 | Both secrets exist. Neither was pasted anywhere else |
| 3 | Read-only check of both sub-accounts | Proves the tokens, lists what exists, and shows whether the workflow API is enabled | Claude through the API | S | 2 | A short report: account names, existing custom values, fields, tags, pipelines, calendars, and the answer to the workflow API question |
| 4 | Create custom values, custom fields, tags, pipeline and calendar in NL Demo | The skeleton every workflow and the agent refer to | Claude through the API | S | 3, and Ray's yes to the new names in the blueprints | Every name in the spec and the blueprints exists once in NL Demo. A list of IDs is in the report |
| 5 | Buy the demo number, set the timeout low, recording off, confirm it is not the default number | The agent needs a number that always reaches it | Diana | S | 1 | A call to the number rings the agent. No audio file after the call |
| 6 | Create the receptionist in NL Demo: prompt from the slots, welcome message with the disclosure line, English, maximum call length | The product | Claude through the API, then Diana for voice and advanced settings | M | 4, 5 | The agent answers the demo line, says it is an AI first, and asks the questions one at a time |
| 7 | Check that the prompt can read the `nl_` custom values | Decides whether the prompt is one template or pasted per client | Diana | S | 6 | Yes or no written into the spec |
| 8 | Build NL 00 Unsubscribe and STOP, NL 01 AI call finished, NL 01 Needs a human | Promises 12 and 15 | Diana. Claude drafts them through the API only if item 3 says the workflow API is enabled | M | 4, 6 | A test call produces the summary by text and email. An urgent test call produces the alert in under a minute. STOP ends everything |
| 9 | Build NL 01 Missed-call text-back and switch the built-in setting off | A caller who hangs up still gets one reply | Diana | S | 4, 5 | Blueprint 2 tests 1 to 6 pass |
| 10 | Build NL 01 Appointment reminders | Bookings are confirmed and chased | Diana | M | 4 | Blueprint 4 tests 1 to 9 pass |
| 11 | Test: recording off, summary still arrives | Promise 9 and the recording line in the offer | Diana | S | 8 | Result written down. If no summary without recording, Ray changes the offer wording before selling |
| 12 | Set the cap: SaaS plan allowance, overage rule, AI Usage Limit with block, agency default | Promise 2. The round 3 offer depends on it | Diana with Ray | M | 1 | Blueprint 8 set-up steps 1 to 5 done in NL Demo |
| 13 | Test: what a caller hears when AI is blocked, and build the voicemail fallback | The offer says calls reach the client's phone or voicemail at the cap | Diana with Ray | M | 12 | Blueprint 8 tests 1 to 4 pass, or the offer wording is changed |
| 14 | Build NL 00 Usage (the 80 percent and cap-reached messages) | The client must be told | Diana | S | 4 | Adding each tag sends the right text and email |
| 15 | Run the 10-call test on the demo line, then on Ray Homes | No client goes live on an untested agent | Ray and Diana | M | 6, 8, 9, 10 | All 10 pass in one run on each line |
| 16 | Text sending for a Canadian number: find out what must be filed, and file it for the demo number | Texts fail without it | Diana | M | 5 | A text from the demo number arrives on an outside phone |
| 17 | Offboarding procedure written as a checklist and run once on a test sub-account | Promises 11 and 17 | Diana | M | 4 | Blueprint 9 tests 1 to 4 pass. The call-log export limit is known |
| 18 | Counsel: disclosure line, recording line, consent for the missed-call text, deletion wording, client agreement | These are legal lines, not build choices | Ray | M | Nothing | Each line is approved in writing, or changed |
| 19 | Ask HighLevel support in writing what remains after a sub-account is deleted, and for how long | The agreement says "deleted" | Ray | S | Nothing | The reply is saved with the agreement |
| 20 | Decide the voice model for the plan: Voice Engine plus a $0.015 voice, or a speech-to-speech model at $0.10 to $0.20 a minute | It sets the real cost of the 250 minutes | Ray | S | 6 | One choice written into the spec. The arithmetic in `testing/facts-round3.md` is rerun with Ray's real bill |
| 21 | Save master snapshot v1 from NL Demo | Onboarding step 3 clones it | Diana | S | 8 to 15 | A new test sub-account made from the snapshot has the agent, workflows, fields, values, pipeline and calendar, and nothing else needs building except the number |
| 22 | Replace the answered `[verify in HighLevel]` marks in `saas-build-spec.md` with what the official pages say | The spec still asks questions that are now answered | Claude, on Ray's go-ahead | S | Ray's yes | Each answered mark carries the answer and its source |

## Before client 3

| # | Item | Why | Who builds | Effort | Depends on | Done when |
|---|---|---|---|---|---|---|
| 23 | Forms (website contact, buyer, seller) and NL 01 Speed-to-lead | Web leads get a reply and the client gets a task | Diana | M | 4 | Blueprint 3 tests 1 to 6 pass |
| 24 | Dashboard, the `nl_report_` values and NL 00 Monthly report | The first report is due a month after client 1 goes live | Diana for the dashboard and workflow, Claude for the values | M | 4 | A sample report email matches the dashboard and shows no caller details |
| 25 | Intake form: add the call-mapping questions and the five question slots. Onboarding step 8: add message sign-off | The agent asks the client's own questions, and the client approves every message | Diana | S | 4 | The form holds them. A signed-off message list is kept per client |
| 26 | CRM push tested for Follow Up Boss and BoldTrail in a test account | Promise 13: a CRM is on the list only after a test record arrived | Diana | M | 8 | A test caller appears in each CRM. The written list is updated |
| 27 | Staff access procedure and log, with a look at what the audit log records | Promise 7 | Diana with Ray | S | Nothing | A staff user with no open job cannot open a client account. The log shows who, when and why |
| 28 | Weekly call-review routine: same day each week, read every client's calls, fix the prompt, note one change | Retention, and the "one thing we changed" line in the report | Ray and Diana | S per week | Client 1 live | A dated note per client per week |
| 29 | A way to push a prompt fix to every client: snapshot refresh and push, or the agent clone to sub-accounts | A fix made once reaches everyone | Diana | S | 21 | A changed line in the NL Demo agent appears in a test client account |
| 30 | Second-language test on Ray's own line | 22 of 100 test personas needed a language that is not promised | Ray | S | 6 | A written result per language tried. `nl_languages` unchanged until a client's own test passes |
| 31 | Business-edition question slots for mortgage brokers and for contractors | Three founding spots are open to them now | Claude drafts, Ray approves, Diana loads | S | 6 | Two prompt blocks exist and pass the 10-call test with trade wording |
| 32 | Daily lead check: every call and form lead landed with a source tag | Catches a broken trigger within a day | Viktor, as a proposal | S | Ray's approval of the instruction | A daily line in Slack per client account |
| 33 | Weekly usage watch: minutes used against the allowance for each client, flagged at 70 percent | The client alert in blueprint 8 depends on someone seeing the threshold | Viktor, as a proposal | S | 12 | A weekly line per client. Diana adds the tag when flagged |
| 34 | A plain comparison table for the sales page: Next Level Answer, a human answering service, a self-serve app | Buyers ask it on every call | Claude drafts from our own facts, Ray approves | S | 20 | Ray has approved each cell. No competitor is named |

## Before client 10

| # | Item | Why | Who builds | Effort | Depends on | Done when |
|---|---|---|---|---|---|---|
| 35 | NL 02 Review request at closing, at day 30, and the reply-draft notification | Next Level Reviews, when Ray opens that rung | Diana | M | 4, and counsel on consent | Blueprint 5 tests 1 to 8 pass on Ray Homes |
| 36 | NL 03 Reactivation, Hand-raiser follow-up and Past-client touches | Next Level Nurture, when Ray opens that rung | Diana | L | 4, and counsel on consent | Blueprint 6 tests 1 to 6 pass on Ray Homes with Ray's own list |
| 37 | Three short client videos of our own: reading a call summary, changing your hours and answers, reading your report | Fewer support questions | Ray records or approves, Diana loads | M | 21 | Linked from the welcome email |
| 38 | Decide whether the monthly report numbers are filled through the API | Saves about 10 minutes per client per month, and touches promise 7 | Ray decides. Claude builds if yes | M | 24 | Decision written. If yes: the agreement names it and the extra read scope is added |
| 39 | Decide whether replies to the missed-call text are answered by a text AI | It books more of those callers, costs more per reply and adds a second agent to test | Ray decides. Diana builds if yes | M | 9 | Decision written |
| 40 | Listing question lookup during a call | Callers ask whether a home is still available | Ray confirms the data licence. Then Claude designs, Diana builds | L | Ray's licence check | A test call gets a correct status, or the agent keeps taking a message |
| 41 | Lofty and Sierra Interactive pushes, tested | The offer names them | Diana | M | 26 | A test record arrives, or the offer wording changes |
| 42 | Try HighLevel's official Claude connector on NL Demo | It signs in without a stored token and may replace the private integrations | Ray connects, Claude tests | S | 21 | A note: what it can do that the token cannot, and what it should not be allowed to do |
| 43 | Buyer-question articles for Ontario agents: cost, what the caller hears, what happens to a recording | Inbound interest | Claude drafts, Ray approves | M | 18, 20 | Three articles approved |
| 44 | Master snapshot v2 with a written change log | Clients 4 to 10 start from what the first three taught | Diana | S | 28 | Version, date and changes recorded. The promise tests rerun |

## Later

| # | Item | Why | Who builds | Effort | Depends on | Done when |
|---|---|---|---|---|---|---|
| 45 | Follow-up after a showing or a listing presentation | The agent-edition version of chasing a quote | Diana | M | Founding 10 live | Ray approves the trigger and the copy |
| 46 | Website chat that books to the calendar | Parked in the spec | Ray decides | M | Founding 10 live | Decision written |
| 47 | Replies to social comments and direct messages | Parked in the spec | Ray decides | M | Founding 10 live | Decision written |
| 48 | The licence rung: onboarding lessons, a resource library and a partner page, all our own | Ladder rung 5 | Ray decides | L | A repeatable onboarding | Decision written |
| 49 | Invoicing and payment reminders for business-edition clients | A trade need, not an agent need | Ray decides | L | Business edition open | Decision written |
| 50 | Outbound AI calls | Next Level Answer is inbound only. Outbound brings consent and calling rules | Ray, with counsel | L | Counsel | Stays off unless Ray decides otherwise |

## What is not on this backlog, on purpose

- Importing or adapting anyone else's snapshot, workflow, prompt or script.
- Anything that reads a client's contacts or transcripts from outside the client's account, beyond what the agreement names.
- Any token created by anyone other than Ray, or stored anywhere other than the environment's secrets.
