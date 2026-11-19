// CVCEC website: menu, sub-menus, photo lightbox, email form
(function () {
  "use strict";

  // mobile menu
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // sub-menus (click/tap and keyboard)
  document.querySelectorAll(".sub-toggle").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var li = btn.parentElement;
      var open = li.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      document.querySelectorAll(".has-sub.open").forEach(function (other) {
        if (other !== li) {
          other.classList.remove("open");
          other.querySelector(".sub-toggle").setAttribute("aria-expanded", "false");
        }
      });
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.querySelectorAll(".has-sub.open").forEach(function (li) {
        li.classList.remove("open");
        li.querySelector(".sub-toggle").setAttribute("aria-expanded", "false");
      });
    }
  });

  // photo lightbox for .gallery links
  var box = document.querySelector(".lightbox");
  if (box) {
    var img = box.querySelector("img");
    var cap = box.querySelector("figcaption");
    var set = [], index = 0, lastFocus = null;
    var show = function (i) {
      index = (i + set.length) % set.length;
      var a = set[index];
      img.src = a.getAttribute("href");
      img.alt = a.querySelector("img") ? a.querySelector("img").alt : "";
      cap.textContent = a.getAttribute("data-caption") || img.alt || "";
    };
    var close = function () {
      box.hidden = true;
      img.removeAttribute("src");
      document.body.style.overflow = "";
      if (lastFocus) lastFocus.focus();
    };
    document.querySelectorAll(".gallery").forEach(function (g) {
      var links = Array.prototype.slice.call(g.querySelectorAll("a"));
      links.forEach(function (a, i) {
        a.addEventListener("click", function (e) {
          e.preventDefault();
          set = links; lastFocus = a;
          show(i);
          box.hidden = false;
          document.body.style.overflow = "hidden";
          box.querySelector(".lb-close").focus();
        });
      });
    });
    box.querySelector(".lb-close").addEventListener("click", close);
    box.querySelector(".lb-prev").addEventListener("click", function () { show(index - 1); });
    box.querySelector(".lb-next").addEventListener("click", function () { show(index + 1); });
    box.addEventListener("click", function (e) { if (e.target === box) close(); });
    document.addEventListener("keydown", function (e) {
      if (box.hidden) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") show(index - 1);
      if (e.key === "ArrowRight") show(index + 1);
    });
  }

  // contact form: opens the visitor's email app with the message filled in
  document.querySelectorAll("form.contact-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = form.querySelector("[name=name]").value.trim();
      var email = form.querySelector("[name=email]").value.trim();
      var msg = form.querySelector("[name=message]").value.trim();
      var subject = "Message from the CVCEC website" + (name ? " – " + name : "");
      var body = msg + "\n\n— " + name + (email ? " (" + email + ")" : "");
      window.location.href = "mailto:contact@cvcec.org?subject=" +
        encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
      var note = form.querySelector(".form-status");
      if (note) note.textContent = "Your email app should open with your message. If it doesn’t, please write to contact@cvcec.org.";
    });
  });
})();
