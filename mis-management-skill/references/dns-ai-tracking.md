# DNS-based AI usage tracking

Track which employees use which AI services (Claude, OpenAI, Gemini, Perplexity, DeepSeek, Kimi) by correlating Windows DNS server logs with FortiGate forward traffic logs.

## Why DNS-based

| Approach | Pros | Cons |
|---|---|---|
| Web proxy / SSL inspection | Most accurate (sees URLs) | Requires deploying CA cert to every PC; Slack from users |
| FG `app=` field detection | No agent | FG may not classify modern AI services accurately |
| **DNS log + FG byte log correlation** | Zero agent deploy; works on any DNS-aware app | Coarser (per-domain, not per-URL); needs Windows DNS server logging |

## Architecture

```
Each employee PC                                            
        ↓                                                   
DNS query: "claude.ai"  ─┐                                  
                          │                                 
        ↓                 │                                 
Windows AD DNS server     │                                 
(10.0.0.206)              │  PowerShell aggregator          
- DNS Server log          │  C:/scripts/dns-ai-aggregator.ps1
                          │  (greps log for AI domains)     
                          ↓                                 
                       JSON file: dns-ai-counts.json        
                          │                                 
                          │  scp from hub                   
                          ↓                                 
              Hub /opt/mis-http/dns-ai-counts.json          
                          ↓                                 
    ┌─────────────────────┼─────────────────────┐           
    ↓                     ↓                     ↓           
  ingest-dns-ai-events.py  correlate-dns-ai.py   gen-ai-usage-report.py
  ↓                       ↓                     ↓           
  SQLite dns_ai_events    dns-ai-attribution.json  ai-usage.html (web)
  table                                                      
```

## Components

### `fetch-dns-ai.sh`

Hub script, runs every 30 min:

1. SSH to AD DC, runs aggregator PowerShell script (writes JSON to `C:/dns-ai-counts.json`)
2. `scp` JSON back to hub (`/opt/mis-http/dns-ai-counts.json`)
3. Strips BOM (Windows JSON)
4. **Filters out FortiGate's own DNS queries** — FG (`<FG_IP>`) does its own DNS lookups for FortiGuard / threatfeeds; not user attribution
5. Runs `ingest-dns-ai-events.py` (insert into SQLite)
6. Runs `correlate-dns-ai.py` (compute per-user attribution)

```bash
# JSON sample
{
  "rows": [
    {"ip": "10.0.0.88", "service": "Anthropic", "count": 72},
    {"ip": "10.0.0.90", "service": "Perplexity", "count": 73}
  ],
  "events": [
    {"ts": "2026-05-05T08:30:00", "src": "10.0.0.88",
     "qname": "api.anthropic.com", "service": "Anthropic",
     "ips": ["160.79.104.10"]}
  ]
}
```

### `ingest-dns-ai-events.py`

Appends events from JSON into SQLite `dns_ai_events` table. Idempotent (PK on `ts, src_ip, qname, ip` — re-running is safe).

```sql
CREATE TABLE dns_ai_events (
    ts TEXT,
    src_ip TEXT,
    qname TEXT,
    service TEXT,
    ip TEXT,
    PRIMARY KEY (ts, src_ip, qname, ip)
);
```

### `correlate-dns-ai.py`

Joins `dns_ai_events` (DNS query log) with `user_dest` (FG forward log byte counts) on `(src_ip, dst_ip)` within ±10 min window. Each correlation attributes that flow's bytes to the AI service.

```sql
WITH attributed AS (
  SELECT u.src_ip, u.bytes_sent, u.first_seen,
    (SELECT e.service FROM dns_ai_events e
     WHERE e.src_ip = u.src_ip AND e.ip = u.dst_ip
       AND datetime(e.ts) <= datetime(u.first_seen)
       AND datetime(e.ts, '+10 minutes') >= datetime(u.first_seen)
     ORDER BY datetime(e.ts) DESC LIMIT 1) AS service
  FROM user_dest u
  WHERE u.src_ip LIKE '10.0.0.%'
    AND u.dst_ip IN (SELECT DISTINCT ip FROM dns_ai_events)
)
SELECT date, src_ip, service, SUM(bytes_sent) AS bytes
FROM attributed WHERE service IS NOT NULL
GROUP BY date, src_ip, service
```

Output: `/opt/mis-http/dns-ai-attribution.json`.

### `gen-ai-usage-report.py`

Generates `/opt/mis-http/ai-usage.html`:

- **IP-based section**: count traffic to known AI service IPs (e.g. Anthropic at `160.79.104.10`)
- **DNS-based section**: per-user/per-service breakdown from attribution.json
- **Daily series chart**: bytes/day per service over last N days

Pulls names from `ip-names.tsv` so `.113` shows as "Janey 范竹瑩".

## On-AD-DC PowerShell aggregator (`dns-ai-aggregator.ps1`)

This is the script run on the AD DC. **Not included in this skill** (depends on your specific AD DNS server logging setup), but typical structure:

```powershell
# C:/scripts/dns-ai-aggregator.ps1
$LogPath = 'C:/Windows/System32/dns/dns.log'   # or via Get-DnsServerCache
$Out = 'C:/dns-ai-counts.json'

$AIDomains = @{
    'anthropic.com' = 'Anthropic'
    'claude.ai'     = 'Anthropic'
    'openai.com'    = 'OpenAI'
    'chatgpt.com'   = 'OpenAI'
    'gemini.google.com' = 'Gemini'
    'perplexity.ai' = 'Perplexity'
    'deepseek.com'  = 'DeepSeek'
    'kimi.moonshot.cn' = 'Kimi'
}

# Parse DNS log for matching qnames + extract (timestamp, src_ip, qname, resolved_ip)
# Aggregate into JSON {rows: [...], events: [...]}
```

You'll need to tailor this to your DNS server's log format (Windows DNS Server "Debug Logging", or DNSSEC logging, or via `Get-DnsServerStatistics`).

## Common AI service IPs (for IP-based fallback)

These are stable enough to track by IP without DNS correlation:

| Service | IPs (as of 2025-2026) |
|---|---|
| Claude (Anthropic) | `160.79.104.10` (api.anthropic.com fixed IP) |
| DeepSeek | `3.173.21.63` |
| Kimi | `103.143.17.156`, `8.147.223.37` |
| OpenAI / ChatGPT | (CDN-fronted, varies — needs DNS correlation) |
| Gemini / Google AI | (CDN-fronted, varies) |
| Perplexity | (CDN-fronted, varies) |

For CDN-fronted services, **DNS correlation is essential** — IP alone won't identify the service.

## Schedule

```
Every 30 min: fetch-dns-ai.sh
              (SSH AD DC, scp JSON, ingest, correlate)
Every 5 min: gen-ai-usage-report.sh (separate cron)
              (re-render HTML from latest data)
```

## Privacy considerations

This pipeline sees:
- Which employee asked which AI service
- How much data they exchanged (bytes_sent)
- NOT the actual conversation content (stays inside HTTPS)

Treat the aggregated reports as confidential — don't share publicly. Especially:
- Per-employee AI usage rankings
- Detection of AI tool adoption pre-announcement

Local company AI policy should disclose this monitoring exists.

## Limitations

1. **DoH (DNS-over-HTTPS) bypass**: if a browser uses DoH (Cloudflare, Google), the local DNS server doesn't see queries. Block DoH at FG (FQDN block `*.cloudflare-dns.com` etc.) to enforce.
2. **VPN bypass**: if employee on VPN, DNS may resolve via VPN provider — your AD DC won't see it.
3. **DNS cache**: client may have cached the IP → hits AI service IP without re-querying DNS. Window the correlation period (`±10 min`) accommodates this somewhat but heavy users on long-lived TCP connections may miss attribution.
4. **CDN multi-tenant**: many AI services on Cloudflare share IPs with millions of other sites — IP alone is meaningless. Always correlate with DNS.

## Web report URL

After deployment: `http://10.0.0.200:8081/ai-usage.html`

Shows:
- Total MB / unique users per service
- Daily series chart
- Per-user breakdown (top 20)
- Last refresh timestamp
