#!/bin/bash
# Poll FG ARP every minute, append IP→MAC to ${MIS_HOME:-/opt/mis-log-db}/mac-history.tsv (deduped)
T=$(cat /root/.fg_token)
HIST=${MIS_HOME:-/opt/mis-log-db}/mac-history.tsv

curl -sk "https://<FG_IP>/api/v2/monitor/system/arp?access_token=$T" 2>/dev/null > /tmp/arp-snapshot.json

python3 << 'PY'
import json, os, time
hist_path = '${MIS_HOME:-/opt/mis-log-db}/mac-history.tsv'

# Load existing
existing = {}
if os.path.exists(hist_path):
    with open(hist_path) as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 2: existing[(parts[0], parts[1])] = True

# Read new ARP
try:
    d = json.load(open('/tmp/arp-snapshot.json'))
except:
    raise SystemExit(0)

ts = time.strftime('%Y-%m-%d %H:%M:%S')
new = 0
with open(hist_path, 'a') as f:
    for r in d.get('results', []):
        ip = r.get('ip','')
        mac = r.get('mac','')
        if not (ip.startswith('192.168.') and mac and mac != '00:00:00:00:00:00'):
            continue
        key = (ip, mac)
        if key not in existing:
            f.write(f'{ip}\t{mac}\t{ts}\n')
            new += 1
print(f'  appended {new} new IP→MAC pairs (total file: {sum(1 for _ in open(hist_path))} lines)')
PY
