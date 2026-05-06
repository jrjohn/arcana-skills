#!/bin/bash
LOG=/var/log/remote/fortigate/fortigate.log
CUTOFF_NS=$(( ($(date +%s) - 3600) * 1000000000 ))
read HITS TOP < <(awk -v c="$CUTOFF_NS" '
  /srcintf="wan[12]"/ && /action="deny"/ {
    if (match($0, /eventtime=[0-9]+/)) {
      et = substr($0, RSTART+10, RLENGTH-10) + 0
      if (et >= c) {
        n++
        if (match($0, /srcip=[0-9.]+/)) m[substr($0,RSTART+6,RLENGTH-6)]++
      }
    }
  } END {
    print n+0, " "
    for (i in m) print m[i] " " i > "/tmp/.deny_in"
  }' "$LOG")
TOP=$(sort -rn /tmp/.deny_in 2>/dev/null | head -3 | awk '{printf "%s[%d] ", $2, $1}')
rm -f /tmp/.deny_in
if   [ $HITS -ge 5000 ]; then S=CRITICAL; C=2
elif [ $HITS -ge 1000 ]; then S=WARNING; C=1
else S=OK; C=0
fi
echo "$S - $HITS inbound denies/h - top srcs:[$TOP]|hits=$HITS;1000;5000;0;"
exit $C
