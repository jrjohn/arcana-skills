# Architecture Qube — Reference

Authoritative catalog of every rule, profile, and CLI option. Source of truth: [`jrjohn/arcana-arch-qube`](https://github.com/jrjohn/arcana-arch-qube) (`src/arch_qube/rules/`, `src/arch_qube/profiles/`).

---

## 1. Rule Catalog (21 rules)

Check types: **AST** = deterministic static analysis (no false positives) · **AI** = Claude semantic review · **AST+AI** = both.
Any **critical** rule below 100% compliance forces an automatic FAIL.

### Common — all platforms (rules 1–8)

| # | Rule | Severity | Weight | Check | What it guards / how to fix |
|---|------|----------|--------|-------|------------------------------|
| 1 | Layer Direction | Critical | 15 | AST | Imports flow inward only (presentation→domain→data). Fix: remove upward import; invert via an inner-layer interface. |
| 2 | Interface/Impl Colocation | Major | 5 | AST | Implementation sits beside its interface in `impl/`. Fix: move the `*Impl` next to the interface. |
| 3 | Impl Import Restriction | Critical | 8 | AST | Only the DI container imports concrete `*Impl`. Fix: depend on the interface everywhere else. |
| 4 | Impl Naming Convention | Minor | 3 | AST | Implementations named `*Impl`. Fix: rename. |
| 5 | DTO/Entity Separation | Major | 7 | AI | Entities never cross the API boundary. Fix: map Entity→DTO at the boundary. |
| 6 | No Business Logic in Boundary | Major | 8 | AI | Controllers/Views are routing/binding only. Fix: push domain logic into Service/UseCase. |
| 7 | Defense-in-Depth Security | Critical | 5 | AI | Auth/validation at multiple layers. Fix: add the missing layer guard. |
| 8 | Test Coverage ≥ 95% | Major | 5 | AST | Fix: raise coverage to ≥ 95%. |

### Client — web + mobile + desktop (rules 9–15)

| # | Rule | Severity | Weight | Check | What it guards / how to fix |
|---|------|----------|--------|-------|------------------------------|
| 9 | MVVM I/O/E Structure | Critical | 3 | AI | ViewModel has Input / Output / Effect segments. Fix: split the ViewModel. |
| 10 | MVVM I/O/E Models | Major | 3 | AI | I/O/E are typed models, not loose fields. |
| 11 | Unidirectional Data Flow | Critical | 3 | AST+AI | View → Input → ViewModel → Output → View. No back-channels. |
| 12 | View Cannot Call Service | Critical | 3 | AST | View binds Output only. Fix: route through the ViewModel. |
| 13 | 4-Layer Progressive Cache | Major | 3 | AI | Memory→DB→Network cascade implemented. |
| 14 | Type-Safe NavGraph | Major | 3 | AST+AI | Navigation routes are typed. |
| 15 | Offline-First Design | Major | 3 | AI | Local source of truth, sync on reconnect. |

### Backend — cloud services (rules 16–21)

| # | Rule | Severity | Weight | Check | What it guards / how to fix |
|---|------|----------|--------|-------|------------------------------|
| 16 | Controller→Service→Repo→DAO | Critical | 5 | AST | Strict one-directional chain. Fix: insert the missing layer. |
| 17 | Service Cannot Access DB | Critical | 5 | AST | Service uses Repository, never the DB/DAO directly. |
| 18 | Controller Cannot Use DAO | Critical | 4 | AST | Controller only talks to Service. |
| 19 | Transaction at Service Only | Critical | 4 | AST | `@Transactional` (or equiv) lives on the Service. |
| 20 | Controller Uses DTO | Major | 3 | AI | Controller I/O is DTOs, not Entities. |
| 21 | Repository Cannot Call Service | Critical | 2 | AST | No upward call from data→domain. |

**Total weight = 100** (15+5+8+3+7+8+5+5 + 3+3+3+3+3+3+3 + 5+5+4+4+3+2).

---

## 2. Profiles (14 frameworks)

Each profile defines: layer paths · allowed dependencies · import patterns · file extensions · DI container files · naming conventions. Pick the profile that matches the **framework**, not just the language.

| Platform | Profile (`-f` value) | Repo |
|----------|----------------------|------|
| Web | `angular` | arcana-angular |
| Web | `react` | arcana-react |
| Web | `vue` | arcana-vue |
| Mobile | `ios` (SwiftUI) | arcana-ios |
| Mobile | `android` (Compose) | arcana-android |
| Mobile | `harmonyos` (ArkUI) | arcana-harmonyos |
| Desktop | `windows` (WinUI 3) | arcana-windows |
| Backend | `springboot` | arcana-cloud-springboot |
| Backend | `python` (Flask) | arcana-cloud-python |
| Backend | `go` | arcana-cloud-go |
| Backend | `rust` | arcana-cloud-rust |
| Backend | `nodejs` | arcana-cloud-nodejs |
| Embedded | `stm32` | arcana-embedded-stm32 |
| Embedded | `esp32` | arcana-embedded-esp32 |

Which rule-sets apply: **common (1–8)** to all · **client (9–15)** to web/mobile/desktop · **backend (16–21)** to backend services. Embedded profiles apply common + a reduced client/HAL-layer set as defined in their profile YAML.

---

## 3. CLI Reference

```
arch-qube scan <path> [options]

  -f, --framework TEXT    Framework profile (required)
      --rules PATH        Custom rules directory (adds to bundled rules)
      --profiles PATH     Custom profiles directory
      --threshold FLOAT   Pass/fail score 0–100 (default: 95)
  -o, --output PATH       Output directory (default: arch-qube-reports/)
      --format TEXT       json,markdown,sonar,junit,badge (default: json,markdown)
      --ci                CI mode: exit 1 on fail
      --no-ai             Skip AI analysis (AST only — free, instant)
      --diff-only         Only scan git-changed files
      --base-branch TEXT  Base branch for diff (default: main)
      --api-key TEXT      Claude API key (or ANTHROPIC_API_KEY env)
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | PASS — score ≥ threshold and no critical violation |
| `1` | FAIL — score < threshold **or** any critical violation |
| `2` | ERROR — config/setup issue (bad profile, missing API key for AI rule, etc.) |

### Reporters (`--format`)

| Format | File | Use |
|--------|------|-----|
| `json` | `arch-qube.json` | machine-readable full report |
| `markdown` | `arch-qube.md` | PR comment / human summary |
| `sonar` | `arch-qube-sonar.json` | SonarQube external issues |
| `junit` | `arch-qube-junit.xml` | Jenkins/CI test reporting |
| `badge` | shields.io badge | README status badge |

---

## 4. Install / runtime

```bash
pip install -e .          # from the arcana-arch-qube repo
# Python ≥ 3.10 · deps: click, pyyaml, rich, anthropic
# entry point: arch-qube = arch_qube.cli:main
```

Source layout worth knowing when extending:
- `src/arch_qube/scanners/` — `import_graph.py`, `file_structure.py`, `parsers/{java,typescript}.py` (AST stage).
- `src/arch_qube/ai/` — `analyzer.py`, `prompt_builder.py`, `response_parser.py`, `cache.py`, `diff_extractor.py` (AI stage).
- `src/arch_qube/rules/` — rule YAML + `loader.py`, `models.py`.
- `src/arch_qube/profiles/` — one YAML per framework + `loader.py`.
- `src/arch_qube/scoring/engine.py` — weighted scoring + grades.
- `src/arch_qube/reporters/` — json / markdown / sonar / junit / badge.
