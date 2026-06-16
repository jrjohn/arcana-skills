# Methodology — archive → knowledge graph (the 7 stages in depth)

The premise: an AI-CLI session archive is the **most complete, most current ground truth**
about a domain you operate — more complete than hand-written memory (a lossy summary), more
current than the code/config (which doesn't record *why*), and it captures the *reasoning*,
not just the result. This methodology mines it into a graph.

The flow is **domain-agnostic**. Only Stage 1 (ontology) is domain-specific.

---

## Stage 0 — Coverage gating

**Before anything, ask: does this domain have enough archive depth to graph honestly?**

A graph synthesized from thin coverage is fabrication dressed as authority. Probe first
(see `coverage-assessment.md`): sample `vsearch`/`csearch` for the domain, count related
memory files, eyeball entity density. Classify **rich / partial / thin**.

- **rich** → proceed, expect a complete graph.
- **partial** → proceed but scope the claim ("flow/topology yes, infra-layer detail thin"),
  mark the gaps on the artifact.
- **thin** → **stop**. Tell the user the archive doesn't hold enough yet; the fix is to
  accumulate sessions in that domain, not to hallucinate a graph. This is the bounded-RAG
  flywheel being honest: you can only map what you've recorded.

> Why this is stage 0 and not an afterthought: the single biggest failure mode is a
> confident, wrong graph. Gating kills it up front.

---

## Stage 1 — Ontology design (the only domain-specific step)

Decide three things, from a template in `ontology-templates.md`:

1. **Entity types** — what nodes exist (device, service, person, account, container, …).
2. **Relationship types** — what edges mean (routes-to, depends-on, monitors, authenticates,
   backs-up-to, applied-to, …). Distinguish **structural** edges (physical/containment) from
   **logical** edges (service/data dependency) — they render differently (solid vs dotted).
3. **Facet split** — how to divide the domain into N non-overlapping slices so parallel
   agents cover it without stepping on each other (e.g. MIS → core-network / servers /
   monitoring / endpoints). Facets are the unit of parallelism in Stage 2.

Good facets are **MECE-ish**: mutually exclusive enough to avoid duplicate work, collectively
exhaustive enough to cover the domain. 3–6 facets is typical.

---

## Stage 2 — Faceted retrieval

Fan out **one subagent per facet** (see `faceted-retrieval.md` for the recipe). Each agent:

- Runs **`vsearch` first** — concept queries ("how did we handle the deny-log spam",
  cross-language), which also unlocks the archive preflight sentinel for the session.
- Then **`csearch`** for literals it now knows to look for — exact IPs, hostnames, employee
  IDs, file paths, error strings, config keys (FTS phrase/boolean).
- **Trims output** (`| head`) — transcripts are huge; the agent reads excerpts, not dumps.
- Returns **distilled structured data**, never raw transcript. This is the whole point of the
  fan-out: the orchestrator's context stays clean, and N facets cover the domain in parallel.

Why subagents and not inline queries: a single `csearch` can return 30KB. Doing 20 of them
inline buries the orchestrator. A facet agent absorbs that noise and hands back 40 tidy lines.

---

## Stage 3 — Extraction

Each facet agent emits rows shaped like:

```
entity | attributes (IP/version/role/…) | relationships | last-confirmed-date
```

Three non-negotiables:

- **Cite dates.** Every fact gets the date of the most recent transcript that confirms it.
  This is what makes the graph staleness-aware downstream.
- **Flag uncertainty.** "possibly the same device as X, IP changed", "port open but role
  unconfirmed" — mark it; don't launder a guess into a fact.
- **Mask secrets at the source.** Extract "auth: SSH key via the relay" not the key itself.

This is LLM-as-NER: the model reads transcripts and pulls typed entities + edges. It's
imperfect — which is exactly why Stage 4 exists.

---

## Stage 4 — Synthesis & adversarial reconciliation

Merge the facets into one entity/edge set, dedup (the same host shows up in three facets),
and resolve conflicts (facet A says role=X, facet B says role=Y → go back to the archive).

Then the highest-value move: **try to refute what you assembled.**

- For each "obvious" claim, ask: does the archive actually say this, or did I infer it?
- Re-query the literals. The archive routinely corrects the operator's mental model.

Real corrections from building such graphs:
- "There's a site-to-site VPN to the branch office" → archive shows **no tunnel config at
  all**; the cross-site traffic is ordinary outbound from a few PCs.
- "Host .24 is at the remote site" → it's a **local printer** that once spiked traffic.
- "Box X is our Zabbix server" → every concrete command shows it's a **syslog + scripts host**;
  no Zabbix UI ever appears.
- "The HR master data lives on the HR server" → it's actually on the **ERP DB**; the HR box is
  just a front-end + backup server.

Surfacing these is a **primary deliverable**. A graph that only confirms what you assumed is
worth far less than one that corrects you.

---

## Stage 5 — Graph rendering

Author a markdown **graph-spec** (see `examples/arcana-meta-system.md` for the canonical
format). It is plain markdown with:

- A ` ```mermaid ` block — the topology. Conventions:
  - **Layered subgraphs** (network tiers, system layers).
  - **Solid edges** (`==>`, `-->`) = physical / structural / containment.
  - **Dotted edges** (`-. label .->`) = logical / service / data dependency.
  - `classDef` + `class` to flag **EOL**, **SPOF**, self-referential, or otherwise special
    nodes by colour.
- **Entity tables** grouped by layer/category (IP, role, version, date).
- A **derived-insight section** — the structural payoff a flat inventory can't give:
  single points of failure (one node everything hangs off), EOL chains, orphans, backup
  dependencies, blast radius. This is where the graph *earns its keep*.

Mermaid edge-label gotcha: edge labels (between the arrow tokens) are **not** quoted, so keep
them simple — avoid `...`, `「」`, and other punctuation that the link parser can misread.
Node labels *are* quoted (`X["..."]`) and tolerate more, including `<br/>`.

---

## Stage 6 — Publishing

`scripts/render-graph.sh spec.md out.html` injects the spec into `templates/graph.html.tmpl`;
the page renders Markdown + Mermaid **client-side**, so the output is one portable file.
Default pulls marked.js/mermaid.js from CDN; `--self-host` references `./lib/*.min.js`
(run `fetch-mermaid.sh` first) for offline/air-gapped hosts.

`scripts/publish-graph.sh` ships it to a static host over SSH (e.g. behind an existing
auth-gated dashboard). **Architecture split that matters:** *generation* (Stages 0–5, which
need `crs`/the archive + an LLM) runs on a box with archive access (your Mac, or an agent
container); *publishing* only moves the finished HTML, so the web server itself needs no
archive, no crs, no LLM.

---

## Stage 7 — Regeneration (the flywheel)

A graph is a snapshot; the domain moves. Re-run the pipeline on a cadence (a launchd/cron
job in the spirit of the archive's own `gen-recent-context.sh`) so the graph tracks the
growing archive. Date-stamp nodes so staleness is visible. Each new session you run in the
domain deposits more ground truth → the next regeneration is richer. That is the bounded-RAG
flywheel, made visible.

---

## Principles, condensed

1. Ground truth (transcripts) over memory (lossy index).
2. vsearch for concepts, csearch for literals; vsearch first.
3. Faceted parallelism — never hold raw dumps in the orchestrator.
4. Staleness-aware — date everything; it's a snapshot.
5. Adversarial reconciliation — the corrections are the gold.
6. Coverage-gated — don't fabricate from thin air.
7. Ontology is domain-specific; the flow is not.
8. Privacy boundary — share the method, not the (often sensitive) output; never inline secrets.
