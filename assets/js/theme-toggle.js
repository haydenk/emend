// Theme button: cycles auto -> light -> dark. "auto" means no stored choice, so
// the OS preference applies. A stored choice is applied before first paint by
// the inline script in layouts/_partials/head.html; this file only wires the
// button, so it is safe to load deferred.
(function () {
  var root = document.documentElement;
  var button = document.querySelector(".theme-toggle");
  if (!button) return;

  var modes = ["auto", "light", "dark"];

  function current() {
    var forced = root.getAttribute("data-theme");
    return forced === "light" || forced === "dark" ? forced : "auto";
  }

  // The icon is switched by CSS; the text names the current mode.
  function sync() {
    var label = "Theme: " + current() + " mode";
    button.setAttribute("aria-label", label);
    button.title = label;
  }

  button.addEventListener("click", function () {
    var next = modes[(modes.indexOf(current()) + 1) % modes.length];
    try {
      if (next === "auto") {
        root.removeAttribute("data-theme");
        localStorage.removeItem("theme");
      } else {
        root.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
      }
    } catch (e) {
      // Storage blocked: the choice still applies to this page view.
    }
    sync();
  });

  // A page restored from the back/forward cache still shows the theme it had
  // when it was left: re-apply the stored choice.
  window.addEventListener("pageshow", function (event) {
    if (!event.persisted) return;
    var stored = null;
    try {
      stored = localStorage.getItem("theme");
    } catch (e) {}
    if (stored === "light" || stored === "dark") {
      root.setAttribute("data-theme", stored);
    } else {
      root.removeAttribute("data-theme");
    }
    sync();
  });

  sync();
  button.hidden = false;
})();
