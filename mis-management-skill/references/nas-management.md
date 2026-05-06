# QNAP NAS management

The biggest pain point: **legacy QNAP firmware bundles ancient OpenSSL** that can't TLS 1.2+ to modern Cloudflare-fronted CDNs. The NAS's built-in `freshclam` (ClamAV signature update) silently fails because `clamav.net` requires TLS 1.2+. This module proxies the download via the hub.

Tested on TS-469L running QTS 4.3.4 (firmware EOL ~2024). Pattern works for any older QNAP.

## ClamAV signature update via proxy

### Why proxy

| Layer | Status |
|---|---|
| QNAP firmware | EOL (no future updates for older models) |
| Bundled OpenSSL | TLS 1.0 only — Cloudflare CDN refuses |
| Bundled ClamAV | 0.99.3 (2018), recommends 1.0.9 |
| `freshclam` direct | Fails with "ssl3_read_bytes:tlsv1 alert protocol version" |

Solution: **download fresh sigs on the hub** (modern TLS), `scp` to NAS, update NAS `LastDBUpdate` config so the Web UI shows "update successful".

### Implementation: `nas-clamav-update.sh`

Runs daily 04:30 on hub:

```bash
1. curl -A 'ClamAV/1.0.9 (OS: linux-gnu)' -O https://database.clamav.net/main.cvd
   (also daily.cvd, bytecode.cvd)
2. Compare to local cache; skip scp if unchanged
3. scp $f admin@<NAS_IP>:/share/<volume>/.antivirus/usr/share/clamav/
4. ssh NAS:
     - rm stale main.cld / daily.cld / bytecode.cld
     - setcfg Antivirus LastDBUpdate "$NOW" -f /etc/config/antivirus.global
     - setcfg Antivirus AntivirusStatus 4 -f /etc/config/antivirus.global  # 4 = update successful
```

### `User-Agent` matters

`clamav.net` Cloudflare CDN returns 403 to plain `curl`. Set User-Agent to mimic freshclam:

```bash
curl -A 'ClamAV/1.0.9 (OS: linux-gnu, ARCH: x86_64, CPU: x86_64)' \
    https://database.clamav.net/main.cvd
```

### Where the sigs live on QNAP

```
/share/<VOLUME>/.antivirus/usr/share/clamav/
    main.cvd      ~85 MB (changes infrequently, weekly-ish)
    daily.cvd     ~22 MB (updates ~daily)
    bytecode.cvd  ~280 KB
```

Find your volume:
```bash
ssh admin@<NAS_IP> 'getcfg Public path -f /etc/config/smb.conf | cut -d/ -f3'
# Returns e.g. MD1_DATA, CACHEDEV1_DATA
```

### `AntivirusStatus` values

```
0/empty = idle
1       = scan complete
2       = scan stopped
3       = currently updating
4       = update successful   ← what we set after proxy push
5       = update failed
```

If you don't set `AntivirusStatus = 4`, the Web UI keeps showing "更新失敗 / Update failed" forever even though the sigs are fresh.

## SSH key auth (hub → NAS)

QNAP has TWO `authorized_keys` locations:

```
/share/homes/admin/.ssh/authorized_keys     ← VOLATILE (wiped on reboot)
/etc/config/ssh/authorized_keys             ← PERSISTENT (survives reboot)
```

**Always use the persistent one**. Push hub's pubkey:

```bash
HUB_PUB=$(ssh root@hub 'cat /root/.ssh/id_ed25519.pub')

# Push to NAS via password ssh (one-time)
sshpass -p "$NAS_PASS" ssh admin@<NAS_IP> "
mkdir -p /etc/config/ssh
chmod 700 /etc/config/ssh
echo '$HUB_PUB' >> /etc/config/ssh/authorized_keys
chmod 600 /etc/config/ssh/authorized_keys
# Also copy to volatile location for current session
mkdir -p /share/homes/admin/.ssh
chmod 700 /share/homes/admin/.ssh
cp /etc/config/ssh/authorized_keys /share/homes/admin/.ssh/authorized_keys
chmod 600 /share/homes/admin/.ssh/authorized_keys
"
```

Test: `ssh root@hub 'ssh admin@<NAS_IP> hostname'` should return NAS hostname without password prompt.

## Quarantine cleanup

QNAP antivirus quarantines files matching ClamAV signatures. Files moved from original path to:

```
/share/<VOLUME>/.antivirus/quarantine/<original-path-mirrored>
```

Index in `/etc/config/antivirus.quarantine` (INI format with `[Infected-X.Y]` blocks).

### Common false-positive categories

| FP source | Why ClamAV flags |
|---|---|
| Realtek HD Audio drivers (`AlcWzrd.exe`, `MicCal.exe`) | VB6/Borland packed binaries — generic Trojan signature |
| Old MSI installers (`409.msi`) | MSI container heuristic |
| AutoIt-compiled tools (`CSEdit.exe`, ERP tools) | `Win.Dropper.Autoit` signature |
| NI LabVIEW installers (`ni_error.cab`) | `Win.Malware.Separ` signature |
| 7-Zip self-extracting installers | `Win.Virus.Pioneer` signature |
| Avast antivirus installer (older versions) | mutual paranoia |

These appear in IT tool repositories — restoring + adding scan exclusion is the right call.

### Real malware to actually delete

| Threat | Real risk |
|---|---|
| Crack/keygen tools | High — pirated software has known backdoor history |
| ASUS LiveUpdate (pre-2019/Jul) | **ShadowHammer** supply chain compromise (2019) — real |
| Old Microsoft Office files (`CVE-2018-5028`) | Possible exploit payload in PowerPoint |
| `Win.Virus.Sality` matches | Old Windows worm — usually in archived data |

### Restore + scan exclusion script

```bash
QBASE=/share/<VOLUME>/.antivirus/quarantine

# Find all files in IT tool area
find "$QBASE/share/$IT_TOOL_PATH" -type f | while read f; do
    target="${f#$QBASE}"
    mkdir -p "$(dirname "$target")"
    mv "$f" "$target"
done

# Add path to scan exclusion (Job 1 = weekly scan)
JOBS=/etc/config/antivirus.jobs
EXCLUDE="<path1>;<path2>;..."  # semicolon-separated
setcfg "Job 1" "JobExcludeEnable" "1" -f "$JOBS"
setcfg "Job 1" "JobExcludeFilesDirs" "$EXCLUDE" -f "$JOBS"
```

### Purge all remaining (after careful review)

```bash
QBASE=/share/<VOLUME>/.antivirus/quarantine

# Backup config first
cp /etc/config/antivirus.quarantine /etc/config/antivirus.quarantine.bak-$(date +%Y%m%d)

# Delete all files
find $QBASE -type f -delete
find $QBASE -type d -empty -delete

# Reset config
echo "" > /etc/config/antivirus.quarantine
```

Web UI shows cached state until you refresh the 隔離區 (quarantine) tab.

## QNAP API auth (when SSH not preferred)

```bash
# Login (returns sid)
B64PASS=$(printf %s "$NAS_PASS" | base64)
SID=$(curl -sk "http://<NAS_IP>:8080/cgi-bin/authLogin.cgi?user=admin&pwd=$B64PASS" \
    | sed -n 's/.*<authSid><!\[CDATA\[\(.*\)\]\]><\/authSid>.*/\1/p')

# Use sid for further API calls
curl -sk "http://<NAS_IP>:8080/cgi-bin/.../endpoint?sid=$SID&..."
```

Most operations are easier via SSH; API needed mainly for things SSH can't do (e.g. trigger Web UI scan jobs without manual CLI).

## When to give up — replace the NAS

Symptoms that indicate NAS replacement is overdue:

- TLS issues (this module's whole reason)
- ClamAV engine years out of date
- 1 GB RAM bottleneck (multi-user SMB load)
- 13+ year hardware (disk SMART rising)
- QTS firmware EOL (no security patches)

Modern equivalent: TS-x53D / TS-x73A / TS-x33A class. ~USD $400-1000 for a small business 4-bay. Includes:
- Modern OpenSSL (freshclam works directly)
- Container Station for arbitrary Docker workloads
- ClamAV 1.x or modern alternatives

When you replace, this proxy module becomes unnecessary — `freshclam` runs on the new NAS directly.
