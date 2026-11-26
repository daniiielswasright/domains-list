"""Fill the `note` and `block` columns of _data/domains.csv.

Each domain gets one note from a fixed list (NOTES), chosen by keyword
rules on the hostname, falling back to a default for its category
(read from the type/ pages). `block` follows from the note.

Rows that already have a note or block are left alone, so hand edits
stick. Run from the repo root:  python3 scripts/fill_notes.py
Pass --all to recompute every row.
"""
import csv, glob, re, sys

# note -> block value. safe = fine to block, partial = blocks one feature,
# breaks = blocking breaks the app or site.
NOTES = {
    "Ad serving": "safe",
    "Ad tracking": "safe",
    "Analytics": "safe",
    "Telemetry": "safe",
    "Crash reporting": "partial",
    "Consent banner": "partial",
    "Push notifications": "partial",
    "Location lookup": "partial",
    "Security check": "partial",
    "Content delivery": "breaks",
    "Cloud hosting": "breaks",
    "Media streaming": "breaks",
    "App backend": "breaks",
    "Device services": "breaks",
    "App updates": "breaks",
    "Login": "breaks",
    "Payments": "breaks",
    "Shopping": "breaks",
    "Messaging": "breaks",
    "Maps": "breaks",
    "Network check": "breaks",
    "DNS": "breaks",
    "Cloud storage": "breaks",
    "AI service": "breaks",
    "Bot protection": "breaks",
    "Help and support": "breaks",
    "Website": "breaks",
}

# Hostname keyword rules, checked in order. The first match wins.
# Each: (note, regex, where, categories)
#   where: "host" checks the full hostname, "sub" only the part before the
#          root domain (so a root like "cdn77.org" doesn't make every host
#          on it "Content delivery"). A trailing "." is added to both.
#   categories: only apply to domains in one of these type/ categories,
#          or None for any.
RULES = [
    ("Crash reporting", r"sentry|crashlytics|bugsnag|crash|error|raygun", "host", None),
    ("Consent banner", r"consent|cookielaw|onetrust|cookiebot|didomi|trustarc|privacymanager|usercentrics|transcend|privacy-center|fides", "host", None),
    ("Bot protection", r"captcha|challenges\.|turnstile|perimeterx|px-cloud|datadome|arkose|appcheck|incognia|fraud", "host", None),
    ("Ad tracking", r"appsflyer|branch\.io|singular\.net|adjust\.com|kochava|app-measurement", "host", None),
    ("Ad tracking", r"pixel|pxl|conversion|attribution|click|track|events|measure|sync|\bfls\.|\bcm\.", "sub", {"ads"}),
    ("Ad serving", r".", "host", {"ads"}),
    ("Push notifications", r"\bpush|pusher|notif|mtalk|onesignal|urbanairship|braze|moengage|airship", "host", None),
    ("Network check", r"connectivity|captive|portal-detection|detectportal|ipv4only|ipv[46]\.|\bstun|\bturn\.|\bntp\.|\btime\.|rpki|dnsotls|metric\.gstatic|msftconnecttest|msftncsi", "host", None),
    ("Telemetry", r"telemetry|vortex|watson|diagnostic|\blogs?\.|logging|beacons?\d*\.|metrics?\.|\bnel\.|csp-report|reporting|-log\.|\bevents?\.|collector|ingest|\bstats|\brum\b|\botel", "sub", None),
    ("Analytics", r".", "host", {"analytics"}),
    ("Login", r"login|\bauth|oauth|account|signin|\bsso\.|\bid\.|\bidp|identity|passport|token|cryptauth|passwords|\botp\.|verify", "sub", None),
    ("Payments", r"\bpay|checkout|billing|stripe|paypal|braintree|adyen|klarna|wallet|\bcard", "host", None),
    ("DNS", r"\bdns\.|-dns\.|dns-|\bdoh\.|resolver|nextdns|controld|quad9", "host", None),
    ("Security check", r"safebrowsing|safety|phishing|spamprotect|\bcsp\.|\bwaf\.|ocsp|\bcrl\.|\bpki\.|malware", "host", None),
    ("App updates", r"update|\bdl\.|download|rr\d+---|edgedl|\binstall|appstore|itunes|\bstore\b|swcdn", "host", None),
    ("Location lookup", r"\bgeo|location|ip2location|ipinfo|ipapi|timezone", "host", None),
    ("Maps", r"maps?[.-](?!fastly)|mapbox|\btiles?\.|basemaps|streetview|places\.|mapping", "host", None),
    ("Cloud storage", r"\bs3\.|\bs3-|storage|upload|backup|\bdrive|blob|\bsync|photos|attachment|\bdoc-", "host", None),
    ("AI service", r".", "host", {"ai"}),
    ("Help and support", r"\bhelp|support|\bfaq\.|zendesk|freshdesk|\bdocs\.|community\.|\bstatus\.|\bdeveloper|\blearn", "host", None),
    ("Content delivery", r"scontent|\bi\.|\bmedia\.|avatar|ytimg|ggpht|\btbn|\blh\d|\bimg|image|\bi\d\.|photo|thumb|emoji|sticker|static", "sub", {"streaming", "social"}),
    ("Media streaming", r"video|\bhls|stream|\bvod\b|\blive|manifest|playback|audio|music|podcast|googlevideo|scdn|spotify|ttvnw|twitch", "host", {"streaming", "social"}),
    ("Media streaming", r".", "host", {"streaming"}),
    ("Content delivery", r"cdn|static|assets|\bimg|images?|media|cache|\bedge|\bfonts?\.|fbcdn|scontent|cloudfront|fastly|akamai|azureedge|ampproject|gstatic|jsdelivr|jquery|unpkg|typekit|fontawesome|\bstc", "host", None),
    ("Messaging", r".", "host", {"messaging"}),
    ("Website", r"^(www|m)\.$", "sub", None),
    ("Cloud hosting", r".", "host", {"cloud-hosting"}),
    ("Location lookup", r".", "host", {"location"}),
    ("Network check", r".", "host", {"dns-network"}),
    ("Security check", r".", "host", {"security-privacy"}),
    ("Help and support", r".", "host", {"help-support"}),
    ("Login", r".", "host", {"identity-authentication"}),
    ("Shopping", r"target\.com|walmart|chipotle|shopify|dutchie|ubereats", "host", {"payments-commerce"}),
    ("Payments", r".", "host", {"payments-commerce"}),
    ("Device services", r".", "host", {"device-browser-app-store"}),
]


# Hand-checked answers that the rules get wrong: domain -> (note, block).
OVERRIDES = {
    # Advertiser dashboards and ad-settings pages, not ads themselves.
    "ads-api.twitter.com": ("Website", "breaks"),
    "ads-api.x.com": ("Website", "breaks"),
    "business.x.com": ("Website", "breaks"),
    "marketing.x.com": ("Website", "breaks"),
    "advertising.walmart.com": ("Website", "breaks"),
    "marketingplatform.google.com": ("Website", "breaks"),
    "myadcenter.google.com": ("Website", "breaks"),
    # Facebook's SDK: tracking, but also "Log in with Facebook" on other sites.
    "connect.facebook.net": ("Ad tracking", "partial"),
    # AWS's monitoring API, used by AWS tools and consoles.
    "monitoring.us-west-1.amazonaws.com": ("Cloud hosting", "breaks"),
}


def categories():
    cats = {}
    for f in sorted(glob.glob("type/*/index.html")):
        c = f.split("/")[1]
        for d in re.findall(r"<li>([^<]+)</li>", open(f, encoding="utf-8").read()):
            cats.setdefault(d.strip().lower(), set()).add(c)
    return cats


def classify(domain, root, cats):
    host = domain.lower()
    sub = host[: -len(root)].rstrip(".") if host.endswith(root) else host
    for note, pattern, where, only in RULES:
        if only is not None and not (cats & only):
            continue
        target = (host if where == "host" else sub) + "."
        if re.search(pattern, target):
            return note
    # Bare root or www. with no other signal: the site itself.
    if sub in ("", "www", "m"):
        return "Website"
    return "App backend"


def main():
    redo = "--all" in sys.argv
    path = "_data/domains.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())
    cats = categories()
    for r in rows:
        if r["domain"] in OVERRIDES:
            r["note"], r["block"] = OVERRIDES[r["domain"]]
            continue
        if redo or not r["note"].strip():
            r["note"] = classify(r["domain"], r["root"], cats.get(r["domain"].lower(), set()))
        if redo or not r["block"].strip():
            r["block"] = NOTES.get(r["note"], "")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
