/* lead.js — lead-capture form handling.
 * POSTs to SITE_CONFIG.FORM_ENDPOINT (Formspree-style) when configured;
 * otherwise falls back to a prefilled mailto: link.
 */

var Lead = (function () {
  /** Render a lead form into container. context = extra fields (e.g. wizard answers). */
  function renderForm(container, options) {
    var opts = options || {};
    var cta = opts.cta || "Contact me";
    var heading = opts.heading || "Want expert help with this?";

    container.innerHTML =
      '<h3 style="color:var(--navy);margin-top:0">' +
      heading +
      "</h3>" +
      '<form class="lead-form" novalidate>' +
      '<div class="field"><label for="lead-name">Name</label>' +
      '<div class="control"><input id="lead-name" name="name" type="text" autocomplete="name" required></div></div>' +
      '<div class="field"><label for="lead-email">Email</label>' +
      '<div class="control"><input id="lead-email" name="email" type="email" autocomplete="email" required></div></div>' +
      '<div class="field"><label for="lead-phone">Phone <small>optional</small></label>' +
      '<div class="control"><input id="lead-phone" name="phone" type="tel" autocomplete="tel"></div></div>' +
      '<p class="error-msg" aria-live="polite"></p>' +
      '<button type="submit" class="btn btn-accent btn-block">' +
      cta +
      "</button>" +
      "</form>";

    var form = container.querySelector("form");
    var errorEl = container.querySelector(".error-msg");

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      errorEl.textContent = "";

      var name = form.querySelector("#lead-name").value.trim();
      var email = form.querySelector("#lead-email").value.trim();
      var phone = form.querySelector("#lead-phone").value.trim();

      if (!name || !email || email.indexOf("@") < 0) {
        errorEl.textContent = "Please enter your name and a valid email.";
        return;
      }

      var payload = {
        name: name,
        email: email,
        phone: phone,
        page: location.pathname,
        interest: opts.interest || "general",
        details: opts.context || {},
      };

      var endpoint = (window.SITE_CONFIG && window.SITE_CONFIG.FORM_ENDPOINT) || "";
      if (endpoint) {
        var btn = form.querySelector("button[type=submit]");
        btn.disabled = true;
        btn.textContent = "Sending…";
        fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(payload),
        })
          .then(function (res) {
            if (!res.ok) throw new Error("HTTP " + res.status);
            showThanks(container);
          })
          .catch(function () {
            btn.disabled = false;
            btn.textContent = cta;
            errorEl.textContent =
              "Something went wrong sending your request — please try again or email us directly.";
          });
      } else {
        // No endpoint configured: open the visitor's mail client with a prefilled message.
        var to = (window.SITE_CONFIG && window.SITE_CONFIG.CONTACT_EMAIL) || "";
        var subject = "Mortgage inquiry — " + (opts.interest || "general");
        var lines = [
          "Name: " + name,
          "Email: " + email,
          "Phone: " + (phone || "n/a"),
          "Interested in: " + (opts.interest || "general"),
          "",
          "Details:",
          JSON.stringify(opts.context || {}, null, 2),
        ];
        location.href =
          "mailto:" +
          encodeURIComponent(to) +
          "?subject=" +
          encodeURIComponent(subject) +
          "&body=" +
          encodeURIComponent(lines.join("\n"));
        showThanks(container);
      }
    });
  }

  function showThanks(container) {
    container.innerHTML =
      '<h3 style="color:var(--navy);margin-top:0">Thank you!</h3>' +
      "<p>We received your request and will get back to you shortly.</p>";
  }

  return { renderForm: renderForm };
})();
