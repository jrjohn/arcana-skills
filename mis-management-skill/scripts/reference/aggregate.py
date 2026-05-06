#!/usr/bin/env python3
"""
Parse FG log P6 traffic events, aggregate to SQLite.

v2 fix (2026-04-24):
  - session_id added to PRIMARY KEY so same session across multiple log entries
    (start → accept periodic → close) collapses to one row
  - bytes_sent/bytes_recv use MAX() not SUM() — FG emits cumulative values per
    accept/close entry for the same session, so SUM over-counts by the number
    of emitted entries (seen 13× inflation on .90 MAX Wed).
  - accept multiple action types instead of only "accept":
      start / accept / close / timeout / server-rst / client-rst
    (skip "deny" — those are dropped, no legit bytes; skip "ip-conn" — no bytes info)
"""
import re, sqlite3, sys, os, time
from datetime import datetime

DB = '/opt/mis-log-db/mis-log.db'
LOG = '/var/log/remote/fortigate/fortigate.log'
STATE = '/opt/mis-log-db/.offset'

VALID_ACTIONS = {'close', 'timeout', 'server-rst', 'client-rst'}  # v3 2026-04-28 — drop start/accept (cumulative bytes per session = double-count when crossing hour boundary)

INTERNAL_PREFIX = ('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
                   '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                   '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')

FIELD_RE = {
    'date':        re.compile(r'\bdate=(\S+)'),
    'time':        re.compile(r'\btime=(\S+)'),
    'srcip':       re.compile(r'\bsrcip=(\S+)'),
    'dstip':       re.compile(r'\bdstip=(\S+)'),
    'dstport':     re.compile(r'\bdstport=(\S+)'),
    'proto':       re.compile(r'\bproto=(\S+)'),
    'sessionid':   re.compile(r'\bsessionid=(\d+)'),
    'action':      re.compile(r'\baction="([^"]+)"'),
    'service':     re.compile(r'\bservice="([^"]+)"'),
    'dstcountry':  re.compile(r'\bdstcountry="([^"]+)"'),
    'sentbyte':    re.compile(r'\bsentbyte=(\d+)'),
    'rcvdbyte':    re.compile(r'\brcvdbyte=(\d+)'),
}


def get_offset():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return int(f.read().strip() or '0')
    return 0


def save_offset(off):
    with open(STATE, 'w') as f:
        f.write(str(off))


def parse_fg(line):
    if 'policyid=6' not in line or 'subtype="forward"' not in line:
        return None
    out = {}
    for k, rx in FIELD_RE.items():
        m = rx.search(line)
        if m:
            out[k] = m.group(1)
    if 'action' not in out or out['action'] not in VALID_ACTIONS:
        return None
    if 'srcip' not in out or 'dstip' not in out or 'sessionid' not in out:
        return None
    return out


def main():
    off = get_offset()
    log_size = os.path.getsize(LOG)
    if log_size < off:
        off = 0

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    cur = conn.cursor()

    count = skipped = 0
    # batch keyed by (date, hour, src, dst, dport, proto, session_id)
    batch = {}

    proto_map = {'6': 'tcp', '17': 'udp', '1': 'icmp'}

    with open(LOG, 'rb') as f:
        f.seek(off)
        for raw in f:
            try:
                line = raw.decode('utf-8', errors='ignore')
            except Exception:
                continue
            data = parse_fg(line)
            if not data:
                skipped += 1
                continue

            dst = data['dstip']
            if dst.startswith(INTERNAL_PREFIX):
                skipped += 1
                continue

            try:
                dt = datetime.strptime(f"{data['date']} {data['time']}", "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            proto = proto_map.get(data.get('proto', ''), data.get('proto', ''))
            sid = int(data['sessionid'])
            dport = int(data.get('dstport') or 0)
            sent = int(data.get('sentbyte') or 0)
            recv = int(data.get('rcvdbyte') or 0)

            key = (dt.strftime('%Y-%m-%d'), dt.hour, data['srcip'], dst, dport, proto, sid)

            count += 1
            if key in batch:
                b = batch[key]
                if sent > b['bytes_sent']:
                    b['bytes_sent'] = sent
                if recv > b['bytes_recv']:
                    b['bytes_recv'] = recv
                b['hit_count'] += 1
                b['last_seen'] = dt.isoformat()
                # last-known country/service
                if data.get('dstcountry'):
                    b['dst_country'] = data['dstcountry']
                if data.get('service'):
                    b['service'] = data['service']
            else:
                batch[key] = {
                    'dst_country': data.get('dstcountry', ''),
                    'service': data.get('service', ''),
                    'hit_count': 1,
                    'bytes_sent': sent,
                    'bytes_recv': recv,
                    'first_seen': dt.isoformat(),
                    'last_seen': dt.isoformat(),
                }
        new_off = f.tell()

    # Upsert batch → DB; MAX semantics on bytes (cross-run safety)
    for k, v in batch.items():
        date, hour, src_ip, dst_ip, dst_port, proto, sid = k
        cur.execute("""
            INSERT INTO user_dest(date, hour, src_ip, dst_ip, dst_port, proto, session_id,
                                  dst_country, service, hit_count, bytes_sent, bytes_recv,
                                  first_seen, last_seen)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(date, hour, src_ip, dst_ip, dst_port, proto, session_id) DO UPDATE SET
              hit_count  = hit_count + excluded.hit_count,
              bytes_sent = MAX(bytes_sent, excluded.bytes_sent),
              bytes_recv = MAX(bytes_recv, excluded.bytes_recv),
              last_seen  = excluded.last_seen,
              dst_country = COALESCE(NULLIF(excluded.dst_country,''), dst_country),
              service     = COALESCE(NULLIF(excluded.service,''),     service)
        """, (date, hour, src_ip, dst_ip, dst_port, proto, sid,
              v['dst_country'], v['service'], v['hit_count'],
              v['bytes_sent'], v['bytes_recv'], v['first_seen'], v['last_seen']))

    conn.commit()
    conn.close()
    save_offset(new_off)
    print(f"parsed={count} skipped={skipped} sessions={len(batch)} new_offset={new_off}")


if __name__ == '__main__':
    main()
