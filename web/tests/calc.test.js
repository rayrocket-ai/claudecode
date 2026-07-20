// Run: node web/tests/calc.test.js
const assert = require("node:assert");
const c = require("../js/calc.js");

const close = (a, b, tol, msg) =>
  assert.ok(Math.abs(a - b) <= tol, `${msg}: got ${a}, expected ~${b}`);

// Land transfer tax
assert.strictEqual(c.ontarioLTT(1000000), 16475, "ON LTT $1M");
assert.strictEqual(c.torontoLTT(1000000), 16475, "Toronto MLTT $1M");
assert.strictEqual(c.ontarioLTT(55000), 275, "ON LTT $55k");
assert.strictEqual(c.ontarioLTT(2000000), 36475, "ON LTT $2M");
assert.strictEqual(c.ontarioLTT(3000000), 61475, "ON LTT $3M (2.5% top)");
// Toronto luxury tiers: $3.5M = 36,475 (to 2M) + 25,000 (2-3M @2.5%) + 17,500 (3-3.5M @3.5%)
assert.strictEqual(c.torontoLTT(3500000), 78975, "Toronto MLTT $3.5M luxury tiers");

// First-time buyer rebates
assert.strictEqual(c.ontarioFtbRebate(1000000), 4000, "ON FTB rebate cap");
assert.strictEqual(c.torontoFtbRebate(1000000), 4475, "Toronto FTB rebate cap");
assert.strictEqual(c.ontarioFtbRebate(200000), 1725, "ON FTB rebate below cap");

// Minimum down payment
assert.strictEqual(c.minDownPayment(500000), 25000, "min down $500k");
assert.strictEqual(c.minDownPayment(800000), 55000, "min down $800k");
assert.strictEqual(c.minDownPayment(1000000), 75000, "min down $1M");
assert.strictEqual(c.minDownPayment(1500000), 300000, "min down $1.5M (20%)");

// CMHC
assert.strictEqual(c.cmhcPremiumRate(500000, 100000), 0, "no CMHC at 20%");
assert.strictEqual(c.cmhcPremiumRate(500000, 25000), 0.04, "CMHC 5% down band");
assert.strictEqual(c.cmhcPremium(500000, 25000), 19000, "CMHC premium $500k/5%");
close(c.cmhcPst(500000, 25000), 1520, 0.01, "CMHC PST");
assert.strictEqual(c.cmhcPremiumRate(1600000, 200000), 0, "uninsurable >= $1.5M");

// Monthly payment (Canadian semi-annual compounding)
close(c.monthlyPayment(100000, 0.05, 25), 581.6, 0.05, "payment $100k @5%/25y");
close(c.monthlyPayment(800000, 0.04, 30), 3804.15, 0.05, "payment $800k @4%/30y");
assert.strictEqual(c.monthlyPayment(120000, 0, 10), 1000, "zero-rate payment");

// Stress test
assert.strictEqual(c.stressTestRate(0.04), 0.06, "stress 4% -> 6%");
assert.strictEqual(c.stressTestRate(0.029), 0.0525, "stress floor 5.25%");

// Income to qualify
{
  const q = c.incomeToQualify(800000, 0.04, 30);
  assert.ok(q.atStressTest > q.atContract, "stress income > contract income");
  const expected = ((c.monthlyPayment(800000, 0.04, 30) + 750) * 12) / 0.39;
  close(q.atContract, expected, 0.01, "income formula");
}

// Closing costs integration
{
  const r = c.closingCosts({
    price: 1000000,
    inToronto: true,
    firstTimeBuyer: false,
    downPayment: 200000,
  });
  assert.strictEqual(r.onLtt, 16475, "closingCosts ON LTT");
  assert.strictEqual(r.torontoLtt, 16475, "closingCosts Toronto LTT");
  assert.strictEqual(r.cmhcPremium, 0, "no CMHC at 20% down");
  assert.strictEqual(r.totalClosing, 16475 + 16475 + 2000 + 500 + 500, "total closing");
  assert.strictEqual(r.totalCashNeeded, 200000 + r.totalClosing, "total cash");
}
{
  const r = c.closingCosts({ price: 500000, downPayment: 25000, inToronto: false });
  close(r.cmhcPst, 1520, 0.01, "closingCosts includes CMHC PST");
  assert.strictEqual(r.mortgageTotal, 475000 + 19000, "premium added to mortgage");
}
{
  const r = c.closingCosts({ price: 800000 });
  assert.strictEqual(r.downPayment, 55000, "defaults to min down");
}

console.log("All calc.js tests passed.");
