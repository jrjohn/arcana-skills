#!/bin/bash
# Generate full top-20 deny reports as HTML, served via :8081/deny-report.html
# Runs every 5 min from cron.
LOG=/var/log/remote/fortigate/fortigate.log
OUT=${WEB_ROOT:-/opt/mis-http}/deny-report.html
NOW_NS=$(( $(date +%s) * 1000000000 ))
CUTOFF_NS=$(( NOW_NS - 3600000000000 ))

INBOUND=$(awk -v c="$CUTOFF_NS" '
  /srcintf="wan[12]"/ && /action="deny"/ {
    if (match($0, /eventtime=[0-9]+/)) {
      et = substr($0, RSTART+10, RLENGTH-10) + 0
      if (et >= c) {
        if (match($0, /srcip=[0-9.]+/))   ip = substr($0, RSTART+6, RLENGTH-6)
        if (match($0, /dstport=[0-9]+/))  dp = substr($0, RSTART+8, RLENGTH-8)
        if (match($0, /srccountry="[^"]+"/)) cc = substr($0, RSTART+12, RLENGTH-13)
        if (match($0, /service="[^"]+"/)) svc = substr($0, RSTART+9, RLENGTH-10)
        m[ip]++
        port[ip][dp]++
        country[ip] = cc
        last_svc[ip] = svc
      }
    }
  } END {
    for (i in m) {
      best_p = ""; best_pn = 0
      for (p in port[i]) if (port[i][p] > best_pn) { best_pn = port[i][p]; best_p = p }
      print m[i] "\t" i "\t" country[i] "\t" best_p "(" best_pn ")\t" last_svc[i]
    }
  }' "$LOG" | sort -rn | head -20)

OUTBOUND=$(awk -v c="$CUTOFF_NS" '
  /srcintf="lan"/ && /action="deny"/ {
    if (match($0, /eventtime=[0-9]+/)) {
      et = substr($0, RSTART+10, RLENGTH-10) + 0
      if (et >= c) {
        if (match($0, /srcip=[0-9.]+/))   ip = substr($0, RSTART+6, RLENGTH-6)
        if (match($0, /dstport=[0-9]+/))  dp = substr($0, RSTART+8, RLENGTH-8)
        if (match($0, /dstcountry="[^"]+"/)) cc = substr($0, RSTART+12, RLENGTH-13)
        if (match($0, /service="[^"]+"/)) svc = substr($0, RSTART+9, RLENGTH-10)
        m[ip]++
        port[ip][dp]++
        last_svc[ip] = svc
        last_cc[ip] = cc
      }
    }
  } END {
    for (i in m) {
      best_p = ""; best_pn = 0
      for (p in port[i]) if (port[i][p] > best_pn) { best_pn = port[i][p]; best_p = p }
      print m[i] "\t" i "\t" last_cc[i] "\t" best_p "(" best_pn ")\t" last_svc[i]
    }
  }' "$LOG" | sort -rn | head -20)

cat > "$OUT" <<HTML
<!doctype html>
<html><head><meta charset="utf-8"><title>FG Deny Top 20 (last 1h)</title>
<meta http-equiv="refresh" content="60">
<style>
body{font-family:-apple-system,Segoe UI,sans-serif;margin:20px;background:#fafafa}
h2{margin-top:30px;color:#333}
table{border-collapse:collapse;width:100%;background:white;box-shadow:0 1px 3px rgba(0,0,0,.1)}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #eee}
th{background:#444;color:white;font-weight:500}
tr:hover{background:#f0f8ff}
.count{font-weight:bold;color:#c00}
.meta{color:#888;font-size:12px}
</style></head><body>
<h1>FortiGate Deny Top 20 (last 1h)</h1>
<p class="meta">Generated: $(date '+%Y-%m-%d %H:%M:%S')  ·  Auto-refresh: 60s  ·  Window: 60min</p>

<h2>📥 Inbound — wan → lan/dmz (外部攻擊 / 掃描)</h2>
<table>
<tr><th>#</th><th>Hits</th><th>Source IP</th><th>Country</th><th>Top dst port</th><th>Service</th></tr>
HTML

i=0
while IFS=$'\t' read hits ip country port svc; do
  i=$((i+1))
  echo "<tr><td>$i</td><td class=count>$hits</td><td>$ip</td><td>$country</td><td>$port</td><td>$svc</td></tr>" >> "$OUT"
done <<< "$INBOUND"

cat >> "$OUT" <<HTML
</table>

<h2>📤 Outbound — lan → wan (內部對外 / 看誰不正常)</h2>
<table>
<tr><th>#</th><th>Hits</th><th>Source IP</th><th>Top dst country</th><th>Top dst port</th><th>Service</th></tr>
HTML

i=0
while IFS=$'\t' read hits ip country port svc; do
  i=$((i+1))
  echo "<tr><td>$i</td><td class=count>$hits</td><td>$ip</td><td>$country</td><td>$port</td><td>$svc</td></tr>" >> "$OUT"
done <<< "$OUTBOUND"

cat >> "$OUT" <<HTML
</table>
<p class="meta">Source: /var/log/remote/fortigate/fortigate.log  ·  Refreshed by ${MIS_HOME:-/opt/mis-log-db}/gen-deny-report.sh (cron @ */5 min)</p>
</body></html>
HTML

echo "wrote $OUT ($(stat -c%s $OUT) bytes)"
