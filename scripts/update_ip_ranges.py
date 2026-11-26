#!/usr/bin/env python3
"""Rebuild _data/ip-ranges.csv: the IP ranges each provider owns.

Amazon comes from Amazon's official list. Every other provider comes from
RIPEstat (stat.ripe.net), which shows the ranges each network (ASN) announces.

Run from the repo root:  python3 scripts/update_ip_ranges.py
"""
import csv
import datetime
import ipaddress
import json
import os
import urllib.request

# Provider -> network numbers (ASNs). Each was checked against RIPEstat's
# holder records. Providers in A-Z order.
ASNS = {
    "Amazon": [16509, 14618],
    "Apple": [714, 6185],
    "ByteDance": [396986, 138699, 11983],
    "Cloudflare": [13335],
    "Google": [15169, 19527, 36040, 43515, 396982],
    "Meta": [32934, 63293],
    "Microsoft": [8068, 8069, 8075, 12076],
    "X Corp": [13414, 35995, 63179],
    # Reddit and Snap have no network of their own on RIPEstat.
}

AMAZON_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
RIPE_URL = "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{}"
OUT = os.path.join(os.path.dirname(__file__), "..", "_data", "ip-ranges.csv")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "domains-list-ip-ranges"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def amazon_ranges():
    data = get_json(AMAZON_URL)
    nets = [p["ip_prefix"] for p in data["prefixes"] if p["service"] == "AMAZON"]
    nets += [p["ipv6_prefix"] for p in data["ipv6_prefixes"] if p["service"] == "AMAZON"]
    return nets, "Amazon official list (ip-ranges.amazonaws.com)"


def ripe_ranges(asns):
    nets = []
    for asn in asns:
        data = get_json(RIPE_URL.format(asn))["data"]
        nets += [p["prefix"] for p in data["prefixes"]]
    return nets, "RIPEstat announced prefixes"


def merge(nets):
    """Merge overlapping/adjacent ranges and sort them (IPv4 first)."""
    parsed = [ipaddress.ip_network(n, strict=False) for n in nets]
    out = []
    for v in (4, 6):
        same = [n for n in parsed if n.version == v]
        merged = sorted(ipaddress.collapse_addresses(same))
        # every original range must still be covered by a merged one
        assert all(any(n.subnet_of(m) for m in merged) for n in same)
        out += merged
    return out


def main():
    today = datetime.date.today().isoformat()
    rows = []
    for provider, asns in ASNS.items():
        nets, source = amazon_ranges() if provider == "Amazon" else ripe_ranges(asns)
        asn_text = " ".join(f"AS{a}" for a in asns)
        for n in merge(nets):
            rows.append({"provider": provider, "asn": asn_text, "version": f"IPv{n.version}",
                         "range": str(n), "source": source, "checked": today})
        v4 = sum(1 for r in rows if r["provider"] == provider and r["version"] == "IPv4")
        v6 = sum(1 for r in rows if r["provider"] == provider and r["version"] == "IPv6")
        print(f"{provider:11} {asn_text:40} IPv4 {v4:5}  IPv6 {v6:5}")
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["provider", "asn", "version", "range", "source", "checked"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} ranges to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
