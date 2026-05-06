# LibreNMS custom service checks

LibreNMS supports Nagios-format service checks for arbitrary metrics. This skill uses them to surface FortiGate threatfeed effectiveness and deny rates as graphed/alertable services.

## Architecture

```
LibreNMS containers (Docker on monitoring host)
                ↓
        ssh root@hub "<script-name>"
                ↓
  /root/.ssh/authorized_keys on hub:
    command="/opt/mis-log-db/librenms-dispatch.sh" ssh-ed25519 ...
                ↓
  librenms-dispatch.sh:
    case "$SSH_ORIGINAL_COMMAND" in
        check_deny_inbound.sh)   exec /opt/mis-log-db/check_deny_inbound.sh ;;
        check_deny_outbound.sh)  exec /opt/mis-log-db/check_deny_outbound.sh ;;
        ...
    esac
                ↓
  Script outputs Nagios format:
    OK - 123 inbound denies/h - top srcs:[1.2.3.4[567] ]|hits=123;1000;5000;0;
                ↓
  LibreNMS parses → stores in services-N.rrd → graphs + alerts
```

## Dispatcher (`librenms-dispatch.sh`)

A forced-command wrapper to limit which scripts the LibreNMS user can invoke. Typical content:

```bash
#!/bin/bash
case "$SSH_ORIGINAL_COMMAND" in
    check_p33_threatfeed.sh)         exec /opt/mis-log-db/check_p33_threatfeed.sh ;;
    check_deny_inbound.sh)           exec /opt/mis-log-db/check_deny_inbound.sh ;;
    check_deny_outbound.sh)          exec /opt/mis-log-db/check_deny_outbound.sh ;;
    check-fg-threatfeed-inbound.sh)  exec /opt/mis-log-db/check-fg-threatfeed-inbound.sh ;;
    *) echo "UNKNOWN - command not allowed: $SSH_ORIGINAL_COMMAND"; exit 3 ;;
esac
```

### `authorized_keys` entry on hub

For each LibreNMS container's pubkey:

```
command="/opt/mis-log-db/librenms-dispatch.sh",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAAC3...
```

The `command="…"` forces only the dispatcher to run regardless of what `ssh user@hub <anything>` requests; `SSH_ORIGINAL_COMMAND` env var carries the requested script name.

## Adding a new service check

1. **Write the script** at `/opt/mis-log-db/check_<name>.sh`. Output format:
   ```
   <STATUS> - <human readable> | <metric>=<value>;<warn>;<crit>;<min>;<max> [<metric2>=...]
   ```
   Exit code: 0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN.

2. **Add a `case` arm** to `librenms-dispatch.sh`.

3. **Configure in LibreNMS** UI:
   - Services → Add Service
   - Type: SSH (`by_ssh` check type — runs `ssh user@host <command>`)
   - Remote Host: hub IP
   - Parameters: just the script name (becomes `$SSH_ORIGINAL_COMMAND`)
   - Description: human-friendly name shown in alerts

## Critical perfdata gotcha

LibreNMS' Nagios parser is greedy: it grabs `<word>=<value>` patterns from the **message body** (before the `|` perfdata pipe), not just the perfdata section. If your script outputs:

```
WARNING - 1900 inbound denies/h - top: 51.15.19.159(728) 188.166.223.22(33) |hits=1900;...
                                       ^^^^^^^^^^^^^^^^^
                                       parser may invent DS named "top" from this
```

LibreNMS sometimes interprets this as a perfdata field `top=51.15.19.159(728)`, creates an RRD field named `top`, and your real `hits` field collides with it. Result: chart shows `-nan` forever.

### Fix pattern

**Avoid** in the message body:
- `<word>:` followed by anything that looks numeric (like `<ip>(<n>)`)
- `<word>=<value>` style at all
- Parens around digits — use `[]` or just text

**Good output**:
```
WARNING - 1900 inbound denies/h - top srcs:[51.15.19.159[728] 188.166.223.22[33] ]|hits=1900;1000;5000;0;
```

Note the `[]` instead of `()` and no bare `=` in the message.

### If RRD already broken

If a check has been running with a misparsed perfdata, the RRD has the wrong field name. After fixing the script:

1. Delete the existing RRD file: `rm /opt/librenms/data/librenms/rrd/<host>/services-N.rrd`
2. Wait for next LibreNMS poll (~5 min) — it'll recreate with clean field names.
3. Chart starts populating ~15-30 min later.

To find the right RRD:
```sql
mysql ... librenms -e "SELECT service_id, service_name, service_ds FROM services WHERE service_name LIKE '%<name>%';"
```
Then `services-<id>.rrd` is the file.

### "Chart suddenly jumps from 0 to N" — RRD recreate artifact

If a service chart shows a long flat 0 then a sudden spike to a real value, **before assuming it's a real attack burst**, check whether the RRD was recently recreated:

```bash
ls -la /opt/librenms/data/librenms/rrd/<host>/services-N.rrd*
# If you see a *.bak-YYYY-MM-DD sibling, the RRD was reset that day
```

The "0" before the recreate timestamp is `unknown` (no data because field names didn't match), not a real "no traffic". The real value has likely been steady — you just couldn't see it. Cross-check by greppping the source log:

```bash
grep -aE '<filter>' /var/log/<source>.log | tail -3000 | wc -l
# Compare against pre-spike timestamp range
```

## Inspect RRD content (debugging)

```bash
# All datasource (DS) fields in the RRD
docker exec librenms rrdtool info /data/rrd/<host>/services-3.rrd \
    | grep -E "^ds\[.*\]\.index"

# Last 1h of values
docker exec librenms rrdtool fetch /data/rrd/<host>/services-3.rrd LAST -s -1h
```

Healthy output should have ds names matching your perfdata field names (lowercase `hits`, `uniq_src`, etc.). Garbage like `ds[19216811122807]` means LibreNMS parsed an IP from the message body — fix the script + delete RRD.

## Built-in alert rules

LibreNMS auto-fires alerts based on Nagios exit code. Key rules to set:

| Service | Warn threshold | Crit threshold | Delay | Count | Interval |
|---|---|---|---|---|---|
| `fg-deny-inbound` | 1000 hits/h | 5000 hits/h | 180 | 1 | 1800 |
| `fg-deny-outbound` | 10000 hits/h | 50000 hits/h | 180 | 1 | 1800 |
| `fg-threatfeed-inbound` | (varies — context dependent) | | | | |

### `extra` JSON semantics — what `count` / `delay` / `interval` actually mean

Easy to mis-interpret. As of LibreNMS 26.x:

| Field | Meaning | NOT what it means |
|---|---|---|
| **`delay`** (sec) | Wait this many seconds after condition first becomes true before sending the first alert. The condition must remain true throughout, otherwise the timer resets. | Not a re-notification interval. |
| **`interval`** (sec) | Re-notify cadence — every N seconds while still firing, send another email. | Not "polling interval" (that's the global poller, fixed at 5 min). |
| **`count`** (int) | Maximum number of notifications to send for this fire-cycle, then mute until recovery. `count=1` = fire once then silence until condition recovers and re-trips. | **NOT** "require N consecutive polls before alerting" — that's a common misread. |

**The right primitive for "must be sustained for N minutes before alerting" is `delay`**, not `count`.

### Cron-induced flap (CPU rules)

If a host has a regular cron that briefly spikes CPU (heavy log aggregator, PowerShell DNS dump, ClamAV signature load), a CPU rule with `delay=180` will fire on every cron run because spikes typically last 3-5 min.

Symptom: alert email pairs every 30 min like clockwork, fire→recover within 2-3 min, multiple hosts simultaneously.

**Fix**: increase `delay` past the spike duration, AND set `count=1` so even if the spike DOES exceed the delay, you only get one email per cycle (not a flap-storm).

```sql
UPDATE alert_rules
SET extra = JSON_SET(extra, '$.count', 1, '$.delay', 600, '$.interval', 1800)
WHERE name = '[CRIT] CPU >=95%';
```

After UPDATE: short spikes (≤10 min) absorbed by `delay=600`. Sustained ≥10 min saturation still alerts (once), then mutes until recovery, then re-arms.

**If alerts continue flapping after rule UPDATE**: dispatcher may have cached old rule values. Restart the alerter container:

```bash
docker restart librenms_dispatcher
```

(Caveat: this affects all alert evaluation for ~30s. Generally safe but get authorization on shared infra.)

Don't blanket-apply this pattern to all rules — only ones flapping. Real sustained saturation still needs to alert promptly, and `count=1` permanently mutes a stuck-stuck condition until recovery.

## Operational notes

- **Stagger your check scripts** to avoid all running at the same minute. LibreNMS polls services every 5 min; the cron jobs that produce data should run on different minutes (e.g. `*/5 + offset`).
- **Heavy log greps** (FG syslog 1M+ lines/day) — check scripts should use file pointer + size limit (last 100 MB), not full-file scan.
- **Empty perfdata** breaks LibreNMS — even on `OK` state, output something like `|hits=0;1000;5000;0;` so RRD has a value.
