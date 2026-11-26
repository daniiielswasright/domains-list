// Adds the "what it does" note and the safe-to-block marker under each
// domain in the site's domain lists. The data comes from _data/domains.csv
// (served as assets/data/notes.json), so the pages themselves stay plain
// lists and search keeps reading them as before.
(function () {
  "use strict";

  var lists = Array.prototype.filter.call(
    document.querySelectorAll("ol.domain-list"),
    function (ol) { return !ol.closest("details") && ol.id !== "search-results"; }
  );
  if (!lists.length) return;

  var LABELS = {
    safe: "Safe to block",
    partial: "Blocking turns off one feature",
    breaks: "Blocking breaks the app or site"
  };

  var script = document.currentScript || document.querySelector('script[src*="notes.js"]');
  var url = new URL("../data/notes.json", script.src).href;

  fetch(url).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
    if (!data) return;
    var shown = false;
    lists.forEach(function (ol) {
      ol.querySelectorAll(":scope > li").forEach(function (li) {
        if (li.children.length) return; // already decorated or not a plain domain
        var d = li.textContent.trim().toLowerCase();
        var info = data[d];
        if (!info) return;
        var note = info[0], block = info[1];
        if (block && LABELS[block]) {
          var dot = document.createElement("span");
          dot.className = "block-dot block-" + block;
          dot.title = LABELS[block];
          dot.setAttribute("aria-label", LABELS[block]);
          dot.setAttribute("role", "img");
          li.insertBefore(dot, li.firstChild);
          shown = true;
        }
        if (note) {
          var n = document.createElement("span");
          n.className = "domain-note";
          n.textContent = note;
          li.appendChild(n);
          shown = true;
        }
      });
    });
    if (shown) lists[0].parentNode.insertBefore(legend(), lists[0]);
  }).catch(function () { /* notes are extra; the plain list still works */ });

  function legend() {
    var p = document.createElement("p");
    p.className = "block-legend";
    ["safe", "partial", "breaks"].forEach(function (k) {
      var item = document.createElement("span");
      var dot = document.createElement("span");
      dot.className = "block-dot block-" + k;
      item.appendChild(dot);
      item.appendChild(document.createTextNode(LABELS[k]));
      p.appendChild(item);
    });
    return p;
  }
})();
