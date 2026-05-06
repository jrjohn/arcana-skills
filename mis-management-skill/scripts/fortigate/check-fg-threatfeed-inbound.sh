#!/bin/bash
# Nagios-format check for FG inbound threatfeed block hit count.
# Counts policyid=5/6 + subtype=local denies in the last 5 min (matches LibreNMS poll cadence).
# Used by LibreNMS service check via check_by_ssh.
LOG=/var/log/remote/fortigate/fortigate.log
NOW=$(date +%s)
CUTOFF=$((NOW - 300))

# Count hits + unique src IPs in last 5 min window
COUNT=$(awk -v c=$CUTOFF -F'eventtime=' '
  /policyid=5/ || /policyid=6/ {
    if (!/subtype="local"/) next
    split($2, a, " ")
    ts = substr(a[1], 1, 10) + 0
    if (ts >= c) print
  }' "$LOG" 2>/dev/null | wc -l)

UNIQ_SRC=$(awk -v c=$CUTOFF -F'eventtime=' '
  /policyid=5/ || /policyid=6/ {
    if (!/subtype="local"/) next
    split($2, a, " ")
    ts = substr(a[1], 1, 10) + 0
    if (ts >= c) print
  }' "$LOG" 2>/dev/null | grep -oE 'srcip=[0-9.]+' | sort -u | wc -l)

# Total feed members (gauges threatfeed list size)
FEED=$(wc -l < ${WEB_ROOT:-/opt/mis-http}/threatfeed.txt 2>/dev/null || echo 0)

# Nagios output: status code 0 = OK (just reporting metrics, no threshold)
echo "OK - $COUNT inbound threatfeed denies/5min from $UNIQ_SRC unique IPs (feed_size=$FEED) | denies=$COUNT;;;0 unique_src=$UNIQ_SRC;;;0 feed_size=$FEED;;;0"
exit 0
