#!/usr/bin/env python3
"""
Generate /opt/mis-log-db/ip-names.tsv automatically from authoritative sources:

  Primary  : NetBox  (.204:8006)  — IP address + contact assignment
  Fallback : FortiGate DHCP reserved-address description
  Manual   : /opt/mis-log-db/ip-names-manual.tsv  (overrides both — for non-NetBox/DHCP entries
             like infra labels: "FortiGate", "PABX", external services)

Output    : /opt/mis-log-db/ip-names.tsv  (atomic write)

Designed to be cron-friendly (silent on success, exit 0/1).
"""
import urllib.request, urllib.parse, ssl, json, os, sys, subprocess
from pathlib import Path

NB_URL    = 'http://10.0.0.204:8006'
NB_USER   = 'admin'
NB_PASS   = 'Ss25181598'
FG_HOST   = '10.0.0.1'
FG_TOKEN_FILE = '/root/.fg_token'
OUT       = '/opt/mis-log-db/ip-names.tsv'
MANUAL    = '/opt/mis-log-db/ip-names-manual.tsv'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def netbox_session():
    """Login to NetBox via web form, return cookie-jar string + csrf token."""
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=ctx),
    )

    # GET /login/ for csrf
    opener.open(NB_URL + '/login/').read()
    csrf = next((c.value for c in cj if c.name == 'csrftoken'), None)
    if not csrf:
        raise RuntimeError('NetBox login: no csrf cookie')

    data = urllib.parse.urlencode({
        'csrfmiddlewaretoken': csrf,
        'username': NB_USER,
        'password': NB_PASS,
        'next': '/',
    }).encode()
    req = urllib.request.Request(NB_URL + '/login/', data=data, headers={'Referer': NB_URL + '/login/'})
    opener.open(req).read()
    return opener


def fetch_all(opener, path):
    """Paginate NetBox list endpoint until no more 'next'."""
    url = NB_URL + path
    out = []
    while url:
        r = json.loads(opener.open(url).read())
        out.extend(r.get('results', []))
        url = r.get('next')
    return out


def get_netbox_ips():
    """Return {ip: 'Name (label)'} from NetBox IP + contact assignments."""
    opener = netbox_session()
    ips = fetch_all(opener, '/api/ipam/ip-addresses/?limit=200')

    # Build IP-id → contact-name map via contact-assignments
    asgs = fetch_all(opener, '/api/tenancy/contact-assignments/?limit=200')
    ip_to_contact = {}
    for a in asgs:
        if a.get('object_type') == 'ipam.ipaddress':
            obj_id = a.get('object_id')
            cname = (a.get('contact') or {}).get('display') or (a.get('contact') or {}).get('name')
            if obj_id and cname:
                # primary wins over secondary
                if a.get('priority', {}).get('value') == 'primary' or obj_id not in ip_to_contact:
                    ip_to_contact[obj_id] = cname

    result = {}
    for r in ips:
        addr = r.get('address', '')
        if '/' in addr:
            ip = addr.split('/')[0]
        else:
            ip = addr
        if not ip.startswith('192.168.'):
            continue
        cname = ip_to_contact.get(r['id'])
        desc = (r.get('description') or '').strip()
        # Prefer contact name (clean) > description (may be verbose)
        if cname:
            result[ip] = cname
        elif desc:
            # Truncate description if super long
            result[ip] = desc[:80]
    return result


def get_fg_dhcp_descriptions():
    """Return {ip: description} from FG DHCP reserved-address."""
    if not os.path.exists(FG_TOKEN_FILE):
        return {}
    token = open(FG_TOKEN_FILE).read().strip()
    req = urllib.request.Request(
        f'https://{FG_HOST}/api/v2/cmdb/system.dhcp/server/1',
        headers={'Authorization': f'Bearer {token}'},
    )
    data = json.loads(urllib.request.urlopen(req, context=ctx, timeout=10).read())
    result = {}
    for r in data['results'][0].get('reserved-address', []):
        ip = r.get('ip', '')
        desc = (r.get('description') or '').strip()
        if ip and desc:
            result[ip] = desc[:80]
    return result


def get_manual_overrides():
    if not os.path.exists(MANUAL):
        return {}
    out = {}
    with open(MANUAL) as f:
        for line in f:
            line = line.split('#', 1)[0].strip()
            if not line or '\t' not in line:
                continue
            ip, name = line.split('\t', 1)
            out[ip.strip()] = name.strip()
    return out


def main():
    nb = get_netbox_ips()
    fg = get_fg_dhcp_descriptions()
    manual = get_manual_overrides()

    # Merge: manual > NetBox > FG DHCP description
    merged = {}
    for src in (fg, nb, manual):  # later overrides earlier
        merged.update(src)

    # Sort by IP last octet (numeric)
    def ip_key(ip):
        try:
            return tuple(int(p) for p in ip.split('.'))
        except ValueError:
            return (999, 999, 999, 999)

    lines = [f'{ip}\t{name}' for ip, name in sorted(merged.items(), key=lambda kv: ip_key(kv[0]))]

    tmp = OUT + '.tmp'
    Path(tmp).write_text('\n'.join(lines) + '\n')
    Path(tmp).rename(OUT)

    print(f'wrote {len(lines)} entries to {OUT}', file=sys.stderr)
    print(f'  sources: NetBox={len(nb)}, FG-DHCP={len(fg)}, manual={len(manual)}', file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
