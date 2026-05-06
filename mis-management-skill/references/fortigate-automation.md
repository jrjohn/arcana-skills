# FortiGate threatfeed automation

End-to-end pipeline for inbound attacker blocking on FortiGate (tested on FG-100D running FortiOS 6.2.17, but logic should work on 6.4 / 7.x with minor adjustment).

## Pipeline

```
Cron sequence (every 30 min, staggered to avoid :00/:30 minute marks):

:15/:45  auto-curate-threatfeed.py     scan FG inbound deny log →
                                       append qualifying IPs to manual-auto.txt
:20/:50  mis-threatfeed-sync-v3.py     merge 6 upstream feeds + manual + auto-curated
                                       → threatfeed.txt (single dedup'd list)
:25/:55  threatfeed-to-fg-addrgrp.py   PUT IPs into FG firewall.address (TFI-* prefix)
                                       + nested addrgrp (8 sub-grps + parent)

Worst-case attacker block latency: ~30 min.
```

## Components

### `mis-threatfeed-sync-v3.py`

Pulls 6 community feeds + manual files → single dedup'd `threatfeed.txt`:

| Source | Coverage | Update freq |
|---|---|---|
| Feodo Tracker (abuse.ch) | banking trojan C2 | hourly |
| Tor Project exit list | anonymizer source | every 30 min |
| Spamhaus DROP | hijacked CIDRs | every 12 hours |
| Emerging Threats compromised | known-bad IPs | hourly |
| DShield topips (SANS ISC) | global top scanner sources | hourly |
| SSLBL (abuse.ch) | C2 by SSL fingerprint | hourly |
| **Manual** (`threatfeed-manual.txt`) | human-curated | on-demand |
| **Manual-auto** (`threatfeed-manual-auto.txt`) | auto-curate output | every 30 min |

Output: `/opt/mis-http/threatfeed.txt` — one IP/CIDR per line. Served via Apache on port 8081 so FG can `external-resource` fetch it.

**FG `external-resource` config**:
```
config system external-resource
  edit "threatfeed-tor-feodo"
    set type address
    set resource "http://10.0.0.200:8081/threatfeed.txt"
    set refresh-rate 60
  next
end
```

### `threatfeed-to-fg-addrgrp.py`

Pushes `threatfeed.txt` IPs into FG via REST API. Why two delivery paths (`external-resource` AND addrgrp)?

- `external-resource` is **only available to firewall policies**, NOT `local-in-policy`. So if you want the threatfeed to block traffic destined for FG itself (SSL VPN port, admin port), you need `local-in-policy` referencing an `addrgrp`.

**FG 6.2 600-member group cap workaround**:
- Single `addrgrp` can't hold > 600 entries.
- Solution: 8 sub-groups (`Threatfeed-Inbound-Auto-{0..7}`) + 1 parent (`Threatfeed-Inbound-Auto`).
- Each IP is hashed `md5(name) % 8` → assigned to a bucket.
- Parent group contains the 8 sub-groups.
- `local-in-policy` references the parent.
- Capacity: 8 * 600 = 4800 IPs. Bump bucket count for more.

The script:
1. Diffs current FG `firewall.address` (`TFI-*` prefix) vs new `threatfeed.txt`.
2. Adds new IPs as `TFI-<ip>` address objects via POST.
3. Removes obsolete `TFI-*` via DELETE.
4. Recomputes bucket membership; PUTs each sub-group with the new member list.
5. PUTs parent group (no change unless sub-groups changed).

### `auto-curate-threatfeed.py`

Every 30 min: reads last 1h of FG inbound deny log (`subtype="local"` + `action="deny"`), aggregates by `srcip`, and appends qualifying IPs to `threatfeed-manual-auto.txt`.

**Filters**:
- Whitelist: RFC1918 (`192.168/16`, `10/8`, `172.16/12`), HiNet DNS (`168.95/16`), Google/Cloudflare DNS, your WAN /24.
- Skip: IPs already in `threatfeed.txt` (CIDR membership check, not just literal match).
- Threshold: configurable `THRESHOLD_PER_IP = 100` hits/h.

**CIDR aggregation**: when ≥ 3 IPs from same /24 all qualify in same window, promote to `<subnet>.0/24` block. Keeps the threatfeed compact and pre-empts botnet rotation.

**Idempotent**: outputs to a separate file (`threatfeed-manual-auto.txt`) — `mis-threatfeed-sync-v3.py` reads it. Easy to revert (just delete a line).

### `check_deny_inbound.sh` / `check_deny_outbound.sh`

LibreNMS Nagios-format service checks. Greps last 1h FG log, returns:
```
WARNING - 1234 inbound denies/h - top srcs:[1.2.3.4[567] 5.6.7.8[123] ]|hits=1234;1000;5000;0;
```

Exit code: 0=OK, 1=WARNING, 2=CRITICAL.

**Critical perfdata gotcha**: LibreNMS' parser is greedy — anything matching `<word>=<value>` in the **message body** (before the `|`) gets pulled out as a fake datasource. Keep the message body free of `=` and `(<digit>)` — use `[]` or plain text. See `references/librenms-services.md`.

### `check-fg-threatfeed-inbound.sh`

Reports threatfeed block effectiveness — counts `policyid=5/6 + subtype=local + action=deny` events in last 5 min, plus unique source IPs and current threatfeed size.

## Configuring FG `local-in-policy`

After `threatfeed-to-fg-addrgrp.py` has populated the addrgrp, create:

```
config firewall local-in-policy
  edit 5
    set intf wan2
    set srcaddr Threatfeed-Inbound-Auto
    set dstaddr all
    set action deny
    set service ALL
    set schedule always
  next
  edit 6
    set intf wan1   # if you have a second WAN
    set srcaddr Threatfeed-Inbound-Auto
    set dstaddr all
    set action deny
    set service ALL
    set schedule always
  next
end
```

**Order matters**: `local-in-policy` is first-match. Put threatfeed deny BEFORE any allow rules (e.g. SSL VPN allow).

## Runtime tuning

### `auto-curate-threatfeed.py` THRESHOLD_PER_IP

Default: **100 hits/h** per IP triggers add.

| Setting | Trade-off |
|---|---|
| 50 | Catches more attackers; more false positives (legit scanners, search engines) |
| **100** (default) | Balanced |
| 200 | Only the loudest attackers; misses persistent low-rate brute force |

### `auto-curate-threatfeed.py` CIDR_AGGREGATE_MIN

Default: **3 IPs in same /24** → promote.

| Setting | Trade-off |
|---|---|
| 2 | Aggressive — easily blocks /24s for noisy ISPs |
| **3** (default) | Targets botnets without over-blocking |
| 5 | Conservative — only obvious botnet sweeps |

### Cron staggering

Avoid `:00/:30` minute marks (heavy `aggregate.py` runs at every `*/10` including those). Default staggering:
- `:15/:45` auto-curate
- `:20/:50` sync
- `:25/:55` push to FG

This puts the chain in the gap between aggregate runs (`:10`-`:20` and `:40`-`:50`).

## Common ops

### Manually block an IP / CIDR

```bash
echo '203.0.113.42  # known bad' | sudo tee -a /opt/mis-http/threatfeed-manual.txt
sudo /opt/mis-log-db/mis-threatfeed-sync-v3.py
sudo /opt/mis-log-db/threatfeed-to-fg-addrgrp.py
```

### Unblock (false positive)

```bash
# Remove from auto-list (if auto-curate flagged it)
sudo sed -i '/203\.0\.113\.42/d' /opt/mis-http/threatfeed-manual-auto.txt

# Also remove from manual if applicable
sudo sed -i '/203\.0\.113\.42/d' /opt/mis-http/threatfeed-manual.txt

# Sync + push (otherwise next 30-min cron will re-add)
sudo /opt/mis-log-db/mis-threatfeed-sync-v3.py
sudo /opt/mis-log-db/threatfeed-to-fg-addrgrp.py

# Also add to whitelist in auto-curate-threatfeed.py if it's a recurring FP source
```

### Emergency disable

```bash
# Disable cron temporarily
sudo chmod 644 /etc/cron.d/mis-auto-curate-threatfeed   # remove +x
# Or rename so cron skips:
sudo mv /etc/cron.d/mis-auto-curate-threatfeed /etc/cron.d/mis-auto-curate-threatfeed.disabled
```

### Inspect what's currently blocked

```bash
# Total IPs in feed
wc -l /opt/mis-http/threatfeed.txt

# Auto-curated entries
cat /opt/mis-http/threatfeed-manual-auto.txt

# What FG actually has (via REST API)
curl -sk -H "Authorization: Bearer $(cat /root/.fg_token)" \
  https://10.0.0.1/api/v2/cmdb/firewall/address \
  | jq '.results[] | select(.name | startswith("TFI-")) | .name' | wc -l
```

### Audit recent activity

```bash
tail -50 /var/log/mis-auto-threatfeed.log
tail -50 /var/log/mis-threatfeed.log
tail -50 /var/log/mis/threatfeed-fg-sync.log
```
