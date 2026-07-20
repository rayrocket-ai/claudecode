# Ray Homes Real Estate — mortgage tools static site

A self-contained public mini-site with Ontario/Toronto mortgage calculators and a
wowa-style wizard. Plain HTML/CSS/JS — no build step. Calculators are completely
free and frictionless: results render live as numbers are typed, and no contact
info is ever required. The only (clearly optional) contact form is at the end of
the wizard, after results are shown.

## Pages

| URL | File | What it does |
|---|---|---|
| `/` | `index.html` | Step wizard (Renew / New Mortgage / Refinance / Learn) + quick links |
| `/closing-costs` | `closing-costs.html` | Itemized closing costs: land transfer tax (ON + Toronto), FTB rebates, down payment + deposit-already-paid split, CMHC premium + 8% PST, editable legal/title/inspection, HST notes |
| `/payment-calculator` | `payment-calculator.html` | Monthly payment (Canadian semi-annual compounding) + income needed to qualify (39% GDS, stress test) |

All math lives in `js/calc.js` (pure functions, no DOM). The closing-cost model
mirrors the Ray Homes "Buyer Property Tracker" workbook (minus the broker fee,
intentionally excluded).

## Configure lead capture (wizard only)

Edit `js/config.js`:

- `FORM_ENDPOINT` — paste a [Formspree](https://formspree.io) form endpoint
  (e.g. `https://formspree.io/f/abcdwxyz`) to receive wizard lead submissions by
  email. Leads include everything the visitor entered, so you can see what they want.
- `CONTACT_EMAIL` — used for the footer contact links and the `mailto:` fallback
  when no endpoint is set.

## Deploy (Vercel)

Static deploy, **root directory = `web/`**, framework preset "Other", no build
command, no output directory. `vercel.json` enables clean URLs
(`/closing-costs` instead of `/closing-costs.html`).

## Tests

```bash
node web/tests/calc.test.js       # unit tests + Ray Homes spreadsheet fixtures
node web/tests/simulate.test.js   # 1,000 randomized simulations (amortization
                                  # proof, bracket cross-checks, invariants)
# browser end-to-end (serves web/ and drives Chromium, incl. 25-scenario fuzz):
python3 -m http.server 8080 --directory web &
NODE_PATH=/opt/node22/lib/node_modules node web/tests/smoke.js
```

## Updating assumptions

Defaults live where they're used and are easy to change:

- Rate (4%) and amortization (30y) defaults: input values in the two calculator
  pages and `wizard.js`.
- Property tax ($500/mo) and heat & insurance ($250/mo): defaults in
  `calc.js` (`incomeToQualify`) and the payment page inputs.
- Legal/title/inspection estimates: defaults in `calc.js` (`closingCosts`).
- Tax brackets and CMHC bands: constants at the top of `calc.js`.
