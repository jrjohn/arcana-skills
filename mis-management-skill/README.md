# mis-management-skill

Central infrastructure for managing a small business network from a single CentOS hub. Wires together FortiGate, NetBox, LibreNMS, QNAP NAS, AD LDAP, and DNS-based AI-usage tracking — all driven from one Linux box on the LAN.

## What you get

- **Auto-blocking inbound attackers** — every 30 min, scan FG inbound deny log; any IP exceeding 100 hits/h gets pushed to FG `local-in-policy` block list. CIDR aggregation auto-promotes /24 when ≥ 3 IPs in same subnet.
- **Threatfeed merging** — combine 6 community feeds (Feodo, Tor, Spamhaus DROP, ET, DShield, SSLBL) + manual + auto-curated → single .txt for FG `external-resource` (HTTP-pulled).
- **Nested addrgrp wrap** — work around FortiOS 6.2's 600-member group cap by splitting IPs across 8 sub-groups + 1 parent.
- **NetBox-driven IP labeling** — every hour, regenerate `ip-names.tsv` from NetBox contact assignments + FG DHCP descriptions + manual override → other tools display "Janey" instead of `.113`.
- **LibreNMS custom services** — Nagios-format check scripts via SSH dispatcher (whitelisted commands).
- **QNAP NAS ClamAV signature update** — proxy via hub when NAS bundled OpenSSL too old to TLS-fetch from clamav.net Cloudflare CDN.
- **AD LDAP queries from Linux** — query users / computers / lastLogon without leaving CentOS.
- **DNS-AI usage tracking** — correlate Windows DNS log with FG forward log → per-employee AI service usage report (Anthropic / OpenAI / Gemini / etc.).

## Architecture

```
                    FortiGate                    Public Internet
                    (10.0.0.1)                    /
                       │                         /
            syslog ────┴──── REST API           /
                       │                       /  (CDN fetch)
                       ▼                      /
                  ┌────────────┐             /
                  │   HUB      │ ───────────/
                  │ 10.0.0.200 │             clamav.net mirrors
                  │  CentOS 8  │             threatfeed providers
                  │ /opt/mis-* │
                  └────────────┘
                       │
       ┌───────────────┼───────────────┬──────────────┐
       ▼               ▼               ▼              ▼
   AD DC 10.x.206   NetBox 10.x.204   QNAP NAS      LibreNMS
   - LDAP query     - Secrets API     10.0.0.14     10.0.0.204
   - DNS log scp    - IP/contact      - ClamAV      - SSH dispatcher
                                       proxy push    - Nagios checks
```

## Quick install

> **Prerequisites**: CentOS 8 (or compatible) hub host with: `python3` ≥ 3.6, `openssh-clients`, `cronie`, `sqlite`, `jq`, `curl`. For LDAP queries also `openldap-clients`. For shell-based password SSH (e.g. NAS), `sshpass` (via EPEL).

### 1. Bootstrap directories

```bash
sudo mkdir -p /opt/mis-log-db /opt/mis-http /var/log/mis /var/lock
sudo touch /opt/mis-http/threatfeed.txt /opt/mis-http/threatfeed-manual.txt
```

### 2. Copy scripts

```bash
sudo cp scripts/fortigate/*.{py,sh} /opt/mis-log-db/
sudo cp scripts/netbox/gen-ip-names-tsv.py /opt/mis-log-db/
sudo cp scripts/librenms/librenms-dispatch.sh /opt/mis-log-db/
sudo cp scripts/nas/nas-clamav-update.sh /opt/mis-log-db/
sudo cp scripts/dns-ai/*.{py,sh} /opt/mis-log-db/
sudo cp scripts/reference/*.{py,sh} /opt/mis-log-db/
sudo chmod +x /opt/mis-log-db/*.sh /opt/mis-log-db/*.py
```

### 3. Customize for your environment

Each script has a CONFIG section at the top. Adjust:

| Constant | Default | What |
|---|---|---|
| `FG_HOST` / `10.0.0.1` | FortiGate management IP | every script that hits FG REST API |
| `NB_URL` / `10.0.0.204:8006` | NetBox URL | `gen-ip-names-tsv.py` |
| `NAS=10.0.0.14` | QNAP NAS IP | `nas-clamav-update.sh` |
| `AD_IP` / `10.0.0.206` | AD DC IP | `fetch-dns-ai.sh` |
| `LAN_NET` | `10.0.0` (env var) | internal /24 prefix for SQL filters |

For sensitive config (FG API token, NetBox admin password, NAS admin password):

```bash
# FG API token (read-write, used by threatfeed-to-fg-addrgrp.py)
echo 'YOUR_FG_TOKEN' | sudo tee /root/.fg_token
sudo chmod 600 /root/.fg_token
```

NetBox / NAS passwords: hardcoded in `gen-ip-names-tsv.py` and `nas-clamav-update.sh` for now. **Recommend**: move to env vars, systemd EnvironmentFile, or pull from NetBox secrets API at runtime.

### 4. Initial threatfeed sync (manual)

```bash
sudo /opt/mis-log-db/mis-threatfeed-sync-v3.py    # populate threatfeed.txt
sudo /opt/mis-log-db/threatfeed-to-fg-addrgrp.py  # push to FG (creates TFI-* + addrgrp)
```

Verify on FG: `firewall/address` should now contain `TFI-*` entries; `Threatfeed-Inbound-Auto-{0..7}` sub-groups + `Threatfeed-Inbound-Auto` parent.

Then create FG `local-in-policy` referencing the parent addrgrp:
```
config firewall local-in-policy
  edit 5
    set intf wan2
    set srcaddr Threatfeed-Inbound-Auto
    set dstaddr all
    set action deny
  next
end
```

(Optional: also create policy id=6 with `intf wan1` if you have multiple WANs.)

### 5. Install cron jobs

```bash
sudo cp scripts/cron/* /etc/cron.d/
# Edit /etc/cron.d/mis-* to set the right Python path / paths for your env
```

Default schedule (staggered to avoid `:00/:30` heavy minute marks):
```
:02      mis-gen-ip-names           ip-names.tsv from NetBox
:15/:45  mis-auto-curate-threatfeed scan FG log → manual-auto.txt
:20/:50  mis-threatfeed-sync        merge → threatfeed.txt
:25/:55  threatfeed-to-fg-addrgrp   (root crontab) push to FG
04:30    mis-nas-clamav-update      ClamAV sigs proxy → NAS
*/10     mis-log-aggregate          FG log → SQLite
```

### 6. SSH key setup for inter-host access

Hub needs key auth to:
- **AD DC** (Windows Server, OpenSSH installed): `ssh-copy-id -i ~/.ssh/id_ed25519.pub administrator@10.0.0.206`. Then `chmod 600 C:\ProgramData\ssh\administrators_authorized_keys` (Windows).
- **QNAP NAS**: append hub pubkey to `/etc/config/ssh/authorized_keys` (persistent across reboots; `/share/homes/admin/.ssh/` gets wiped). See `references/nas-management.md`.
- **LibreNMS containers**: forced `command=` in NAS authorized_keys, only allows running scripts in `/opt/mis-log-db/check_*.sh` whitelist. See `scripts/librenms/librenms-dispatch.sh`.

## Per-component setup

For details on each subsystem:

- `references/architecture.md` — hub + spokes overview
- `references/fortigate-automation.md` — threatfeed pipeline (sync + push + auto-curate)
- `references/netbox-integration.md` — secrets API + IP labeling
- `references/librenms-services.md` — custom service checks + perfdata gotchas
- `references/nas-management.md` — QNAP ClamAV proxy + scan exclusion
- `references/ad-ldap.md` — query AD from Linux (base DN traps)
- `references/dns-ai-tracking.md` — AI usage from DNS log

## What's NOT included

- **FortiGate base config** — assumes FG already has `wan2` policy, SSL VPN, basic policies, an API token (`api_shaping` profile or similar with `firewall: read-write`).
- **NetBox install** — assumes NetBox already running with secrets plugin + at least one IP/contact populated.
- **LibreNMS install** — assumes Docker-based LibreNMS already running.
- **AD DC** — assumes Windows Server AD DC + OpenSSH service installed for `ssh administrator@<AD_IP>`.

These all have plenty of upstream documentation.

## Privacy / sensitive data

This skill is **intended to be sanitized** — no real IPs, names, or secrets in the source. When you deploy:

- **Never commit your customized config back to a public repo.** Either fork to a private repo, or keep customizations in a separate `private-config/` directory.
- **NetBox PEM key** for secrets decryption — store in OS keychain (macOS Keychain / Linux libsecret) ideally, or at minimum `chmod 600` and never sync to cloud.
- **FG API token** — rotate every quarter. If token leaks, regenerate via FG GUI immediately.
- **AD admin password** — pull dynamically from NetBox secrets at script-run time rather than baking into scripts.

## License / origin

Built from real production MIS work on a small business network (~50 employees, ~30 networked devices, FG-100D / TS-469L / Win Server 2019 AD). Sanitized and packaged 2026-05-06. Free to use and modify.
