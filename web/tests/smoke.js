/*
 * Playwright smoke + browser-fuzz test for the mortgage tools site.
 *
 * Usage:
 *   python3 -m http.server 8080 --directory web &
 *   NODE_PATH=/opt/node22/lib/node_modules node web/tests/smoke.js
 *
 * Optional env: CHROMIUM_PATH (defaults to the preinstalled browser),
 * BASE_URL (defaults to http://localhost:8080), SCREENSHOT_DIR.
 */
const assert = require("node:assert");
const { chromium } = require("playwright");
const calc = require("../js/calc.js");

const BASE = process.env.BASE_URL || "http://localhost:8080";
const SHOT_DIR = process.env.SCREENSHOT_DIR || "";
const FUZZ_RUNS = 25;

function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(42);
const toNumber = (s) => parseFloat(String(s).replace(/[^0-9.]/g, ""));

(async () => {
  const launchOpts = {};
  if (process.env.CHROMIUM_PATH) launchOpts.executablePath = process.env.CHROMIUM_PATH;
  const browser = await chromium.launch(launchOpts);
  const page = await browser.newPage();
  page.on("pageerror", (err) => {
    throw new Error("Page JS error: " + err.message);
  });

  async function shot(name, width) {
    if (!SHOT_DIR) return;
    await page.setViewportSize({ width, height: 900 });
    await page.screenshot({ path: `${SHOT_DIR}/${name}-${width}.png`, fullPage: true });
    await page.setViewportSize({ width: 1280, height: 900 });
  }

  // --- Closing costs page: instant results, no lead form ---
  await page.goto(`${BASE}/closing-costs.html`);
  assert.strictEqual(await page.locator("form.lead-form").count(), 0, "no lead form on closing-costs");
  assert.strictEqual(await page.locator("input[type=email]").count(), 0, "no email field on closing-costs");
  await page.fill("#cc-price", "1000000");
  await page.waitForSelector("#cc-results-card:not([hidden])");
  let body = await page.textContent("main");
  const lttCount = (body.match(/\$16,475/g) || []).length;
  assert.ok(lttCount >= 2, `expected ON + Toronto LTT of $16,475 twice, saw ${lttCount}`);

  // First-time buyer toggle adds rebate lines
  await page.click('#cc-ftb button[data-value="yes"]');
  body = await page.textContent("main");
  assert.ok(body.includes("$4,000"), "ON FTB rebate shown");
  assert.ok(body.includes("$4,475"), "Toronto FTB rebate shown");

  // Outside Toronto removes the municipal tax
  await page.click('#cc-location button[data-value="outside"]');
  body = await page.textContent("main");
  assert.ok(!body.includes("Toronto municipal land transfer tax"), "MLTT hidden outside Toronto");

  // Deposit feature (spreadsheet parity)
  await page.fill("#cc-deposit", "30000");
  body = await page.textContent("main");
  assert.ok(body.includes("Deposit already paid"), "deposit row shown");
  assert.ok(body.includes("Balance of down payment at closing"), "balance-of-down row shown");
  await page.fill("#cc-deposit", "");
  await shot("closing-costs", 375);
  await shot("closing-costs", 1280);
  console.log("closing-costs.html OK");

  // --- Payment calculator page: instant results, no lead form ---
  await page.goto(`${BASE}/payment-calculator.html`);
  assert.strictEqual(await page.locator("form.lead-form").count(), 0, "no lead form on payment page");
  assert.strictEqual(await page.locator("input[type=email]").count(), 0, "no email field on payment page");
  await page.fill("#pc-price", "1000000");
  await page.waitForSelector("#pc-results-card:not([hidden])");
  const paymentText = await page.textContent("#pc-payment");
  // $800k @ 4% / 30y semi-annual => $3,804.15
  assert.ok(paymentText.includes("3,804"), `expected payment ~$3,804, saw ${paymentText}`);
  body = await page.textContent("main");
  assert.ok(body.includes("Income needed"), "income section renders");
  await shot("payment-calculator", 375);
  await shot("payment-calculator", 1280);
  console.log("payment-calculator.html OK");

  // --- Browser fuzz: rendered numbers must equal calc.js outputs ---
  for (let i = 0; i < FUZZ_RUNS; i++) {
    const price = Math.round(100000 + rand() * 4900000);
    const pct = Math.round((5 + rand() * 45) * 2) / 2; // 5–50% in 0.5 steps
    const deposit = rand() < 0.5 ? Math.round(rand() * price * 0.05) : 0;
    const inToronto = rand() < 0.5;
    const ftb = rand() < 0.5;

    await page.goto(`${BASE}/closing-costs.html`);
    await page.fill("#cc-price", String(price));
    await page.fill("#cc-down-pct", String(pct));
    if (deposit) await page.fill("#cc-deposit", String(deposit));
    await page.click(`#cc-location button[data-value="${inToronto ? "toronto" : "outside"}"]`);
    await page.click(`#cc-ftb button[data-value="${ftb ? "yes" : "no"}"]`);
    await page.waitForSelector("#cc-results-card:not([hidden])");

    // replicate the page's min-down clamp
    let down = (price * pct) / 100;
    const minDown = calc.minDownPayment(price);
    if (down < minDown - 0.5) down = minDown;
    const expected = calc.closingCosts({
      price, inToronto, firstTimeBuyer: ftb, downPayment: down, depositPaid: deposit,
    });
    const shown = toNumber(await page.textContent("#cc-total-cash"));
    assert.ok(
      Math.abs(shown - Math.round(expected.cashAtClosing)) <= 1,
      `fuzz ${i}: closing-costs display ${shown} != expected ${Math.round(expected.cashAtClosing)} ` +
      `(price=${price} pct=${pct} deposit=${deposit} toronto=${inToronto} ftb=${ftb})`
    );

    // payment page
    const rate = Math.round(rand() * 800) / 100; // 0–8.00%
    const years = [30, 25, 20, 15][Math.floor(rand() * 4)];
    await page.goto(`${BASE}/payment-calculator.html`);
    await page.fill("#pc-price", String(price));
    await page.fill("#pc-down", String(pct));
    await page.fill("#pc-rate", String(rate));
    await page.selectOption("#pc-amort", String(years));
    await page.waitForSelector("#pc-results-card:not([hidden])");
    const principal = price - down + calc.cmhcPremium(price, down);
    const expPmt = calc.monthlyPayment(principal, rate / 100, years);
    const shownPmt = toNumber(await page.textContent("#pc-payment"));
    assert.ok(
      Math.abs(shownPmt - expPmt) < 0.02,
      `fuzz ${i}: payment display ${shownPmt} != expected ${expPmt.toFixed(2)} ` +
      `(price=${price} pct=${pct} rate=${rate} yrs=${years})`
    );
  }
  console.log(`browser fuzz OK (${FUZZ_RUNS} random scenarios matched calc.js)`);

  // --- Wizard: New Mortgage path end-to-end ---
  await page.goto(`${BASE}/index.html`);
  await page.click('.option-card[data-path="buy"]');
  await page.waitForSelector("#wizard input#price");
  await page.fill("#price", "1000000");
  await page.click('[data-answer-toggle="location"] button[data-value="toronto"]');
  await page.click("#wizard-next");

  await page.waitForSelector("#downPct");
  await page.click('[data-answer-toggle="ftb"] button[data-value="no"]');
  await page.click('[data-answer-toggle="newbuild"] button[data-value="resale"]');
  await page.click("#wizard-next");

  await page.waitForSelector("#rate");
  await page.click("#wizard-next");

  await page.waitForSelector("#wizard-lead");
  body = await page.textContent("main");
  assert.ok(body.includes("$16,475"), "wizard results include LTT");
  assert.ok(body.includes("3,804"), "wizard results include monthly payment");
  assert.ok(body.includes("Income needed"), "wizard results include income section");
  assert.ok(body.includes("Optional"), "wizard lead form clearly optional");

  // Step indicator: 4 completed checkmarks + active results step
  const doneSteps = await page.locator(".step.done").count();
  assert.ok(doneSteps >= 4, `expected >=4 completed steps, saw ${doneSteps}`);
  await shot("wizard-results", 375);
  await shot("wizard-results", 1280);
  console.log("wizard (new mortgage path) OK");

  // --- Landing: chooser + branding ---
  await page.goto(`${BASE}/index.html`);
  const options = await page.locator(".option-card").count();
  assert.strictEqual(options, 4, "4 wizard paths on landing");
  const header = await page.textContent(".site-header");
  assert.ok(header.includes("Ray") && header.includes("Homes"), "Ray Homes branding in header");
  await shot("landing", 375);
  await shot("landing", 1280);
  console.log("index.html OK");

  await browser.close();
  console.log("All smoke tests passed.");
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
