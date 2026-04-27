# FTS5 Query Syntax — Quick Reference

The session archive uses SQLite's [FTS5](https://www.sqlite.org/fts5.html) full-text engine with `tokenize='unicode61 remove_diacritics 2'`. Mixed Chinese/English content is handled automatically.

## Cheat sheet

| Goal | Syntax | Example |
|---|---|---|
| Plain keyword | `word` | `csearch ZyXEL` |
| Multiple words (implicit AND) | `a b` | `csearch 'switch port'` |
| Exact phrase | `'"a b c"'` | `csearch '"auto-power-down"'` |
| Boolean AND | `'A AND B'` | `csearch 'Sophos AND SEDService'` |
| Boolean OR | `'A OR B'` | `csearch 'Sophos OR Bitdefender'` |
| Boolean NOT | `'A NOT B'` | `csearch 'Windows NOT Server'` |
| Prefix (wildcard right) | `'word*'` | `csearch 'somnic*'` |
| Proximity (within N words) | `'NEAR(a b, N)'` | `csearch 'NEAR(DHCP reservation, 5)'` |

## The hyphen / colon / dot trap

FTS5 treats `-`, `:`, `.` as syntax characters:
- `-` is boolean NOT
- `:` is column qualifier (`column:term`)
- `.` is parsing boundary

So a search for `local-in-deny-broadcast` is parsed as `local AND NOT in AND NOT deny AND NOT broadcast`, then it tries to find a column named `in` and errors with `no such column: in`.

**Fix**: phrase-quote anything with these characters:

```bash
csearch '"local-in-deny-broadcast"' network    # ✓ works
csearch 'local-in-deny-broadcast' network      # ✗ ERROR: no such column: in

csearch '"192.168.11.34"' network              # ✓ for IPs
csearch '"https://"'                           # ✓ for URLs
csearch '"BTRFS-balance"' nas                  # ✓ for hyphenated names
```

## Direct SQL form

The CLI helper is just sugar over:

```sql
SELECT * FROM msg
WHERE rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH '<query>')
ORDER BY ts DESC
LIMIT 20;
```

For complex queries, drop into raw SQL:

```bash
# Aggregate: which days did we touch FortiGate config?
sqlite3 ~/claude-archive/sessions.db "
SELECT date(ts) AS day, COUNT(*) AS hits
FROM msg
WHERE rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH '\"fortigate.conf\"')
  AND project LIKE '%network%'
GROUP BY day ORDER BY day DESC LIMIT 10"

# Find a specific session by content snippet
sqlite3 ~/claude-archive/sessions.db "
SELECT DISTINCT session_id, MIN(ts), MAX(ts)
FROM msg
WHERE rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH '\"some unique phrase\"')
GROUP BY session_id"

# Last tool_use Bash command containing 'rsync'
sqlite3 ~/claude-archive/sessions.db "
SELECT ts, content
FROM msg
WHERE tool_name='Bash'
  AND rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH 'rsync')
ORDER BY ts DESC LIMIT 1"
```

## Tokenization

`unicode61` tokenizer:
- Lowercases ASCII (so `FortiGate` matches `fortigate`)
- Treats Unicode word boundaries reasonably for CJK (each CJK char is its own token)
- `remove_diacritics 2` strips combining marks (so `café` matches `cafe`)

Caveat: CJK without proper word segmentation means searching `防火牆` matches occurrences of all three chars adjacent. False positives are rare in practice but not impossible. For better Chinese segmentation, look at `fts5-jieba` extension (not bundled by default).

## Ranking (relevance)

By default FTS5 doesn't rank — `ORDER BY ts DESC` is what `csearch` uses. To rank by relevance:

```sql
SELECT *, bm25(msg_fts) AS score
FROM msg JOIN msg_fts ON msg.rowid = msg_fts.rowid
WHERE msg_fts MATCH 'query'
ORDER BY bm25(msg_fts) ASC    -- BM25: lower = more relevant
LIMIT 10;
```

Most ad-hoc historical lookups care about "when" not "what's most relevant", so `ORDER BY ts DESC` is the right default for `csearch`.
