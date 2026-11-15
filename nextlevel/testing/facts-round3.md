# Facts for round 3 (researched 2026-11-15)

Purpose: replace vague lines in the offer with lines that are true, or that are clearly labelled offer decisions.

## How to read this file

- Every row was found on 2026-11-15.
- **No official page could be opened.** In this session `help.gohighlevel.com` and `gohighlevel.com` did not resolve (blocked by the session's network settings), so page fetching was stopped after those two hosts, as instructed. Everything below comes from web search result text. That is why no row is marked "confirmed on an official page".
- Confidence labels used:
  - **Snippet, official page**: seen in search result text only, and the result is the vendor's or the government's own page. Open the URL and check before publishing.
  - **Snippet, third party**: seen in search result text only, from a blog, a reseller or a connector listing.
  - **Not found**: no source turned up.
- To raise any row to "confirmed", someone opens the URL in a normal browser, or checks the setting inside the HighLevel account. The in-account check is the stronger one for prices, languages and recording.
- All HighLevel prices are in US dollars. This is headline information, not legal advice.

## The table

### a. Cost

| Question | What the source says | URL | Confidence |
|---|---|---|---|
| Voice AI price per minute, pay per use | Voice Engine $0.045 per minute, effective 20 May 2026. Speech (text to speech) is billed on top: OpenAI and Cartesia voices $0.015 per minute, ElevenLabs V2.5 $0.035, ElevenLabs V3 $0.170. Language model tokens and phone charges are billed on top again. Worked example on the page: a 10-minute call on an OpenAI voice is $0.60 before model tokens and phone charges. The page warns that rates can change and says to check in-app settings before quoting. | https://help.gohighlevel.com/support/solutions/articles/155000006652-ai-product-pricing-update | Snippet, official page |
| Language model cost | Priced per million tokens, for example $0.15 for GPT-4o Mini and $3.00 for Claude 4.5 Sonnet. No per-minute figure is given. | Same article | Snippet, official page |
| Older Voice AI figure | $0.13 per minute, quoted by older guides. Superseded by the engine plus speech structure. | https://botpenguin.com/blogs/gohighlevel-ai-pricing | Snippet, third party |
| AI Employee plans | Growth: $50 a month, 100 AI agent minutes a month shared across inbound, outbound and widget. Unlimited: $97 a month per enabled location, Voice AI "unlimited, subject to fair use". Phone charges still apply separately. HighLevel's articles disagree on what happens past the allowance (paused by default unless Extra Usage is on, or billed automatically). The most recent article, updated 10 November 2026, says paused by default. | https://help.gohighlevel.com/support/solutions/articles/155000003906-ai-employee and the pricing article above | Snippet, official page |
| Can an agency rebill with markup | Yes. Two modes: a percentage markup on HighLevel's cost (examples 1.5x, 2x), or a fixed rate (example $0.10 per Voice AI minute) charged to the sub-account whatever the token cost. | https://help.gohighlevel.com/support/solutions/articles/155000008422-fixed-rate-rebilling-for-ai-products | Snippet, official page |
| LC Phone inbound call, Canada and US | $0.01165 per minute for an inbound call answered on web, mobile or deskphone (discounted rate). Another version of the same guide shows $0.0129. Inbound to a US toll-free number: $0.0198. Inbound calls can have two billed legs. Calls bill in full minutes, part minutes round up. | https://help.gohighlevel.com/support/solutions/articles/48001223556-phone-system-pricing-billing-guide | Snippet, official page |
| LC Phone outbound call, Canada and US | $0.0166 per minute (discounted); $0.0180 also appears on the page. | Same guide | Snippet, official page |
| SMS, Canada and US | $0.00747 per segment, same for inbound and outbound, same for Canada and the US (10% off the $0.0083 list price). Carrier fees are extra. | Same guide | Snippet, official page |
| Carrier fee per text | "About $0.005 per segment" as a planning estimate. A Canadian carrier fee figure was not found. | https://autogencrm.com/?p=16405 | Snippet, third party |
| Phone number rent | Local number $1.15 a month. A 2025 guide said $3.45. | LC Phone guide above | Snippet, official page (figures disagree across versions) |
| Recording and transcription charges | Call recording $0.0025 per minute, storage $0.0005 per minute per month. Call transcription $0.024 per minute. Whether the $0.024 is charged on Voice AI calls, where the transcript is part of the product, was not found. | LC Phone guide above | Snippet, official page |
| Outbound webhook cost | Custom Webhook is a premium workflow action at $0.01 per execution. | https://ideas.gohighlevel.com/changelog/new-workflow-pricing-categories-premium-features-ai-models | Snippet, official page |
| October 2026 voice price change | Covers international routes only, not Canada or US rates and not the Voice Engine. | https://ideas.gohighlevel.com/changelog/voice-pricing-updates-effective-october-13-2026 | Snippet, official page |

### b. Languages

| Question | What the source says | URL | Confidence |
|---|---|---|---|
| Languages for Voice AI today | The current article says languages are chosen in a Language picker, one language or several per agent, the first one chosen being the primary. It says the old fixed "Multilingual" group must not be treated as the supported list. Existing multilingual agents were moved to ten languages: English (US), Spanish, French, German, Hindi, Russian, Portuguese (Brazil), Japanese, Italian, Dutch. Some languages can only be used on their own. | https://help.gohighlevel.com/support/solutions/articles/155000009013-multi-language-support-for-voice-ai-agents | Snippet, official page |
| Longer list | An older article (last modified 27 April 2026) gives a longer roster that includes Chinese, Persian, Arabic, Tamil and Urdu. It does not separate Mandarin from Cantonese. A roundup says 22 languages were added in April 2026 for a total of 54, Persian and Urdu among them. | https://help.gohighlevel.com/support/solutions/articles/155000004683-voice-ai-multi-language-support and https://netpartners.marketing/highlevel-updates-week-april-20-24-2026/ | Snippet, official page (list not read in full); snippet, third party for the count |
| Dari | Not listed anywhere found. | n/a | Not found |
| Punjabi | Not listed in either Voice AI article. | n/a | Not found |
| Mandarin, Cantonese | "Chinese" appears on the older list with no dialect named. | Older article above | Snippet, official page; dialect not found |
| Persian (Farsi) | Appears on the older list. Not read on the page itself, and the newer article says not to rely on the older grouping. | Older article above | Snippet, official page; not safe to promise |
| Does it switch language by itself on an inbound call | Not confirmed. A request on HighLevel's ideas board asks for automatic language detection, which suggests it is not automatic. | https://highlevel.canny.io/voice-ai/p/feature-request-automatic-multilingual-language-detection-for-voice-ai-agents | Snippet, official board; behaviour not found |
| Transcripts in other languages | Call transcription supports 10 languages (the same ten as above), per a March 2026 changelog. A separate service translates Voice AI transcripts and summaries. | https://ideas.gohighlevel.com/changelog/multi-lingual-transcription-for-voice-calls-via-labs and https://help.gohighlevel.com/support/solutions/articles/155000005797-voice-ai-translation-service-for-call-transcript-summary | Snippet, official page |

### c. Recording and transcripts

| Question | What the source says | URL | Confidence |
|---|---|---|---|
| Can recording be turned off for phone numbers | Yes for LC Phone numbers: call recording is a setting, and the "this call is being recorded" message can also be switched off. | https://ideas.gohighlevel.com/changelog/call-recording-message-can-now-be-disabled and the LC Phone guide | Snippet, official page |
| Can recording be turned off for a Voice AI phone agent while it still produces a transcript and summary | No article found that says so. Voice AI widget calls are never recorded. For Voice AI calls "transcription is enabled by default". The "Transcript Generated" workflow trigger fires on recorded calls. | https://help.gohighlevel.com/support/solutions/articles/155000006632-workflow-trigger-transcript-generated | Not found. Must be tested in the account |
| Are transcripts kept | Yes. Summary and transcript stay in the Voice AI call logs. Admins can view, delete or export transcripts. Call logs can be exported and recordings downloaded. | https://help.gohighlevel.com/support/solutions/articles/155000005900-call-logs-for-voice-ai-agents | Snippet, official page |
| How long | Recordings: an auto-delete setting exists, default 90 days, changeable. Deleting recordings does not delete transcripts. No automatic retention period for transcripts was found. | https://ideas.gohighlevel.com/changelog/control-recording-storage-bills-by-auto-deleting-older-call-recordings | Snippet, official page; transcript period not found |
| Does a transcript leave the platform | Only when a workflow action sends it, such as an email or a webhook. | Transcript trigger article above | Snippet, official page |

### d. Hosting and compliance

| Question | What the source says | URL | Confidence |
|---|---|---|---|
| Who hosts and where | HighLevel "outsources hosting of its product infrastructure to leading cloud infrastructure providers such as Google Cloud Platform Services and Amazon Web Services". "Our product infrastructure resides in the United States." No region is named. | https://help.gohighlevel.com/support/solutions/articles/155000000574-highlevel-security-and-compliance-overview | Snippet, official page |
| Canadian data storage | No Canadian option found. Users have asked for it on HighLevel's ideas board. | https://ideas.gohighlevel.com/hipaa-compliance/p/data-storage-in-canada | Snippet, official board |
| Published compliance statements | SOC 2 Type II on security, availability and confidentiality. An ISO/IEC 27001:2022 certificate is reported in the Trust Center (scope not seen). EU-U.S. Data Privacy Framework. Encryption in transit (TLS 1.2 or 1.3) and at rest (AES-256). | https://www.gohighlevel.com/privacy-and-security and https://help.gohighlevel.com/support/solutions/articles/155000007495-highlevel-achieves-soc-2-type-ii-certification | Snippet, official page |
| Canada in the data processing agreement | A clause says processing is to comply with PIPEDA where applicable. That is a compliance commitment, not a promise of storage in Canada. | https://www.gohighlevel.com/data-processing-agreement | Snippet, official page |

### e. CRM connections

| Question | What the source says | URL | Confidence |
|---|---|---|---|
| Does HighLevel have a built-in connection to any of these real estate CRMs | None found. | n/a | Not found |
| How HighLevel sends data out | Through Zapier (HighLevel's Zapier app is called LeadConnector), or a Custom Webhook workflow action ($0.01 per execution). Voice AI can trigger a workflow when a call is completed. | https://help.gohighlevel.com/support/solutions/articles/155000004107-how-to-create-voice-ai-agents | Snippet, official page |
| Follow Up Boss | Has a Zapier app (API key sign-in). Its own help pages recommend the "New Inquiry or Website Event" action for new leads so action plans can start. Zapier lists ready-made LeadConnector and Follow Up Boss pairings in both directions. Follow Up Boss can also create leads from forwarded lead emails. One vendor's documentation says a plain webhook struggles with the nested phone and email fields, so Zapier is the safer route. | https://zapier.com/apps/follow-up-boss/integrations/leadconnector and https://help.followupboss.com/hc/en-us/articles/4420151624343-Lead-Sources-Websites-with-API-Integrations | Snippet, official pages (Zapier and Follow Up Boss) |
| BoldTrail (formerly kvCORE) | Has a Zapier app with one action, "Create Contact (Post)", set up with a Zapier key from the Lead Dropbox. Help article about 73 days old. | https://help.insiderealestate.com/en/articles/3317483-boldtrail-zapier-overview | Snippet, official page |
| Lofty | Zapier lists a "Create Lead" action. The listing looks old and still mentions the former name, Chime. | https://zapier.com/apps/kvcore/integrations/lofty | Snippet, official listing, stale |
| Sierra Interactive | Zapier lists a "Create Lead" action that requires first name, last name, password and email. A caller who gives only a phone number may not meet those required fields. | https://zapier.com/apps/kvcore/integrations/sierra-interactive | Snippet, official listing, stale |
| Kind of connection | In every case: one way, through Zapier, creating or updating a contact or lead after the call. Not a built-in sync, not two-way, and none of the four was tested here. | n/a | Summary of the rows above |

### f. Canadian rules (headline and link only, not legal advice)

| Question | What the source says | URL | Confidence |
|---|---|---|---|
| CASL and texts | CASL covers commercial messages sent to mobile phones, SMS included. The sender needs express or implied consent and must be able to prove it, must identify itself, and must give a working unsubscribe that is honoured within 10 business days. The CRTC's example for texts is replying STOP or Unsubscribe. A reply to a request or inquiry, sent at the recipient's request, is exempt. | https://crtc.gc.ca/eng/com500/faq500.htm and https://ised-isde.canada.ca/site/canada-anti-spam-legislation/en/texting-good-client-relations | Snippet, official page |
| Recording a call: criminal law | Criminal Code section 184 makes it an offence to intercept a private communication. An exception covers a person who has the consent, express or implied, of the originator or of the intended recipient. That is the "one-party consent" rule. The current consolidated text was not opened; the wording was seen in archived versions. | https://laws-lois.justice.gc.ca/eng/acts/c-46/section-184.html | Snippet, official page |
| Recording a call: privacy practice for a business | The Privacy Commissioner's position under PIPEDA: tell the caller at the start of the call that it is being recorded and why, and give an alternative if they object. In a 2002 case the Commissioner did not accept "only one party has to consent" as a reason to skip the notice. | https://www.priv.gc.ca/en/opc-actions-and-decisions/investigations/investigations-into-businesses/2002/pipeda-2002-086/ and https://www.priv.gc.ca/en/opc-actions-and-decisions/investigations/investigations-into-businesses/2007/pipeda-2007-384/ | Snippet, official page |
| CRTC and automated or AI voice | Current rules: an automatic dialing-announcing device (ADAD) conveys "a pre-recorded or synthesized voice message". Using one to sell needs prior express consent. The ADAD rules cover all unsolicited calls made with one, including calls that are not telemarketing. These are rules about calls placed outward. | https://crtc.gc.ca/eng/trules-reglest.htm and https://crtc.gc.ca/eng/phone/telemarketing/tobligations/rules-regles.htm | Snippet, official page |
| Is the CRTC changing this for AI | Open consultation, CRTC 2026-132. It asks whether the ADAD definition is enough for AI and synthesized voices, and whether callers should have to say that it is not a live person. No outcome was found. | https://crtc.gc.ca/eng/archive/2026/2026-132.htm | Snippet, official page |

## Arithmetic for the minute bundle

All rates are the snippet figures above, in US dollars. Nothing here was read off Ray's own bill. Ray's real bill should replace this table as soon as he has it.

**Cost of one AI call minute**

| Part | Low case | Planning case | Note |
|---|---|---|---|
| Voice Engine | 0.045 | 0.045 | |
| Speech | 0.015 | 0.035 | Low: OpenAI or Cartesia voice. Planning: ElevenLabs V2.5. ElevenLabs V3 at 0.170 is excluded and must not be used on this plan. |
| Language model tokens | 0.002 | 0.010 | **Assumption.** No per-minute figure exists. Small models are priced in cents per million tokens. |
| Phone, inbound | 0.01165 | 0.0129 | The two figures on the guide. |
| Transcription | 0 | 0.024 | Included in the planning case in case it is charged on Voice AI calls. |
| Recording | 0 | 0 | Off by default in the offer. |
| **Total, USD** | **0.0737** | **0.1269** | |
| **Total, CAD at 1.40** | **0.103** | **0.178** | **Assumption:** 1 USD = 1.40 CAD. No exchange rate was looked up. |

**The bundle: 250 AI call minutes, the number, and 500 text segments**

| Item | Sum | USD | CAD at 1.40 |
|---|---|---|---|
| 250 minutes, planning case | 250 x 0.1269 | 31.73 | 44.42 |
| Local number | 1 x 1.15 | 1.15 | 1.61 |
| 500 text segments | 500 x (0.00747 + 0.005 carrier estimate) | 6.24 | 8.73 |
| **Bundle cost** | | **39.12** | **54.76** |
| **Share of $300 CAD** | 54.76 / 300 | | **18.3%** |

- Low case for the same bundle: 250 x 0.0737 = 18.43 USD, plus 1.15 and 6.24 = 25.82 USD = 36.14 CAD, or 12.0% of $300.
- The bundle stays at or under 20% ($60 CAD) while the all-in minute costs up to 0.142 USD at 1.40, or while the exchange rate stays under about 1.53 at the planning cost.
- The same 250 minutes at the standard price of $400 a month is 13.7%.

**Extra minutes: $0.30 CAD each**

- Planning cost 0.178 CAD. Margin 0.122 CAD a minute, 41% of the price.
- Low-case cost 0.103 CAD. Margin 0.197 CAD, 66%.
- Break-even: the price covers cost up to 0.214 USD a minute at 1.40.
- 100 extra minutes cost the client $30.

**Extra agent line at half price ($150 founding)**

- Adds 125 minutes and its own number: 125 x 0.1269 = 15.86 USD, plus 1.15, plus 250 segments x 0.01247 = 3.12. Total 20.13 USD = 28.18 CAD = 18.8% of $150.

**Why not the $97 Unlimited plan**

- $97 USD is about $135.80 CAD a client, or 45% of $300. It only beats pay per use above roughly 1,000 minutes a month (97 / 0.09 for engine, speech and tokens). Pay per use with a 250-minute bundle is the cheaper base. For a client who regularly passes about 1,000 minutes, Unlimited becomes the cap on Next Level's cost.

**What would break this arithmetic**

1. Ray's real bill shows a higher all-in minute than 0.142 USD.
2. A premium voice (ElevenLabs V3) is chosen.
3. Two phone legs are billed on every call.
4. The Canadian dollar weakens past about 1.53.
5. Average text use is far above 500 segments (long summaries, many alerts).

## What we can safely say

1. "$300 a month includes 250 AI call minutes, your phone number and the summary texts." This is an offer decision. The arithmetic above supports it at the published rates.
2. "Extra minutes are $0.30 each, and you set the cap." Offer decision.
3. "English is live today."
4. "The platform lists French, Spanish, Hindi, German, Portuguese, Italian, Dutch, Russian and Japanese. Any language is tested on your own line first, and you are not charged if it is not good enough." Check the ten in the Language picker before publishing.
5. "Your account runs on HighLevel, a US software company. HighLevel says its infrastructure is in the United States, on Google Cloud and Amazon Web Services." Say plainly that this is not storage in Canada.
6. "HighLevel publishes a SOC 2 Type II report." Check the page first. Say "HighLevel publishes", never "we are certified".
7. "Next Level is a customer of HighLevel. It is not a partner, reseller under contract, or affiliate of HighLevel, Zapier or any CRM company." (Check the exact agency terms for the right word.)
8. "Calls reach your CRM one way, through Zapier, for Follow Up Boss and BoldTrail (kvCORE). Lofty and Sierra Interactive are listed by Zapier and are tested in your account during set-up."
9. "The AI says it is an AI. When recording is on, it says so at the start of the call." This matches the Privacy Commissioner's stated practice.
10. "Next Level Answer only answers calls that come in. It does not place sales calls." This keeps it outside the outbound ADAD rules as they read today.
11. "Texts carry your business name and a way to stop them."

## Do not say

1. Do not say the AI speaks Dari, Farsi, Persian, Punjabi, Mandarin, Cantonese, Urdu or Arabic. Dari and Punjabi were not found at all. Persian and "Chinese" appear only on an older list that was not read in full.
2. Do not say the AI detects or switches language by itself.
3. Do not say data is stored in Canada. It is in the United States.
4. Do not say "PIPEDA compliant", "CASL compliant", "CRTC approved" or "legal in Canada". Link to the official page and stop there.
5. Do not say Next Level is SOC 2 or ISO certified. Those belong to HighLevel.
6. Do not say "integrates with" or "syncs with" a CRM. It is a one-way push through Zapier.
7. Do not say "unlimited minutes".
8. Do not say "at cost, no markup" beside the new bundle. The two do not fit together. Round 3 replaces that line.
9. Do not quote HighLevel's per-minute rates to a buyer as Next Level's rate. They are in US dollars, they change, and the buyer's number is the bundle.
10. Do not say recording is off and a transcript is still produced until that has been tested in the account (see below).
11. Do not name HighLevel, Zapier or a CRM in a way that suggests a partnership or endorsement.

## Things only the account can settle (before the first client)

1. **Recording off with transcript on.** v2 already promises "audio recording is off unless you turn it on". No source confirmed that a Voice AI phone agent still produces its transcript and summary with recording off. Test it on Ray's line. If it does not, the promise must change to "the recording is deleted within a day" or similar, which HighLevel's auto-delete setting supports (it can be set to 1 day).
2. **The cap.** A request on HighLevel's ideas board asks for Voice AI usage limits with rebilling, which suggests a per-client minute cap may not exist as a setting. Find out how the cap will be enforced: wallet balance, plan allowance with Extra Usage off, or a manual check.
3. **The real per-minute cost** from Ray's own usage, including whether transcription and a second phone leg are charged.
4. **The Language picker list**, and a test call in each language offered.
5. **Each Zapier connection**, tested with a real call, and the Zapier plan cost.
6. **Who can read transcripts.** The one-person-company system has AI roles that build client reports from account data (Team 7). If any AI tool outside the platform reads client transcripts, the data line in the pitch must say so.
