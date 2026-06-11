# Architecture Qube — Examples

Real invocations, reports, and violation→fix walkthroughs.

---

## Example 1 — local AST scan (free)

```bash
arch-qube scan ./src --framework angular --no-ai
```

```text
                      Architecture Qube Results
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┓
┃ Rule                             ┃ Severity ┃ Compliance ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━┩
│ Layer Direction Enforcement      │ critical │       100% │  PASS  │
│ Only DI Container Imports Impl    │ critical │       100% │  PASS  │
│ MVVM I/O/E Structure             │ critical │       100% │  PASS  │
│ Interface/Impl Colocation        │  major   │       100% │  PASS  │
│ Implementation Naming Convention │  minor   │       100% │  PASS  │
└──────────────────────────────────┴──────────┴────────────┴────────┘

PASS — 100.0/100 (A+)
```

Exit `0`. AST-only, no API key, ~0.5s — ideal for a pre-commit hook.

---

## Example 2 — full AI scan before push

```bash
export ANTHROPIC_API_KEY=sk-ant-...
arch-qube scan ./src --framework springboot
```

Runs Stage 1 (AST) + Stage 2 (AI semantic). Catches things AST can't — e.g. domain logic hiding in a Controller (#6) or an Entity leaking through the API (#5).

---

## Example 3 — CI / PR mode

```bash
arch-qube scan ./src --framework react --ci --diff-only \
  --format json,markdown,sonar,junit
```

- `--diff-only` → only git-changed files vs `main` (cheap, ~$0.01).
- `--ci` → exit `1` on FAIL so the pipeline stage goes red.
- Reports land in `arch-qube-reports/` for Jenkins `junit` + `archiveArtifacts`.

---

## Walkthrough A — fixing a critical FAIL (#12 View Cannot Call Service)

```text
│ View Cannot Call Service │ critical │ 60% │ FAIL │
violations:
  src/presentation/UserPage.tsx:42  UserPage imports UserService directly
```

❌ Before:
```tsx
// UserPage.tsx
const user = await userService.getUser(id);   // View calling a Service
```

✅ After — route through the ViewModel (Input → Output):
```tsx
// UserPage.tsx
viewModel.send({ type: 'LoadUser', id });      // emit Input
const user = useObservable(viewModel.output);  // bind Output only
```
```ts
// UserViewModel.ts
onInput({ type, id }) { if (type==='LoadUser') this.output.next(await this.getUser.exec(id)); }
```

Re-scan → #12 back to 100%, critical clears, exit `0`.

---

## Walkthrough B — score below threshold, no critical

```text
PASS criteria not met — 91.3/100 (B), threshold 95
majors failing: DTO/Entity Separation (#5, w7), No Business Logic in Boundary (#6, w8)
```

No critical, but accumulated majors dropped you under 95. Fix by **weight**: #6 (weight 8) and #5 (weight 7) first — mapping entities to DTOs at the boundary and moving the `if/else` domain logic into the Service recovers ~15 weighted points → over 95.

---

## Walkthrough C — exit code 2 (not an architecture problem)

```text
ERROR: unknown framework 'reactjs' — available: angular, react, vue, ios, android,
harmonyos, windows, springboot, python, go, rust, nodejs, stm32, esp32
```

Exit `2` = bad invocation, not a violation. Fix the `--framework` value (`react`, not `reactjs`). Other exit-2 causes: AI rule requested without `ANTHROPIC_API_KEY`, missing `--profiles` for a custom profile.

---

## Example 4 — README status badge

```bash
arch-qube scan ./src -f go --format badge -o badges/
# → shields.io endpoint JSON → embed in the repo README
```
