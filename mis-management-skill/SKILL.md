# MIS Management Skill

Central infrastructure for managing a small/medium business network from a single CentOS hub. Pulls together FortiGate threatfeed automation, NetBox-driven IP labeling, LibreNMS service monitoring, QNAP NAS management (including ClamAV signature update proxy when the NAS itself can't TLS), AD LDAP queries from Linux, and DNS-based AI-usage tracking.

## When to use this skill

Reach for this skill when the user is:

- Setting up or extending a **central management host** (typically a Linux box on the LAN — call it the "hub") that aggregates FortiGate logs, runs cron jobs against multiple network devices, and serves a small dashboard.
- Building **threatfeed automation** for FortiGate (mostly FG 6.2 / 6.4 with `local-in-policy`): pulling community feeds, auto-curating attackers from FG deny logs, pushing into nested address-groups to bypass FortiOS 6.2's 600-member group cap.
- Wiring **NetBox** as the source of truth for IP/contact/secret data, and surfacing it in plain `ip-name.tsv` files that other tooling consumes.
- Adding **LibreNMS custom services** that grep FG syslog and produce Nagios-format check output, with an SSH dispatcher that limits which scripts the LibreNMS containers can invoke.
- Working around **legacy QNAP NAS** issues — bundled OpenSSL too old for modern Cloudflare CDNs, ClamAV freshclam silently failing, quarantine cleanup, scan exclusion of IT tool repos.
- Querying **Active Directory via LDAP** from a CentOS box (`ldapsearch` patterns), avoiding common base-DN traps.
- Tracking **AI-service usage by employee** (Anthropic / OpenAI / Gemini / Perplexity / DeepSeek / Kimi) by correlating Windows DNS logs with FG forward traffic.

Do NOT use this skill for:

- Generic Linux server admin (use general bash/sysadmin knowledge).
- Cloud-native deployments — this is on-prem network gear.
- Greenfield FortiGate installs — assumes FG already configured with API token + SSL VPN + basic policy structure.

## Architecture

```
                         FortiGate (10.0.0.1)
                              ↑ syslog + REST API
                              |
   AD DC (10.0.0.206) ←── HUB (10.0.0.200) ──→ QNAP NAS (10.0.0.14)
        |  LDAP /             |  CentOS 8         |  ClamAV proxy
        |  DNS log scp        |  cron + scripts   |  scp fresh sigs
                              |
        NetBox (10.0.0.204)   |
              ↑ secrets API   |
                              ↓
                        LibreNMS (10.0.0.204)
                              ↑ SSH service-check dispatcher
```

The HUB at `10.0.0.200` is where 90% of this skill's scripts live. Everything else is reached out to via SSH key auth, REST API, or LDAP.

## Components

### FortiGate threatfeed automation (`scripts/fortigate/`)
- `mis-threatfeed-sync-v3.py` — pulls 6 upstream feeds (Feodo, Tor, Spamhaus DROP, ET, DShield, SSLBL) + merges manual + auto-curated lists → writes single `threatfeed.txt` for FG `external-resource` to fetch over HTTP.
- `threatfeed-to-fg-addrgrp.py` — pushes IPs into FG `firewall.address` (`TFI-` prefix) + nested `addrgrp` (8 sub-groups + 1 parent) to work around FG 6.2's 600-member group limit.
- `auto-curate-threatfeed.py` — every 30 min: greps last 1h FG inbound deny log, finds source IPs > 100 hits/h, applies whitelist + dedup against existing threatfeed, optionally promotes /24 when ≥ 3 IPs in same subnet, appends to `threatfeed-manual-auto.txt`.
- `check_deny_inbound.sh` / `check_deny_outbound.sh` / `check-fg-threatfeed-inbound.sh` — Nagios-format LibreNMS service checks. Produces `OK/WARNING/CRITICAL` text + perfdata.

See `references/fortigate-automation.md` for the full pipeline.

### NetBox integration (`scripts/netbox/`)
- `gen-ip-names-tsv.py` — every hour: pulls all NetBox IPs + their assigned contact names, merges with FG DHCP reservation descriptions, plus a manual override file → outputs `ip-names.tsv`. This file is consumed by everything that wants to label an IP with "Janey" instead of `.113`.

### LibreNMS extensions (`scripts/librenms/`)
- `librenms-dispatch.sh` — installed at the hub; called by LibreNMS containers via `ssh root@hub <script-name>` with `command="…"` in `authorized_keys`. Whitelists which check scripts the LibreNMS user is allowed to invoke.

### NAS management (`scripts/nas/`)
- `nas-clamav-update.sh` — daily 04:30 cron on hub: downloads ClamAV `main/daily/bytecode.cvd` from `database.clamav.net` (using a `freshclam`-style User-Agent; modern TLS only available on hub), `scp`s to NAS, removes stale `.cld` files, updates NAS `antivirus.global` `LastDBUpdate` + `AntivirusStatus` so the NAS Web UI shows "update successful".

### DNS-AI usage tracking (`scripts/dns-ai/`)
- `fetch-dns-ai.sh` — every 30 min: SSH to AD DC, runs PowerShell aggregator that reads Windows DNS server log, returns JSON of `(client_ip, qname, ai_service, resolved_ip)`. Filters out FG's own DNS queries (it's not a "user").
- `ingest-dns-ai-events.py` — appends events into SQLite `dns_ai_events`.
- `correlate-dns-ai.py` — joins `dns_ai_events` with FG forward log (`user_dest`) on `(src_ip, dst_ip)` within ±10 min window → attributes bytes-transferred to a service.
- `gen-ai-usage-report.py` — renders HTML showing per-user / per-service AI usage MB/day.

### Aggregator + helpers (`scripts/reference/`)
- `aggregate.py` — every 10 min: parses FG forward log, populates SQLite `user_dest` table (src_ip, dst_ip, bytes, first_seen).
- `gen-deny-report.sh` — every 5 min: produces HTML deny-report visualization.
- `mac-harvester.sh` — every minute: snapshots active DHCP leases.

## Critical guidance

**1. Threatfeed sync chain ordering.** Three jobs must run in sequence:
   1. `auto-curate-threatfeed.py` — adds IPs to manual-auto.txt
   2. `mis-threatfeed-sync-v3.py` — merges all sources → threatfeed.txt
   3. `threatfeed-to-fg-addrgrp.py` — pushes to FG addrgrp
   Stagger cron times so they run in this order with ≥ 5 min between, and avoid `:00/:30` minute marks (heavy aggregator runs there).

**2. FG 6.2 `firewall/address` group 600-member limit.** A single addrgrp can't hold > 600 entries. Use the **nested addrgrp wrap pattern**: split IPs across N sub-groups (e.g. md5(name) % 8), then make a parent group containing those sub-groups. `local-in-policy` references the parent. `threatfeed-to-fg-addrgrp.py` implements this. If you have > 4800 IPs, raise the bucket count.

**3. LibreNMS perfdata parsing pitfall.** LibreNMS' Nagios parser is greedy — it grabs `<word>=<value>` patterns from the **message body** (before the `|`), not just from after the perfdata pipe. If your script outputs `top: 192.168.1.5(728)`, LibreNMS may invent a DS named `top` from it, which then collides with the real `hits` field. **Always use plain text in the message body — no `=`, no `(<digits>)`.**

**4. RRD field name persistence.** Once a LibreNMS service is created and its RRD is initialized, the perfdata field names are baked in. Renaming a perfdata key in your check script will produce `-nan` forever. Either (a) match the original name, or (b) delete the RRD file and let LibreNMS recreate it on the next poll.

**5. QNAP TLS workaround pattern.** Old QNAP firmware bundles ancient OpenSSL that can't TLS 1.2+ to Cloudflare. Don't try to upgrade the NAS — instead do all CDN-fetch work on the hub (modern TLS), then `scp` files to the NAS. Set up SSH key auth from hub → NAS via `/etc/config/ssh/authorized_keys` (the persistent location; `/share/homes/admin/.ssh/` gets wiped).

**6. AD LDAP from Linux.** Base DN is the **AD forest root**, not your DNS domain. If `domain` is `arcana.com.tw` but AD is `arcana.com`, base DN is `DC=arcana,DC=com`. Discover with: `ldapsearch -x -H ldap://<AD_IP> -s base -b '' '(objectClass=*)' defaultNamingContext`.

**7. NAS conn log lives on the hub, not the NAS.** QNAP NAS sends syslog to `/var/log/remote/qnap/qnap.log` on the hub (configured via QNAP Notification Center). **Don't SSH into the NAS to grep logs** — busybox-style shell + version-dependent paths waste round-trips. The conn log includes `Users: <employee_id>` field, which is often the most reliable IP→employee mapping (more complete than NetBox or DHCP). See `references/nas-management.md`.

## Snippet for `~/.claude/CLAUDE.md`

Paste this near the top so future Claude sessions know how to use this skill in the project:

```markdown
# MIS hub layout

The MIS management scripts live on the hub host (10.0.0.200, CentOS 8) under
/opt/mis-log-db/ + /opt/mis-http/. Cron entries in /etc/cron.d/mis-*.

Source-of-truth for IP→employee mapping: NetBox at 10.0.0.204:8006
(secrets via the secrets plugin + PEM key — see references/netbox-integration.md).

For threatfeed work (FG inbound block automation), see
references/fortigate-automation.md. The chain runs every 30 min:
auto-curate → sync → push-to-FG.

For QNAP NAS work, the NAS itself can't TLS-fetch from clamav.net
(bundled OpenSSL too old). All CDN downloads happen on the hub then scp
to the NAS. See references/nas-management.md.
```

## Files in this skill

```
mis-management-skill/
├── SKILL.md                          # this file
├── README.md                         # human-friendly intro + install
├── references/
│   ├── architecture.md               # hub + spokes diagram
│   ├── fortigate-automation.md       # threatfeed pipeline
│   ├── netbox-integration.md         # secrets API + IP labeling
│   ├── librenms-services.md          # custom services + perfdata gotchas
│   ├── nas-management.md             # ClamAV proxy + quarantine
│   ├── ad-ldap.md                    # query AD from Linux
│   └── dns-ai-tracking.md            # AD DNS log → AI usage report
└── scripts/
    ├── fortigate/                    # threatfeed automation + FG checks
    ├── netbox/                       # IP labeling
    ├── librenms/                     # SSH dispatcher
    ├── nas/                          # ClamAV proxy
    ├── dns-ai/                       # AI usage tracking
    ├── cron/                         # /etc/cron.d/ examples
    └── reference/                    # supporting scripts
```

## Author / origin

Built incrementally from real production MIS work on a small business network.
Sanitized and packaged 2026-05-06. Generic placeholders throughout — adapt to your
own network by editing the config sections at the top of each script (and via
the env vars listed in README.md).
