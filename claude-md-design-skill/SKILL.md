---
name: claude-md-design-skill
description: Write CLAUDE.md files (and any always-loaded instruction prose) that a model actually acts on, and check them mechanically. Built from a controlled measurement, not from taste: on 2026-07-30 one capability offered to AI pipeline nodes was used 15 times when phrased as an imperative sentence and 0 times when phrased as a 783-character section saying "you may" and "not every time" — same capability, same nodes, delivery verified. Ships `scripts/claude-md-lint.sh`, which flags self-exempting rules ("not every time", "as needed"), triggers only the executor can evaluate ("when relevant"), permission grammar where an instruction belongs, rules pointing at commands or paths that do not exist in the environment where they will run, an opening rule that never states the cost of breaking it, and duplicate sections (two generations of one rule, where the more specific one wins regardless of which is current). Three-valued verdict (pass / findings / notRun — "could not check" is never reported as "checked and fine"), bad-vs-sad severity so cosmetics never block, baseline support so inherited debt stays visible without flooding, `--in-docker` to check paths in the environment the rule will actually run in, a two-axis grade (violations plus positively-detected structure, so an empty file cannot score well), `--suggest` printing the closed set of honest resolutions per finding, `--patch` emitting a reviewable diff for the one rewrite that changes wording without changing policy while never writing a file, and `--selftest` proving every check can both fire and stay silent. Activates when the user is writing, reviewing, or debugging a CLAUDE.md / AGENTS.md / system prompt / skill instruction file, asks why an instruction is being ignored, asks where a rule belongs (prose vs hook vs injected prompt), or wants an instruction file audited.
version: 1.1.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# CLAUDE.md Design

An always-loaded instruction file competes with the task for the model's attention, every
turn. This skill is about making that trade pay: say the few things that change behaviour,
in the grammar that gets acted on, and check the result with a script instead of taste.

Every rule here comes from an incident or a measurement. The evidence is in
`references/evidence-2026-07-30.md`; the short version is in the table below.

## When to use

| Trigger | Action |
|---|---|
| Writing or editing a CLAUDE.md / AGENTS.md / skill instructions | Follow §1–§4, then run the linter |
| "Why is the model ignoring this instruction?" | Run the linter first — it names the three grammars that measure at zero |
| Deciding where a rule belongs | §1. Prose is the weakest instrument; say so out loud when you use it |
| Reviewing someone's instruction file | `claude-md-lint.sh <file>`; treat `notRun` as unchecked, never as clean |
| An instruction names a command | Verify it exists **where the rule will run** — `--in-docker <container>` |

## 1. First: does this belong in prose at all?

| What you need | Where it goes | Why |
|---|---|---|
| Must never be violated, consequences irreversible | **hook** | Prose gets bypassed — §2 |
| Should happen every time, recoverable if missed | CLAUDE.md **and** injected prompt | Both; neither alone measured well |
| Depends on the situation | **Not a rule.** Delete it | §3 |
| Only meaningful when some capability exists | **Generated** CLAUDE.md, gated on that capability | §5 |

The strongest rule in this operator's own global CLAUDE.md is enforced by
`~/.claude/hooks/archive-preflight.sh`, not by its position in the file. The prose explains
why; the hook is what makes it true.

## 2. Imperative, not permission — the largest measured gap

Same capability, two phrasings, same four nodes, delivery verified in the running image:

| Phrasing | Uses |
|---|---|
| "動手前請**真的去查**" (go and check before you start) | **15** |
| "你**可以**主動查" + "**不是每次都要**" (you may / not every time) | **0** |

- ✅ `在你要重做任何事之前,先查它。`
- ❌ `你可以主動查。`
- ❌❌ `不是每次都要。` ← this sentence authorises skipping, on its own

A capability marked optional loses to whatever concrete task the model already has. It has
one; it always has one.

## 3. The trigger must be mechanically decidable

A rule whose trigger the executor evaluates in the moment is not a rule. The operator's own
file records deleting one for exactly this reason: *"「什麼算 drill-down」由執行者當場認定,
判準落在執行者身上的規則等於沒有規則"*.

| ❌ Executor decides | ✅ Mechanically decidable |
|---|---|
| "when relevant" | "when the spec names an AC / PR / defect id, look up that id" |
| "for important files" | "if the file appears in history, look it up first" |
| "escalate if necessary" | "escalate when the verdict is `gap`" |

## 4. Shape

1. **Table over list, list over paragraph.** In the 2026-07-21 incident the losing rule was
   prose and the winning one was a table — *"更具體、更好 pattern-match"*.
2. **State the cost.** A rule with no consequence is a suggestion. If nothing enforces it,
   write *"this one is on you"* — an honestly-labelled weak rule beats a fake strong one.
3. **Delete the old version.** Do not annotate it as superseded. Two generations coexisting
   means the more specific one wins, regardless of which is current.
4. **Trim.** It reloads every turn. Prefer terms already dense in training data (`Data
   Clumps`, `N+1`, `TOCTOU`) over paragraphs explaining them.

## 5. Never point at a capability that is not there

Five capabilities on one stack went dark for one missing environment variable each, and all
five failed **silently** — the run succeeded and the report looked identical.

> Told to run a command that returns nothing, a node reports having consulted history when it
> consulted an empty file. **That is worse than not consulting it.**

So: generate the file, gate the section on the capability actually resolving, and lint with
`--in-docker` when the rule runs somewhere other than where you are.

## 6. Run the checker

```bash
scripts/claude-md-lint.sh CLAUDE.md                        # exit 0 / 1 / 2
scripts/claude-md-lint.sh --score --suggest CLAUDE.md      # grade + what to do about each finding
scripts/claude-md-lint.sh --patch CLAUDE.md | git apply    # diff on stdout; never writes
scripts/claude-md-lint.sh --in-docker agent-task-node CLAUDE.md
scripts/claude-md-lint.sh --selftest                       # 24 assertions, both directions
scripts/claude-md-lint.sh --update-baseline .lint-baseline CLAUDE.md
```

| Exit | Verdict | Meaning |
|---|---|---|
| 0 | `pass` | Checked; nothing above baseline |
| 1 | `findings` | Checked; `bad` findings |
| 2 | `notRun` | **Not checked.** Never read as clean |

`bad` blocks, `sad` never does. A gate that fails a hundred times on code nobody touched gets
switched off — that has happened twice in this codebase, and both times the gate was right.

## 7. The grade

Two questions, never collapsed into one number on its own:

| | |
|---|---|
| **violations** | what was found wrong (`bad` / `sad`) |
| **structure** | what was found **right**, detected positively (0–3) |

| Grade | Meaning |
|---|---|
| A | no known defects, and all three structures present |
| B | no known defects, structure mostly present |
| C | **nothing found wrong, and almost no positive evidence** — an empty file lands here |
| D | at least one rule that will be skipped or points at something absent |
| E | several |

Grading on violations alone would hand a perfect score to an empty file — the same error as
reading a skipped gate as a passed one, one level up. Structure points require positive
detection and cannot be satisfied vacuously (a document naming zero paths does not earn
"all its paths resolve"), so **deleting content lowers the grade instead of raising it**.

The grade says nothing about whether the advice is correct. Nothing here reads content.

## 8. Fixing

`--suggest` prints, per finding, the closed set of honest resolutions. `--patch` emits a
unified diff on stdout and **never writes a file**.

Exactly one finding kind has a rewrite that changes wording without changing policy:
permission grammar (`你可以主動查` → `主動查`). Everything else — an exemption, a vague
trigger, a missing consequence — is a decision about what the rule should *be*, and a tool
that picks silently is choosing policy while claiming to fix grammar. Those emit choices and
no diff, and say so out loud.

## What this skill deliberately does not check

Whether the advice is *good*. A linter that guesses produces findings people learn to
ignore, and an ignored gate is the failure this tool exists to prevent. Six checks, each
answering a question a script can answer, each traceable to something that actually broke.

## Files

| Path | What |
|---|---|
| `scripts/claude-md-lint.sh` | The checker. No dependencies beyond `awk`; `--in-docker` needs `docker` |
| `references/evidence-2026-07-30.md` | The measurement, the three false reds, the five dark capabilities |
| `README.md` | Same material for a human reading the repo |
