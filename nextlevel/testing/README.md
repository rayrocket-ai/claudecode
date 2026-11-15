# Next Level: the test panel

`personas.json` is a fixed panel of 100 made-up buyers. We read a draft sales page through each one's eyes to find what is confusing, missing or off-putting before real people see it.

## What this is

- 100 personas written by an AI model, in one sitting, from the offer in `../offer.md`.
- A fixed list. The same 100 are used every time, so two versions of a page can be compared against the same readers.
- Mostly sceptical on purpose. A cold audience mostly says no, and the panel is built to behave that way.
- Good for one job: finding gaps. Examples: the price is not stated, the page never says which languages the AI speaks, a mortgage broker cannot tell if the page is for him, a phone reader sees nothing useful in the first screen.

## What this is NOT

- **Not market research.** Nobody was interviewed or surveyed. The mix of people was chosen by us, not measured.
- **Not real people.** Every name, business and quote is invented. Any match with a real person is a coincidence. Brokerage and software names are there for realism only and say nothing true about those companies or their policies.
- **Not a sales forecast.** If 13 of 100 personas "book a call", that does not mean 13% of visitors will. The numbers in this panel say nothing about conversion rates, revenue or demand.
- **Not proof of anything.** Do not quote a persona on a page, in an ad or on a call as if a client said it. Do not use panel results as a claim about the product.
- **Not legal advice.** Several personas raise recording, privacy and licensing worries. Those are questions a reader might ask. The answers must come from counsel (see the open items in `../offer.md`).

A page that does well with this panel can still fail with real visitors. The only real test is real traffic and real calls.

## Composition

100 personas, ids P001 to P100.

| Group | Count |
|---|---|
| Real estate agents and brokers (P001 to P070) | 70 |
| Local business owners, waitlist path (P071 to P100) | 30 |

**Agents by market (70)**

| Market | Count |
|---|---|
| GTA suburbs | 18 |
| Downtown and central Toronto | 6 |
| Small-town and mid-size Ontario | 6 |
| Vancouver area | 5 |
| Calgary area | 4 |
| Montreal area (French first) | 4 |
| Other Canada (Halifax, Winnipeg, Ottawa, Edmonton) | 4 |
| United States (18 states) | 23 |

Agents range from 0 to 25 years licensed and 0 to 120 deals a year, and include solo agents, small teams, team leaders, broker-owners, a commercial broker and a salaried agent.

**Business owners by industry (30)**

| Industry | Count |
|---|---|
| Mortgage brokers | 6 |
| Real estate lawyers | 5 |
| Accountants and tax preparers | 5 |
| Contractors and renovators | 6 |
| Insurance | 4 |
| Outside the listed industries (dentist, salon, auto shop, physio clinic) | 4 |

**Required types across the 100** (one persona can carry more than one tag)

| Tag in `tags` | Meaning | Count | Minimum asked for |
|---|---|---|---|
| `unfixable_no` | Will say no for a reason no page can fix: no budget, already has a solution, brokerage or employer forbids it, distrusts AI talking to clients, leaving the business | 27 | 20 |
| `trust_objection` | Trust objection about Ray, or about a broker selling software | 18 | 15 |
| `legal_privacy_worry` | Worried about legality, privacy or call recording | 17 | 10 |
| `ready_if_one_question_answered` | Ready buyer if the page answers one specific question | 14 | 10 |
| `phone_under_30_seconds` | On a phone, skims for about 20 seconds | 14 | 8 |
| `competitor_or_tyre_kicker` | Competitor or tyre-kicker | 6 | 5 |

**Other spreads**

| Measure | Count |
|---|---|
| Device: phone / desktop | 33 / 67 |
| Attention: skims 20 seconds / reads half / reads everything | 19 / 50 / 31 |
| Arrived from: Instagram reel / referral / YouTube / cold | 27 / 23 / 14 / 36 |
| Scepticism 4 or 5 out of 5 | 53 |
| Prior outcome before seeing any page: bounce / quiz only / books call / buys | 46 / 41 / 13 / 0 |
| Serve clients in Dari / Farsi / Punjabi / Mandarin / Italian / Portuguese / French | 5 / 6 / 10 / 6 / 4 / 4 / 9 |

## Fields

Each persona has: `id`, `name`, `segment`, `role`, `market`, `years`, `deals_per_year` (agents) or `business_size` (business owners), `team`, `tech_comfort` (1 to 5), `current_tools`, `device`, `attention`, `arrived_from`, `languages`, `primary_pain`, `budget_sensitivity` (1 to 5), `scepticism` (1 to 5), `must_see_to_continue`, `deal_breakers`, `reason_to_say_yes`, `reason_to_say_no`, `the_question_they_want_answered`, `likely_outcome_prior`, `tags`.

- `likely_outcome_prior` is a guess made before any page existed. It starts with one of `bounce`, `quiz only`, `books call`, `buys`, followed by a rough likelihood. For business owners, "quiz only" includes joining the waitlist, since they cannot buy yet.
- `segment`, `languages` and `tags` were added so the panel can be filtered and counted.

## How to use it

1. Keep the file fixed. If a persona must change, note it here with the date, because results before and after will not compare.
2. For each page version, ask of each persona: did they find `must_see_to_continue`? Did the page answer `the_question_they_want_answered`? Did it trip a `deal_breaker`?
3. Read the results as a list of gaps to fix. Do not read them as a score.
4. The `unfixable_no` personas should still say no. If a page "converts" them, the test is being too kind.

## Check the file

```
python3 -c "
import json, collections
P = json.load(open('nextlevel/testing/personas.json', encoding='utf-8'))
assert len(P) == 100 and len({p['id'] for p in P}) == 100
print(collections.Counter(p['segment'] for p in P))
print(collections.Counter(t for p in P for t in p['tags']))
"
```

Last validated 2026-11-15: 100 personas, 100 unique ids, all fields present, all composition minimums met.
