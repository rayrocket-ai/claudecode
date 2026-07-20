/*
 * calc.js — pure mortgage/closing-cost math for Ontario & Toronto.
 * No DOM access. Loaded in the browser via <script>; also runnable in Node
 * for tests via the module.exports guard at the bottom.
 *
 * Conventions: rates are decimals (0.04 = 4%), money is plain CAD numbers.
 * Round only at display time — these functions keep cents.
 */

/** Marginal bracket helper: brackets = [[upperBound, rate], ...], last upperBound = Infinity. */
function marginalTax(amount, brackets) {
  let tax = 0;
  let lower = 0;
  for (const [upper, rate] of brackets) {
    if (amount <= lower) break;
    tax += (Math.min(amount, upper) - lower) * rate;
    lower = upper;
  }
  return tax;
}

const ON_LTT_BRACKETS = [
  [55000, 0.005],
  [250000, 0.01],
  [400000, 0.015],
  [2000000, 0.02],
  [Infinity, 0.025],
];

// Toronto MLTT: mirrors provincial brackets to $2M, then the 2024 luxury tiers.
const TORONTO_LTT_BRACKETS = [
  [55000, 0.005],
  [250000, 0.01],
  [400000, 0.015],
  [2000000, 0.02],
  [3000000, 0.025],
  [4000000, 0.035],
  [5000000, 0.045],
  [10000000, 0.055],
  [20000000, 0.065],
  [Infinity, 0.075],
];

function ontarioLTT(price) {
  return marginalTax(price, ON_LTT_BRACKETS);
}

function torontoLTT(price) {
  return marginalTax(price, TORONTO_LTT_BRACKETS);
}

/** First-time buyer rebates (cannot exceed the tax itself). */
function ontarioFtbRebate(price) {
  return Math.min(ontarioLTT(price), 4000);
}

function torontoFtbRebate(price) {
  return Math.min(torontoLTT(price), 4475);
}

/**
 * Canadian legal minimum down payment:
 * 5% of first $500k + 10% of the portion between $500k and $1.5M;
 * 20% of the full price at/above $1.5M.
 */
function minDownPayment(price) {
  if (price >= 1500000) return price * 0.2;
  const first = Math.min(price, 500000) * 0.05;
  const second = Math.max(price - 500000, 0) * 0.1;
  return first + second;
}

/**
 * CMHC default-insurance premium rate by down-payment band.
 * 0 when down >= 20%, price >= $1.5M (uninsurable), or below legal minimum.
 */
function cmhcPremiumRate(price, down) {
  if (price >= 1500000) return 0;
  const ratio = down / price;
  if (ratio >= 0.2) return 0;
  if (ratio >= 0.15) return 0.028;
  if (ratio >= 0.1) return 0.031;
  if (ratio >= 0.05) return 0.04;
  return 0; // below legal minimum — caller should flag invalid input
}

/** Premium dollars (added to the mortgage, not paid in cash). */
function cmhcPremium(price, down) {
  return (price - down) * cmhcPremiumRate(price, down);
}

/** Ontario charges 8% PST on the CMHC premium — payable in cash at closing. */
function cmhcPst(price, down) {
  return cmhcPremium(price, down) * 0.08;
}

/** Canadian fixed-rate mortgages compound semi-annually. */
function monthlyRate(annualRate) {
  return Math.pow(1 + annualRate / 2, 1 / 6) - 1;
}

function monthlyPayment(principal, annualRate, years) {
  const n = Math.round(years * 12);
  if (n <= 0 || principal <= 0) return 0;
  if (annualRate === 0) return principal / n;
  const i = monthlyRate(annualRate);
  return (principal * i) / (1 - Math.pow(1 + i, -n));
}

/** Federal stress test: qualify at the greater of contract + 2% or 5.25%. */
function stressTestRate(annualRate) {
  return Math.max(annualRate + 0.02, 0.0525);
}

/**
 * Approximate gross annual income needed to carry a mortgage, GDS-style.
 * Assumes no other debts. opts: { propertyTaxMonthly, heatMonthly, gds }.
 * Returns { atContract, atStressTest, paymentAtContract, paymentAtStressTest }.
 */
function incomeToQualify(principal, annualRate, years, opts) {
  const o = Object.assign(
    { propertyTaxMonthly: 500, heatMonthly: 250, gds: 0.39 },
    opts
  );
  const income = (rate) => {
    const pmt = monthlyPayment(principal, rate, years);
    return {
      payment: pmt,
      income: ((pmt + o.propertyTaxMonthly + o.heatMonthly) * 12) / o.gds,
    };
  };
  const contract = income(annualRate);
  const stressed = income(stressTestRate(annualRate));
  return {
    atContract: contract.income,
    atStressTest: stressed.income,
    paymentAtContract: contract.payment,
    paymentAtStressTest: stressed.payment,
  };
}

/**
 * Itemized closing-cost estimate.
 * opts: { price, inToronto, firstTimeBuyer, newConstruction, downPayment,
 *         legalFees, titleInsurance, homeInspection }
 * NOTE: intentionally no mortgage/broker fee line.
 */
function closingCosts(opts) {
  const o = Object.assign(
    {
      inToronto: false,
      firstTimeBuyer: false,
      newConstruction: false,
      legalFees: 2000,
      titleInsurance: 500,
      homeInspection: 500,
    },
    opts
  );
  const price = o.price || 0;
  const down = o.downPayment != null ? o.downPayment : minDownPayment(price);

  const onLtt = ontarioLTT(price);
  const torLtt = o.inToronto ? torontoLTT(price) : 0;
  const onRebate = o.firstTimeBuyer ? ontarioFtbRebate(price) : 0;
  const torRebate = o.inToronto && o.firstTimeBuyer ? torontoFtbRebate(price) : 0;
  const premium = cmhcPremium(price, down);
  const pst = premium * 0.08;

  const totalClosing =
    onLtt - onRebate + torLtt - torRebate + pst + o.legalFees + o.titleInsurance + o.homeInspection;

  return {
    price: price,
    downPayment: down,
    minDown: minDownPayment(price),
    mortgageBeforePremium: price - down,
    cmhcPremium: premium,
    mortgageTotal: price - down + premium,
    onLtt: onLtt,
    torontoLtt: torLtt,
    onRebate: onRebate,
    torontoRebate: torRebate,
    cmhcPst: pst,
    legalFees: o.legalFees,
    titleInsurance: o.titleInsurance,
    homeInspection: o.homeInspection,
    hstApplies: !!o.newConstruction,
    totalClosing: totalClosing,
    totalCashNeeded: down + totalClosing,
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    marginalTax,
    ontarioLTT,
    torontoLTT,
    ontarioFtbRebate,
    torontoFtbRebate,
    minDownPayment,
    cmhcPremiumRate,
    cmhcPremium,
    cmhcPst,
    monthlyRate,
    monthlyPayment,
    stressTestRate,
    incomeToQualify,
    closingCosts,
  };
}
