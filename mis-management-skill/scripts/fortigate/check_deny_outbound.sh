#!/bin/bash
LOG=/var/log/remote/fortigate/fortigate.log
CUTOFF_NS=$(( ($(date +%s) - 3600) * 1000000000 ))
read HITS UNIQ_SRC < <(awk -v c="$CUTOFF_NS" '
  /srcintf="lan"/ && /action="deny"/ {
    if (match($0, /eventtime=[0-9]+/)) {
      et = substr($0, RSTART+10, RLENGTH-10) + 0
      if (et >= c) {
        n++
        if (match($0, /srcip=[0-9.]+/)) {
          ip = substr($0,RSTART+6,RLENGTH-6); m[ip]++; src[ip]=1
        }
      }
    }
  } END {
    u=0; for (s in src) u++; print n+0, u+0
    for (i in m) print m[i] " " i > "/tmp/.deny_out"
  }' "$LOG")
TOP=$(sort -rn /tmp/.deny_out 2>/dev/null | head -3 | awk '{printf "%s[%d] ", $2, $1}')
rm -f /tmp/.deny_out
if   [ $HITS -ge 50000 ]; then S=CRITICAL; C=2
elif [ $HITS -ge 10000 ]; then S=WARNING; C=1
else S=OK; C=0
fi
echo "$S - $HITS outbound denies/h - top srcs:[$TOP]|hits=$HITS;10000;50000;0; uniq_src=$UNIQ_SRC;;;0;"
exit $C
