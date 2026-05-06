#!/bin/bash
KEY=/root/.ssh/console_relay_ed25519
set -e

# Run aggregator on .206
ssh -n -i $KEY -o StrictHostKeyChecking=no administrator@<AD_IP> \
  'powershell -ExecutionPolicy Bypass -File C:/scripts/dns-ai-aggregator.ps1' >/dev/null 2>&1

# Fetch JSON
scp -i $KEY -o StrictHostKeyChecking=no \
  administrator@<AD_IP>:'C:/dns-ai-counts.json' \
  ${WEB_ROOT:-/opt/mis-http}/dns-ai-counts.json >/dev/null 2>&1

# Strip BOM + filter out FortiGate (.1) — its DNS resolver activity is not user attribution
python3 << 'PYEOF'
import json
SRC = '${WEB_ROOT:-/opt/mis-http}/dns-ai-counts.json'
EXCLUDE_IPS = {'<FG_IP>'}  # FortiGate own DNS resolution; not a user

with open(SRC, 'rb') as f:
    d = f.read()
if d.startswith(b'\xef\xbb\xbf'):
    d = d[3:]
obj = json.loads(d)

# Filter rows (per-user summary)
before_rows = len(obj.get('rows', []))
obj['rows'] = [r for r in obj.get('rows', []) if r.get('ip') not in EXCLUDE_IPS]
# Filter events (raw event log)
before_evs = len(obj.get('events', []))
obj['events'] = [e for e in obj.get('events', []) if e.get('src') not in EXCLUDE_IPS]
removed_rows = before_rows - len(obj['rows'])
removed_evs = before_evs - len(obj['events'])

with open(SRC, 'w') as f:
    json.dump(obj, f, separators=(',', ':'), ensure_ascii=False)

if removed_rows or removed_evs:
    print(f'fetch-dns-ai: filtered {removed_rows} rows + {removed_evs} events from FortiGate (.1)')
PYEOF

# Accumulate events into mis-log.db
python3 ${MIS_HOME:-/opt/mis-log-db}/ingest-dns-ai-events.py >/dev/null 2>&1

# Compute attribution (DNS-IP correlation × user_dest)
python3 ${MIS_HOME:-/opt/mis-log-db}/correlate-dns-ai.py >/dev/null 2>&1
