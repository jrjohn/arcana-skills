#!/usr/bin/env python3
"""
Sync /opt/mis-http/threatfeed.txt → FG firewall/address (TFI- prefix) +
nested addrgrp Threatfeed-Inbound-Auto (8 sub-groups of ≤500 members each,
because FG-100D addrgrp member limit ≈ 597).

Used by FG local-in-policy id=5/6 to block inbound probing from known-bad IPs.
Mirror of P33 outbound (which uses external-resource directly — local-in-policy
in FortiOS 6.2.17 doesn't accept external-resource references).

Idempotent. Reconciles state. Run via cron every 30 min.
"""
import urllib.request, ssl, json, ipaddress, hashlib, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

FEED_FILE   = '/opt/mis-http/threatfeed.txt'
FG_HOST     = 'https://10.0.0.1'
PARENT      = 'Threatfeed-Inbound-Auto'
SUB_PREFIX  = 'Threatfeed-Inbound-Auto-'
N_BUCKETS   = 8        # 3209/8 ≈ 401 per bucket, safe under 597 limit
PREFIX      = 'TFI-'
TOKEN       = open('/root/.fg_token').read().strip()
LOG         = '/var/log/mis/threatfeed-fg-sync.log'
WORKERS     = 10

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
Path(LOG).parent.mkdir(parents=True, exist_ok=True)

def log(m):
    line = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {m}'
    print(line); open(LOG,'a').write(line+'\n')

def api(method, path, body=None):
    url = f'{FG_HOST}/api/v2/cmdb{path}?access_token={TOKEN}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={'Content-Type':'application/json'})
    try:
        return json.loads(urllib.request.urlopen(req, context=ctx, timeout=60).read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except: return {'error': str(e), 'http_status': e.code}

def entry_name(e):
    return f'{PREFIX}{e.replace("/","-")}'

def entry_subnet(e):
    n = ipaddress.IPv4Network(e, strict=False)
    return f'{n.network_address} {n.netmask}'

def bucket_for(name):
    return int(hashlib.md5(name.encode()).hexdigest(), 16) % N_BUCKETS

def load_feed():
    out = {}
    for line in open(FEED_FILE):
        e = line.strip()
        if not e or e.startswith('#'): continue
        try:
            ipaddress.IPv4Network(e, strict=False)
            out[entry_name(e)] = entry_subnet(e)
        except ValueError:
            log(f'skip invalid: {e}')
    return out

def list_addresses():
    r = api('GET', '/firewall/address')
    return {a['name']: a.get('subnet','') for a in r.get('results',[]) if a.get('name','').startswith(PREFIX)}

def add_address(name, subnet):
    return name, api('POST', '/firewall/address',
                     {'name': name, 'type': 'ipmask', 'subnet': subnet,
                      'comment': 'auto: threatfeed.txt'}).get('http_status')

def del_address(name):
    return name, api('DELETE', f'/firewall/address/{name}').get('http_status')

def upsert_subgroup(idx, members):
    name = f'{SUB_PREFIX}{idx}'
    body = {'member': [{'name': n} for n in sorted(members)]}
    r = api('GET', f'/firewall/addrgrp/{name}')
    if r.get('http_status') == 404:
        body['name'] = name
        body['comment'] = f'auto sub-group {idx}/{N_BUCKETS-1} for {PARENT}'
        return api('POST', '/firewall/addrgrp', body).get('http_status')
    else:
        return api('PUT', f'/firewall/addrgrp/{name}', body).get('http_status')

def main():
    log(f'--- sync start (buckets={N_BUCKETS}, workers={WORKERS}) ---')
    feed = load_feed()
    have = list_addresses()
    log(f'feed: {len(feed)}  current TFI-*: {len(have)}')

    add_set = set(feed) - set(have)
    del_set = set(have) - set(feed)
    log(f'address ops: +{len(add_set)} -{len(del_set)}')

    add_ok = del_ok = add_fail = del_fail = 0
    if add_set:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for f in as_completed([ex.submit(add_address, n, feed[n]) for n in add_set]):
                n, s = f.result()
                if s == 200: add_ok += 1
                else: add_fail += 1; log(f'  ADD FAIL {n}: {s}')
    if del_set:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for f in as_completed([ex.submit(del_address, n) for n in del_set]):
                n, s = f.result()
                if s == 200: del_ok += 1
                else: del_fail += 1; log(f'  DEL FAIL {n}: {s}')
    log(f'addr  done: +{add_ok}/{len(add_set)} -{del_ok}/{len(del_set)}')

    # Bucket and upsert sub-groups
    buckets = {i: [] for i in range(N_BUCKETS)}
    for n in feed:
        buckets[bucket_for(n)].append(n)
    for i, members in buckets.items():
        s = upsert_subgroup(i, members)
        log(f'  sub-grp {SUB_PREFIX}{i}: {len(members)} members → http {s}')

    # Parent group reconciles to point to all sub-groups
    parent_body = {'member': [{'name': f'{SUB_PREFIX}{i}'} for i in range(N_BUCKETS)]}
    s = api('PUT', f'/firewall/addrgrp/{PARENT}', parent_body).get('http_status')
    log(f'parent {PARENT}: → http {s}')

    log(f'--- sync end (total members across buckets: {sum(len(v) for v in buckets.values())}) ---')

if __name__ == '__main__':
    main()
