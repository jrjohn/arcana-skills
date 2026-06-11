---
name: arch-qube-skill
description: Architecture Qube usage guide based on the Arcana arch-qube AI-powered Architecture Quality Gate. Provides comprehensive support for running architecture scans, interpreting the 21 rules / 14 framework profiles, fixing MVVM / Clean Architecture / layer-direction violations, CI/CD integration (Jenkins / SonarQube / GitHub Actions / pre-commit), AI semantic analysis, scoring, and adding custom rules / profiles. Suitable for enforcing architecture quality gates across the Arcana fleet, debugging arch-qube failures, and extending the tool.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# Architecture Qube Skill

Professional usage skill for [Architecture Qube (`arch-qube`)](https://github.com/jrjohn/arcana-arch-qube) — the AI-powered Architecture Quality Gate that detects MVVM, Clean Architecture, and GoF pattern violations automatically across the Arcana fleet.

> This is a **tool skill**, not a language skill. It teaches you to *run* arch-qube, *interpret* and *fix* the violations it reports, *integrate* it into CI, and *extend* it with custom rules/profiles. For language-specific architecture rules, pair it with the matching `arcana-<lang>-developer-skill`.

---

## Quick Reference Card

```bash
# AST-only scan (free, ~0.5s) — no API key needed
arch-qube scan ./src --framework angular

# AST + AI semantic analysis (Claude API, ~$0.01/PR)
arch-qube scan ./src --framework springboot --api-key $ANTHROPIC_API_KEY

# PR / CI mode: only changed files, exit 1 on fail
arch-qube scan ./src --framework react --diff-only --ci

# All report formats
arch-qube scan ./src -f vue --ci --format json,markdown,sonar,junit,badge
```

| Concept | Value |
|---|---|
| Entry point | `arch-qube` CLI (`pip install -e .`, Python ≥ 3.10) |
| Rules | **21** (8 common · 7 client · 6 backend) |
| Profiles | **14** frameworks (web / mobile / desktop / backend / embedded) |
| Stages | Stage 1 AST scanner (free) → Stage 2 AI analyzer (Claude API) |
| Pass threshold | default **95** (0–100); any **critical** failure = auto-FAIL |
| Exit codes | `0` PASS · `1` FAIL · `2` ERROR |
| Reporters | json · markdown · sonar · junit · badge |
| Deps | click · pyyaml · rich · anthropic |

---

## Rules Priority

When fixing a failing scan, address in this order — **critical rules cause an automatic FAIL regardless of numeric score**:

1. 🚨 **Critical (AST)** — deterministic, no false positives. Fix first: layer direction (#1), impl import restriction (#3), view→service (#12), backend layer chain (#16–19, #21).
2. 🚨 **Critical (AI)** — semantic: defense-in-depth security (#7), MVVM I/O/E structure (#9), unidirectional data flow (#11).
3. ⚠️ **Major** — colocation (#2), DTO/Entity separation (#5), no business logic in boundary (#6), test coverage (#8), cache/navgraph/offline (#10, #13–15), controller-uses-DTO (#20).
4. ℹ️ **Minor** — impl naming convention (#4).

> See `reference.md` for the full 21-rule catalog with weight, check type (AST / AI / AST+AI), and per-rule fix guidance.

---

## The Three Architecture Layers arch-qube Enforces

arch-qube checks the **same** Arcana Clean Architecture across every framework — only the layer *paths* differ per profile.

### 1. Common (all platforms) — rules 1–8
- **Layer Direction (#1, critical):** imports only flow *inward* (presentation → domain → data). No upward/backward imports.
- **Interface/Impl Colocation (#2) + Impl Import Restriction (#3, critical) + Impl Naming (#4):** implementations live next to their interface in `impl/`, only the DI container imports concrete `*Impl`, and impls are named `*Impl`.
- **DTO/Entity Separation (#5) + No Business Logic in Boundary (#6):** entities never leak through the API boundary; controllers/views hold no domain logic.
- **Defense-in-Depth Security (#7, critical) + Test Coverage ≥ 95% (#8).**

### 2. Client — web / mobile / desktop — rules 9–15
- **MVVM I/O/E Structure (#9, critical) + Models (#10):** ViewModel has explicit **Input / Output / Effect** segments.
- **Unidirectional Data Flow (#11, critical) + View Cannot Call Service (#12, critical).**
- **4-Layer Progressive Cache (#13) + Type-Safe NavGraph (#14) + Offline-First (#15).**

### 3. Backend — cloud services — rules 16–21
- **Controller → Service → Repository → DAO (#16, critical)**, strictly one direction.
- **Service Cannot Access DB (#17) · Controller Cannot Use DAO (#18) · Transaction at Service Only (#19) · Controller Uses DTO (#20) · Repository Cannot Call Service (#21).**

> Full pattern detail + correct/incorrect code in `patterns.md`.

---

## Instructions — running a scan & fixing violations

```bash
# 1. Install (once, in the arch-qube repo or any venv)
cd arcana-arch-qube && pip install -e .

# 2. Pick the profile that matches the target repo
#    angular | react | vue | ios | android | harmonyos | windows
#    | springboot | python | go | rust | nodejs | stm32 | esp32

# 3. Fast local AST scan first (free, deterministic)
arch-qube scan ./src --framework <fw> --no-ai

# 4. Read the Rich table → each row = rule, severity, compliance %, PASS/FAIL

# 5. Fix CRITICAL rows first (AST ones are never false positives)

# 6. Re-scan until critical = PASS, then run full AI pass before pushing
arch-qube scan ./src --framework <fw> --api-key $ANTHROPIC_API_KEY

# 7. In CI use --ci --diff-only so it exits 1 on regressions of changed files
```

### Interpreting a FAIL

- **`1` exit + a critical row at < 100%** → a hard architecture violation. Must fix; threshold is irrelevant.
- **`1` exit, no critical, score < 95** → accumulated major/minor debt dropped you below threshold. Fix the heaviest-weight majors first (weight column in `reference.md`).
- **`2` exit** → config/setup issue (bad `--framework`, missing profile, no API key for an AI rule). Not an architecture problem — fix the invocation.

### Fixing — map the rule to the layer

Every violation names a rule id. Look it up in `reference.md`, find the layer it guards, then apply the canonical fix from `patterns.md`. Common ones:

| Symptom in report | Rule | Fix |
|---|---|---|
| `View Cannot Call Service` FAIL | #12 | Route the call through a ViewModel; View binds to Output only |
| `Layer Direction` FAIL | #1 | Remove the upward import; invert via an interface in the inner layer |
| `Service Cannot Access DB` FAIL | #17 | Move the query into a Repository; Service depends on the Repo interface |
| `MVVM I/O/E Structure` FAIL | #9 | Split the ViewModel into Input / Output / Effect |
| `Impl Import Restriction` FAIL | #3 | Only the DI container may import `*Impl`; everyone else imports the interface |

---

## AI Analysis (Stage 2)

Stage 2 uses the Claude API for semantic checks AST cannot make:
- Is this `if/else` in a Controller **routing** or **domain logic**? (#6)
- Does the ViewModel actually implement **I/O/E** segments? (#9/#10)
- Does an Entity **leak** through the API boundary? (#5)
- Is the **4-layer cache** cascade real? (#13)

**Cost control (already built in):** `--diff-only` scans only changed files; results cached by file SHA-256; files > 50 KB skipped; uses a fast Sonnet model; ~**$0.01 per PR**. Use `--no-ai` for instant local/pre-commit gating, full AI pass in CI.

---

## Scoring

```
Score = Σ(rule_weight × compliance%) / Σ(weight) × 100

A+ 98–100 · A 95–97 · B 85–94 · C 70–84 · D 50–69 · F 0–49
```

Any **critical** rule below 100% → automatic **FAIL**, regardless of the numeric score. Tune the bar with `--threshold` (default 95) but never to mask a critical.

---

## CI/CD Integration (Arcana fleet uses Jenkins)

```groovy
stage('Architecture Qube') {
    steps {
        sh '''arch-qube scan ./src \
                --framework ${FRAMEWORK} --ci --diff-only \
                --format json,markdown,sonar,junit'''
    }
    post { always {
        junit 'arch-qube-reports/arch-qube-junit.xml'
        archiveArtifacts 'arch-qube-reports/**'
    } }
}
```

- **SonarQube:** `sonar.externalIssuesReportPaths=arch-qube-reports/arch-qube-sonar.json`
- **Pre-commit:** `arch-qube scan ./src -f <fw> --no-ai --ci --diff-only`
- **GitHub Actions:** `arch-qube scan ./src -f <fw> --ci --diff-only` with `ANTHROPIC_API_KEY` secret.

> Full snippets in `verification/commands.md`. Note: in the Arcana CI this gate runs as the "Architecture Qube" Jenkins stage on every fleet pipeline — a FAIL blocks the green-PR automerge.

---

## Extending arch-qube

**Add a rule = add a YAML file. No code changes.** Drop it in a `--rules` directory:

```yaml
# rules/custom/my-rule.yaml
id: my-custom-rule
name: "My Custom Architecture Rule"
category: common          # common | client | backend
severity: major           # critical | major | minor
weight: 5
ast_checks:
  - type: import_direction
    check: "no_upward_imports"
ai_checks:
  - type: semantic_review
    prompt_template: |
      Check this file for <pattern>...
      {file_content}
      Respond JSON: {"compliant": true/false, "violations": [...]}
scoring: { method: percentage, pass_threshold: 100 }
```

**Add a framework = add a profile YAML** defining layer paths, allowed dependencies, import patterns, file extensions, DI container files, and naming conventions. See `patterns/custom-rules.md` for both flows end-to-end.

---

## Files in this skill

- `reference.md` — full 21-rule catalog (severity/weight/check/fix) · 14-profile catalog · complete CLI reference · exit codes · scoring.
- `patterns.md` — the architecture patterns arch-qube enforces, with correct ✅ / violating ❌ code per layer.
- `patterns/custom-rules.md` — author a custom rule and a custom profile, step by step.
- `examples.md` — real scan invocations, example reports, and violation→fix walkthroughs.
- `checklists/production-ready.md` — pre-merge architecture-gate checklist.
- `verification/commands.md` — copy-paste commands to install, scan, and wire into every CI.
- `README.md` — one-screen overview.

---

## Rules of engagement (when assisting on arch-qube)

1. **Never weaken a critical to make a build green.** Fix the architecture, not the threshold.
2. **AST results are ground truth** — if AST says a layer is violated, it is. Don't argue with it via AI.
3. **Match the profile to the repo's framework**, not its language family (e.g. `arcana-vue` → `vue`, not `react`).
4. **Run `--no-ai` locally, full AI in CI** — keep PR cost ~$0.01 and feedback instant.
5. **A new rule is a YAML file**, never a code patch — preserve the no-code-change extension model.
