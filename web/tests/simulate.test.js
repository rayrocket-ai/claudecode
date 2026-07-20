/*
 * simulate.test.js — 1,000 randomized simulations of the mortgage math.
 * Run: node web/tests/simulate.test.js
 *
 * Deterministic (seeded PRNG). Each scenario checks structural invariants and
 * cross-checks the bracket math against an independent closed-form
 * implementation; the payment formula is proven by simulating the full
 * amortization schedule month-by-month down to a zero balance.
 */
const assert = require("node:assert");
const c = require("../js/calc.js");

const RUNS = 1000;

// Mulberry32 seeded PRNG — deterministic across runs.
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(20260720);
const pick = (arr) => arr[Math.floor(rand() * arr.length)];

// Independent closed-form LTT: tax = rate * price - constant per bracket.
function closedFormLTT(price, brackets) {
  let cum = 0;
  let lower = 0;
  for (const [upper, rate] of brackets) {
    if (price <= upper) return cum + (price - lower) * rate;
    cum += (upper - lower) * rate;
    lower = upper;
  }
  return cum;
}
const ON = [
  [55000, 0.005], [250000, 0.01], [400000, 0.015], [2000000, 0.02], [Infinity, 0.025],
];
const TOR = [
  [55000, 0.005], [250000, 0.01], [400000, 0.015], [2000000, 0.02], [3000000, 0.025],
  [4000000, 0.035], [5000000, 0.045], [10000000, 0.055], [20000000, 0.065], [Infinity, 0.075],
];

let failures = 0;
let prevPrice = null;
let prevOn = null;
let prevTor = null;

for (let i = 0; i < RUNS; i++) {
  // --- random scenario ---
  const price = Math.round(50000 + rand() * 24950000); // $50k – $25M
  const downPct = rand() * 0.95 + 0.03; // 3% – 98%, includes below-minimum
  const down = Math.round(price * downPct);
  const rate = rand() * 0.1; // 0% – 10%
  const years = pick([5, 10, 15, 20, 25, 30]);
  const inToronto = rand() < 0.5;
  const ftb = rand() < 0.5;
  const newBuild = rand() < 0.5;
  const deposit = Math.round(rand() * down * 1.2); // sometimes exceeds down (must clamp)

  const label = `run ${i}: price=${price} down=${down} rate=${(rate * 100).toFixed(2)}% yrs=${years}` +
    ` toronto=${inToronto} ftb=${ftb} deposit=${deposit}`;

  try {
    // --- land transfer tax vs independent implementation ---
    const onLtt = c.ontarioLTT(price);
    const torLtt = c.torontoLTT(price);
    assert.ok(Math.abs(onLtt - closedFormLTT(price, ON)) < 0.01, "ON LTT cross-check");
    assert.ok(Math.abs(torLtt - closedFormLTT(price, TOR)) < 0.01, "Toronto LTT cross-check");
    assert.ok(torLtt >= onLtt - 0.01, "Toronto LTT >= Ontario LTT");
    if (prevPrice !== null && price > prevPrice) {
      assert.ok(onLtt >= prevOn - 0.01 && torLtt >= prevTor - 0.01, "LTT monotonic in price");
    }
    prevPrice = price; prevOn = onLtt; prevTor = torLtt;

    // --- rebates ---
    assert.ok(c.ontarioFtbRebate(price) <= Math.min(4000, onLtt) + 0.01, "ON rebate capped");
    assert.ok(c.torontoFtbRebate(price) <= Math.min(4475, torLtt) + 0.01, "Toronto rebate capped");

    // --- minimum down payment ---
    const minDown = c.minDownPayment(price);
    const expectedMin = price >= 1500000
      ? price * 0.2
      : Math.min(price, 500000) * 0.05 + Math.max(price - 500000, 0) * 0.1;
    assert.ok(Math.abs(minDown - expectedMin) < 0.01, "min down formula");

    // --- CMHC bands ---
    const ratio = down / price;
    const prate = c.cmhcPremiumRate(price, down);
    if (price >= 1500000 || ratio >= 0.2 || ratio < 0.05) {
      assert.strictEqual(prate, 0, "no CMHC outside insurable range");
    } else if (ratio >= 0.15) assert.strictEqual(prate, 0.028, "CMHC 15-19.99 band");
    else if (ratio >= 0.1) assert.strictEqual(prate, 0.031, "CMHC 10-14.99 band");
    else assert.strictEqual(prate, 0.04, "CMHC 5-9.99 band");
    assert.ok(Math.abs(c.cmhcPst(price, down) - c.cmhcPremium(price, down) * 0.08) < 0.01, "PST = 8% of premium");

    // --- payment formula proven by amortization schedule ---
    const principal = price - down + c.cmhcPremium(price, down);
    const pmt = c.monthlyPayment(principal, rate, years);
    assert.ok(isFinite(pmt) && pmt > 0, "payment finite/positive");
    const mi = rate === 0 ? 0 : c.monthlyRate(rate);
    let bal = principal;
    const n = years * 12;
    for (let m = 0; m < n; m++) bal = bal * (1 + mi) - pmt;
    assert.ok(Math.abs(bal) < 1, `amortization zeroes balance (residual ${bal.toFixed(4)})`);

    // --- income to qualify ---
    const q = c.incomeToQualify(principal, rate, years, { propertyTaxMonthly: 500, heatMonthly: 250 });
    const gds = ((q.paymentAtContract + 750) * 12) / q.atContract;
    assert.ok(Math.abs(gds - 0.39) < 1e-9, "GDS recovered = 39%");
    assert.ok(q.atStressTest > q.atContract - 1e-9, "stress income >= contract income");
    assert.ok(Math.abs(c.stressTestRate(rate) - Math.max(rate + 0.02, 0.0525)) < 1e-12, "stress rate rule");

    // --- closing costs totals ---
    const r = c.closingCosts({
      price: price, inToronto: inToronto, firstTimeBuyer: ftb,
      newConstruction: newBuild, downPayment: down, depositPaid: deposit,
    });
    const parts = r.onLtt - r.onRebate + r.torontoLtt - r.torontoRebate + r.cmhcPst +
      r.legalFees + r.titleInsurance + r.homeInspection;
    assert.ok(Math.abs(r.totalClosing - parts) < 0.01, "totalClosing = sum of parts");
    assert.ok(Math.abs(r.totalCashNeeded - (r.downPayment + r.totalClosing)) < 0.01, "totalCash = down + closing");
    assert.ok(Math.abs(r.cashAtClosing - (r.balanceOfDownAtClosing + r.totalClosing)) < 0.01, "cashAtClosing formula");
    assert.ok(r.depositPaid <= r.downPayment + 0.01, "deposit clamped to down payment");
    assert.ok(r.balanceOfDownAtClosing >= -0.01, "balance of down >= 0");
    if (!inToronto) assert.strictEqual(r.torontoLtt, 0, "no MLTT outside Toronto");
    if (!ftb) assert.strictEqual(r.onRebate + r.torontoRebate, 0, "no rebates unless FTB");
    assert.strictEqual(r.hstApplies, newBuild, "HST flag follows new-construction");
    for (const [k, v] of Object.entries(r)) {
      if (typeof v === "number") assert.ok(isFinite(v), `output ${k} finite`);
    }
  } catch (err) {
    failures++;
    console.error(`FAIL ${label}\n  ${err.message}`);
    if (failures > 5) {
      console.error("Too many failures, aborting.");
      process.exit(1);
    }
  }
}

if (failures) {
  console.error(`${RUNS - failures}/${RUNS} scenarios passed, ${failures} FAILED`);
  process.exit(1);
}
console.log(`${RUNS}/${RUNS} scenarios passed.`);
