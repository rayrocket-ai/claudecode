/*
 * GSAP timelines for the composition.
 *
 * Hyperframes seeks a hidden Chromium page frame-by-frame and captures each
 * frame, so timelines must be deterministic. That means:
 *   - No `Date.now()`, no `Math.random()`, no timers.
 *   - Every property change goes through a GSAP timeline you seek by time.
 *
 * The engine drives GSAP by setting the global timeline's time; we build
 * timelines here and hand them to `window.__hf__` if available.
 */

(function () {
  const tl = gsap.timeline({ paused: true });

  // --- Title card (0.5s - 4.5s) ---
  tl.to(
    "#title-card .title",
    { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" },
    0.5,
  );
  tl.from(
    "#title-card .title",
    { y: 60, duration: 0.6, ease: "power3.out" },
    0.5,
  );
  tl.to(
    "#title-card .subtitle",
    { opacity: 1, duration: 0.5, ease: "power2.out" },
    0.9,
  );
  tl.to(
    "#title-card",
    { opacity: 0, duration: 0.4, ease: "power2.in" },
    4.0,
  );

  // --- Stat reveal (4.5s - 9s) ---
  const statValue = document.querySelector(".stat-value");
  const counterFrom = parseFloat(statValue.dataset.counterFrom || "0");
  const counterTo = parseFloat(statValue.dataset.counterTo || "100");
  const counterObj = { v: counterFrom };

  tl.fromTo(
    "#stat",
    { opacity: 0, scale: 0.92 },
    { opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" },
    4.5,
  );
  tl.to(
    counterObj,
    {
      v: counterTo,
      duration: 1.8,
      ease: "power3.out",
      onUpdate: () => {
        statValue.textContent = Math.round(counterObj.v).toString();
      },
    },
    4.5,
  );
  tl.to(
    ".stat-label",
    { opacity: 1, duration: 0.6, ease: "power2.out" },
    5.8,
  );
  tl.to(
    "#stat",
    { opacity: 0, duration: 0.4, ease: "power2.in" },
    8.6,
  );

  // Expose for Hyperframes' seek-driven renderer.
  // @ts-ignore
  window.__hyperframesTimeline = tl;

  // In browser preview, auto-play so you can eyeball it without the CLI.
  if (!window.__HYPERFRAMES_RENDER__) {
    tl.play();
  }
})();
