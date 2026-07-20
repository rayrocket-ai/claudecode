# Mortgage Tools — static site

A self-contained public mini-site with Ontario/Toronto mortgage calculators and a
wowa-style lead wizard. Plain HTML/CSS/JS — no build step.

## Pages

| URL | File | What it does |
|---|---|---|
| `/` | `index.html` | Step wizard (Renew / New Mortgage / Refinance / Learn) + quick links |
| `/closing-costs` | `closing-costs.html` | Itemized closing costs: land transfer tax (ON + Toronto), FTB rebates, down payment, CMHC + PST, legal/title/inspection, HST notes |
| `/payment-calculator` | `payment-calculator.html` | Monthly payment (Canadian semi-annual compounding) + income needed to qualify (39% GDS, stress test) |

All math lives in `js/calc.js` (pure functions, no DOM).

## Configure lead capture

Edit `js/config.js`:

- `FORM_ENDPOINT` — paste a [Formspree](https://formspree.io) form endpoint
  (e.g. `https://formspree.io/f/abcdwxyz`) to receive lead submissions by email.
  Wizard leads include everything the visitor entered, so you can see what they want.
- `CONTACT_EMAIL` — used for the `mailto:` fallback when no endpoint is set.

## Deploy (Vercel)

Static deploy, **root directory = `web/`**, framework preset "Other", no build
command, no output directory. `vercel.json` enables clean URLs
(`/closing-costs` instead of `/closing-costs.html`).

## Tests

```bash
node web/tests/calc.test.js   # math against known-good Ontario/Toronto values
```

## Updating assumptions

Defaults live where they're used and are easy to change:

- Rate (4%) and amortization (30y) defaults: input values in the two calculator
  pages and `wizard.js`.
- Property tax ($500/mo) and heat & insurance ($250/mo): defaults in
  `calc.js` (`incomeToQualify`) and the payment page inputs.
- Legal/title/inspection estimates: defaults in `calc.js` (`closingCosts`).
- Tax brackets and CMHC bands: constants at the top of `calc.js`.
