#!/bin/bash
# nas-clamav-update.sh — fetch ClamAV sigs from .200 (modern TLS), push to NAS .14
#
# Why .200 not NAS: QNAP's bundled ClamAV is 0.99.3 (2018) and its OpenSSL
# can't TLS 1.2+ to clamav.net CDN. .200 (CentOS 8) has modern TLS so we
# download here then scp to NAS.
#
# Schedule: cron daily 04:30 (well before NAS scheduled scan Friday 20:00).

set -uo pipefail

NAS=<LAN_NET>.14
NAS_USER=admin
NAS_SIG_DIR=/share/MD1_DATA/.antivirus/usr/share/clamav
WORK_DIR=/var/tmp/nas-clamav
LOG_TAG=nas-clamav-update
UA='ClamAV/1.0.9 (OS: linux-gnu, ARCH: x86_64, CPU: x86_64)'

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

log() { echo "[$(date -Iseconds)] $*"; }

ok=0
for f in main.cvd daily.cvd bytecode.cvd; do
    log "downloading $f"
    new="${f}.new"
    http=$(curl -sL -A "$UA" -o "$new" -w "%{http_code}" "https://database.clamav.net/$f")
    sz=$(stat -c%s "$new" 2>/dev/null || echo 0)
    if [ "$http" != "200" ] || [ "$sz" -lt 100000 ]; then
        log "  FAIL: http=$http size=$sz — keep old, skip"
        rm -f "$new"
        continue
    fi
    # Compare to local cache; skip scp if identical
    if [ -f "$f" ] && cmp -s "$f" "$new"; then
        log "  unchanged ($sz bytes) — skip scp"
        rm -f "$new"
        continue
    fi
    mv "$new" "$f"
    log "  scp $f → $NAS:$NAS_SIG_DIR/  ($sz bytes)"
    if scp -q -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        "$f" "$NAS_USER@$NAS:$NAS_SIG_DIR/"; then
        ok=$((ok+1))
    else
        log "  scp FAILED"
    fi
done

if [ "$ok" -gt 0 ]; then
    # Drop conflicting .cld + update LastDBUpdate
    NOW=$(date "+%Y/%m/%d %H:%M:%S")
    log "updating NAS state (rm .cld + setcfg LastDBUpdate=$NOW)"
    ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        "$NAS_USER@$NAS" \
        "rm -f $NAS_SIG_DIR/main.cld $NAS_SIG_DIR/daily.cld $NAS_SIG_DIR/bytecode.cld 2>/dev/null
         /sbin/setcfg Antivirus LastDBUpdate \"$NOW\" -f /etc/config/antivirus.global; /sbin/setcfg Antivirus AntivirusStatus 4 -f /etc/config/antivirus.global"
    log "done — $ok file(s) updated"
else
    log "no updates — sigs unchanged or download failed"
fi
