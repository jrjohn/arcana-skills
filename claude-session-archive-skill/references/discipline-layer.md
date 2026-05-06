# Discipline Layer (Hooks)

The archive DB by itself only stores history. The **discipline layer** is what makes Claude actually use it consistently — by enforcing "vsearch first" via PreToolUse / UserPromptSubmit hooks, instead of relying on Claude's memory of a CLAUDE.md instruction.

This file documents the two hooks that ship with this skill, why they exist, and the sentinel mechanism they share.

## Why hooks (not just CLAUDE.md instructions)

Pure CLAUDE.md instructions are best-effort: Claude reads them, but under load (long context, distractions, time pressure) it forgets and SSHes straight into a device to grep logs that the archive already has. Hooks make the rule mechanical:

| Approach | Behavior under load |
|---|---|
| CLAUDE.md only | Claude *might* remember the rule. Drift over weeks. |
| Hook + sentinel | Tool call is **denied** until vsearch/csearch runs. Cannot drift. |

Real incidents that prompted this layer:
- **2026-04-XX** — Claude SSHed 3 times into a device to ID `.98` before being reminded archive had the answer. Wasted 3 round-trips. → preflight hook now blocks SSH-log-grep without vsearch.
- **2026-05-05** — Asked "who's in 品質法規部". Claude grepped memory file, hit 2/5 people (memory was a stale curated index). vsearch on archive returned 4/24 in one shot. → preflight hook now blocks memory grep without vsearch, and the rule "memory ≠ archive replacement" is encoded in the deny reason.

## The two hooks

### 1. `archive-preflight.sh` — PreToolUse (reactive)

Registered against `Bash` and `Read` matchers. Inspects the tool input and **denies** if the call is one of:

| Trigger | Why blocked |
|---|---|
| `sqlite3 ... sessions.db` (raw SQL on archive DB) | Want vsearch/csearch first — they're often enough, and they prime the cache |
| `grep / cat / tail / less / sed / awk` on `~/.claude/projects/*/memory/*.md` | Memory files are stale curated indexes, not source of truth |
| `Read` on a memory file (except `MEMORY.md` itself) | Same reason — memory is index, archive is authoritative |
| `ssh ... grep|tail|cat ... /var/log/...` or `*.log` | Investigative remote log queries often duplicate prior work — archive may already have the answer |
| Local `grep|tail|cat /var/log/...` or `*.log` | Same logic for local logs |

**Unblocking**: any `vsearch ...` or `csearch ...` invocation creates a sentinel file (`/tmp/claude-archive-preflight-<session_id>`). All blocked patterns then unblock for the rest of the session. The sentinel is per-session, not persistent — every new session re-locks until vsearch/csearch runs.

**Critically**: vsearch/csearch returning **zero results** still sets the sentinel. The rule is "you must check archive first", not "archive must contain the answer". A genuine new investigation just gets a one-line empty result, then proceeds normally.

### 2. `auto-vsearch-on-prompt.sh` — UserPromptSubmit (proactive)

Doesn't block anything — it preempts. When the user's prompt contains "look something up" intent (identity / history / status / question keywords), this hook:

1. Runs `crs vsearch <prompt>` cross-project
2. Injects top hits as `additionalContext` (Claude sees them in its first turn)
3. Sets the preflight sentinel (we did query, even if empty)

This means common questions like *"who is .45?"* or *"did we fix the broadcast deny?"* often skip the preflight dance entirely — the answer arrives pre-injected, Claude responds directly.

**Trigger keyword set** (covers Chinese + English):
- Identity: `.NN` IPs, `工號`, `MAC`, `hostname`, `是誰`, `誰的`
- History: `上次`, `之前`, `歷史`, `曾經`, `以前`, `當初`, `先前`, `昨天`, `早上`, `前幾天`
- Status: `修了嗎`, `修好了`, `完成了`, `處理了`, `解了`, `搞定了`, `fixed`, `resolved`, `做完`, `還是`, `還沒`, `目前`, `現在`, `狀態`
- Question: `查`, `對到`, `為何`, `為什麼`, `怎麼`, `哪個`, `哪些`, `是不是`, `有沒有`, `請問`, `可以嗎`, `能不能`

False positives are inevitable (the regex is permissive). The cost of a false positive is one wasted vsearch (~500ms, runs in background) — much cheaper than a missed lookup that triggers a 3-round-trip SSH dive.

## Sentinel mechanics

```
/tmp/claude-archive-preflight-<session_id>
```

- **Created by**: `vsearch` / `csearch` invocation (preflight hook), or any `auto-vsearch-on-prompt` archive-trigger match
- **Checked by**: preflight hook on every Bash / Read call
- **Cleared by**: nothing. `/tmp` clears on reboot, but each session has its own `session_id`, so cross-session contamination is impossible.

### Manual override

If Claude (or you) genuinely need to bypass the preflight without running vsearch — for example, in a single-purpose script that has no relation to past sessions — touch the sentinel:

```bash
SID=$(cat ~/.claude/projects/<project>/<latest>.jsonl | head -1 | jq -r '.sessionId')
: > /tmp/claude-archive-preflight-${SID}
```

This is escape-hatch only. Normal flow is: run vsearch, get results (even if empty), proceed.

## Composition with other skills

This skill ships **archive-only** hooks. If you have other skills that also want UserPromptSubmit injection (e.g. an emotional persona that triggers on life-decision keywords), they should ship **their own** hook script — don't bundle unrelated triggers into `auto-vsearch-on-prompt.sh`.

Multiple UserPromptSubmit hooks can coexist in `settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [{ "type": "command", "command": "~/.claude/hooks/auto-vsearch-on-prompt.sh", "timeout": 5 }] },
      { "hooks": [{ "type": "command", "command": "~/.claude/hooks/auto-other-skill.sh", "timeout": 5 }] }
    ]
  }
}
```

Both run; both can inject `additionalContext`; Claude sees the union. Keep each hook responsible for one concern.

## Performance notes

- **Preflight overhead**: ~5ms per Bash/Read call (jq + a few greps on small input). Hook timeout is set to 5s, but real cost is sub-frame.
- **Auto-vsearch overhead**: ~500ms when triggered (vsearch latency dominated by Ollama embedding inference). Hook timeout is also 5s. If Ollama is down or slow, the hook fails silently (vsearch returns empty), prompt goes through unmodified — never blocks the user.
- **No state persistence**: sentinel is `/tmp`-based; no DB writes, no I/O contention with `crs build`.

## Disabling

If the discipline layer is too aggressive for a particular workflow, remove the hook entries from `~/.claude/settings.json` (don't delete the scripts — they're cheap to keep around). The archive itself keeps working: `csearch` and `vsearch` remain usable manually, and `crs build` continues its 15-min ingest.
