// main.js — students will add JavaScript here as features are built

document.addEventListener("DOMContentLoaded", function () {
    var autoDismissEls = document.querySelectorAll("[data-auto-dismiss='true']");
    autoDismissEls.forEach(function (el) {
        setTimeout(function () {
            el.style.transition = "opacity 0.4s ease";
            el.style.opacity = "0";
            setTimeout(function () {
                el.remove();
            }, 400);
        }, 3500);
    });
});
