# Roadmap

The working to-do list for the site. The public summary is on the
[Updates & Roadmap](https://daniiielswasright.github.io/domains-list/pages/updates/) page.
This file is kept off the published site (see `exclude` in `_config.yml`).

Suggested order: 1 → 8 (owner column) → 2 → 12, then the rest as data comes in.

---

## 1. Search bar ✅

- [x] Search page at `/domains-list/search/` with results as you type
- [x] Search box in the menu on every page (opens the search page with `?q=`)
- [x] Each result links to its A–Z page and its categories
- [x] Shareable searches (`/search/?q=tiktok`)
- [x] Match on owner too, so "Meta" finds `fbcdn.net`

## 2. Provider pages ✅

Amazon, Apple, ByteDance (TikTok, CapCut), Cloudflare, Google, Meta (Facebook, Instagram,
Threads, WhatsApp), Microsoft, Reddit, Snap, X Corp.

- [x] Fill in the `owner` column in `_data/domains.csv` first (item 8)
- [x] Generate `providers/<name>/index.html` for each company: domain count, list grouped by root domain (built from the CSV by `_includes/provider-domains.html`)
- [x] Add a `providers/` hub page (table of providers and their root domains)
- [x] Add a "Browse by Provider" section to the Domains Index
- [x] Add `providers/` to the README tree
- [ ] Add more providers as needed: create `providers/<name>/index.html` with `owner: <Owner>` in the front matter

## 3. Main blocklist

- [ ] Decide what goes in (e.g. Ads, Analytics, tracking hosts) and what never does (logins, payments, CDNs)
- [ ] Build it from the `block` column (item 9)
- [ ] Publish it as a plain domains list

## 4. Adult content blocklist

- [ ] Upload the list
- [ ] Sort it, remove duplicates, publish it

## 5. Blocklist formats

- [ ] Generate each list from one source in three formats: plain domains (NextDNS, Blokada), hosts file (`0.0.0.0 domain`), AdBlock (`||domain^`)
- [ ] Add a `blocklists/` page with raw download links
- [ ] Add short setup instructions for NextDNS and Blokada

## 6. About 1,000 more domains

- [ ] Upload them
- [ ] Sort each into its letter page and a category
- [ ] Update the counts, the All page and the totals on the Domains Index and Search page
- [ ] Re-check that every count matches

## 7. Uncategorized hostnames

- [ ] Work through the ~530 left over from the working list and give each a category

## 8. "What it does" notes and owner

- [x] Create `_data/domains.csv` with the columns `domain, root, owner, note, block`
- [x] Fill in `owner` for every domain (quick, and it unlocks provider pages and owner search)
- [ ] Review the domains whose owner is `Unknown` (26 root domains, mostly ad and adult networks)
- [ ] Fill in `note`, starting with the largest categories
- [ ] Show the note as a small grey line under each domain on the A–Z pages (owner is **not** shown there; it lives on the provider pages)
- [ ] Domains without a note just show the domain

## 9. Safe to block / breaks apps

- [ ] Fill in the `block` column: `safe` (ads, tracking) or `breaks` (logins, payments, content delivery)
- [ ] Show a small marker and a legend
- [ ] Use it to build the blocklists (item 3)

## 10. "Last updated" dates

- [ ] Add a short "Last updated" line to each page when it changes

## 11. PCAPdroid how-to guide

- [ ] New `pages/guide/` page: install PCAPdroid, capture one app, export the domains, look them up here

## 12. IP ranges on provider pages ✅

A domain's IP changes constantly (CDNs, load balancing, location), so IPs are **not**
listed per domain. The ranges each company owns are stable, so they go on the provider pages.

- [x] Create `_data/ip-ranges.csv` with the columns `provider, asn, version, range, source, checked` (built by `scripts/update_ip_ranges.py`)
- [x] Fill it: Amazon from its official list (`ip-ranges.amazonaws.com`); everyone else from RIPEstat by ASN (Google and Cloudflare too, since `www.gstatic.com` and `www.cloudflare.com` aren't allowed in the environment)
- [x] Add an "IP ranges" section to each provider page: ASN, IPv4/IPv6 ranges, source, last checked date
- [x] Reddit and Snap: no network of their own, so their pages say so
- [ ] Optional: an "IPs seen" section with IPs observed in PCAPdroid captures, dated and marked as observations

---

## How to update the site

- Every page is a folder with an `index.html` inside (for example `a-z/g/index.html`).
- When a list changes, update the domain count at the top of that page, the All page, and the totals on the Domains Index and Search page.
- When adding a domain, also add a row to `_data/domains.csv` (keep it sorted by root, then domain). Provider pages and owner search update from it automatically.
- Search reads the live pages, so it updates itself.
- To refresh the IP ranges, run `python3 scripts/update_ip_ranges.py` from the repo root, then commit `_data/ip-ranges.csv`.
- The site is published from the `home` branch.
