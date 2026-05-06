#!/usr/bin/env python3
"""Read /opt/mis-http/dns-ai-counts.json events list → accumulate into mis-log.db dns_ai_events table.

Idempotent: PK on (ts, src, qname, ip) so re-running is safe.
"""
import json, sqlite3, sys, os

DB = '/opt/mis-log-db/mis-log.db'
SRC = '/opt/mis-http/dns-ai-counts.json'

if not os.path.exists(SRC):
    print(f'no source: {SRC}'); sys.exit(0)

with open(SRC, 'rb') as f:
    raw = f.read()
if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
d = json.loads(raw)

evs = d.get('events', [])
if not evs:
    print('no events'); sys.exit(0)

con = sqlite3.connect(DB)
con.execute("PRAGMA busy_timeout = 5000")
cur = con.cursor()
inserted = 0
for e in evs:
    ts, src, qname, svc, ips = e['ts'], e['src'], e['qname'], e['service'], e.get('ips') or []
    for ip in ips:
        cur.execute(
            'INSERT OR IGNORE INTO dns_ai_events (ts, src_ip, qname, service, ip) VALUES (?,?,?,?,?)',
            (ts, src, qname, svc, ip)
        )
        inserted += cur.rowcount
con.commit()

# stats
total = cur.execute('SELECT COUNT(*) FROM dns_ai_events').fetchone()[0]
oldest, newest = cur.execute('SELECT MIN(ts), MAX(ts) FROM dns_ai_events').fetchone()
con.close()
print(f'ingested {inserted} new rows | table total={total} | range {oldest} → {newest}')
