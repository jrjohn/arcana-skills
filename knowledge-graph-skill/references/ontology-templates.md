# Ontology templates

Stage 1 picks one of these. Each template = **entity types** + **relationship types** +
a suggested **facet split** (the parallel slices for Stage 2). Adapt freely — these are
starting points, not schemas to obey.

Conventions used below: `►` structural/physical edge (solid in Mermaid), `┈►` logical/service
edge (dotted).

---

## Network / MIS

**Entities:** Device (firewall/switch/AP) · Server · Endpoint · Person · Department ·
Service (DNS/DHCP/AD/ERP) · Network/VLAN · StoragePath · DoorAccess/Physical · Printer.

**Relations:**
`gateway ► switch ► endpoint` · `device ┈► syslog ► collector` · `monitor ┈► SNMP ► device`
· `endpoint ┈► owned-by ► person` · `person ┈► in ► department` · `server ┈► backs-up-to ►
NAS` · `VM ► hosted-on ► hypervisor` · `firewall ┈► shaping-policy ► subnet`.

**Facets:** core-network/topology · servers & core systems · monitoring/management ·
endpoints/people/physical.

**Derived insights to compute:** SPOF (one box doing AD+DNS+DHCP+…), EOL chain
(firmware/OS/hardware end-of-life), SAN/single-storage blast radius, orphan IPs.

---

## Security

**Entities:** Asset (device/endpoint/service) · Policy (firewall rule/QoS/ACL) ·
ThreatIntel (feed/blocklist) · Vulnerability (scan finding/CVE) · AccessLog (deny record) ·
Credential (secret/token/key — *reference only, never the value*) · Control (auth/MFA/segmentation).

**Relations:**
`policy ┈► applied-to ► asset` · `threatfeed ┈► blocks ► address-group` · `scan ┈► finds ►
vuln ► on ► asset` · `secret ┈► authenticates ► service` · `deny-log ┈► classified-as ►
pattern` · `asset ┈► in ► segment/VLAN`.

**Facets:** assets & exposure · policies & controls · threat intel & deny patterns ·
vulnerabilities & remediation status.

**Derived insights:** asset-criticality × vuln-severity × exposure (risk ranking), audit
trail (config-change timeline), control coverage gaps, EOL signatures/feeds.

---

## Cloud / infra

**Entities:** Host/VPS · Container · Service · Network · Volume/Storage · Pipeline (CI/CD job)
· Process/Workflow · Registry/Artifact · EventSource (cron/webhook).

**Relations:**
`container ► runs ► service` (compose) · `service ┈► depends-on ► service` · `build ┈►
pushes ► image ► to ► registry` · `pipeline ┈► triggers ► workflow` · `container ► on ►
network` · `service ► persists-to ► volume` · `workflow ┈► dispatches ► task`.

**Facets:** host/network/storage · container & service topology · CI/CD & build pipelines ·
workflow/orchestration & event sources.

**Derived insights:** deploy dependency chain, image-rebuild blast radius, single-host
concentration, storage/GC pressure points. *Note:* infra-layer detail (disk policy, SLO,
network ACLs) is often thin in archives — scope the claim if Stage 0 says partial.

---

## Finance / ERP (e.g. an Odoo or GP migration)

**Entities:** ChartOfAccount (code/type/parent) · Document (AR invoice / AP bill / PO / SO /
journal) · LineItem · Tax (category/rate/mapped-account) · MasterData (customer/supplier/
employee/SKU) · MigrationPhase (scope/rows/reconciliation).

**Relations:**
`AR-line ┈► customer` · `AP-line ┈► supplier` · `line ┈► posts-to ► account` · `GL-entry ┈►
maps ► COA-node` · `tax-amount ┈► category` · `phase ┈► reconciles ► gp-total vs odoo-total`
· `phase ┈► has ► data-quality-issue`.

**Facets:** chart of accounts & hierarchy · documents & GL flow · tax & field mappings ·
master data & migration-phase reconciliation.

**Derived insights:** COA hierarchy tree, AR/AP reconciliation variance, document flow
(PO→receipt→AP→GL), data-quality issues per phase. *Note:* this domain is frequently **thin**
in archives — the migration work must have been recorded conversationally first. Stage 0
will usually say so.

---

## Meta-system (a layered platform mapping itself)

For graphing the *system that runs the agents* — inherently layered and self-referential.
See `examples/arcana-meta-system.md` for a full instance.

**Layers (each a subgraph):** Skills · Cognitive/Methodology framework · Agent fleet ·
Archive/memory · Infrastructure · Memory-graph.

**Entity types per layer:** Skill · MethodFacet · Process/Node/Task/Engine · SearchEngine/
StorageBackend/IngestPipeline · Host/Container/Network/Volume · Insight/Pitfall/Decision node.

**Cross-layer relations:** `framework ┈► realized-by ► skills ┈► realized-by ► fleet` ·
`fleet ► writes-transcript-to ► archive` · `archive ┈► recalled-by ► fleet` (the
self-referential loop) · `everything ┈► deployed-on ► infra`.

**Derived insights:** the self-referential observability loop (the system records itself →
queries itself), layer coupling, single-host concentration.

---

## Generic (no template fits)

**Entities:** name them by the nouns that recur in the domain's transcripts.
**Relations:** name them by the verbs ("X talks to Y", "X owns Y", "X derives from Y").
**Facets:** split by sub-area, by lifecycle stage, or by team/owner — whatever gives 3–6
non-overlapping slices.
**Derived insights:** always ask "what does seeing the *whole* reveal that any single row
doesn't?" — concentration, chains, cycles, orphans, staleness clusters.
