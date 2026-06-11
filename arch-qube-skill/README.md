# Architecture Qube Skill

Usage skill for [**Architecture Qube** (`arch-qube`)](https://github.com/jrjohn/arcana-arch-qube) — the AI-powered Architecture Quality Gate for the Arcana fleet. Detects MVVM, Clean Architecture, and GoF pattern violations automatically in CI/CD.

This is a **tool skill** (not a language skill): it teaches Claude to run scans, interpret and fix violations, integrate the gate into CI, and extend it with custom rules/profiles. Pair with a `<lang>-developer-skill` for language-exact fixes.

## What's inside
| File | Purpose |
|------|---------|
| `SKILL.md` | Main guide — quick reference, the 3 layers, rule priority, running/fixing, scoring, CI, extension |
| `reference.md` | Full 21-rule catalog · 14-profile catalog · CLI · exit codes |
| `patterns.md` | Enforced patterns with ✅ correct / ❌ violating code |
| `patterns/custom-rules.md` | Add a custom rule / profile (no code change) |
| `examples.md` | Real scans, reports, violation→fix walkthroughs |
| `checklists/production-ready.md` | Pre-merge architecture-gate checklist |
| `verification/commands.md` | Install / scan / CI command snippets |

## At a glance
- **21 rules** (8 common · 7 client · 6 backend), **14 framework profiles**.
- **Two stages:** AST (free, deterministic) → AI (Claude semantic, ~$0.01/PR).
- **Exit:** `0` PASS · `1` FAIL · `2` ERROR. Default pass threshold **95**; any critical miss = auto-FAIL.
- `arch-qube scan ./src -f <framework> --ci --diff-only`

## Install (live)
```bash
# part of the arcana-skills collection
curl -fsSL https://raw.githubusercontent.com/jrjohn/arcana-skills/main/install.sh | bash
```

Source of truth for the tool itself: https://github.com/jrjohn/arcana-arch-qube
