// Domain search for /domains-list/search/
// Reads the same pages visitors browse (the All page and the category pages),
// so it never needs a separate index to be kept up to date.
(function () {
  "use strict";

  var input = document.getElementById("domain-search");
  var status = document.getElementById("search-status");
  var results = document.getElementById("search-results");
  if (!input || !status || !results) return;

  var MAX_RESULTS = 100;
  var MIN_CHARS = 2;
  var base = new URL("../", window.location.href); // site root: /domains-list/
  var data = null; // [{ domain, letter, cats: [{ name, url }] }]
  var loading = null;
  var timer = null;

  function fetchDoc(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(r.status + " " + url);
      return r.text();
    }).then(function (html) {
      return new DOMParser().parseFromString(html, "text/html");
    });
  }

  function load() {
    if (loading) return loading;
    status.textContent = "Loading domains\u2026";

    var allUrl = new URL("a-z/all/", base).href;
    var indexUrl = new URL("index/", base).href;

    var ownersUrl = new URL("assets/data/owners.json", base).href;
    var owners = fetch(ownersUrl).then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });

    loading = Promise.all([fetchDoc(allUrl), fetchDoc(indexUrl), owners]).then(function (docs) {
      var all = docs[0];
      var index = docs[1];
      var od = docs[2] || { domains: {}, providers: {} };
      var byDomain = Object.create(null);
      var list = [];

      // Domains and their letter, in A-Z order.
      var letter = "";
      all.querySelectorAll("h2, .domain-list li").forEach(function (el) {
        if (el.tagName === "H2") {
          letter = el.textContent.trim();
          return;
        }
        var d = el.textContent.trim().toLowerCase();
        if (!d || byDomain[d]) return;
        var slug = letter === "0-9" ? "0-9" : letter.toLowerCase();
        var owner = od.domains[d] || "";
        var provider = od.providers[owner];
        var entry = {
          domain: d, letter: letter, letterUrl: new URL("a-z/" + slug + "/", base).href, cats: [],
          owner: owner === "Unknown" ? "" : owner,
          ownerKey: owner === "Unknown" ? "" : owner.toLowerCase(),
          ownerUrl: provider ? new URL(provider, window.location.href).href : null
        };
        byDomain[d] = entry;
        list.push(entry);
      });

      // Category pages, found from the Domains Index so nothing is hard-coded.
      var cats = [];
      index.querySelectorAll('a[href*="type/"]').forEach(function (a) {
        var href = new URL(a.getAttribute("href"), indexUrl).href;
        if (/\/type\/$/.test(href)) return; // the type index itself
        if (cats.some(function (c) { return c.url === href; })) return;
        cats.push({ name: a.textContent.trim(), url: href });
      });

      return Promise.all(cats.map(function (c) {
        return fetchDoc(c.url).then(function (doc) {
          doc.querySelectorAll(".domain-list li").forEach(function (li) {
            var e = byDomain[li.textContent.trim().toLowerCase()];
            if (e) e.cats.push(c);
          });
        }).catch(function () { /* a missing category page shouldn't break search */ });
      })).then(function () {
        data = list;
        return data;
      });
    }).catch(function (err) {
      loading = null;
      status.textContent = "Sorry, the domain list couldn't be loaded. Please refresh and try again.";
      throw err;
    });
    return loading;
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function highlight(domain, q) {
    var frag = document.createDocumentFragment();
    var i = domain.indexOf(q);
    if (i < 0) { frag.appendChild(document.createTextNode(domain)); return frag; }
    frag.appendChild(document.createTextNode(domain.slice(0, i)));
    frag.appendChild(el("mark", null, domain.slice(i, i + q.length)));
    frag.appendChild(document.createTextNode(domain.slice(i + q.length)));
    return frag;
  }

  function syncUrl(q) {
    var url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q); else url.searchParams.delete("q");
    window.history.replaceState(null, "", url);
  }

  function render(raw) {
    var q = raw.trim().toLowerCase();
    syncUrl(raw.trim());
    results.textContent = "";

    if (q.length < MIN_CHARS) {
      status.textContent = q.length ? "Keep typing\u2026" : "";
      return;
    }

    // Name matches first, then domains whose owner matches (e.g. "meta" finds fbcdn.net).
    var byName = [], byOwner = [];
    data.forEach(function (e) {
      if (e.domain.indexOf(q) !== -1) byName.push(e);
      else if (e.ownerKey && e.ownerKey.indexOf(q) !== -1) byOwner.push(e);
    });
    var matches = byName.concat(byOwner);

    if (!matches.length) {
      status.textContent = "No domains match \u2018" + raw.trim() + "\u2019.";
      return;
    }

    status.textContent = matches.length > MAX_RESULTS
      ? "Showing " + MAX_RESULTS + " of " + matches.length.toLocaleString() + " matches"
      : matches.length + (matches.length === 1 ? " match" : " matches");

    matches.slice(0, MAX_RESULTS).forEach(function (e) {
      var li = el("li");
      var name = el("span", "search-domain");
      name.appendChild(highlight(e.domain, q));
      li.appendChild(name);

      var tags = el("span", "search-tags");
      if (e.owner) {
        var ow = el(e.ownerUrl ? "a" : "span", "search-owner", e.owner);
        if (e.ownerUrl) ow.href = e.ownerUrl;
        tags.appendChild(ow);
        tags.appendChild(document.createTextNode(" \u00b7 "));
      }
      var lt = el("a", null, e.letter);
      lt.href = e.letterUrl;
      lt.title = "A\u2013Z page " + e.letter;
      tags.appendChild(lt);
      e.cats.forEach(function (c) {
        tags.appendChild(document.createTextNode(" \u00b7 "));
        var a = el("a", null, c.name);
        a.href = c.url;
        tags.appendChild(a);
      });
      li.appendChild(tags);
      results.appendChild(li);
    });
  }

  function onInput() {
    clearTimeout(timer);
    var value = input.value;
    timer = setTimeout(function () {
      if (data) { render(value); return; }
      load().then(function () { render(input.value); });
    }, 150);
  }

  input.addEventListener("focus", function () { load().catch(function () {}); }, { once: true });
  input.addEventListener("input", onInput);
  input.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") { input.value = ""; onInput(); }
  });

  var initial = new URL(window.location.href).searchParams.get("q");
  if (initial) {
    input.value = initial;
    load().then(function () { render(input.value); }).catch(function () {});
  }
})();
