/*
 * Playwright smoke test for the mortgage tools site.
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

const BASE = process.env.BASE_URL || "http://localhost:8080";
const SHOT_DIR = process.env.SCREENSHOT_DIR || "";

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

  // --- Closing costs page ---
  await page.goto(`${BASE}/closing-costs.html`);
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
  await shot("closing-costs", 375);
  await shot("closing-costs", 1280);
  console.log("closing-costs.html OK");

  // --- Payment calculator page ---
  await page.goto(`${BASE}/payment-calculator.html`);
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

  // Step indicator: 4 completed checkmarks + active results step
  const doneSteps = await page.locator(".step.done").count();
  assert.ok(doneSteps >= 4, `expected >=4 completed steps, saw ${doneSteps}`);
  await shot("wizard-results", 375);
  await shot("wizard-results", 1280);
  console.log("wizard (new mortgage path) OK");

  // --- Wizard: chooser renders on load ---
  await page.goto(`${BASE}/index.html`);
  const options = await page.locator(".option-card").count();
  assert.strictEqual(options, 4, "4 wizard paths on landing");
  await shot("landing", 375);
  await shot("landing", 1280);
  console.log("index.html OK");

  await browser.close();
  console.log("All smoke tests passed.");
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
