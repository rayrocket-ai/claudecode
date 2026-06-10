/* RayRocket Studio — landing page interactions */

// ── Reveal on scroll ──────────────────────────────────────────────────────
const observer = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) {
      e.target.classList.add("visible");
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

// ── Pricing toggle (one-time vs subscription) — tours pages only ──────────
document.querySelectorAll(".toggle-opt").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".toggle-opt").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const sub = btn.dataset.mode === "sub";
    document.getElementById("pricing-once").classList.toggle("hidden", sub);
    document.getElementById("pricing-sub").classList.toggle("hidden", !sub);
  });
});

// ── Tour order helper ─────────────────────────────────────────────────────
function openOrder(pkg, rush = false) {
  document.getElementById("order-package").value = pkg;
  document.getElementById("rush-box").checked = rush;
  const panel = document.getElementById("order-panel");
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  setTimeout(() => panel.querySelector('input[name="address"]').focus({ preventScroll: true }), 600);
}

// ── Waitlist modal ────────────────────────────────────────────────────────
function openWaitlist(service, plan) {
  document.getElementById("waitlist-service").value = service;
  document.getElementById("waitlist-title").textContent =
    "Join early access" + (plan ? " — " + plan : "");
  document.getElementById("waitlist-notes").value = plan ? "Interested in: " + plan : "";
  document.getElementById("waitlist-modal").classList.add("open");
}
function closeWaitlist() {
  document.getElementById("waitlist-modal").classList.remove("open");
}
document.getElementById("waitlist-modal").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) closeWaitlist();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeWaitlist();
});

// ── Receptionist scope estimator ──────────────────────────────────────────
// Maps the realtor's selections to a recommended plan, monthly price, and a
// realistic setup-effort estimate shown live in the estimate card.
const PLANS = {
  core: {
    name: "Core", price: 299, setupFee: 99,
    desc: "24/7 answering with message-taking and instant text-back to callers.",
  },
  plus: {
    name: "Plus", price: 499, setupFee: 199,
    desc: "Answering plus lead qualification scripts and live showing bookings on your calendar.",
  },
  concierge: {
    name: "Concierge", price: 899, setupFee: 299,
    desc: "The full front office: qualification, bookings, CRM logging, and automated follow-up sequences.",
  },
};

function estimate() {
  if (!document.getElementById("recep-form")) return; // not on this page
  const tasks = [...document.querySelectorAll('input[name="tasks"]:checked')].map((i) => i.value);
  const volume = document.querySelector('input[name="call_volume"]:checked').value;
  const coverage = document.querySelector('input[name="coverage"]:checked').value;

  // Plan selection: CRM/follow-up work or 24/7 + heavy usage → Concierge;
  // bookings or qualification → Plus; otherwise Core.
  let plan = "core";
  const heavy = tasks.includes("crm_updates") || tasks.includes("follow_up");
  const mid = tasks.includes("book_showings") || tasks.includes("qualify_leads");
  if (heavy || (coverage === "always" && mid)) plan = "concierge";
  else if (mid || tasks.length >= 3) plan = "plus";

  // Setup effort scales with how much custom scripting/integration is needed.
  let setupDays = 3;
  if (mid) setupDays += 2;
  if (heavy) setupDays += 3;
  if (volume === "high") setupDays += 1;

  const workItems = ["Greeting script, your service areas, transfer rules"];
  if (tasks.includes("qualify_leads")) workItems.push("lead qualification questions");
  if (tasks.includes("book_showings")) workItems.push("calendar connection");
  if (tasks.includes("crm_updates")) workItems.push("CRM integration");
  if (tasks.includes("follow_up")) workItems.push("follow-up sequence design");
  if (tasks.includes("faq")) workItems.push("listing FAQ training");

  const p = PLANS[plan];
  const card = document.getElementById("estimate-card");
  card.style.opacity = "0.4";
  setTimeout(() => {
    document.getElementById("est-plan").textContent = `${p.name} — $${p.price}/mo`;
    document.getElementById("est-desc").textContent = p.desc;
    document.getElementById("est-setup").textContent = `~${setupDays} business days`;
    document.getElementById("est-work").textContent =
      workItems.length > 1
        ? workItems[0].split(",")[0] + " + " + workItems.slice(1).join(", ")
        : workItems[0];
    document.getElementById("est-price").textContent =
      `$${p.price}/mo + $${p.setupFee} one-time setup`;
    document.getElementById("recommended-plan-input").value = plan;
    document.querySelectorAll(".rung").forEach((r) =>
      r.classList.toggle("active", r.dataset.plan === plan));
    card.style.opacity = "1";
  }, 160);
}

// Initialize estimate + ladder highlight on load
estimate();
