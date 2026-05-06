#!/usr/bin/env python3
"""
Auto-curate inbound threatfeed from FG local-in-policy deny log.

Every run (cron every 30 min):
  1. Parse last 1h of /var/log/remote/fortigate/fortigate.log
  2. Filter subtype="local" + action="deny" entries
  3. Aggregate by srcip, count hits
  4. Drop whitelisted nets + already-blocked IPs
  5. Find /24s with ≥ CIDR_AGGREGATE_MIN qualifying IPs → promote to /24
  6. Append new entries to /opt/mis-http/threatfeed-manual-auto.txt (idempotent)
  7. Log additions

The output file is read by mis-threatfeed-sync-v3.py and merged into
/opt/mis-http/threatfeed.txt at the next :05 sync, then push to FG.

Designed to be cron-friendly:
  - Idempotent (safe to re-run)
  - Silent on no-op (only logs when adding new entries)
  - Exit 0 unless serious error
"""
import sys
import os
import re
import json
import argparse
import ipaddress
import datetime
from collections import defaultdict
from pathlib import Path

LOG          = '/var/log/remote/fortigate/fortigate.log'
EXISTING     = '/opt/mis-http/threatfeed.txt'
OUT_AUTO     = '/opt/mis-http/threatfeed-manual-auto.txt'

WHITELIST_NETS = [
    ipaddress.ip_network(n) for n in [
        '192.168.0.0/16',     # RFC1918 internal
        '10.0.0.0/8',         # RFC1918
        '172.16.0.0/12',      # RFC1918
        # YOUR_WAN_NET (e.g. ISP-allocated /24 around your public IP) — uncomment and set:
        # '203.0.113.0/24',
        '168.95.0.0/16',      # HiNet DNS / mgmt
        '8.8.8.0/24',         # Google DNS
        '8.8.4.0/24',         # Google DNS alt
        '1.1.1.0/24',         # Cloudflare DNS
        '1.0.0.0/24',         # Cloudflare alt
    ]
]
THRESHOLD_PER_IP   = 100   # hits/h — single IP must exceed
CIDR_AGGREGATE_MIN = 3     # IPs in same /24 to promote to /24 block
LOOKBACK_MIN       = 60    # parse last N minutes


# Regex (compiled once)
RE_SRC = re.compile(r'srcip=([0-9.]+)')
# Match the syslog header timestamp at line start: "May  5 16:30:01 ..."
# We only need to know whether the line is in the last LOOKBACK_MIN minutes.
RE_TS = re.compile(r'^([A-Z][a-z]{2})\s+(\d+)\s+(\d{2}):(\d{2}):(\d{2})')


def is_whitelisted(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # malformed → skip
    return any(ip in net for net in WHITELIST_NETS)


def load_existing_blocked():
    """Load existing threatfeed.txt entries → list of ip_network objects.

    Returns a list of ipaddress.ip_network so we can do CIDR membership checks
    (single IPs as /32). This way ip 1.2.3.4 is correctly recognized as already
    blocked when threatfeed.txt has 1.2.3.0/24.
    """
    if not os.path.exists(EXISTING):
        return []
    out = []
    for line in Path(EXISTING).read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        try:
            net = ipaddress.ip_network(line, strict=False)
            out.append(net)
        except ValueError:
            continue
    return out


def is_already_blocked(ip_or_cidr, blocked_nets):
    """Check if ip_or_cidr is covered by any net in blocked_nets."""
    try:
        candidate = ipaddress.ip_network(ip_or_cidr, strict=False)
    except ValueError:
        return False
    for net in blocked_nets:
        # Python 3.6 compatible: subnet_of() was added in 3.7
        if (candidate.network_address in net and
                candidate.broadcast_address in net):
            return True
    return False


def load_existing_auto():
    """Load already-auto-added entries (so we never duplicate-append)."""
    if not os.path.exists(OUT_AUTO):
        return set()
    out = set()
    for line in Path(OUT_AUTO).read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            out.add(line)
    return out


def parse_recent_log(lookback_min: int):
    """Yield srcip strings from last lookback_min minutes of inbound deny."""
    if not os.path.exists(LOG):
        return
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(minutes=lookback_min)

    # Map English month abbr to number
    months = {m: i+1 for i, m in enumerate(
        ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}

    with open(LOG, 'rb') as f:
        # Read from end; cap at last 100 MB to keep it fast even on huge log
        f.seek(0, 2)
        size = f.tell()
        max_back = 100 * 1024 * 1024
        f.seek(max(0, size - max_back))
        # discard partial first line
        if f.tell() > 0:
            f.readline()
        for raw in f:
            line = raw.decode('utf-8', errors='replace')
            # Quick filters first (avoid expensive parses)
            if 'subtype="local"' not in line:
                continue
            if 'action="deny"' not in line:
                continue
            m = RE_TS.match(line)
            if not m:
                continue
            mon = months.get(m.group(1), 0)
            day = int(m.group(2))
            hh, mm, ss = int(m.group(3)), int(m.group(4)), int(m.group(5))
            try:
                ts = datetime.datetime(now.year, mon, day, hh, mm, ss)
            except ValueError:
                continue
            # Handle year wrap (Dec → Jan)
            if ts > now + datetime.timedelta(days=1):
                ts = ts.replace(year=now.year - 1)
            if ts < cutoff:
                continue
            sm = RE_SRC.search(line)
            if sm:
                yield sm.group(1)


def main():
    ap = argparse.ArgumentParser(description='Auto-curate inbound threatfeed.')
    ap.add_argument('--dry-run', action='store_true',
                    help='Print what would be added; do not write file.')
    ap.add_argument('--lookback', type=int, default=LOOKBACK_MIN,
                    help='Minutes of log to scan (default 60).')
    ap.add_argument('--threshold', type=int, default=THRESHOLD_PER_IP,
                    help='Per-IP hits threshold (default 100).')
    args = ap.parse_args()

    # Aggregate hits
    hits = defaultdict(int)
    for ip in parse_recent_log(args.lookback):
        hits[ip] += 1

    # Filter
    blocked = load_existing_blocked()
    already_auto = load_existing_auto()

    candidates = {}
    for ip, n in hits.items():
        if n < args.threshold:
            continue
        if is_whitelisted(ip):
            continue
        if is_already_blocked(ip, blocked):
            continue
        candidates[ip] = n

    # CIDR aggregation
    by_24 = defaultdict(list)
    for ip in candidates:
        try:
            net24 = str(ipaddress.ip_network(f'{ip}/24', strict=False))
            by_24[net24].append(ip)
        except ValueError:
            continue

    promoted = set()        # /24 CIDRs to add
    consumed_ips = set()    # individual IPs covered by a promoted /24
    for net24, ips in by_24.items():
        if len(ips) >= CIDR_AGGREGATE_MIN:
            if not is_already_blocked(net24, blocked):
                promoted.add(net24)
                consumed_ips.update(ips)

    # Final entries to add
    to_add = []
    today = datetime.date.today().isoformat()

    for cidr in sorted(promoted):
        entry = (cidr, sum(candidates[ip] for ip in by_24[cidr]),
                 f'/24 promote ({len([1 for ip in candidates if ip in by_24[cidr]])} IPs in subnet)')
        if cidr not in already_auto:
            to_add.append(entry)

    for ip in sorted(candidates, key=lambda x: ipaddress.ip_address(x)):
        if ip in consumed_ips:
            continue  # covered by promoted /24
        if ip in already_auto:
            continue
        to_add.append((ip, candidates[ip], f'{candidates[ip]} hits/{args.lookback}min'))

    if not to_add:
        # Silent — only log when something happens
        return 0

    # Format added lines
    new_lines = []
    for entry, n, reason in to_add:
        new_lines.append(f'{entry}\t# auto-added {today}: {reason}')

    if args.dry_run:
        print(f'[dry-run] would add {len(to_add)} entries:', file=sys.stderr)
        for ln in new_lines:
            print(f'  {ln}', file=sys.stderr)
        return 0

    # Idempotent append (header if file new)
    Path(OUT_AUTO).parent.mkdir(parents=True, exist_ok=True)
    is_new = not os.path.exists(OUT_AUTO)
    with open(OUT_AUTO, 'a') as f:
        if is_new:
            f.write('# Auto-curated inbound threatfeed entries.\n')
            f.write('# Source: /opt/mis-log-db/auto-curate-threatfeed.py (cron */30 min)\n')
            f.write('# Format: <IP-or-CIDR>\\t# auto-added <date>: <reason>\n')
            f.write('# Edit threatfeed-manual.txt instead for permanent manual entries.\n')
            f.write('# Remove a line here if you want to un-block (next sync within 30 min).\n\n')
        for ln in new_lines:
            f.write(ln + '\n')

    # Log to stderr (cron captures into /var/log/mis-auto-threatfeed.log)
    print(f'[{datetime.datetime.now().isoformat(timespec="seconds")}] '
          f'added {len(to_add)} entries: '
          + ', '.join(e[0] for e in to_add), file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
