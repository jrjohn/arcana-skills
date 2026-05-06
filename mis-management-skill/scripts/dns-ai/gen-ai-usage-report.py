#!/usr/bin/env python3
"""Generate ai-usage.html merging IP-based UL traffic + DNS-based AI detection."""
import sqlite3, json, html, os, datetime
from collections import defaultdict

LAN_NET = os.environ.get('LAN_NET', '10.0.0')  # set to your internal /24 prefix
DB = '/opt/mis-log-db/mis-log.db'
OUT = '/opt/mis-http/ai-usage.html'
NAMES = '/opt/mis-log-db/ip-names.tsv'
DNS_JSON = '/opt/mis-http/dns-ai-counts.json'
ATTR_JSON = '/opt/mis-http/dns-ai-attribution.json'
TODAY = datetime.date.today().isoformat()

# IP-based services we can track by destination IP
IP_SERVICES = [
    ("Claude (Anthropic)", ["160.79.104.10"]),
    ("DeepSeek",           ["3.173.21.63"]),
    ("Kimi",               ["103.143.17.156", "8.147.223.37"]),
]
ALL_AI_IPS = [ip for _, ips in IP_SERVICES for ip in ips]

# Map IP-based label → canonical service name shared with DNS data
IP_TO_DNS_NAME = {"Claude (Anthropic)": "Anthropic", "DeepSeek": "DeepSeek", "Kimi": "Kimi"}

# Load name map
name_map = {}
try:
    with open(NAMES) as f:
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) == 2: name_map[p[0]] = p[1]
except FileNotFoundError: pass

def label(ip):
    short = ip.rsplit('.', 1)[-1]
    n = name_map.get(ip)
    return (f'{html.escape(n)} (.{short})' if n else f'.{short}',
            'unknown' in (n or '').lower() or '隨機' in (n or ''))

# === IP-based aggregations ===
con = sqlite3.connect(DB)
con.execute("PRAGMA busy_timeout = 5000")
cur = con.cursor()

ip_svc_mb, ip_svc_users = {}, {}
for name, ips in IP_SERVICES:
    placeholders = ','.join('?'*len(ips))
    total = cur.execute(f"SELECT COALESCE(SUM(bytes_sent),0) FROM user_dest WHERE dst_ip IN ({placeholders})", ips).fetchone()[0]
    users = cur.execute(f"SELECT COUNT(DISTINCT src_ip) FROM user_dest WHERE dst_ip IN ({placeholders})", ips).fetchone()[0]
    ip_svc_mb[name] = total / 1024 / 1024
    ip_svc_users[name] = users

# Daily Anthropic trend
daily_rows = cur.execute("SELECT date, COALESCE(SUM(bytes_sent),0) FROM user_dest WHERE dst_ip='160.79.104.10' GROUP BY date ORDER BY date").fetchall()
daily_labels = [r[0] for r in daily_rows]
daily_mb = [round(r[1]/1024/1024, 1) for r in daily_rows]

# Today top 10 — IP-based, with services GROUP_CONCAT
ph = ','.join('?'*len(ALL_AI_IPS))
today_top = cur.execute(f"""
  SELECT src_ip, SUM(bytes_sent),
         GROUP_CONCAT(DISTINCT CASE
           WHEN dst_ip='160.79.104.10' THEN 'Anthropic'
           WHEN dst_ip='3.173.21.63' THEN 'DeepSeek'
           WHEN dst_ip IN ('103.143.17.156','8.147.223.37') THEN 'Kimi' END)
  FROM user_dest
  WHERE date=? AND dst_ip IN ({ph})
  GROUP BY src_ip ORDER BY 2 DESC LIMIT 10
""", [TODAY] + ALL_AI_IPS).fetchall()

# Today's attributed services per src (DNS-IP correlation, today only)
today_attr_per_src = {}
attr_today = cur.execute(f"""
  WITH attributed AS (
    SELECT u.src_ip, u.bytes_sent,
      (SELECT e.service FROM dns_ai_events e
        WHERE e.src_ip=u.src_ip AND e.ip=u.dst_ip
          AND datetime(e.ts) <= datetime(u.first_seen)
          AND datetime(e.ts, '+10 minutes') >= datetime(u.first_seen)
        ORDER BY datetime(e.ts) DESC LIMIT 1) AS service
    FROM user_dest u
    WHERE u.date=?
      AND u.src_ip LIKE '{LAN_NET}.%'
      AND u.dst_ip IN (SELECT DISTINCT ip FROM dns_ai_events)
  )
  SELECT src_ip, GROUP_CONCAT(DISTINCT service)
  FROM attributed WHERE service IS NOT NULL GROUP BY src_ip
""", [TODAY]).fetchall()
for src, svcs in attr_today:
    today_attr_per_src[src] = svcs.split(',') if svcs else []

# Hist top users (cumulative across all IP-based)
hist_top = cur.execute(f"""
  SELECT src_ip, SUM(bytes_sent), COUNT(DISTINCT date),
         GROUP_CONCAT(DISTINCT CASE
           WHEN dst_ip='160.79.104.10' THEN 'Anthropic'
           WHEN dst_ip='3.173.21.63' THEN 'DeepSeek'
           WHEN dst_ip IN ('103.143.17.156','8.147.223.37') THEN 'Kimi' END)
  FROM user_dest WHERE dst_ip IN ({ph})
  GROUP BY src_ip ORDER BY 2 DESC
""", ALL_AI_IPS).fetchall()
con.close()

# === DNS-based aggregations ===
dns_svc_users = defaultdict(set)   # service -> set(ips)
dns_svc_count = defaultdict(int)   # service -> total queries
dns_user_svcs = defaultdict(dict)  # ip -> {service: count}
dns_meta = {}
if os.path.exists(DNS_JSON):
    with open(DNS_JSON) as f:
        d = json.load(f)
    dns_meta = {
        'generated': d.get('generated', '')[:19],
        'ai_matches': d.get('ai_matches', 0),
        'total_dns': d.get('total_dns_events', 0),
    }
    for r in d.get('rows', []):
        svc, ip, c = r['service'], r['ip'], r['count']
        dns_svc_users[svc].add(ip)
        dns_svc_count[svc] += c
        dns_user_svcs[ip][svc] = dns_user_svcs[ip].get(svc, 0) + c

# === IP-based service-user count for the bar chart (no DNS merge) ===
bar_labels = list(ip_svc_users.keys())
bar_users = [ip_svc_users[k] for k in bar_labels]

# === DNS-IP correlated attribution ===
attr = {}
if os.path.exists(ATTR_JSON):
    with open(ATTR_JSON) as f:
        attr = json.load(f)
attr_totals = attr.get('totals_by_service', [])  # [{service, mb, users}]
attr_daily_labels = attr.get('daily_labels', [])
attr_daily_series = attr.get('daily_series', {})  # {service: [mb_per_date]}
attr_meta = {
    'generated': attr.get('generated', ''),
    'window_min': attr.get('window_min', '?'),
    'attributed_rows': attr.get('attributed_rows', 0),
    'unattributed_mb': attr.get('unattributed_mb', 0),
}

# DNS pie sorted desc
dns_pie_labels = sorted(dns_svc_count.keys(), key=lambda k: -dns_svc_count[k])
dns_pie_data = [dns_svc_count[k] for k in dns_pie_labels]

# IP pie
ip_pie_labels = list(ip_svc_mb.keys())
ip_pie_data = [round(ip_svc_mb[k], 2) for k in ip_pie_labels]

# === Render HTML ===
def fmt_user_dns(ip):
    """Render DNS-detected services for a user as 'OpenAI(244), Gemini(26)'."""
    svcs = dns_user_svcs.get(ip, {})
    if not svcs: return ''
    parts = sorted(svcs.items(), key=lambda kv: -kv[1])
    return ', '.join(f'{html.escape(s)}({c})' for s, c in parts)

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
gen_dns_ts = ''
try:
    gen_dns_ts = datetime.datetime.fromtimestamp(os.path.getmtime(DNS_JSON)).strftime('%Y-%m-%d %H:%M')
except Exception: gen_dns_ts = 'N/A'

# Build attribution table HTML
attr_rows_html = ''
for t in attr_totals:
    attr_rows_html += f'      <tr><td>{html.escape(t["service"])}</td><td class=count>{t["mb"]}</td><td>{t["users"]}</td></tr>\n'
if not attr_totals:
    attr_rows_html = '      <tr><td colspan=3 class=meta>(尚無 attribution 資料 — 等下次 fetch 累積後刷新)</td></tr>\n'

# Build line chart JS — multi-series from attribution if available, else fallback Anthropic-only
line_palette = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#14b8a6','#f43f5e','#a855f7']
if attr_daily_series and attr_daily_labels:
    datasets = []
    for i, (svc, vals) in enumerate(attr_daily_series.items()):
        c = line_palette[i % len(line_palette)]
        datasets.append({'label': svc, 'data': vals, 'borderColor': c, 'backgroundColor': c+'33', 'fill': False, 'tension': 0.3})
    line_js = f"new Chart(document.getElementById('line'),{{type:'line',data:{{labels:{json.dumps(attr_daily_labels)},datasets:{json.dumps(datasets, ensure_ascii=False)}}},options:{{plugins:{{legend:{{position:'top'}}}},scales:{{y:{{beginAtZero:true,title:{{display:true,text:'UL MB'}}}}}}}}}});"
else:
    line_js = f"new Chart(document.getElementById('line'),{{type:'line',data:{{labels:{json.dumps(daily_labels)},datasets:[{{label:'Anthropic (IP-based fallback) UL MB',data:{json.dumps(daily_mb)},borderColor:'#3b82f6',backgroundColor:'rgba(59,130,246,.2)',fill:true,tension:.3}}]}},options:{{plugins:{{legend:{{position:'top'}}}},scales:{{y:{{beginAtZero:true}}}}}}}});"

with open(OUT, 'w') as o:
    o.write(f'''<!doctype html>
<html><head><meta charset=utf-8><title>AI Tool Usage — Arcana</title>
<meta http-equiv=refresh content=3600>
<script src=https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js></script>
<style>
body{{font-family:-apple-system,Segoe UI,sans-serif;margin:20px;background:#fafafa;color:#222}}
h1{{margin-bottom:5px}}.meta{{color:#888;font-size:12px;margin-bottom:30px}}
.row{{display:flex;gap:20px;flex-wrap:wrap;margin-top:20px}}
.card{{background:white;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);flex:1;min-width:380px}}
canvas{{max-height:340px}}
table{{border-collapse:collapse;width:100%;margin-top:10px}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #eee;font-size:14px}}
th{{background:#444;color:white;font-weight:500}}
tr:hover{{background:#f0f8ff}}
.count{{font-weight:bold;color:#c00}}
.unknown{{color:#999;font-style:italic}}
.dns-svc{{color:#0a8;font-size:12px}}
.ip-svc{{color:#36c;font-size:12px}}
</style></head><body>
<h1>🤖 AI 工具使用率 (Arcana)</h1>
<p class=meta>Generated: {now} · Auto-refresh: 1 hr · 資料窗：11 天 IP-based 流量 + DNS log（DNS 自 {gen_dns_ts}）<br>
<span class=ip-svc>■ IP-based</span>：可量 UL MB（Anthropic / DeepSeek / Kimi） · <span class=dns-svc>■ DNS-based</span>：可量查詢次數（OpenAI / Gemini / Copilot / Perplexity / Grok / Mistral / GitHub-Copilot 等 Cloudflare-hidden 服務）</p>

<div class=row>
  <div class=card><h3>各 IP-based 服務使用人數</h3><canvas id=bar></canvas></div>
  <div class=card><h3>11 天 IP-based 流量 (UL MB) — 水平比例</h3><canvas id=bar_ip></canvas></div>
</div>

<div class=row>
  <div class=card><h3>DNS 查詢分布（最近 24h）</h3><canvas id=pie_dns></canvas></div>
  <div class=card><h3>各 AI 每日 UL 趨勢 (DNS-IP 關聯，多線)</h3><canvas id=line></canvas></div>
</div>

<div class=row>
  <div class=card>
    <h3>各 AI 服務 attribution（DNS-IP 關聯流量總計）</h3>
    <p class=meta>原理：每筆 user_dest 流量比對 dns_ai_events 在 ±{attr_meta['window_min']} 分鐘內最近一筆 (src_ip, dst_ip) DNS 查詢，把 bytes 歸屬該服務。資料新鮮度：{attr_meta['generated']} · 已歸屬 {attr_meta['attributed_rows']} 筆 / 未歸屬 {attr_meta['unattributed_mb']} MB（DNS 累積 history 不足，跨日後逐漸補齊）</p>
    <table><tr><th>服務</th><th>UL (MB)</th><th>使用者數</th></tr>
{attr_rows_html}    </table>
  </div>
</div>

<div class=row>
  <div class=card>
    <h3>今日 Top 10 AI 使用者（IP-based 流量）</h3>
    <table><tr><th>#</th><th>使用者</th><th>UL (MB)</th><th>使用 AI（IP / <span class=dns-svc>DNS-IP 關聯</span>）</th></tr>
''')
    for i, row in enumerate(today_top, 1):
        ip, by, ip_svcs = row
        lab, unk = label(ip)
        cls = ' class=unknown' if unk else ''
        mb = f'{by/1024/1024:.2f}'
        ip_set = set((ip_svcs or '').split(',')) if ip_svcs else set()
        attr_set = set(today_attr_per_src.get(ip, []))
        only_attr = sorted(attr_set - ip_set)
        ip_part = ', '.join(sorted(ip_set))
        attr_part = f'<span class=dns-svc>{", ".join(only_attr)}</span>' if only_attr else ''
        combined = ', '.join(p for p in [ip_part, attr_part] if p) or '—'
        o.write(f'      <tr><td>{i}</td><td{cls}>{lab}</td><td class=count>{mb}</td><td>{combined}</td></tr>\n')
    o.write('    </table></div>\n</div>\n\n')

    o.write('''<div class=row>
  <div class=card>
    <h3>歷史 Top 使用者 (11 天累積，所有 IP-based 服務合併)</h3>
    <table><tr><th>#</th><th>使用者</th><th>總 UL (MB)</th><th>活躍天數</th><th>使用過的服務</th></tr>
''')
    for i, (ip, by, days, svcs) in enumerate(hist_top, 1):
        lab, unk = label(ip)
        cls = ' class=unknown' if unk else ''
        mb = f'{by/1024/1024:.2f}'
        o.write(f'      <tr><td>{i}</td><td{cls}>{lab}</td><td class=count>{mb}</td><td>{days}</td><td>{svcs or ""}</td></tr>\n')
    o.write('    </table>\n  </div>\n</div>\n\n')

    o.write(f'''<div class=row>
  <div class=card>
    <h3>DNS-based AI 服務偵測 — 詳細表（每位使用者每個服務）</h3>
    <p class=meta>來源：.206 Windows DNS Analytical ETW 每小時 :05 抓取。<b>計數 = DNS 查詢次數</b>，不等於流量。DNS cache 會降低重度使用者的查詢頻率。</p>
    <table><tr><th>使用者</th><th>服務</th><th>DNS 查詢次數</th></tr>
      <tr><td colspan=3 style="font-size:11px;color:#999">資料新鮮度：{dns_meta.get('generated','-')} · 偵測 {dns_meta.get('ai_matches',0)} AI 命中 / {dns_meta.get('total_dns',0)} 總 DNS query</td></tr>
''')
    if os.path.exists(DNS_JSON):
        with open(DNS_JSON) as f:
            d = json.load(f)
        rows = sorted(d.get('rows', []), key=lambda r: -r['count'])
        for r in rows:
            ip = r['ip']
            lab, unk = label(ip)
            cls = ' class=unknown' if unk else ''
            o.write(f'      <tr><td{cls}>{lab}</td><td>{html.escape(r["service"])}</td><td class=count>{r["count"]}</td></tr>\n')
    else:
        o.write('      <tr><td colspan=3 class=meta>(尚無資料)</td></tr>\n')
    o.write('    </table>\n  </div>\n</div>\n\n')

    o.write(f'''<script>
const colors=['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#14b8a6','#f43f5e','#a855f7'];
new Chart(document.getElementById('bar'),{{type:'bar',data:{{labels:{json.dumps(bar_labels, ensure_ascii=False)},datasets:[{{label:'Users',data:{json.dumps(bar_users)},backgroundColor:colors}}]}},options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,ticks:{{stepSize:1}}}}}}}}}});
new Chart(document.getElementById('bar_ip'),{{type:'bar',data:{{labels:{json.dumps(ip_pie_labels, ensure_ascii=False)},datasets:[{{label:'UL MB',data:{json.dumps(ip_pie_data)},backgroundColor:colors}}]}},options:{{indexAxis:'y',plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>c.parsed.x.toFixed(2)+' MB'}}}},datalabels:false}},scales:{{x:{{type:'logarithmic',min:0.1,title:{{display:true,text:'UL MB (log scale)'}}}}}}}}}});
new Chart(document.getElementById('pie_dns'),{{type:'pie',data:{{labels:{json.dumps(dns_pie_labels, ensure_ascii=False)},datasets:[{{data:{json.dumps(dns_pie_data)},backgroundColor:colors}}]}},options:{{plugins:{{legend:{{position:'right'}},tooltip:{{callbacks:{{label:c=>c.label+': '+c.parsed+' queries'}}}}}}}}}});
{line_js}
</script>
</body></html>
''')

print(f'wrote {OUT} ({os.path.getsize(OUT)} bytes)')
