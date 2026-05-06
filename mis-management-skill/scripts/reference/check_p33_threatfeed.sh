#!/bin/bash
LOG=/var/log/remote/fortigate/fortigate.log
CUTOFF_NS=$(( ($(date +%s) - 3600) * 1000000000 ))
read HITS UNIQ_SRC < <(awk -v c="$CUTOFF_NS" '
  /policyid=33/ && /action="deny"/ {
    if (match($0, /eventtime=[0-9]+/)) {
      et = substr($0, RSTART+10, RLENGTH-10) + 0
      if (et >= c) {
        n++
        if (match($0, /srcip=[0-9.]+/)) src[substr($0,RSTART+6,RLENGTH-6)]=1
      }
    }
  } END { u=0; for (s in src) u++; print n+0, u+0 }' "$LOG")
if   [ $HITS -ge 50 ]; then S=CRITICAL; C=2
elif [ $HITS -ge 10 ]; then S=WARNING; C=1
else S=OK; C=0
fi
echo "$S - $HITS ThreatFeed hits / $UNIQ_SRC uniq src in last 60min|hits=$HITS;10;50;0; uniq_src=$UNIQ_SRC;;;0;"
exit $C
