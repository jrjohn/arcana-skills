#!/usr/bin/env python3
"""Join dns_ai_events × user_dest → DNS-IP-correlated AI attribution.

For each user_dest row whose dst_ip ever appeared as a DNS-resolved AI service IP,
find the most recent matching DNS event for the same (src_ip, dst_ip) within
WINDOW_MIN minutes BEFORE the user_dest first_seen — that event's service tag
gets the bytes attributed.

Output: /opt/mis-http/dns-ai-attribution.json
"""
import sqlite3, json, datetime, os
from collections import defaultdict

LAN_NET = os.environ.get('LAN_NET', '10.0.0')  # set to your internal /24 prefix
DB = '/opt/mis-log-db/mis-log.db'
OUT = '/opt/mis-http/dns-ai-attribution.json'
WINDOW_MIN = 10

con = sqlite3.connect(DB)
con.execute("PRAGMA busy_timeout = 5000")
con.row_factory = sqlite3.Row
cur = con.cursor()

# Single SQL with correlated subquery picks the latest pre-flight DNS event
sql = f"""
WITH attributed AS (
  SELECT
    u.date,
    u.src_ip,
    u.dst_ip,
    u.bytes_sent,
    u.first_seen,
    (
      SELECT e.service FROM dns_ai_events e
      WHERE e.src_ip = u.src_ip
        AND e.ip     = u.dst_ip
        AND datetime(e.ts) <= datetime(u.first_seen)
        AND datetime(e.ts, '+{WINDOW_MIN} minutes') >= datetime(u.first_seen)
      ORDER BY datetime(e.ts) DESC LIMIT 1
    ) AS service
  FROM user_dest u
  WHERE u.src_ip LIKE '{LAN_NET}.%'
    AND u.dst_ip IN (SELECT DISTINCT ip FROM dns_ai_events)
)
SELECT date, src_ip, service, SUM(bytes_sent) AS bytes
FROM attributed WHERE service IS NOT NULL
GROUP BY date, src_ip, service
"""

rows = cur.execute(sql).fetchall()

# Rollup
daily_svc = defaultdict(int)            # (date, svc) -> bytes
daily_svc_users = defaultdict(set)      # (date, svc) -> {src_ip}
total_svc = defaultdict(int)            # svc -> bytes
total_svc_users = defaultdict(set)      # svc -> {src_ip}
user_svc = defaultdict(lambda: defaultdict(int))  # src -> svc -> bytes

for r in rows:
    date, src, svc, b = r['date'], r['src_ip'], r['service'], r['bytes'] or 0
    daily_svc[(date, svc)] += b
    daily_svc_users[(date, svc)].add(src)
    total_svc[svc] += b
    total_svc_users[svc].add(src)
    user_svc[src][svc] += b

# Build daily multi-line series for chart: dates × services matrix
all_dates = sorted({d for d, _ in daily_svc.keys()})
all_services = sorted(total_svc.keys(), key=lambda s: -total_svc[s])

daily_series = {svc: [] for svc in all_services}
for date in all_dates:
    for svc in all_services:
        b = daily_svc.get((date, svc), 0)
        daily_series[svc].append(round(b / 1024 / 1024, 2))

# Coverage stats
hit_user_dest_rows = cur.execute("""
  SELECT COUNT(*) FROM user_dest
  WHERE src_ip LIKE '{LAN_NET}.%'
    AND dst_ip IN (SELECT DISTINCT ip FROM dns_ai_events)
""").fetchone()[0]

unattributed_bytes = cur.execute(f"""
  WITH attributed AS (
    SELECT u.bytes_sent,
      (SELECT 1 FROM dns_ai_events e
        WHERE e.src_ip=u.src_ip AND e.ip=u.dst_ip
          AND datetime(e.ts) <= datetime(u.first_seen)
          AND datetime(e.ts, '+{WINDOW_MIN} minutes') >= datetime(u.first_seen)
        LIMIT 1) AS hit
    FROM user_dest u
    WHERE u.src_ip LIKE '{LAN_NET}.%'
      AND u.dst_ip IN (SELECT DISTINCT ip FROM dns_ai_events)
  )
  SELECT SUM(bytes_sent) FROM attributed WHERE hit IS NULL
""").fetchone()[0] or 0

con.close()

out = {
    'generated': datetime.datetime.now().isoformat(timespec='seconds'),
    'window_min': WINDOW_MIN,
    'attributed_rows': len(rows),
    'matching_user_dest_rows': hit_user_dest_rows,
    'unattributed_bytes': unattributed_bytes,
    'unattributed_mb': round(unattributed_bytes/1024/1024, 2),
    'totals_by_service': [
        {'service': s, 'mb': round(total_svc[s]/1024/1024, 2), 'users': len(total_svc_users[s])}
        for s in all_services
    ],
    'totals_by_user': [
        {'src': src, 'services': {svc: round(b/1024/1024, 2) for svc, b in svcs.items()},
         'total_mb': round(sum(svcs.values())/1024/1024, 2)}
        for src, svcs in sorted(user_svc.items(), key=lambda kv: -sum(kv[1].values()))
    ],
    'daily_labels': all_dates,
    'daily_series': daily_series,
}

with open(OUT, 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f'wrote {OUT}: {len(rows)} attributed rows, {len(all_services)} services, {len(all_dates)} dates')
print(f'totals by service:')
for t in out['totals_by_service']:
    print(f"  {t['service']:14s} {t['mb']:10.2f} MB  {t['users']} users")
print(f'unattributed: {out["unattributed_mb"]} MB across {hit_user_dest_rows - len(rows)} rows (DNS event missing within window)')
