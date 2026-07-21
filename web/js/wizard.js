/* wizard.js — wowa-style step wizard for index.html.
 *
 * FLOWS defines the steps per path. Every flow implicitly starts with the
 * shared "I want to" chooser (step 1) and ends with a results step that
 * includes a lead form. State is one object repainted by renderStep().
 */

(function () {
  var state = { path: null, stepIndex: 0, answers: {} };

  var container = document.getElementById("wizard");
  var stepsEl = document.getElementById("wizard-steps");

  /* ---------- helpers ---------- */

  function moneyField(id, label, placeholder, sub) {
    return (
      '<div class="field"><label for="' + id + '">' + label +
      (sub ? "<small>" + sub + "</small>" : "") +
      '</label><div class="control input-prefix"><span>$</span>' +
      '<input id="' + id + '" data-answer="' + id + '" type="text" inputmode="numeric" placeholder="' +
      (placeholder || "") + '"></div></div>'
    );
  }

  function suffixField(id, label, suffix, value, attrs, sub) {
    return (
      '<div class="field"><label for="' + id + '">' + label +
      (sub ? "<small>" + sub + "</small>" : "") +
      '</label><div class="control input-suffix">' +
      '<input id="' + id + '" data-answer="' + id + '" type="number" ' + (attrs || "") +
      ' value="' + value + '"><span>' + suffix + "</span></div></div>"
    );
  }

  function toggleField(id, label, options, sub) {
    var buttons = options
      .map(function (o) {
        return '<button type="button" data-value="' + o.value + '">' + o.label + "</button>";
      })
      .join("");
    return (
      '<div class="field"><label>' + label +
      (sub ? "<small>" + sub + "</small>" : "") +
      '</label><div class="toggle" data-answer-toggle="' + id + '">' + buttons + "</div></div>"
    );
  }

  function resultRow(label, value, cls, sub) {
    return (
      '<tr class="' + (cls || "") + '"><td>' + label +
      (sub ? " <small>" + sub + "</small>" : "") +
      "</td><td>" + value + "</td></tr>"
    );
  }

  function num(id, fallback) {
    var v = UI.parseMoney(state.answers[id]);
    return isNaN(v) ? fallback : v;
  }

  /* ---------- chooser (shared step 1) ---------- */

  var chooserStep = {
    id: "choose",
    title: "I want to",
    render: function () {
      var opts = [
        { path: "renew", icon: "🔄", label: "Renew a Mortgage" },
        { path: "buy", icon: "🏠", label: "Get a New Mortgage" },
        { path: "refi", icon: "💰", label: "Refinance a Mortgage" },
        { path: "learn", icon: "📖", label: "Learn About Mortgages" },
      ];
      return (
        '<div class="option-list">' +
        opts
          .map(function (o) {
            return (
              '<button type="button" class="option-card" data-path="' + o.path + '">' +
              '<span class="icon">' + o.icon + "</span>" + o.label + "</button>"
            );
          })
          .join("") +
        "</div>"
      );
    },
    noNav: true,
  };

  /* ---------- flows ---------- */

  var FLOWS = {
    renew: [
      chooserStep,
      {
        id: "renew-info",
        title: "About your current mortgage",
        sub: "Rough numbers are fine \u2014 you can adjust them any time.",
        render: function (a) {
          return (
            moneyField("balance", "Remaining Mortgage Balance", "550,000", "roughly what you still owe") +
            suffixField("currentRate", "Current Interest Rate", "%", a.currentRate || "", 'min="0" max="20" step="0.05" placeholder="e.g. 5.25"', "optional \u2014 shows what you could save") +
            toggleField("timing", "My renewal is", [
              { value: "30days", label: "Within 30 days" },
              { value: "4months", label: "1\u20134 months" },
              { value: "later", label: "4+ months away" },
            ], "optional")
          );
        },
        validate: function (a) {
          var b = UI.parseMoney(a.balance);
          return isNaN(b) || b <= 0 ? "Please enter your remaining mortgage balance." : null;
        },
      },
      {
        id: "renew-results",
        title: "Your renewal estimate",
        isResults: true,
        render: function (a) {
          var balance = num("balance", 0);
          var rate = 0.04;
          var years = 25;
          var pmt = monthlyPayment(balance, rate, years);

          var html = '<div class="card"><div class="big-figure"><div class="amount">' +
            UI.moneyCents(pmt) + '</div><div class="label">Estimated new payment at ' +
            (rate * 100).toFixed(2) + "% over " + years + " years</div></div>" +
            '<table class="results-table"><tbody>';
          html += resultRow("Remaining balance", UI.money(balance));
          var cur = parseFloat(a.currentRate);
          if (!isNaN(cur) && cur > 0) {
            var curPmt = monthlyPayment(balance, cur / 100, years);
            html += resultRow("Payment at your current rate (" + cur.toFixed(2) + "%)", UI.moneyCents(curPmt) + "/mo");
            var diff = curPmt - pmt;
            html += resultRow(
              diff >= 0 ? "Potential monthly savings" : "Monthly increase at 4.00%",
              UI.moneyCents(Math.abs(diff)) + "/mo",
              diff >= 0 ? "rebate" : "total"
            );
            if (diff > 0) html += resultRow("Savings over a 5-year term", UI.money(diff * 60), "rebate");
          }
          html += "</tbody></table>";
          if (a.timing === "30days") {
            html += '<div class="note"><strong>Renewing within 30 days:</strong> don\'t sign your lender\'s first renewal letter \u2014 it\'s rarely their best rate. Even a quick comparison can save thousands.</div>';
          } else {
            html += '<div class="note"><strong>Good to know:</strong> you can lock in a renewal rate up to 120 days before your term ends \u2014 and switching lenders at renewal usually has no penalty.</div>';
          }
          html += '<p class="disclaimer">Estimates only \u2014 your actual renewal rate depends on your lender, term and profile.</p></div>';
          html += '<div class="card" id="wizard-lead"></div>';
          return html;
        },
        leadOptions: { heading: "Optional \u2014 want us to find your best renewal rate?", cta: "Get my renewal rates", interest: "renewal" },
      },
    ],

    buy: [
      chooserStep,
      {
        id: "buy-price",
        title: "Tell us about the home",
        render: function () {
          return (
            moneyField("price", "Target Purchase Price", "1,000,000") +
            toggleField("location", "Property Location", [
              { value: "toronto", label: "Toronto" },
              { value: "outside", label: "Outside Toronto" },
            ])
          );
        },
        validate: function (a) {
          var p = UI.parseMoney(a.price);
          if (isNaN(p) || p <= 0) return "Please enter a purchase price.";
          if (!a.location) return "Please choose a location.";
          return null;
        },
      },
      {
        id: "buy-down",
        title: "Your down payment",
        render: function (a) {
          var p = UI.parseMoney(a.price) || 0;
          var minPct = p > 0 ? Math.ceil((minDownPayment(p) / p) * 1000) / 10 : 5;
          return (
            suffixField("downPct", "Down Payment", "%", a.downPct || "20", 'min="0" max="100" step="0.5"',
              "legal minimum for this price: " + minPct + "%") +
            toggleField("ftb", "First-time home buyer?", [
              { value: "yes", label: "Yes" },
              { value: "no", label: "No" },
            ], "land transfer tax rebates may apply") +
            toggleField("newbuild", "Property type", [
              { value: "resale", label: "Resale" },
              { value: "new", label: "New Construction" },
            ])
          );
        },
        validate: function (a) {
          if (!a.ftb) return "Please tell us if you're a first-time buyer.";
          if (!a.newbuild) return "Please choose the property type.";
          return null;
        },
      },
      {
        id: "buy-terms",
        title: "Rate and amortization",
        render: function (a) {
          return (
            suffixField("rate", "Interest Rate", "%", a.rate || "4.00", 'min="0" max="20" step="0.05"') +
            '<div class="field"><label for="amort">Amortization</label><div class="control">' +
            '<select id="amort" data-answer="amort">' +
            [30, 25, 20, 15, 10, 5]
              .map(function (y) {
                var sel = String(a.amort || "30") === String(y) ? " selected" : "";
                return '<option value="' + y + '"' + sel + ">" + y + " years</option>";
              })
              .join("") +
            "</select></div></div>"
          );
        },
        validate: function () {
          return null;
        },
      },
      {
        id: "buy-results",
        title: "Your mortgage estimate",
        isResults: true,
        render: function (a) {
          var price = num("price", 0);
          var pct = parseFloat(a.downPct);
          if (isNaN(pct) || pct <= 0) pct = 20;
          var down = (price * pct) / 100;
          var minDown = minDownPayment(price);
          var usedMin = false;
          if (down < minDown - 0.5) {
            down = minDown;
            usedMin = true;
          }
          var rate = parseFloat(a.rate);
          rate = isNaN(rate) ? 0.04 : rate / 100;
          var years = parseInt(a.amort, 10) || 30;

          var cc = closingCosts({
            price: price,
            inToronto: a.location === "toronto",
            firstTimeBuyer: a.ftb === "yes",
            newConstruction: a.newbuild === "new",
            downPayment: down,
          });
          var pmt = monthlyPayment(cc.mortgageTotal, rate, years);
          var q = incomeToQualify(cc.mortgageTotal, rate, years);

          var html = '<div class="card"><div class="big-figure"><div class="amount">' +
            UI.moneyCents(pmt) + '</div><div class="label">Estimated monthly payment at ' +
            (rate * 100).toFixed(2) + "% over " + years + " years</div></div>";

          html += '<table class="results-table"><tbody>';
          html += resultRow("Down payment", UI.money(cc.downPayment), "", usedMin ? "raised to the legal minimum (" + ((minDown / price) * 100).toFixed(1) + "%)" : ((down / price) * 100).toFixed(1) + "%");
          if (cc.cmhcPremium > 0) html += resultRow("CMHC insurance premium", UI.money(cc.cmhcPremium), "", "added to mortgage");
          html += resultRow("Total mortgage", UI.money(cc.mortgageTotal), "total");
          html += "</tbody></table></div>";

          html += '<div class="card"><h3 style="color:var(--navy);margin-top:0">Closing costs</h3>';
          html += '<table class="results-table"><tbody>';
          html += resultRow("Ontario land transfer tax", UI.money(cc.onLtt));
          if (cc.torontoLtt > 0) html += resultRow("Toronto municipal land transfer tax", UI.money(cc.torontoLtt));
          if (cc.onRebate > 0) html += resultRow("First-time buyer rebate (Ontario)", "− " + UI.money(cc.onRebate), "rebate");
          if (cc.torontoRebate > 0) html += resultRow("First-time buyer rebate (Toronto)", "− " + UI.money(cc.torontoRebate), "rebate");
          if (cc.cmhcPst > 0) html += resultRow("Ontario PST on CMHC premium", UI.money(cc.cmhcPst));
          html += resultRow("Legal fees", UI.money(cc.legalFees), "", "estimate");
          html += resultRow("Title insurance", UI.money(cc.titleInsurance), "", "estimate");
          html += resultRow("Home inspection", UI.money(cc.homeInspection), "", "estimate");
          html += resultRow("Total closing costs", UI.money(cc.totalClosing), "total");
          html += resultRow("Total cash needed", UI.money(cc.totalCashNeeded), "total", "down payment + closing costs");
          html += "</tbody></table>";
          if (cc.hstApplies) {
            html += '<div class="note"><strong>HST on new construction:</strong> usually included in the builder\'s price with rebates assigned to the builder for primary residences; investors may need to front the rebate at closing.</div>';
          }
          html += "</div>";

          html += '<div class="card"><h3 style="color:var(--navy);margin-top:0">Income needed to qualify</h3>';
          html += '<p style="color:var(--muted);font-size:0.9rem;margin-top:0">Assuming no other debts, $500/mo property taxes and $250/mo heat &amp; insurance.</p>';
          html += '<table class="results-table"><tbody>';
          html += resultRow("At your rate (" + (rate * 100).toFixed(2) + "%)", UI.money(q.atContract) + "/yr");
          html += resultRow("At the stress-test rate (" + (stressTestRate(rate) * 100).toFixed(2) + "%)", UI.money(q.atStressTest) + "/yr", "total", "what lenders must use");
          html += "</tbody></table>";
          html += '<p class="disclaimer">Estimates only — residential rates. Not financial advice.</p></div>';

          html += '<div class="card" id="wizard-lead"></div>';
          return html;
        },
        leadOptions: { heading: "Optional — want help getting pre-approved?", cta: "Get pre-approved", interest: "new-mortgage" },
      },
    ],

    refi: [
      chooserStep,
      {
        id: "refi-value",
        title: "Enter your information",
        sub: "We need the below information to determine your refinance options.",
        render: function () {
          return (
            moneyField("homeValue", "Home Value", "1,000,000", "current fair market value") +
            moneyField("owing", "Mortgage Amount Owing", "550,000")
          );
        },
        validate: function (a) {
          var v = UI.parseMoney(a.homeValue);
          var o = UI.parseMoney(a.owing);
          if (isNaN(v) || v <= 0) return "Please enter your home's value.";
          if (isNaN(o) || o < 0) return "Please enter how much you still owe.";
          if (o > v) return "The amount owing can't be more than the home value.";
          return null;
        },
      },
      {
        id: "refi-results",
        title: "Your refinance estimate",
        isResults: true,
        render: function () {
          var value = num("homeValue", 0);
          var owing = num("owing", 0);
          var maxLoan = value * 0.8;
          var equity = Math.max(maxLoan - owing, 0);
          var rate = 0.04;
          var years = 25;
          var newPmt = monthlyPayment(maxLoan, rate, years);

          var html = '<div class="card"><div class="big-figure"><div class="amount">' +
            UI.money(equity) + '</div><div class="label">Equity you could unlock (up to 80% of your home\'s value)</div></div>';
          html += '<table class="results-table"><tbody>';
          html += resultRow("Home value", UI.money(value));
          html += resultRow("Maximum new mortgage (80% LTV)", UI.money(maxLoan));
          html += resultRow("Current mortgage owing", "− " + UI.money(owing));
          html += resultRow("Available equity", UI.money(equity), "total");
          html += resultRow("Payment if you borrow the maximum", UI.moneyCents(newPmt) + "/mo", "", (rate * 100).toFixed(2) + "% over " + years + " years");
          html += "</tbody></table>";
          html += '<p class="disclaimer">Estimates only — refinancing availability depends on your income, credit and lender.</p></div>';
          html += '<div class="card" id="wizard-lead"></div>';
          return html;
        },
        leadOptions: { heading: "Optional — want to discuss your refinance options?", cta: "Discuss my options", interest: "refinance" },
      },
    ],

    learn: [
      chooserStep,
      {
        id: "learn-topic",
        title: "What do you want to learn about?",
        noNav: true,
        render: function () {
          var topics = [
            { value: "closing", icon: "\ud83e\uddfe", label: "Closing costs" },
            { value: "payments", icon: "\ud83d\udcc5", label: "Monthly payments" },
            { value: "qualify", icon: "\u2705", label: "How much I qualify for" },
            { value: "process", icon: "\ud83d\uddfa\ufe0f", label: "The home-buying process" },
          ];
          return (
            '<div class="option-list">' +
            topics
              .map(function (t) {
                return (
                  '<button type="button" class="option-card" data-choice="topic" data-value="' + t.value + '">' +
                  '<span class="icon">' + t.icon + "</span>" + t.label + "</button>"
                );
              })
              .join("") +
            "</div>"
          );
        },
      },
      {
        id: "learn-results",
        title: "The essentials",
        isResults: true,
        render: function (a) {
          var ex30 = monthlyPayment(800000, 0.04, 30);
          var ex25 = monthlyPayment(800000, 0.04, 25);
          var exIncome = incomeToQualify(800000, 0.04, 30);
          var topics = {
            closing: {
              intro: "Closing costs are what you pay on top of your down payment \u2014 in Ontario, plan for roughly 1.5\u20134% of the purchase price.",
              points: [
                "<strong>Land transfer tax</strong> is the biggest one \u2014 and Toronto properties pay it twice (provincial + municipal). On a $1M home that\'s $16,475 + $16,475.",
                "<strong>First-time buyers</strong> get rebates: up to $4,000 (Ontario) plus $4,475 (Toronto).",
                "<strong>Legal fees</strong> run about $2,000; title insurance and a home inspection add roughly $500 each.",
                "<strong>Under 20% down?</strong> CMHC insurance is added to your mortgage, but Ontario\'s 8% tax on the premium is due in cash at closing.",
                "<strong>Resale homes are HST-exempt.</strong> New construction usually includes HST in the builder\'s price.",
              ],
              link: "/closing-costs",
              linkLabel: "Calculate my exact closing costs",
            },
            payments: {
              intro: "Your payment depends on three things: how much you borrow, the interest rate, and the amortization (how long you take to pay it off).",
              points: [
                "Example: an $800,000 mortgage at 4% costs <strong>" + UI.moneyCents(ex30) + "/mo</strong> over 30 years, or " + UI.moneyCents(ex25) + "/mo over 25 years.",
                "A longer amortization lowers the monthly payment but adds a lot of interest over the life of the loan.",
                "Canadian fixed-rate mortgages compound <strong>semi-annually</strong>, so the true monthly rate is slightly lower than rate \u00f7 12.",
                "Early payments are mostly interest; later ones are mostly principal. Our calculator shows the year-by-year split.",
              ],
              link: "/payment-calculator",
              linkLabel: "Calculate my payment",
            },
            qualify: {
              intro: "Lenders decide your maximum mortgage from your gross income, your debts and the federal stress test.",
              points: [
                "Housing costs (mortgage payment + property tax + heat) are capped at roughly <strong>39% of gross income</strong>.",
                "You must qualify at the <strong>stress-test rate</strong> \u2014 your rate + 2%, or 5.25%, whichever is higher \u2014 even though you pay your actual rate.",
                "Example: an $800,000 mortgage at 4% needs about <strong>" + UI.money(exIncome.atStressTest) + "/yr</strong> of household income at the stress-test rate.",
                "To qualify for more: a bigger down payment, a longer amortization, paying down other debts, or adding a co-borrower.",
              ],
              link: "/payment-calculator",
              linkLabel: "See the income I\'d need",
            },
            process: {
              intro: "Buying a home in Ontario usually follows five steps \u2014 and the first one is free.",
              points: [
                "<strong>1. Get pre-approved</strong> \u2014 free, locks a rate for ~120 days, and tells you your real budget.",
                "<strong>2. Shop with confidence</strong> \u2014 you know your maximum price and monthly payment.",
                "<strong>3. Make an offer</strong> \u2014 usually with financing and inspection conditions to protect you.",
                "<strong>4. Satisfy conditions</strong> \u2014 finalize the mortgage and inspection, typically within 5\u201310 days.",
                "<strong>5. Close</strong> \u2014 your lawyer transfers funds, pays the land transfer tax and registers title. Budget 1.5\u20134% of the price for closing costs.",
              ],
              link: "/closing-costs",
              linkLabel: "Start with my numbers",
            },
          };
          var t = topics[a.topic] || topics.closing;
          return (
            '<div class="card"><p style="font-size:1.05rem;margin-top:0">' + t.intro + "</p>" +
            '<ul style="padding-left:1.2rem;line-height:1.7;margin:0.8rem 0 1.2rem">' +
            t.points
              .map(function (pt) {
                return '<li style="margin-bottom:0.5rem">' + pt + "</li>";
              })
              .join("") +
            "</ul>" +
            '<a class="btn btn-primary btn-block" href="' + t.link + '">' + t.linkLabel + "</a></div>" +
            '<div class="card" id="wizard-lead"></div>'
          );
        },
        leadOptions: { heading: "Optional \u2014 have a question? Ask us anything", cta: "Ask us a question", interest: "learn" },
      },
    ],
  };

  /* ---------- rendering ---------- */

  function currentFlow() {
    return state.path ? FLOWS[state.path] : [chooserStep];
  }

  function renderIndicator() {
    var flow = currentFlow();
    var total = state.path ? flow.length : 5; // show 5 placeholder dots before a path is chosen
    var html = "";
    for (var i = 0; i < total; i++) {
      var cls = "step";
      if (i < state.stepIndex) cls += " done";
      else if (i === state.stepIndex) cls += " active";
      html += '<div class="' + cls + '">' + (i + 1) + "</div>";
      if (i < total - 1) html += '<div class="step-line"></div>';
    }
    stepsEl.innerHTML = html;
  }

  function collectAnswers() {
    container.querySelectorAll("[data-answer]").forEach(function (el) {
      state.answers[el.dataset.answer] = el.value;
    });
    // toggles store their value on render via attachToggle below
  }

  function renderStep() {
    var flow = currentFlow();
    var step = flow[Math.min(state.stepIndex, flow.length - 1)];

    var html = '<div class="wizard-body"><h2>' + step.title + "</h2>";
    if (step.sub) html += '<p class="step-sub">' + step.sub + "</p>";
    html += step.render(state.answers);
    if (!step.noNav && !step.isResults) {
      html += '<p class="error-msg" id="wizard-error" aria-live="polite"></p>';
    }
    html += "</div>";

    html += '<div class="wizard-nav">';
    html += state.stepIndex > 0
      ? '<button type="button" class="btn btn-ghost" id="wizard-back">← Back</button>'
      : "<span></span>";
    if (!step.noNav && !step.isResults) {
      html += '<button type="button" class="btn btn-primary" id="wizard-next">Continue</button>';
    } else if (step.isResults) {
      html += '<button type="button" class="btn btn-ghost" id="wizard-restart">Start over</button>';
    }
    html += "</div>";

    container.innerHTML = html;
    renderIndicator();

    // Wire chooser cards
    container.querySelectorAll(".option-card[data-path]").forEach(function (card) {
      card.addEventListener("click", function () {
        state.path = card.dataset.path;
        state.stepIndex = 1;
        state.answers = {};
        renderStep();
      });
    });

    // Option cards that record an answer and advance (e.g. Learn topics)
    container.querySelectorAll(".option-card[data-choice]").forEach(function (card) {
      card.addEventListener("click", function () {
        state.answers[card.dataset.choice] = card.dataset.value;
        state.stepIndex++;
        renderStep();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });

    // Wire money masks
    container.querySelectorAll('input[inputmode="numeric"]').forEach(function (input) {
      UI.attachMoneyMask(input);
      if (state.answers[input.dataset.answer]) input.value = state.answers[input.dataset.answer];
    });

    // Restore plain input values on back-navigation
    container.querySelectorAll("[data-answer]").forEach(function (el) {
      var saved = state.answers[el.dataset.answer];
      if (saved != null && saved !== "" && !el.value) el.value = saved;
    });

    // Wire toggles: store selection directly into answers
    container.querySelectorAll("[data-answer-toggle]").forEach(function (el) {
      var key = el.dataset.answerToggle;
      UI.attachToggle(
        el,
        function (value) {
          state.answers[key] = value;
          var err = document.getElementById("wizard-error");
          if (err) err.textContent = "";
        },
        state.answers[key] || null
      );
    });

    // Nav buttons
    var back = document.getElementById("wizard-back");
    if (back)
      back.addEventListener("click", function () {
        collectAnswers();
        if (state.stepIndex <= 1) {
          state.path = null;
          state.stepIndex = 0;
        } else {
          state.stepIndex--;
        }
        renderStep();
      });

    var next = document.getElementById("wizard-next");
    if (next)
      next.addEventListener("click", function () {
        collectAnswers();
        var error = step.validate ? step.validate(state.answers) : null;
        var errEl = document.getElementById("wizard-error");
        if (error) {
          if (errEl) errEl.textContent = error;
          return;
        }
        state.stepIndex++;
        renderStep();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });

    var restart = document.getElementById("wizard-restart");
    if (restart)
      restart.addEventListener("click", function () {
        state = { path: null, stepIndex: 0, answers: {} };
        renderStep();
      });

    // Lead form on results steps — include the visitor's answers so we learn what they want
    if (step.isResults) {
      var leadEl = document.getElementById("wizard-lead");
      if (leadEl) {
        var opts = Object.assign({}, step.leadOptions, {
          context: Object.assign({ path: state.path }, state.answers),
        });
        Lead.renderForm(leadEl, opts);
      }
    }
  }

  renderStep();
})();
