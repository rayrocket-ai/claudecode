# The improvement loop

How to rerun the offer test, in plain steps. Anyone can run it at any time: after a change to the offer, the sales page or the call script.

## Read this first

These are simulated people. The 100 personas were written by an AI model and their answers are written by an AI model. A round shows where the wording is weak, missing or off-putting. It does not show what real agents will do, and its counts are not conversion rates. See `README.md` in this folder.

The real test is the first 10 sales calls. When the personas and the real calls disagree, the real calls win. Fill in the real-world scoreboard at the bottom of this file after every call.

## The loop

1. **Change the offer or the page.** Make the change in `../offer.md` first, then in the sales files. Change a few things at a time, so you can tell what moved the result.
2. **Write the pitch file.** Save it here as `offer-pitch-v3.md`, then v4, and so on. It holds everything a persona is told and nothing else. State only what Next Level can keep. End it with a "Still not stated" line that lists what the pitch leaves out. Do not edit an old pitch file.
3. **Run the same 100 personas, in four batches of 25.** Use `personas.json` as it is. Batch 1 is P001 to P025, batch 2 is P026 to P050, batch 3 is P051 to P075, batch 4 is P076 to P100. Give each batch the pitch file, its 25 personas and the evaluator rules below. Save the output as `offer-round3/batch-1.json` to `batch-4.json`.
4. **Aggregate.** Count the decisions, the missing information, the lines that helped and the lines that hurt. Check that there are 100 results and 100 unique ids before counting.
5. **Compare with the previous round.** Same measures, side by side, in one table.
6. **Record the lines that helped and the lines that hurt.** Quote each line exactly, with how many personas named it. Write all of it in `offer-round3/RESULTS.md`, in the same shape as round 2.
7. **Fix.** A line that hurt is rewritten or backed with a fact, and stays true. A gap that only a fact can close goes on the "Still open" list in `../README.md` for Ray. Do not close a gap with a claim Next Level cannot keep.
8. **Repeat.** Stop when a round changes little. Round 2 found that wording was close to its limit and that what remained were facts from Ray and proof from founding clients. At that point, more rounds are not the work. Sales calls are.

## Evaluator rules

Give these to the evaluator with every batch. They are the round 2 rules. Keep them the same from round to round, or the rounds will not compare.

1. **The pitch file is everything the persona is told.** Nothing else may be assumed. If the pitch does not say it, the persona does not know it.
2. **Default to pass.** A cold audience mostly says no. A persona books a call or buys only when the pitch answers what that persona needs. When in doubt, the answer is "passes".
3. **"Confirmed on the call" is weaker than a fact.** A line that promises an answer later can earn a booking. It almost never earns a purchase. Only a stated fact can do that.
4. **Unfixable stays unfixable.** A persona tagged `unfixable_no` still says no, whatever the wording. If a round converts them, the round is too kind and is run again.
5. **Cite the exact line.** For the line that helped most and the line that hurt most, quote the words from the pitch file exactly. No paraphrase.
6. **Stay inside the persona.** Use their `must_see_to_continue`, `deal_breakers`, `the_question_they_want_answered`, budget, device and attention. A persona who skims for 20 seconds does not weigh the fine print.
7. **Business owners cannot buy.** Personas P071 to P100 can join the waitlist or pass.

### What each result holds

One record per persona, in the same fields as round 2:

`id`, `segment`, `decision_founding`, `decision_standard`, `would_refer`, `main_reason`, `what_almost_changed_their_mind`, `missing_info`, `price_reaction`, `max_monthly_they_would_pay_cad`, `trust_in_ray`, `best_product_for_them`, `line_that_helped_most`, `line_that_hurt_most`.

Decisions are one of: `buys`, `books call only`, `joins waitlist`, `passes`.

### Check a round before counting

```
python3 -c "
import json, collections
R = [r for b in (1, 2, 3, 4) for r in json.load(open(f'nextlevel/testing/offer-round3/batch-{b}.json', encoding='utf-8'))]
assert len(R) == 100 and len({r['id'] for r in R}) == 100
print(collections.Counter(r['decision_founding'] for r in R))
print(collections.Counter(r['line_that_hurt_most'] for r in R).most_common(10))
"
```

## What to compare each round

| Group | Measure | Round 1 | Round 2 | Round 3 |
|---|---|---|---|---|
| 70 agents, founding price | Buys | 0 | 3 | |
| | Books a call | 7 | 19 | |
| | Passes | 63 | 48 | |
| 70 agents, standard price | Buys | 0 | 1 | |
| | Books a call | 2 | 9 | |
| 30 business owners | Joins waitlist | 1 | 5 (one is a competitor) | |
| All 100 | Would refer someone | 4 | 11 | |
| Agents | Trust in Ray, out of 5 | 2.8 | 2.7 | |

Sources: `offer-round1/RESULTS.md` and `offer-round2/RESULTS.md`.

## Rules for using a result

- Do not quote a persona on a page, in an ad or on a call. Nobody said it.
- Do not use a count from this panel as a claim about the product or the market.
- A term added because of a round is marked with the date and "Ray to confirm" until Ray approves it.
- The pitch file and the live offer must say the same thing. If the page promises less than the pitch, the round tested an offer nobody is being sold.

## Real-world scoreboard

Fill this from real calls. One row per week, or one row per call while there are few. Counts and reasons only. No names, no phone numbers, no brokerage names.

| Week starting | Calls booked | Shows | Offers made | Yes | No | The stated reason for each no, in their words |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

- **Calls booked:** 15-minute calls put on the calendar.
- **Shows:** booked calls where the person turned up.
- **Offers made:** calls where Ray stated the founding offer and the price.
- **Yes:** paid, or agreed and waiting on the checkout link.
- **No:** a clear no, or no next step agreed.
- **The stated reason:** what the person said, not what we think they meant.

### After every 10 calls

1. Count the reasons for each no. Group the ones that match.
2. Set them beside the "Lines that hurt most" and "Still unanswered" lists in the latest `RESULTS.md`. Note where the real calls agree with the panel and where they do not.
3. A reason heard three times or more is fixed in `../sales/call-script.md` first, then in `../offer.md` and on the page.
4. If the fix is a wording change, run one more persona round on it. If the fix is a fact only Ray can supply, it goes on the "Still open" list in `../README.md`.
