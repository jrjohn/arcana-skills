# Faceted retrieval — the Stage 2 recipe

The engine of the methodology: instead of one giant query session that buries the
orchestrator in raw transcript, **fan out one subagent per facet**, each returning distilled
structured data. N facets cover the domain in parallel; the orchestrator only ever sees tidy
results.

## Why fan out

- A single `csearch` can return tens of KB of transcript. Twenty of them inline drown the
  orchestrator's context and you lose the thread.
- A facet agent **absorbs that noise** — it runs 10–30 queries, reads excerpts, and returns
  ~40 lines of `entity | attrs | relations | date`.
- Facets run **in parallel** → wall-clock is one facet, not the sum.
- Each facet is **blind to the others**, which (with a good MECE split) means no duplicated work.

## Launching the agents

Spawn them in one batch (parallel). Each prompt should contain:

1. **The domain + this facet's scope** (and explicitly: "don't cover the other facets").
2. **The query tools + the discipline:** "`vsearch '<concept>' <project>` and `csearch
   '<literal>' <project>`. Run a `vsearch` **first** (unlocks the archive sentinel). Pipe
   `| head` — transcripts are large; extract facts, don't dump."
3. **A starter query list** for the facet (5–10 concrete `vsearch`/`csearch` lines) — and tell
   it to expand on them.
4. **The exact return format:** entity rows `name | attrs | relations | last-confirmed-date`,
   relationship edges, **dates cited**, uncertainty flagged, **secrets masked** (auth method,
   not the secret).
5. **Length budget** (e.g. "30–50 lines, distilled, no raw transcript").

## vsearch vs csearch — which, when

| Want | Use |
|------|-----|
| "how did we handle X" but you forget the exact wording | **vsearch** (semantic) |
| cross-language ("防火牆" ↔ "firewall") | **vsearch** |
| a concept / decision / past approach | **vsearch** |
| an exact IP / hostname / employee ID / file path / error string | **csearch** (FTS) |
| a config key, a phrase you remember verbatim | **csearch** (phrase-quote it) |

In a facet agent: **vsearch first** to discover the territory and unlock the sentinel, then
**csearch** the specific literals the vsearch results revealed. Scan *all* returned rows —
the answer is often rank 2–4, not 1.

`csearch` literal gotchas (FTS): phrase-quote anything with `.` `/` `:` `-` —
`csearch '"10.0.0.1"' net`, `csearch '"local-in-policy"' net`. Boolean: `csearch 'A AND B'`.

## Project scoping

Pass the archive `project` label so a facet stays in its domain's history
(`vsearch '...' network`, `csearch '...' aaf`). One domain may span projects (e.g. a migration
recorded under a general dev project) — Stage 0 tells you which label(s) hold it.

## Worked shape (network/MIS, 4 facets)

```
facet 1  core-network/topology   → firewall, switches, subnets, VPN?, shaping, syslog
facet 2  servers & core systems  → AD/DNS/DHCP, ERP, HR, hypervisor, NAS, UPS, SAN
facet 3  monitoring/management   → NMS, IPAM/secrets, SNMP, alert rules, maintenance windows
facet 4  endpoints/people/phys   → IP→person→dept, door access, APs, printers, roster
```

Each returns its entities + edges + dates; Stage 4 merges and reconciles (e.g. facet 1's
"VPN to branch" gets refuted when no tunnel config surfaces anywhere).

## When NOT to fan out

For a **small/partial** domain (Stage 0 = partial, one obvious slice), a single facet — or
just inline `vsearch`+`csearch` by the orchestrator — is fine. Reserve the fan-out for
domains broad enough that parallel coverage + context hygiene actually pay off (≈3+ facets).
