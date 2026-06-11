# Extending Architecture Qube — Custom Rules & Profiles

arch-qube's core design: **a rule is data, not code.** You add architecture checks by dropping YAML files into a `--rules` directory and new frameworks by adding a profile YAML — no Python changes, no rebuild.

---

## A. Add a custom rule

1. Create a rules directory, e.g. `my-rules/custom/`.
2. Add one YAML file per rule:

```yaml
# my-rules/custom/no-god-service.yaml
id: no-god-service
name: "Service Method Count Limit"
category: backend          # common | client | backend
severity: major            # critical | major | minor  (critical → auto-FAIL)
weight: 5                  # contribution to the weighted score

ast_checks:
  - type: import_direction
    check: "no_upward_imports"
  # other AST check types are defined in src/arch_qube/rules/models.py

ai_checks:
  - type: semantic_review
    prompt_template: |
      Does this Service class exceed a single responsibility
      (e.g. > 10 public methods or mixed domains)?
      {file_content}
      Respond JSON: {"compliant": true/false, "violations": [{"line": N, "msg": "..."}]}

scoring:
  method: percentage
  pass_threshold: 100
```

3. Run with the custom rules merged onto the bundled set:

```bash
arch-qube scan ./src --framework springboot --rules my-rules/
```

**Notes**
- `severity: critical` makes any non-100% compliance fail the whole gate — reserve it for true invariants.
- Pure-AST rules run free and instantly; add an `ai_checks` block only when the check needs semantics.
- The `id` must be unique; it appears in every reporter (json/junit/sonar) so keep it stable.

---

## B. Add a custom framework profile

A profile teaches arch-qube where each layer lives for a framework. Model it on a bundled one (`src/arch_qube/profiles/<fw>.yaml`).

```yaml
# my-profiles/myfw.yaml
name: myfw
extends: client            # inherit client rules (or: backend / common)
file_extensions: [".ts", ".tsx"]

layers:
  presentation:
    paths: ["src/presentation/**", "src/ui/**"]
    may_depend_on: ["domain"]
  domain:
    paths: ["src/domain/**"]
    may_depend_on: ["data"]
  data:
    paths: ["src/data/**"]
    may_depend_on: []

di_container_files: ["src/di/container.ts"]   # the only place *Impl may be imported
naming:
  implementation_suffix: "Impl"
import_patterns:
  - { from: "domain", to: "presentation", allowed: false }  # enforce inward-only
```

Run it:

```bash
arch-qube scan ./src --framework myfw --profiles my-profiles/
```

---

## C. Deeper extension (code-level)

Only needed for a brand-new **check type** or **language parser** — not for ordinary rules.

- **New AST check type** → add it to `src/arch_qube/rules/models.py` + the relevant scanner in `src/arch_qube/scanners/`.
- **New language parser** → add `src/arch_qube/scanners/parsers/<lang>.py` (mirror `java.py` / `typescript.py`) so the import graph + file structure scanners understand it.
- **New reporter** → add `src/arch_qube/reporters/<name>_reporter.py` and register it in `--format`.

Keep the no-code-change promise for *rules*: if a new requirement can be expressed as YAML, do it as YAML.

---

## D. Versioning custom rules across the fleet

For Arcana, custom rules/profiles that should apply to every repo belong **in the arch-qube repo** (so the published `arch-qube` carries them), not scattered per-repo. Per-repo overrides go in that repo's CI invocation via `--rules`/`--profiles`. Bump `arch-qube` (`pyproject.toml version`) when the bundled rule set changes so pipelines pin a known gate.
