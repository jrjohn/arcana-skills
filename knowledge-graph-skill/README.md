# knowledge-graph-skill

> Turn a **Claude session archive** into a **domain knowledge graph** — automatically,
> for any domain that has accumulated session history.

You've spent months working a domain through an AI CLI — your network, your cloud stack,
a migration, a security posture. Every command, result, and decision is sitting in the
session archive ([`claude-session-archive-skill`](../claude-session-archive-skill/)). This
skill mines that archive into a living map: entities, how they connect, and the structural
risks that only show up once you see the whole picture.

It's the applied answer to *"the more I use AI, the more it knows my world — can I see that
world?"* Yes: as a graph.

```
session archive (ground truth)
        │  faceted RAG retrieval (vsearch concepts + csearch literals)
        ▼
  entities + relations + dates  ──►  adversarial reconciliation (bust the myths)
        │
        ▼
  Mermaid graph + risk map  ──►  standalone HTML  ──►  dashboard
        │
        └──►  regenerate as the archive grows  (the flywheel)
```

## Why it works (and its honest limits)

- **The graph is only as good as your archive coverage of that domain.** Worked it a lot →
  rich graph. Barely touched it → thin/fabricated. Stage 0 gates on this; it's a feature,
  not a bug — it mirrors the bounded-RAG flywheel (you can't graph what you never recorded).
- **It maps *your* world, not generic knowledge.** The value is precisely that it's bounded
  and private. The methodology + this tooling are shareable; your graphs are yours.
- **It's retrieval, not a live source of truth.** Everything is a dated snapshot. The
  artifact says so. Verify before acting on a node.
- **The myth-busting is half the value.** Mining ground truth routinely corrects what you
  *thought* was true ("we have a VPN to the branch" → the archive shows there isn't one).

## The 7-stage methodology

| # | Stage | What |
|---|-------|------|
| 0 | **Coverage gating** | Probe archive depth for the domain → rich/partial/thin. Thin = stop. |
| 1 | **Ontology design** | Pick entity/relation types + facet split (the only domain-specific step). |
| 2 | **Faceted retrieval** | One subagent per facet: `vsearch` concepts + `csearch` literals → distilled data. |
| 3 | **Extraction** | `entity \| attrs \| relations \| date`, staleness-aware, uncertainty flagged. |
| 4 | **Synthesis + reconciliation** | Merge, dedup, and **adversarially bust assumptions** vs ground truth. |
| 5 | **Graph rendering** | Layered Mermaid + entity tables + **derived risk insights** (SPOF/EOL/orphans). |
| 6 | **Publishing** | `render-graph.sh` → standalone HTML → `publish-graph.sh` to a dashboard. |
| 7 | **Regeneration** | Re-run as the archive grows; date-stamp nodes. The flywheel. |

Full detail: [`references/methodology.md`](references/methodology.md). Claude's operating
SOP: [`SKILL.md`](SKILL.md).

## Domain-agnostic? Yes — gated by coverage

The flow is the same for every domain; only the **ontology** changes. Whether you *can*
graph a domain depends on how much it lives in your archive:

| Domain | Ontology template | Typical coverage | Notes |
|--------|-------------------|------------------|-------|
| Network / MIS | device · IP · person · service · topology | usually rich | classic first graph |
| Security | asset · policy · threat · vuln · access-log | rich if you run scans/policy work | risk/control/audit graph |
| Cloud / infra | host · container · service · process · pipeline | partial | flow & container topology graphable; infra-layer detail often thin |
| Finance / ERP (e.g. Odoo) | account · document · line · tax · migration-phase | often thin | needs the migration work itself recorded first |
| **Meta-system** | layered (skills · cognition · agents · archive · infra · memory) | rich (it's all in the archive) | the system mapping itself — see the example |

Templates: [`references/ontology-templates.md`](references/ontology-templates.md).

## Quick start

```bash
# 1. (optional, offline/air-gapped only) pin the render libs locally
scripts/fetch-mermaid.sh

# 2. author a graph-spec (markdown with a ```mermaid block + tables + a risk section)
#    — Claude does this by running the 7 stages; see examples/arcana-meta-system.md

# 3. render to a standalone page (CDN libs by default; --self-host for offline)
scripts/render-graph.sh examples/arcana-meta-system.md out.html            # plain: Mermaid + tables
scripts/render-graph.sh examples/arcana-meta-system.md out.html --report   # polished: interactive
                                                                           #   markmap mind map +
                                                                           #   themed Mermaid + cards
scripts/render-graph.sh examples/arcana-meta-system.md out.html --report --self-host  # offline

# 4. publish to a static host / dashboard (generic; no site paths baked in)
scripts/publish-graph.sh out.html my-host /var/www/dashboard
scripts/publish-graph.sh out.html my-host /opt/dashboard --with-lib examples/lib
```

The rendered page renders Markdown + Mermaid **client-side** (marked.js + mermaid.js), so
it's a single self-contained file. **Generation** (the archive mining in steps 1–2) must run
where `crs`/the archive is reachable — your Mac, or an agent container; **publishing** just
ships the static HTML, so the web host needs no archive access.

## Worked example: the Arcana meta-system

[`examples/arcana-meta-system.md`](examples/arcana-meta-system.md) →
[`examples/arcana-meta-system.html`](examples/arcana-meta-system.html) maps the very system
that produces these graphs — a 6-layer, **self-referential** meta-system (skills → cognitive
framework → AI-agent fleet → archive → infra → memory graph). The agent fleet writes its own
execution transcripts into the archive, which the agents then `vsearch` to recall themselves:
the system mapping itself, with the map drawn from the system's own memory.

## Privacy

This skill (methodology + tooling) is meant to be shared. **Graphs you generate are not.**
A graph of an internal network contains employee names, internal IPs, and topology; never
commit those to a public repo or send them to an external service. Keep secrets out of the
graph entirely — reference your secret store (NetBox, vault, etc.), never inline a password.
The example shipped here (Arcana meta-system) is deliberately a *public* system with all
credentials/hosts masked.

## See also

- [`claude-session-archive-skill`](../claude-session-archive-skill/) — the `csearch`/`vsearch`
  query layer this builds on.
- [`doc-indexer-skill`](../doc-indexer-skill/) — complementary knowledge-organization.

— part of [arcana-skills](https://github.com/jrjohn/arcana-skills)
