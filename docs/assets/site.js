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

  // journey timeline filters
  var chips = document.querySelectorAll(".filters .chip");
  if (chips.length) {
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var f = chip.getAttribute("data-filter");
        chips.forEach(function (c) { c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
        document.querySelectorAll(".tl-item").forEach(function (it) {
          it.hidden = !(f === "all" || it.getAttribute("data-cat") === f);
        });
        document.querySelectorAll(".tl-year").forEach(function (y) {
          y.hidden = !y.querySelector(".tl-item:not([hidden])");
        });
      });
    });
  }

  // contact form: sends through Formspree; until a Formspree ID is set, opens the email app instead
  var VI = document.documentElement.lang === "vi";
  document.querySelectorAll("form.contact-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var note = form.querySelector(".form-status");
      var hp = form.querySelector("[name=_gotcha]");
      if (hp && hp.value) return; // spam trap
      var name = form.querySelector("[name=name]").value.trim();
      var email = form.querySelector("[name=email]").value.trim();
      var msg = form.querySelector("[name=message]").value.trim();
      var topicEl = form.querySelector("[name=topic]");
      var topic = topicEl ? topicEl.value : "";
      var action = form.getAttribute("action") || "";
      if (action.indexOf("YOUR_FORM_ID") === -1 && window.fetch) {
        var btn = form.querySelector("button[type=submit]");
        if (btn) btn.disabled = true;
        if (note) note.textContent = VI ? "Đang gửi…" : "Sending…";
        fetch(action, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
          .then(function (r) {
            if (!r.ok) throw new Error("send failed");
            form.reset();
            if (note) note.textContent = VI ? "Cảm ơn bạn. Tin nhắn đã được gửi đến contact@cvcec.org." : "Thank you. Your message has been sent to contact@cvcec.org.";
          })
          .catch(function () {
            if (note) note.textContent = VI ? "Rất tiếc, chưa gửi được tin nhắn. Xin email trực tiếp tới contact@cvcec.org." : "Sorry, the message could not be sent. Please email contact@cvcec.org.";
          })
          .then(function () { if (btn) btn.disabled = false; });
        return;
      }
      var subject = "CVCEC website" + (topic ? ": " + topic : "") + (name ? " – " + name : "");
      var body = msg + "\n\n— " + name + (email ? " (" + email + ")" : "");
      window.location.href = "mailto:contact@cvcec.org?subject=" +
        encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
      if (note) note.textContent = VI ? "Ứng dụng email của bạn sẽ mở kèm nội dung tin nhắn. Nếu không, xin viết tới contact@cvcec.org." : "Your email app should open with your message. If it doesn’t, please write to contact@cvcec.org.";
    });
  });

  // gentle count-up for the numbers in stats bands
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce && "IntersectionObserver" in window) {
    var nums = [];
    document.querySelectorAll(".stat .num, .num-card .n, .prog-card .big").forEach(function (el) {
      var node = el.firstChild;
      if (!node || node.nodeType !== 3) return;
      var m = node.nodeValue.match(/^(\s*)(\d[\d,]*)(.*)$/);
      if (!m) return;
      var target = parseInt(m[2].replace(/,/g, ""), 10);
      if (!(target > 9) || target >= 1900 && target <= 2100) return; // skip small numbers and years
      nums.push({ node: node, pre: m[1], post: m[3], target: target, comma: m[2].indexOf(",") > -1 });
    });
    var fmt = function (n, comma) { return comma ? n.toLocaleString("en-CA") : String(n); };
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        nums.forEach(function (o) {
          if (o.node.parentNode !== en.target) return;
          var t0 = null;
          var step = function (ts) {
            if (!t0) t0 = ts;
            var k = Math.min(1, (ts - t0) / 1200);
            var v = Math.round(o.target * (1 - Math.pow(1 - k, 3)));
            o.node.nodeValue = o.pre + fmt(v, o.comma) + o.post;
            if (k < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        });
      });
    }, { threshold: 0.4 });
    nums.forEach(function (o) { io.observe(o.node.parentNode); });
  }
})();
