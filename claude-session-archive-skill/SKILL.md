---
name: claude-session-archive-skill
description: Cross-platform (macOS / Linux / Windows) cross-session full-text + semantic history of every Claude Code conversation. Ingests all ~/.claude/projects/*/*.jsonl into a local SQLite FTS5 database (~/claude-archive/sessions.db) every 15 minutes (launchd on macOS, Task Scheduler on Windows, cron / systemd on Linux), so any new session can recall verbatim what you did before — across all projects, all sessions, all tool_use inputs and tool_result outputs. Two query modes: `csearch` (FTS5 lexical, exact phrase / boolean / prefix) and optionally `vsearch` (semantic via Ollama + sqlite-vec + bge-m3 — multilingual SOTA, concept queries, synonym / cross-language matching, strong Chinese). Activates when user wants to (a) install the archive on a new machine (macOS/Linux/Windows), (b) query past sessions ("上週/昨天/之前做了什麼", "csearch ...", "vsearch ...", "查歷史對話 / past conversations / semantic search"), (c) install or troubleshoot Ollama / sqlite-vec semantic stack, (d) tune SQLite performance, or (e) troubleshoot FTS5 syntax / ingest issues.
version: 1.10.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Claude Session Archive

Permanent, local, full-text searchable history of every Claude Code session you've ever run on this Mac. Pairs with Memory: Memory holds curated signal (identity, traps, invariants); this archive holds the verbatim log (what you actually did, when, with what command and what result).

## When to use this skill

| Trigger | Action |
|---|---|
| User asks you to recall something from a past session ("上週那個 X 怎麼設的？", "we discussed Y last Thursday") | Run `vsearch '<natural-language paraphrase>' [project]` first (semantic, default); fall back to `csearch '<exact phrase>' [project]` only when query is a precise literal (IP / hostname / file path / FTS5 syntax) or vsearch returns nothing useful |
| User about to SSH / dig logs to identify someone or look up history (".98 是誰?", "上次怎麼處理 X 的") | **Discipline layer** (preflight hook) blocks the SSH/log-grep until vsearch runs. The answer is often already in archive. See `references/discipline-layer.md` |
| User invokes `/claude-session-archive-skill` or types `csearch ...` and it errors | Diagnose: archive not installed yet → walk through install. Already installed → check FTS5 syntax. |
| User on a fresh Mac wants the archive set up | Walk through Steps 1-6 in `references/installation-guide.md` |
| User reports queries are slow or DB grew large | See `references/tuning.md` |
| User asks a one-shot historical question ("when did port X get shut down?", "what password did we use for device Y?") | Use direct `sqlite3` SQL **after** running vsearch/csearch first (preflight hook blocks raw sqlite3 until then). See `references/fts5-syntax.md` |

## How it works (architecture)

```
~/.claude/projects/*/*.jsonl    ← Claude Code writes session JSONL (automatic)
            │
            ▼  crs build (idempotent incremental ingest, Rust binary)
~/claude-archive/sessions.db    ← SQLite + FTS5 + sqlite-vec (all bundled in crs)
            │  (launchd every 15 min)
            ├── ~/bin/crs                      single binary: build / csearch / vsearch / vsearch-since / gen-recent / embed-missing
            ├── sqlite3 <db> "SELECT ..."      raw SQL
            ├── ~/.sqliterc                    cache=512MB / mmap=512MB tuning
            └── ~/.claude/CLAUDE.md            instructions so any new Claude
                                               session knows to query first
```

DB schema:
```sql
msg(session_id, project, seq, ts, role, tool_name, content)  -- main table
msg_fts                                                      -- FTS5 over content
ingest_state(file_path, mtime, lines)                        -- incremental tracking
```

## Quick install — pick your OS

Detailed instructions in `references/installation-guide.md`.

Prerequisite: **Rust toolchain** (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`). The installer compiles a single `crs` binary (~5 MB, bundles SQLite + FTS5 + sqlite-vec). No Python venv anywhere.

### macOS / Linux (bash)

```bash
cd scripts
./install.sh                  # build crs + launchd (mac) / cron (linux) + sqliterc + first ingest
# (Optional) semantic search:
./install-semantic.sh         # native Ollama + bge-m3 model + backfill via crs embed-missing
# or
./install-semantic-docker.sh  # Ollama in Docker Desktop / docker-engine
```

### Windows (PowerShell)

```powershell
# Allow local script execution once:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# Then from inside scripts/:
.\install.ps1                  # build crs.exe + Scheduled Task + sqliterc + first ingest
.\install-semantic.ps1         # OPTIONAL: native Ollama (OllamaSetup.exe) + bge-m3
# or
.\install-semantic-docker.ps1  # OPTIONAL: Ollama in Docker Desktop
```

Then in any new Claude session add the snippet at the bottom of this file to `~/.claude/CLAUDE.md` (or `%USERPROFILE%\.claude\CLAUDE.md`) so Claude knows to query the DB.

## Daily usage patterns

### CLI — `csearch` (FTS5 lexical, always available)

```bash
# 簡單關鍵字
csearch ZyXEL

# Phrase（含 - / : / . 必須用 phrase）
csearch '"auto-power-down"' network

# Boolean
csearch 'Sophos AND SEDService' network
csearch 'Sophos OR Bitdefender'

# Prefix
csearch 'somnic*'

# 限定 project（slug 部分匹配）
csearch FortiGate network
```

### CLI — `vsearch` (semantic, optional Step 7)

```bash
# Concept search without remembering specific keywords
vsearch '上次廣播 deny log 太多怎麼解的'

# Cross-language: 防火牆 finds firewall
vsearch '防火牆規則調整' network

# Vague description
vsearch 'wireless AP keeps disconnecting' network
```

When to pick which:
- **csearch** — you remember a specific phrase / IP / hostname / file path / FTS5 syntax
- **vsearch** — you forgot the exact wording, or need synonym / cross-language matching (Chinese ↔ English, etc.)
- **csearch + date filter SQL** — time-bounded questions ("what did we do today / yesterday / last Thursday?")

vsearch sweet spot vs blind spot (verified 2026-05-04):
- ✅ **Strong on concrete technical concepts.** "rowid 殘留 導致 INSERT 衝突" → finds the actual `cmd_embed_missing` INSERT-collision discussion. "防火牆規則調整" → finds the firewall policy edit. The embedding clusters around the technical terms even when wording differs.
- ❌ **Weak on time-relative queries.** "今天修了什麼 bug" / "what did we do this morning" → low hit-rate. The embedding weight goes mostly to the generic words ("今天", "bug", "we"), not to *what* you actually did. The DB has no notion of "today" — date is a column, not a concept. Use `csearch '<keyword>' [project]` plus a `WHERE date(ts) = ...` SQL clause instead — the FTS layer is real-time (every 15 min ingest tick) and `date()` filtering is exact.
- ⚠️ **Embedding lag.** vsearch needs `bge-m3` to embed each new row, which happens during the next `crs build` tick. So messages from the *current ongoing* session may not be vsearchable for up to 15 minutes (FTS via `csearch` is updated synchronously during ingest — no lag there).

### Direct SQL (for complex queries)

```sql
sqlite3 ~/claude-archive/sessions.db "
SELECT session_id, substr(ts,1,19), role, substr(content,1,200)
FROM msg
WHERE project LIKE '%network%'
  AND date(ts) = '2026-04-23'
  AND rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH 'shaper quota')
ORDER BY ts LIMIT 20"
```

## Auto-context for Memory (`gen-recent-context.sh` + SessionStart hook)

Bridges session.db with Memory: every time `claude` starts, a hook runs `gen-recent-context.sh` which writes a fresh per-project `auto_recent.md` (loaded into Memory) containing:

- **vsearch ranking of last-48h msgs against the project's pending list** — KNN over `msg_vec` (cosine, max-distance 0.65), top 6 hits. Pending excerpt itself is **NOT** duplicated; Claude reads `project_pending.md` directly via the MEMORY.md index when it needs that. This avoids doubling tokens and keeps the auto file small (~20 lines).

**Skip guard** — the script exits early (no Ollama call, no disk write) when nothing has changed:
- `pending_mtime <= auto_recent_mtime` AND `latest_msg_ts <= auto_recent_mtime` → SKIP
- override with `FORCE_REGEN=1 ~/claude-archive/gen-recent-context.sh`
- log at `~/claude-archive/gen-recent-context.log` records `[OK] / [SKIP] / [ERROR]` per run

Every time `crs build` runs (every 15 min via launchd / Task Scheduler), it ALSO calls `crs gen-recent` for every known project — so even long-running sessions see fresh context, but the skip guard prevents wasted CPU on idle projects.

**Three layers working together:**

```
JSONL (raw, auto)           ← Claude Code writes
   ↓ crs build (15 min)
session.db (queryable)      ← csearch / vsearch
   ↓ crs gen-recent
auto_recent.md (curated)    ← Memory auto-loads at session start
   +
project_pending.md          ← Manually curated, also auto-loaded
   +
other memory files
   ↓
Claude session              ← Has all of the above in context
```

**Setup**: `install.sh` (base) registers the SessionStart hook into `~/.claude/settings.json` automatically. The hook command is `crs gen-recent`.

## Discipline layer (hooks)

`install.sh` registers two Claude Code hooks that enforce "vsearch/csearch first" mechanically — so the rule survives long contexts and time pressure, instead of relying on Claude remembering it.

| Hook | Event | What it does |
|---|---|---|
| `archive-preflight.sh` (`.ps1` on Windows) | PreToolUse (Bash + Read) | **Reactive**. Denies raw `sqlite3 ... sessions.db`, memory-file grep/Read, and SSH/local log dig until a `vsearch`/`csearch` runs in this session and sets a sentinel (`/tmp/claude-archive-preflight-<sid>`) |
| `auto-vsearch-on-prompt.sh` | UserPromptSubmit | **Proactive**. On prompts containing identity / history / status / question keywords, auto-runs `crs vsearch <prompt>`, injects top hits as `additionalContext`, and pre-sets the sentinel |

**Three-tier query hierarchy** (from `references/discipline-layer.md`):

1. 🥇 **vsearch** (default) — semantic, cross-language, tolerates fuzzy descriptions. Use for "上次怎麼處理 X" / concept queries / forgot-the-keyword cases.
2. 🥈 **csearch** (drill-down) — FTS5 lexical, exact match. Use after vsearch finds the area, or when the query is itself a known IP / hostname / 工號 / filename / FTS5 boolean.
3. ❌ **memory-file grep — NEVER as archive replacement.** Memory files are stale curated index, not source of truth. Preflight hook blocks `grep / cat / Read` on `~/.claude/projects/*/memory/*.md` until sentinel unlocks. Sole exception: "I just discussed this in *this* session" quick lookups.

**Real-world incidents that drove the design:**
- 2026-04 — Claude SSHed 3× into a device to ID `.98` before being reminded. Wasted round-trips.
- 2026-05-05 — Memory grep returned 2/5 of "品質法規部" (memory was stale curated subset); vsearch found 4/24 in one shot.

These prompted the explicit blocking rules. Don't disable lightly — read `references/discipline-layer.md` first to understand the failure modes.

## Critical guidance

**1. Never delete old rows.** The whole point is permanent memory. If disk gets tight, move `~/claude-archive/` to external storage (rebuild `crs` against the new path), don't `DELETE FROM msg WHERE ts < ...`. Losing history defeats the purpose.

**2. FTS5 hyphen / colon trap.** FTS5 treats `-`, `:`, `.` as boolean / column operators. Anything containing them must be quoted as a phrase:
```bash
csearch '"local-in-deny-broadcast"' network    # ✓ works
csearch 'local-in-deny-broadcast' network      # ✗ error: "no such column: in"
```

**3. DB is sensitive.** It captures every tool output verbatim — including passwords, tokens, API keys, IPs, MACs. Keep `chmod 600`, never sync to iCloud / rsync / Dropbox. On Mac handover, wipe and re-ingest.

**4. Memory and DB have different roles.** Memory = curated signal (identity, traps, invariants — small). DB = verbatim log (any-time-any-detail recall — large). Don't write log facts to Memory; don't curate the DB.

**5. Ingest is incremental + idempotent.** `crs build` uses (file path, mtime) tracking — re-running is safe and only re-reads changed JSONLs. New session content lands in DB at next 15-min launchd tick (or run `crs build` manually for instant indexing).

**6. Memory file is a stale index, not source of truth (since v1.9.0 — enforced by hook).** `~/.claude/projects/*/memory/*.md` is hand-curated — only what someone bothered to write down. For roster / device / credential / history queries, the canonical source is the archive (full transcripts). The `archive-preflight.sh` hook denies `grep`/`Read` on memory files until `vsearch`/`csearch` runs once in the session, preventing the antipattern of grepping memory and silently missing data that's actually in the archive. `MEMORY.md` itself is exempted (it's auto-loaded by the system anyway). Once the sentinel is set, memory access is unblocked for the rest of the session — useful for "I just discussed this in this session" lookups.

## Snippet for `~/.claude/CLAUDE.md`

Paste this near the top so every Claude session knows about the archive **and** the discipline layer:

```markdown
# 🚨 最高優先規則 — Archive DB Preflight

> **每個新 session 的第一個 archive query 必須是 `vsearch` 或 `csearch`，不是 raw `sqlite3`。**
>
> Hook (`~/.claude/hooks/archive-preflight.sh`) 會擋下任何對 `~/claude-archive/sessions.db` 的 raw `sqlite3`、對 `~/.claude/projects/*/memory/*.md` 的 grep/Read、以及 `ssh ... grep ... /var/log/...` 的遠端 log 翻找，直到本 session 跑過一次 `vsearch` / `csearch`（它們會寫 sentinel 解鎖）。
>
> **不看 query 內容** — 連 `GROUP BY date(ts) COUNT(*)` 這種沒 keyword 的 metadata query 也會被擋。
>
> 預設選 `vsearch`；明確 IP / hostname / 檔名 / FTS5 syntax 才直接 `csearch`。

# Cross-session history (use SQLite archive — don't ask the user repeatedly)

All Claude Code session JSONLs are ingested into ~/claude-archive/sessions.db
(SQLite FTS5 + sqlite-vec, every 15 min via the `crs` Rust binary on launchd).
It contains verbatim user / assistant / tool_use input / tool_result output
across all projects, all sessions.

## Schema
msg(session_id, project, seq, ts, role, tool_name, content)
msg_fts = virtual FTS5 over msg.content (tokenize=unicode61)

## When to query
- User asks to recall something from a previous session → query DB first, don't say "I don't remember"
- Picking up interrupted work ("continue from before") → look up that project's most recent session tail
- Investigating historical config drift ("when did port X go down?") → past tool_use Bash + result is ground truth
- Building project mental model → past tool calls beat memory (more complete) and git log (more immediate)
- **Before SSH-ing into a device to grep logs / identify someone** → vsearch first, the answer is often already there

## Three-tier query hierarchy

| 你想找的東西 | 選 |
|---|---|
| 「上次怎麼處理 X 的」但忘記 keyword | **vsearch**（預設） |
| 中英對照（「防火牆」找 firewall） | **vsearch**（預設） |
| 概念查詢「跟 Y 有關的決策」 | **vsearch**（預設） |
| 確切的 phrase / IP / hostname / 設備名 | csearch（直接走，跳過 vsearch） |
| 找一個檔案 / 某天的 log | csearch + date filter SQL |

1. **🥇 vsearch (default)** — 語意命中率高、跨語言、容忍模糊描述。
2. **🥈 csearch (drill-down or known identifier)** — vsearch 找到大範圍後，鎖細節用。
3. **❌ memory file grep — NEVER 當 archive 替代** — memory 是 stale curated index，不是 roster / device / credential / 歷史的 source of truth。Hook 會擋。唯一例外：「我這個 session 剛討論過 X」的 quick lookup。

## How to query
- CLI: `vsearch '<concept>' [project]` or `csearch <fts-query> [project-suffix]`
- SQL (after vsearch/csearch): `sqlite3 ~/claude-archive/sessions.db "SELECT ... WHERE rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH 'xxx') LIMIT 20"`

FTS5 syntax: phrase `'"..."'`, boolean `A AND B / OR / NOT`, prefix `foo*`. Words with `- / : / .` MUST be phrase-quoted.

## Caveats
- DB is a historical snapshot — always verify current state (file content, live config) before acting on it
- DB contains sensitive output (passwords / tokens / IPs) — local only, no sharing
- Memory and DB split: Memory for curated signal, DB for log-style recall

## Auto-context bridging (crs gen-recent + auto-vsearch-on-prompt)
- **SessionStart hook** runs `crs gen-recent` → writes `<project>/memory/auto_recent.md`
  containing the project's pending items ranked against last-48h archive content
  (vsearch KNN top hits). Auto-loads via Memory.
- **UserPromptSubmit hook** (`auto-vsearch-on-prompt.sh`) — on prompts with
  identity/history/status/question keywords, auto-runs `crs vsearch <prompt>`
  cross-project and injects top hits as `additionalContext` (and pre-sets the
  preflight sentinel). Common "who is .NN?" / "did we fix Y?" questions thus
  arrive pre-answered without an extra round-trip.

`crs build` also runs `gen-recent` every 15 min during ingest, refreshing all known projects.
```

## Files in this skill

```
claude-session-archive-skill/
├── SKILL.md                          # this file
├── README.md                         # human-friendly intro
├── references/
│   ├── installation-guide.md         # detailed step-by-step setup
│   ├── fts5-syntax.md                # FTS5 query language reference
│   ├── tuning.md                     # SQLite performance + maintenance
│   ├── faq.md                        # common questions / troubleshooting
│   ├── semantic-search.md            # OPTIONAL: Ollama + sqlite-vec for vsearch
│   └── discipline-layer.md           # hooks: archive-preflight + auto-vsearch-on-prompt
└── scripts/
    ├── crs/                          # Rust source (~720 LOC: build / embed / vsearch / csearch / gen-recent / vsearch-since)
    ├── install.sh                    # macOS/Linux base installer (cargo build + launchd/cron + sqliterc + first ingest + 3 hooks: SessionStart / PreToolUse / UserPromptSubmit)
    ├── install.ps1                   # Windows base installer (cargo build + Scheduled Task + sqliterc + SessionStart hook + PreToolUse preflight hook)
    ├── csearch.ps1                   # Windows PowerShell csearch wrapper (sqlite3.exe)
    ├── vsearch.ps1                   # Windows PowerShell vsearch wrapper (calls crs.exe vsearch)
    ├── archive-preflight.sh          # PreToolUse hook (Bash + Read) — gates raw sqlite3 + memory grep + SSH/local log dig until vsearch/csearch runs once
    ├── archive-preflight.ps1         # Windows port of the preflight hook (rules 1-4 only; SSH/log dig rules pending)
    ├── auto-vsearch-on-prompt.sh     # UserPromptSubmit hook — auto-vsearch on identity/history/status prompts, injects top hits + pre-sets sentinel
    ├── gen-recent-context.sh         # legacy hook target — calls crs vsearch-since (kept for stable hook command path)
    ├── gen-recent-context.ps1        # Windows port of the same
    ├── sqliterc.template             # → ~/.sqliterc
    ├── launchd.plist.template        # → ~/Library/LaunchAgents/com.<USER>.claude-archive.plist (runs crs build)
    ├── ollama.plist.template         # macOS OPTIONAL: launchd auto-start template
    ├── install-semantic.sh           # macOS/Linux OPTIONAL: native Ollama + bge-m3 + crs embed-missing backfill
    ├── install-semantic-docker.sh    # macOS/Linux OPTIONAL: Docker Ollama variant
    ├── install-semantic.ps1          # Windows OPTIONAL: native Ollama (OllamaSetup.exe) + bge-m3
    └── install-semantic-docker.ps1   # Windows OPTIONAL: Docker Desktop variant
```

## Author / version

- 2026-05-06 v1.10.0 **Discipline layer expansion — log-dig blocking + UserPromptSubmit auto-vsearch + dedicated reference doc.** Builds on v1.9.0's preflight hook with three additions:
  - **`archive-preflight.sh` rules 5+6** — hook now denies `ssh ... grep|tail|cat ... /var/log/...` and local `grep|tail|cat ...log` until the sentinel exists. Motivation: 2026-04 incident where Claude SSHed 3× into a device to identify `.98` before being reminded archive had the answer (3 wasted round-trips). Same justification as v1.9.0's memory-grep blocking — investigative log digs duplicate prior session work; vsearch first costs ~500ms and often returns the answer verbatim.
  - **`auto-vsearch-on-prompt.sh` (NEW UserPromptSubmit hook)** — proactive companion to the reactive preflight. Pattern-matches identity/history/status/question keywords (`.NN`, `工號`, `MAC`, `是誰`, `上次`, `修了嗎`, `為什麼`, etc.) in the user's prompt, runs `crs vsearch <prompt>` cross-project, injects top hits as `additionalContext`, and pre-sets the preflight sentinel. Common "who is .NN?" / "did we fix Y?" questions skip the preflight dance entirely — answer arrives pre-loaded in Claude's first turn. Designed to be archive-only (no bundled triggers from other skills); separate concerns ship separate hooks.
  - **`references/discipline-layer.md` (NEW reference doc)** — consolidates hook design rationale, sentinel mechanics, three-tier query hierarchy (vsearch default → csearch drill-down → memory grep forbidden), real-world incidents that drove each rule, performance notes, and composition rules for skills that want their own UserPromptSubmit hooks.
  - `install.sh` extended: step 6 hook copy now handles `auto-vsearch-on-prompt.sh` with detection-and-skip for customized versions; step 8c registers the UserPromptSubmit hook in `~/.claude/settings.json` idempotently. Existing installs: re-run `install.sh` — preflight gets new rules 5+6, UserPromptSubmit hook installed and registered.
  - **Windows port pending** — `archive-preflight.ps1` keeps rules 1-4 (from v1.9.0); rules 5+6 PowerShell port and `auto-vsearch-on-prompt.ps1` are TODO. Windows installs currently get partial discipline (preflight v1.9.0 behavior).
  - SKILL.md gets dedicated "Discipline layer (hooks)" section above Critical guidance; CLAUDE.md snippet rewritten with the 最高優先規則 prefix and three-tier hierarchy table.
- 2026-05-05 v1.9.0 **Preflight enforcement hook — memory grep + sqlite3 gating.** Adds a `PreToolUse` hook (`archive-preflight.sh` / `archive-preflight.ps1`) that mechanically enforces the vsearch-first preflight that has been documented since v1.6.2 but was prose-only and frequently skipped. The hook registers on **both `Bash` and `Read` matchers** in `~/.claude/settings.json` and applies three rules per session: (1) `vsearch` / `csearch` invocation creates a sentinel `/tmp/claude-archive-preflight-<session_id>` and is always allowed, (2) raw `sqlite3 ~/claude-archive/sessions.db ...` is denied until the sentinel exists, (3) **NEW: `grep`/`cat`/`head`/`tail`/`sed`/`awk` on `~/.claude/projects/*/memory/*.md` and `Read` on the same files are also denied until the sentinel exists** — `MEMORY.md` itself is exempted (auto-loaded by system). Motivation: 2026-05-05 audit found Claude grepping memory for a 6-person department roster, hitting only 2/6 because memory was a stale hand-curated subset; a `csearch` would have hit the full audit transcript with all 6. Codifying the rule in a hook prevents the antipattern at runtime, not just in docs. `install.sh` / `install.ps1` install + register the hook idempotently. Re-running the installer is safe.
- 2026-05-04 v1.8.0 **Operational visibility — `crs doctor` + `crs prune-vec` + installer prereq surfacing.** First batch from the 2026-05-04 audit (items 1, 2, 3, 6 of the install-hardening roadmap). `crs doctor` is a single-command health check spanning tooling / storage / DB consistency / schedule / hooks / Ollama, returning exit-code 0/1/2 (clean / warn / fail) for cron-friendly use. `crs prune-vec` drops orphaned `msg_vec` rowids left over after re-ingest cycles (complements v1.7.2's `INSERT OR REPLACE` — collisions are tolerated *and* cleanable). `install.sh` now surfaces optional `jq` / `sqlite3` status with exact install commands per OS before mid-run discovery; `install.ps1` downgrades `sqlite3.exe` from fatal abort to warning since `crs.exe` already bundles SQLite; `install-semantic.ps1` skips its row-count probe gracefully when `sqlite3.exe` is absent. README gains an "Operations — verify it's healthy" section that documents these workflows. Roadmap items 4, 5, 7-10 remain for later patch releases.
- 2026-05-04 v1.7.3 **Docs — vsearch sweet spot vs blind spot.** Added concrete usage guidance distilled from 2026-05-04 verification: vsearch is strong on technical-concept queries (terms cluster well in embedding space, e.g. "rowid 殘留 導致 INSERT 衝突" hits the actual collision discussion) but weak on time-relative ones ("today / 今天 / 昨天 / last Thursday") — the embedding weight goes to the generic time word, not the underlying topic. Time-bounded questions should use `csearch` + `WHERE date(ts) = ...` SQL filter instead, since FTS index is updated synchronously while embeddings backfill in batches up to 15 min behind. Updated `Daily usage patterns` to surface this trade-off and noted the embedding-lag caveat for current-session messages.
- 2026-05-04 v1.7.2 **Bug fix — `embed-missing` INSERT now uses `INSERT OR REPLACE`** (with explicit `DELETE` + `INSERT` fallback). After v1.7.1 fixed the pending-count bug, the actual INSERT step still hit `UNIQUE constraint failed on msg_vec primary key` for every rowid that was stale in `msg_vec` (i.e. `msg.rowid` was reused after a re-ingest, but `msg_vec` never dropped the old vector). The `LEFT JOIN msg_vec WHERE v.rowid IS NULL` predicate misses these because of how the `vec0` virtual table interacts with SQLite's NULL fill-in for outer joins — the planner returns "not in vec_vec" but the underlying storage still holds the rowid. Symptom: every fresh `embed-missing` run noisily failed on hundreds of newest rows (the vsearch tail you most want — today's conversations) while quietly succeeding on older gaps. Fix: use `INSERT OR REPLACE` so a colliding rowid is overwritten with the new embedding; fall back to explicit `DELETE` + `INSERT` if the storage rejects `OR REPLACE`. Existing installs: rebuild and re-run `embed-missing` — stale rows get refreshed in place, no manual prune needed.
- 2026-05-04 v1.7.1 **Bug fix — `embed-missing` skipped all new rows when `msg_vec` accumulated stale rowids**. `cmd_embed_missing` decided "nothing to embed" via `pending = COUNT(msg) - COUNT(msg_vec)`; once historical re-ingests / dedupes left orphan rowids in `msg_vec` (rows whose `msg.rowid` no longer exists), `done > total` made `pending ≤ 0` and the embed step short-circuited indefinitely. In practice this silently broke vsearch backfill for ≥6 days on at least one machine — `crs build` ran every 15 min, FTS index stayed current, but no new row ever reached `msg_vec`, so vsearch returned 4/28-and-older results forever. Fix: compute `pending` directly from `LEFT JOIN msg_vec WHERE v.rowid IS NULL` (the same predicate the actual embed query uses). Existing installs: rebuild with `cd scripts && ./install.sh` (or `cargo build --release` in `~/claude-archive/crs/`), then run `crs embed-missing` once to drain the accumulated backlog.
- 2026-04-29 v1.7.0 **Rust-only**: dropped Python entirely. `crs` is now the **base** install, no longer optional acceleration. `install.sh` / `install.ps1` build cargo and wire up launchd / Scheduled Task / SessionStart hook in one shot. Removed `build.py` / `embed.py` / `embed_parallel.py` / `vsearch.py` / `vsearch-since.py` / `csearch.py` and the bash `csearch` / `vsearch` wrappers. `install-semantic.*` no longer creates a Python venv — it just installs Ollama + bge-m3 and calls `crs embed-missing` for backfill. **Prerequisite changed**: now requires `cargo` (rustup) instead of `python3`. Migration on existing installs: rebuild via the new `install.sh`, which auto-rewires launchd plist + SessionStart hook.
- 2026-04-24 v1.0 initial setup (John Chang)
- 2026-04-27 v1.0.0 packaged as skill, with SQLite tuning (cache 512MB, mmap, temp_store=MEMORY)
- 2026-04-27 v1.1.0 optional semantic search: Ollama + sqlite-vec + nomic-embed-text + `vsearch`
- 2026-04-27 v1.2.0 native Windows support: csearch.ps1 / vsearch.ps1 / install.ps1 / install-semantic.ps1 / install-semantic-docker.ps1 + Scheduled Task instead of launchd
- 2026-04-28 v1.3.2 model upgrade: nomic-embed-text (768d) → **bge-m3 (1024d)**. Multilingual SOTA on MIRACL, native 8192-token context, strong Chinese. Adds `embed_parallel.py` for 4-5× faster initial backfill via ThreadPoolExecutor + OLLAMA_NUM_PARALLEL=4.
- 2026-04-29 v1.4.0 **Memory bridge**: `gen-recent-context.sh` + SessionStart hook + build.py refresh. Per-project `auto_recent.md` is auto-generated at every session start (containing pending + last 48h user prompts + assistant responses) and refreshed every 15 min by build.py — so Claude always has fresh per-project context in its Memory at session start. install-semantic.sh auto-registers the SessionStart hook via jq.
- 2026-04-29 v1.6.1 **vec0 statically linked**: switched from runtime `load_extension(vec0.dylib)` (which required the Python venv to be present) to the `sqlite-vec` crate, which bundles the C source statically. `crs` is now truly venv-free — `mv ~/claude-archive/.venv elsewhere` and vsearch still works. Binary 4.9 → 5.0 MB. FTS5 was already statically linked since v1.6.0 (rusqlite `bundled` feature compiles SQLite with `SQLITE_ENABLE_FTS5`).
- 2026-04-29 v1.6.0 **Optional Rust acceleration**: `crs` — single 4.9 MB binary that replaces every Python helper (build / embed_parallel / vsearch / vsearch-since / csearch / gen-recent-context). Bench (Apple M4): startup 80ms→<5ms (>16×), csearch 20ms→<5ms (>4×), gen-recent SKIP 10ms→<5ms (~3-5×), build steady-state 20-100ms→<5ms (5-20×). The Ollama-bound paths (gen-recent regen, embed-missing) see modest 1.0-1.3× since the bottleneck is `bge-m3` inference, not the client. Real value isn't raw speed — it's no-venv deploy, single-file binary, dropping a Python dependency from the launchd plist. Opt-in via `install-rust-accel.sh` / `install-rust-accel.ps1` (needs rustup, ~2-5 min cargo build). Skill ships full Rust source in `scripts/crs/` (~720 LOC). Python scripts stay as fallback.
- 2026-04-29 v1.5.0 **Energy-aware auto_recent**:
  - **vsearch-on-pending replaces three-section dump.** Previous design dumped pending excerpt + 8 user prompts + 5 assistant replies (49 lines, often noisy). New design uses pending-list as a semantic query against last-48h `msg_vec` rows (KNN, cosine ≤ 0.65) and surfaces the top 6 hits actually related to open work. Pending itself is **not** duplicated (Claude reads `project_pending.md` from the MEMORY.md index when needed) — halves the auto-loaded token budget.
  - **Skip guard.** `gen-recent-context.sh` exits early when `pending_mtime ≤ auto_recent_mtime` AND `latest_msg_ts ≤ auto_recent_mtime`. Idle projects no longer trigger Ollama embed + KNN every 15 min. `FORCE_REGEN=1` overrides. Logs `[OK] / [SKIP] / [ERROR]` to `~/claude-archive/gen-recent-context.log`.
  - **embed.py / embed_parallel.py: newest-first ordering** (`ORDER BY rowid DESC`). During long initial backfills, fresh conversations become queryable immediately instead of waiting for the entire historical corpus to embed.
  - **vsearch-since.py** new helper: time-bounded (`--hours`) + cosine-cutoff (`--max-distance`) + length filter (`--min-len`/`--max-len`) — used by `gen-recent-context.sh`. Standalone-callable for any "what did I do recently about X?" query.
  - install-semantic.sh / install-semantic-docker.sh now copy `vsearch-since.py` and the docker variant also copies `gen-recent-context.sh`.
  - **Windows parity**: `gen-recent-context.ps1` ports the bash version (skip guard, vsearch-on-pending, log file). `install.ps1` now auto-registers the SessionStart hook in `%USERPROFILE%\.claude\settings.json` (replacing the previous WSL-only TODO). `install-semantic.ps1` / `install-semantic-docker.ps1` install `vsearch-since.py` + `gen-recent-context.ps1`. `build.py` picks `.ps1` via `powershell.exe` on Windows, `.sh` elsewhere.
