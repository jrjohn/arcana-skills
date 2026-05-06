#!/usr/bin/env python3
"""
v3 (2026-04-27, manual-merge added 2026-05-05):
Refresh /opt/mis-http/threatfeed.txt for FG external-resource.

FG pulls .txt automatically every 60 min via:
  config system external-resource
    edit "threatfeed-tor-feodo"
      set type address
      set resource "http://10.0.0.200:8081/threatfeed.txt"

This script does NOT touch FG (no auth/lockout/limit issues).

Feeds:
  - Feodo Tracker (abuse.ch)         banking trojan C2
  - Tor exit nodes (Tor Project)     anonymizer source
  - Spamhaus DROP                    hijacked CIDR
  - Emerging Threats compromised     known-bad IPs from multi-source
  - DShield topips (SANS ISC)        global top scanner sources (small but high signal)
  - SSLBL (abuse.ch)                  C2 infrastructure by SSL fingerprint
  - Manual additions (/opt/mis-http/threatfeed-manual.txt) — IPs we caught locally
"""
import urllib.request, ssl, re, sys
from pathlib import Path

OUT = "/opt/mis-http/threatfeed.txt"
MANUAL_FILE = "/opt/mis-http/threatfeed-manual.txt"
MANUAL_AUTO_FILE = "/opt/mis-http/threatfeed-manual-auto.txt"  # auto-curate-threatfeed.py 寫入

FEEDS = {
    "Feodo":    "https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
    "Tor":      "https://check.torproject.org/torbulkexitlist",
    "Spamhaus": "https://www.spamhaus.org/drop/drop.txt",
    "ET":       "https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
    "DShield":  "https://isc.sans.edu/feeds/topips.txt",
    "SSLBL":    "https://sslbl.abuse.ch/blacklist/sslipblacklist.txt",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ips = set()
for name, url in FEEDS.items():
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MIS-threatfeed/3.0"})
        text = urllib.request.urlopen(req, context=ctx, timeout=30).read().decode()
        before = len(ips)
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            tok = line.split(",")[0].split(";")[0].split()[0]
            if re.match(r"^\d+\.\d+\.\d+\.\d+(/\d+)?$", tok):
                ips.add(tok)
        print(f"[{name}] +{len(ips)-before} IPs (running total: {len(ips)})")
    except Exception as e:
        print(f"[{name}] FAIL: {e}", file=sys.stderr)

# Merge manual additions (local-curated bad actors not yet in upstream feeds)
mp = Path(MANUAL_FILE)
if mp.exists():
    before = len(ips)
    for line in mp.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if re.match(r"^\d+\.\d+\.\d+\.\d+(/\d+)?$", line):
            ips.add(line)
    print(f"[Manual] +{len(ips)-before} IPs (running total: {len(ips)})")
else:
    print(f"[Manual] {MANUAL_FILE} not found, skipping")

# Merge auto-curated additions (auto-curate-threatfeed.py output)
ap = Path(MANUAL_AUTO_FILE)
if ap.exists():
    before = len(ips)
    for line in ap.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if re.match(r"^\d+\.\d+\.\d+\.\d+(/\d+)?$", line):
            ips.add(line)
    print(f"[Manual-Auto] +{len(ips)-before} IPs (running total: {len(ips)})")
else:
    print(f"[Manual-Auto] {MANUAL_AUTO_FILE} not found, skipping")

# Atomic write
tmp = OUT + ".tmp"
Path(tmp).write_text("\n".join(sorted(ips)) + "\n")
Path(tmp).rename(OUT)
print(f"wrote {len(ips)} IPs to {OUT}")
