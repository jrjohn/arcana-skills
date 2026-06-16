---
name: knowledge-graph-skill
description: >-
  Turn a Claude session archive into a domain knowledge graph. Faceted RAG
  retrieval (vsearch/csearch) → entity/relation extraction → Mermaid graph +
  derived risk insights → standalone HTML. Domain-agnostic flow; per-domain
  ontology templates (infra/MIS, security, cloud, finance, meta-system).
  Use when asked to "map", "draw the architecture of", "build a knowledge
  graph / 資訊圖譜 of", or "what does our X landscape look like" for any
  subject that has accumulated session history in the archive.
metadata:
  type: skill
  depends_on: claude-session-archive-skill
---

# knowledge-graph-skill

Builds a **knowledge graph of a domain from the session archive** — the archive
(full conversation transcripts) is the ground truth; this skill systematically
mines it into entities, relationships, and a rendered graph.

> Requires [`claude-session-archive-skill`](../claude-session-archive-skill/) (the
> `csearch`/`vsearch`/`crs` query layer). Graph quality is proportional to how much
> the domain has been worked on in CLI sessions — see Stage 0.

## When to use

Trigger on: "map / draw the architecture of X", "build a knowledge graph (資訊圖譜) of X",
"what does our X look like", "inventory X and how it connects". X = any domain with
archive coverage: network/MIS, security, cloud/infra, a migration project, or the
**meta-system** that runs the agents itself.

Do **not** use for: a single-fact lookup (just `csearch`/`vsearch`), or a domain with
no archive history (Stage 0 will tell you — go accumulate sessions first).

## Core idea

The **flow is domain-agnostic**; only the **ontology** (what counts as an entity / a
relationship / a facet) is domain-specific. Pick an ontology template, then run the
same 7 stages.

## The 7-stage methodology

Run these in order. Full detail + rationale in `references/methodology.md`.

0. **Coverage gating** — before anything, probe whether the domain has enough archive
   depth (`references/coverage-assessment.md`). Sample `vsearch`/`csearch` + count
   memory files → rich / partial / thin. **Thin → stop**; tell the user to accumulate
   sessions first (a graph from nothing is fabrication). Graph quality ∝ session depth.

1. **Ontology design** — pick/instantiate a template from
   `references/ontology-templates.md` (MIS, security, cloud, finance, meta-system,
   or generic). Define: entity types, relationship types, and the **facet split**
   (how to divide the domain so parallel agents don't overlap). This is the only
   domain-specific step.

2. **Faceted retrieval** — fan out one subagent per facet (`references/faceted-retrieval.md`).
   Each runs `vsearch` (concepts: "how did we handle X", cross-language) **first**
   (also unlocks the preflight sentinel), then `csearch` (literals: exact IPs, hostnames,
   IDs, file paths). Subagents absorb the raw transcript noise and return **distilled
   structured data**, never raw dumps. This keeps the orchestrator's context clean and
   covers the domain in parallel.

3. **Extraction** — each facet returns rows of `entity | attributes | relations |
   last-confirmed-date`, with **dates cited** (staleness-aware) and uncertainty flagged.

4. **Synthesis & adversarial reconciliation** — merge facets, dedup entities, resolve
   conflicts. **Actively bust assumptions against ground truth** — the archive routinely
   corrects the operator's mental model (e.g. "there's a VPN to the branch" → archive
   shows none; "host X is a Zabbix server" → it's a syslog box). Surfacing these
   corrections is a primary deliverable, not a side effect.

5. **Graph rendering** — author a markdown **graph-spec** (`examples/*.md` is the format):
   a ```mermaid block (layered subgraphs; solid = physical/structural edges, dotted =
   logical/service dependencies; `classDef` to flag EOL / SPOF / special nodes) + entity
   tables + a **derived-insight section** (risk map: single points of failure, EOL chains,
   orphans — the structural payoffs a flat list can't show).

6. **Publishing** — `scripts/render-graph.sh spec.md out.html` → standalone HTML. Two styles:
   default (Mermaid + tables) or **`--report`** (a polished, NotebookLM-style page: an
   **interactive markmap mind map** — collapsible/zoomable — above the themed Mermaid topology
   and cards). For `--report`, add a ```markmap block to the spec (a nested-list hierarchy of
   the same domain; optional `--- markmap: {initialExpandLevel: 3} ---` front-matter). Then
   `scripts/publish-graph.sh` to a static host/dashboard.
   **Generation must run where the archive is reachable** (your Mac, or an agent container
   with `crs`); publishing only ships the static output — the web host needs no archive access.

7. **Regeneration (flywheel)** — re-run periodically so the graph tracks the growing
   archive; date-stamp nodes. This is the bounded-RAG flywheel made concrete: the more
   you work the domain, the richer the graph gets.

## Principles (hold these throughout)

- **Ground truth over memory** — query the full transcripts (`csearch`/`vsearch`), not the
  curated memory index (it's a lossy, stale summary). Memory is a starting hint, not a source.
- **vsearch for concepts, csearch for literals** — and vsearch first (sentinel + recall).
- **Faceted parallelism** — decompose so the orchestrator never holds raw dumps.
- **Staleness-aware** — every fact carries a date; the archive is a historical snapshot,
  not live state. Say so on the artifact.
- **Adversarial reconciliation** — try to refute claims; the corrections are gold.
- **Coverage-gated** — never fabricate a graph for a thin domain.
- **Privacy boundary** — the *methodology + tooling* are shareable; *outputs* with PII /
  internal IPs / credentials stay private. Never put secrets in a graph (reference the
  secret store instead). See README "Privacy".

## Files

- `references/methodology.md` — the 7 stages in depth, with a worked example.
- `references/ontology-templates.md` — entity/relation templates per domain.
- `references/faceted-retrieval.md` — facet decomposition + query patterns + subagent recipe.
- `references/coverage-assessment.md` — Stage 0 probe + rich/partial/thin thresholds.
- `templates/graph.html.tmpl` + `scripts/render-graph.sh` — the renderer.
- `scripts/fetch-mermaid.sh` / `scripts/publish-graph.sh` — offline libs / deploy.
- `examples/arcana-meta-system.md` (+ `.html`) — flagship worked example (a 6-layer
  self-referential meta-system).
