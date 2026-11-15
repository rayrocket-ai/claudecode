# hl_build.py: build the Next Level Answer skeleton in a HighLevel sub-account

A small Python 3 tool (standard library only) that creates the pieces of the Founding 10 snapshot the official API can create: custom values, custom fields, tags, the client pipeline, the call calendar and the voice agent. It creates what is missing and leaves everything else alone.

Nothing has been run against a real account yet. The tool was tested against a fake API only (see "Tests").

## Files

| File | What it is |
|---|---|
| `hl_build.py` | The tool |
| `config/next-level-answer.json` | The definition of what must exist. Notes that start with `_verify` mark what the saved API reference pages do not confirm |
| `test_hl_build.py` | Unit tests. No network |
| `state/<locationId>.json` | Written by `apply --write`. IDs and names of what the tool created. No token |

## Before you start: the two variables per sub-account

A private integration token works only in the sub-account it was created in. Ray creates each one himself and adds it to the environment's secrets. Never paste a token into a chat, a file, Slack or an email.

| Sub-account | Token variable | Location ID variable |
|---|---|---|
| NL Demo (build here first) | `HIGHLEVEL_NL_DEMO_API_TOKEN` | `HIGHLEVEL_NL_DEMO_LOCATION_ID` |
| Next Level sales account | `HIGHLEVEL_NL_API_TOKEN` | `HIGHLEVEL_NL_LOCATION_ID` |

The demo pair is the default. For the sales account, name the other pair on the command line:

```
python3 hl_build.py preflight --token-env HIGHLEVEL_NL_API_TOKEN --location-env HIGHLEVEL_NL_LOCATION_ID
```

The config in this folder is the master snapshot for NL Demo, including the receptionist. The sales account needs its own config file (its own pipeline, no voice agent). That file is not written yet. Pass it with `--config`. A kind that a config leaves out is neither read nor required.

## Scopes to tick on the private integration

Names as written in `../backlog.md` and on the official reference pages. Whether the tick-box list in the account uses the same names: [verify in HighLevel].

Read scopes this tool uses:

- `locations.readonly`
- `locations/customValues.readonly`
- `locations/customFields.readonly`
- `locations/tags.readonly`
- `opportunities.readonly`
- `calendars.readonly`
- `voice-ai-agents.readonly` (NL Demo only)
- `workflows.readonly` (only to learn whether the workflow API is enabled for the sub-account)
- `forms.readonly` (optional; preflight reports it, the build does not need it)

Write scopes this tool uses:

- `locations/customValues.write`
- `locations/customFields.write`
- `locations/tags.write`
- `pipelines.create`
- `calendars.write`
- `voice-ai-agents.write` (NL Demo only)
- `voice-ai-agent-goals.write` (NL Demo only; needed only once an agent action is switched on in the config)

The backlog table also lists `locations/templates.readonly`, `contacts.readonly`, `phonenumbers.read`, `contacts.write` and `workflows.write` for other jobs. This tool does not use them. Leave them unticked unless Ray wants them for those jobs.

Do not tick: `workflows.publish`, `workflows.logs`, `voice-ai-dashboard.readonly`, anything for conversations or messages, `wallet.readonly`, any agency scope.

## The order

Run from this folder. Each step prints what it did. Every step is read-only except step 3.

1. **Preflight.** Makes one read per scope and says allowed or not allowed. Prints the location name. Says whether the workflow API is enabled.
   ```
   python3 hl_build.py preflight
   ```
   Read the location name. If it is not the sub-account you mean, stop.

2. **Plan.** Shows a table: what would be created, what exists and is left alone, what is built by hand.
   ```
   python3 hl_build.py plan
   ```

3. **Apply.** Without `--write` it is the same as plan. With `--write` it creates the missing items, and only if the name you type equals the name the API returns, letter for letter.
   ```
   python3 hl_build.py apply --write --confirm-location-name "NL Demo"
   ```
   Each created item is printed with its ID. The IDs are saved in `state/<locationId>.json`. Put that list in the report to Ray.

4. **Verify.** Reads the account again and confirms each item exists.
   ```
   python3 hl_build.py verify
   ```

Add `--json` to any step for machine-readable output.

If apply stops part way (for example a scope is not ticked), fix the cause and run apply again. It skips what already exists.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Unexpected error |
| 2 | Bad command line |
| 3 | Configuration: token or location variable missing, or a problem in the config file |
| 4 | Refused: the protected Ray Homes location or its token |
| 5 | Refused: `--confirm-location-name` missing or not equal to the API's name |
| 6 | API or network error. The run stopped |
| 7 | Preflight: a required scope is not allowed |
| 8 | Verify: something is missing |

## What the tool will never do

- Run against the Ray Homes CRM. If the location ID equals the value of `HIGHLEVEL_LOCATION_ID`, it exits before any request. There is no flag to override this. It also refuses the Ray Homes token (`HIGHLEVEL_API_TOKEN`). If `HIGHLEVEL_LOCATION_ID` is not set in the environment, the tool cannot recognise that account, and it says so at the top of its output.
- Change anything without `apply --write` plus the exact location name.
- Update, rename or remove anything that exists. The code holds no update and no removal call. If a name exists, it is left as it is, even when it differs from the config (the table says so).
- Create contacts, send messages, or place calls.
- Create or publish a workflow.
- Attach a phone number to the agent, or put a phone number anywhere. The config is rejected if it holds one.
- Print the token, write it to disk, or pass it on the command line. Authorization values are removed from every error message.
- Hurry. It pauses between calls, retries once after a 429, and stops on any other error from 400 up (a 404 on a list is read as "nothing there").

One call is a POST that only reads: the workflow search in preflight. The API offers no GET for it.

## What still has to be built by hand in HighLevel

| Piece | Who | Note |
|---|---|---|
| Workflows `NL 00` and `NL 01` | Diana | From `../automation-blueprints.md`. A person reads and publishes each one |
| Agent actions: booking, save caller details, the two workflow triggers | Diana | The API reference lists these action types but shows the parameter fields for call transfer only. They are in the config as "by hand". Test each on a real call |
| End-of-call workflow on the agent | Diana | Once `NL 01 \| AI call finished` exists |
| Voice, response speed, pronunciation list | Diana, by ear | |
| Phone number: purchase, low timeout, recording off, not the default number, Deploy tab | Diana | Recording is a setting on the number, not on the agent in the API |
| Calendar: type, team member, real hours, activate it | Diana | The tool creates a draft with placeholder hours. The client connects Google or Outlook |
| Check that the prompt and welcome message read the `nl_` custom values | Diana | Backlog item 7. If not, paste per client |
| Forms, email and text templates, dashboard | Diana | The API cannot create them |
| SaaS plan, usage limits, rebilling | Ray and Diana | Agency view |
| Snapshot creation | Diana | Agency view, after the tests in `../TESTS-BEFORE-FIRST-CLIENT.md` |

## Things in the config Ray should look at

Search the config for `_verify`. The main ones:

- **Version header.** Every endpoint page says `v3`. The private integration page shows an example with `2021-07-28`. If `v3` is refused, add `--api-version 2021-07-28`.
- **Choice fields.** The page does not show which request field carries the choices of a single-choice custom field. The tool sends `options`. Check the first one in the account.
- **Empty values.** `nl_transfer_number` and `nl_recording_line` are meant to be empty. If the API refuses an empty value, create those two by hand and run apply again.
- **Calendar name.** Taken from the spec, with the owner-name merge field in it. If it shows the braces, rename it by hand.
- **Post-call email.** Switched off on the agent, because the summary goes out through the workflow and the built-in email would go to every admin user. Ray to confirm.
- **Two names for one figure.** `nl_minutes_included` (spec) and `nl_usage_included` (blueprints). Both are created. Ray to pick one.
- **Consent basis.** The spec lists express, implied, none. Blueprint 3 also stores "inquiry". The field is created with all four.

## Tests

```
python3 -m unittest -v test_hl_build
```

The tests use a fake HTTP layer. They cover: the token never appears in output, the Ray Homes location is refused, apply without `--write` changes nothing, a wrong confirmation name changes nothing, existing items are not recreated, a 401 on one scope is reported while the other scopes are still tested, and the state file holds no token.
