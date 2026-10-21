// Mobile nav toggle + htmx navigation polish. Vanilla JS.
(function () {
    function initNav() {
        var toggle = document.getElementById("nav-toggle");
        var nav = document.getElementById("site-nav");
        if (toggle && nav) {
            toggle.addEventListener("click", function () {
                var open = nav.classList.toggle("open");
                toggle.setAttribute("aria-expanded", open ? "true" : "false");
            });
        }
        markActive();
    }

    // Highlight the nav link matching the current path.
    function markActive() {
        var nav = document.getElementById("site-nav");
        if (!nav) return;
        var path = window.location.pathname.replace(/\/+$/, "") || "/";
        nav.querySelectorAll("a").forEach(function (a) {
            var href = a.getAttribute("href").replace(/\/+$/, "") || "/";
            if (href === path) a.setAttribute("aria-current", "page");
            else a.removeAttribute("aria-current");
        });
    }

    document.addEventListener("DOMContentLoaded", initNav);

    // After an htmx swap: close the mobile menu, update active link, scroll top.
    document.body && document.body.addEventListener("htmx:afterSwap", afterSwap);
    document.addEventListener("htmx:afterSwap", afterSwap);
    function afterSwap() {
        var nav = document.getElementById("site-nav");
        var toggle = document.getElementById("nav-toggle");
        if (nav) nav.classList.remove("open");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
        markActive();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
})();
