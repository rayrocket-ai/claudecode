/* ui.js — shared DOM helpers: currency formatting/parsing, toggles, live recalc. */

var UI = (function () {
  var cad = new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency: "CAD",
    maximumFractionDigits: 0,
  });
  var cadCents = new Intl.NumberFormat("en-CA", {
    style: "currency",
    currency: "CAD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  /** "$1,234,567" — rounded to whole dollars for display. */
  function money(n) {
    return cad.format(Math.round(n || 0));
  }

  /** "$1,234.56" — with cents, for monthly payments. */
  function moneyCents(n) {
    return cadCents.format(n || 0);
  }

  /** Parse "1,000,000", "$1M", "950k", "  1000000 " → number (or NaN). */
  function parseMoney(str) {
    if (typeof str === "number") return str;
    if (!str) return NaN;
    var s = String(str).trim().toLowerCase().replace(/[$,\s]/g, "");
    var mult = 1;
    if (s.endsWith("m")) {
      mult = 1000000;
      s = s.slice(0, -1);
    } else if (s.endsWith("k")) {
      mult = 1000;
      s = s.slice(0, -1);
    }
    var n = parseFloat(s);
    return isNaN(n) ? NaN : n * mult;
  }

  /** Add thousands separators to a money input as the user types. */
  function attachMoneyMask(input) {
    input.addEventListener("input", function () {
      var raw = input.value.replace(/[^0-9.]/g, "");
      if (raw === "") {
        return;
      }
      var parts = raw.split(".");
      var intPart = parts[0].replace(/^0+(?=\d)/, "");
      var formatted = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      if (parts.length > 1) formatted += "." + parts[1].slice(0, 2);
      if (formatted !== input.value) {
        var pos = input.selectionStart;
        var before = input.value.length;
        input.value = formatted;
        var delta = formatted.length - before;
        try {
          input.setSelectionRange(pos + delta, pos + delta);
        } catch (e) {
          /* type=number inputs don't support selection — ignore */
        }
      }
    });
  }

  /**
   * Wire a segmented .toggle element. Buttons need data-value attrs.
   * onChange(value) fires on click; returns { get, set }.
   */
  function attachToggle(el, onChange, initial) {
    var buttons = Array.prototype.slice.call(el.querySelectorAll("button"));
    var current = initial != null ? String(initial) : null;

    function set(value, fire) {
      current = String(value);
      buttons.forEach(function (b) {
        b.classList.toggle("on", b.dataset.value === current);
      });
      if (fire !== false && onChange) onChange(current);
    }

    buttons.forEach(function (b) {
      b.addEventListener("click", function (ev) {
        ev.preventDefault();
        set(b.dataset.value);
      });
    });

    if (current != null) set(current, false);
    return {
      get: function () {
        return current;
      },
      set: set,
    };
  }

  /** Call fn on 'input' events from any of the elements, plus once now. */
  function liveRecalc(elements, fn) {
    elements.forEach(function (el) {
      if (el) el.addEventListener("input", fn);
    });
    fn();
  }

  return {
    money: money,
    moneyCents: moneyCents,
    parseMoney: parseMoney,
    attachMoneyMask: attachMoneyMask,
    attachToggle: attachToggle,
    liveRecalc: liveRecalc,
  };
})();
