# Coverage assessment — Stage 0 gate

A knowledge graph is only as trustworthy as the archive depth behind it. **Probe before you
build.** A graph synthesized from thin coverage is a confident fabrication — the worst
possible output. This stage decides **rich / partial / thin** and acts accordingly.

## How to probe (cheap, ~5 queries)

1. **Semantic breadth** — `vsearch '<domain> 架構 元件 設定' [project]`. Do hits come back
   that are *about the domain's structure* (not just passing mentions)? How many distinct
   sessions/dates?
2. **Literal density** — `csearch` a couple of core identifiers you expect (a hostname, a
   service name, a key term). Many hits across time = worked repeatedly = rich.
3. **Memory corroboration** — count memory files touching the domain
   (`ls ~/.claude/projects/<slug>/memory/` + grep). Memory is a lossy index, but *file count*
   is a decent proxy for "how much was this worked".
4. **Which project label(s)** hold it — a domain may live under one project, or be split.

## Classify

| Signal | rich | partial | thin |
|--------|------|---------|------|
| distinct sessions about the domain's structure | many (10+) | some (3–10) | ~0–2 |
| literal hits for core identifiers | dense, across months | sparse | almost none |
| related memory files | several | 1–2 | 0–1 |
| entity types you can populate | most of the ontology | some layers, gaps in others | a stub |

(Thresholds are heuristic — judge the *substance* of hits, not just counts.)

## Act on the verdict

- **rich** → run all 7 stages; expect a complete, multi-layer graph.
- **partial** → build it, but **scope the claim explicitly** and **mark the gaps on the
  artifact** ("flow & container topology mapped; infra-layer detail — disk/SLO/network ACLs —
  is thin and omitted"). Don't silently present a partial graph as complete.
- **thin** → **do not build.** Report honestly: the archive doesn't hold enough about this
  domain yet. The remedy is to *work the domain through the CLI* (so sessions accumulate),
  not to hallucinate a graph from a stub. Offer to graph it later once coverage grows.

## Why this is non-negotiable

This gate is the methodology being honest about the bounded-RAG flywheel: **you can only map
what you've recorded.** Real spread observed across domains:

- a heavily-operated **network/security** posture → rich, graphs cleanly.
- a **cloud/agent fleet** → partial; flow & containers graph well, infra decisions are thinner.
- a **finance/ERP migration** where the tooling ran but the conversation was sparse → thin;
  the field dictionary, per-phase loads, and tax mappings simply aren't in the archive yet.

Skipping the gate is how you ship a graph that looks authoritative and is quietly wrong.
