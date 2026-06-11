# Architecture Qube — Pre-Merge Gate Checklist

Run before a PR can merge. In the Arcana fleet this is the **"Architecture Qube"** Jenkins stage; a FAIL blocks the green-PR automerge.

## Scan ran correctly
- [ ] Correct `--framework` for the repo (vue→`vue`, react→`react`, springboot→`springboot`, …)
- [ ] Exit code `0` (not `1` FAIL, not `2` ERROR)
- [ ] `--ci` used so failures actually fail the stage
- [ ] `--diff-only` in PR mode (cost + speed); full-tree scan on `main`

## Critical rules (must be 100% — any miss = auto-FAIL)
- [ ] #1 Layer Direction — no upward/backward imports
- [ ] #3 Impl Import Restriction — only DI container imports `*Impl`
- [ ] #7 Defense-in-Depth Security
- [ ] Client: #9 MVVM I/O/E Structure · #11 Unidirectional Data Flow · #12 View ≠ Service
- [ ] Backend: #16 Controller→Service→Repo→DAO · #17 Service ≠ DB · #18 Controller ≠ DAO · #19 Tx@Service · #21 Repo ≠ Service

## Score
- [ ] Total score ≥ threshold (default 95)
- [ ] Threshold **not** lowered to mask a violation
- [ ] Heaviest majors addressed (#1 w15, #6 w8, #3 w8, #5 w7)

## AI stage
- [ ] Full AI pass run in CI (not just `--no-ai`) with `ANTHROPIC_API_KEY` set
- [ ] AI-only rules verified by *behavior*, not renamed symbols (#5 #6 #7 #9 #13 #15)

## Reports / integration
- [ ] `arch-qube-reports/` archived (json + markdown + junit)
- [ ] SonarQube external issues wired if used (`sonar.externalIssuesReportPaths`)
- [ ] Markdown summary posted to the PR

## If extending the gate
- [ ] New rule added as YAML (no code change)
- [ ] New `critical` rules justified (they hard-fail the fleet)
- [ ] `arch-qube` version bumped if the bundled rule set changed
