# claude-md-design-skill

Write CLAUDE.md files a model actually acts on — and check them with a script instead of taste.

Every rule here came from something that broke or something that was measured. Nothing in it
is style advice.

---

## The measurement this is built on

One capability, offered to the same AI pipeline nodes two ways, on the same day, with delivery
verified in the running image:

| Phrasing | Uses |
|---|---|
| `動手前請真的去查` — go and check before you start | **15** |
| `你可以主動查` + `不是每次都要` — you may / not every time | **0** |

Zero. Across four nodes and 1.7 MB of transcript. The 783-character version was confirmed to
have reached the model before that conclusion was drawn.

Rewriting it as an imperative, and adding one generated `CLAUDE.md` per workspace, took the
same pipeline from **0 → 28** queries. The cleanest evidence is SA and SD, which got *only*
the `CLAUDE.md` and no injected text: 0 in the two prior runs, 2 each afterwards.

Full data, including what was ruled out before concluding: [`references/evidence-2026-07-30.md`](references/evidence-2026-07-30.md).

---

## The linter

```bash
scripts/claude-md-lint.sh CLAUDE.md
scripts/claude-md-lint.sh --in-docker agent-task-node /path/to/CLAUDE.md
scripts/claude-md-lint.sh --selftest
scripts/claude-md-lint.sh --json CLAUDE.md
scripts/claude-md-lint.sh --update-baseline .lint-baseline CLAUDE.md
```

No dependencies beyond `awk` (`--in-docker` also needs `docker`).

### Checks

| Kind | Severity | Fires on | Why it exists |
|---|---|---|---|
| `self-exempting` | bad | `不是每次都要`, `視情況`, `必要時`, `as needed`, `if appropriate` | The rule carries its own exemption. Measured at zero uses |
| `executor-judged-trigger` | bad | `相關時`, `適當時`, `when relevant`, `as you see fit` | A criterion only the executor can apply is not a criterion |
| `absent-capability` | bad | a path in a `bash` block that does not exist in the target environment | Five capabilities went dark for one variable each, all silently |
| `no-consequence` | bad | opening block never says what breaking the rule costs | A rule with no cost is a suggestion |
| `permission-not-instruction` | sad | `你可以`, `建議`, `you may`, `consider` | The 0-vs-15 grammar, outside the opening block |
| `duplicate-section` | sad | a heading repeated | Two generations of one rule coexisting: the more specific wins, current or not |
| `size` | sad | > 40 KB | It reloads every turn and competes with the task |

### Verdicts

| Exit | Verdict | Meaning |
|---|---|---|
| 0 | `pass` | Checked; nothing above baseline |
| 1 | `findings` | Checked; `bad` findings |
| 2 | `notRun` | **Not checked** — missing file, unreadable, no `awk`, container down |

`notRun` is never reported as a pass. Conflating "could not check" with "checked and fine" is
the defect this whole toolchain exists to remove.

`bad` blocks; `sad` never does. A check that fails a hundred times on something nobody touched
gets switched off — that has happened twice in this codebase, and the check was right both times.

### Two things the design gets deliberately right

**Prose checks run outside fenced blocks; capability checks run inside them.** A guide that
teaches good wording has to quote bad wording, and matching the quote would flag the document
teaching the rule. On the day this was written, a refusal detector matched `INPUT_INCOMPLETE`
inside the sentence *"no INPUT_INCOMPLETE needed"* and stopped a healthy pipeline. Asking
"is the string present" instead of "is this an instruction" is the same mistake, and
`--selftest` asserts this tool does not make it.

**`--in-docker` exists because the rule runs somewhere else.** A workspace `CLAUDE.md` naming
`/root/bin/crs-sqlite` is correct inside the agent container and absent on the host. The flag
is explicit rather than inferred: guessing the target is how a check starts lying.

---

## Credibility

`--selftest` runs 11 assertions, and every check must prove **both** directions — that it
fires on a bad document *and* stays silent on a good one. A check never observed failing is a
check nobody has reason to trust.

It has already caught its own author twice:

1. On its first run, 4 of 11 checks could not fire at all (a `set -u` bug killed the pipeline),
   and the 7 "passes" were vacuous — nothing fired, so of course nothing false-fired.
2. Once fixed, it reported `no-consequence` against the `CLAUDE.md` its author had generated
   that same day. The document never said what ignoring it would cost. **The document was
   changed; the check was not relaxed.**

---

## Writing rules: the short version

Long version in [`SKILL.md`](SKILL.md).

1. **Ask whether it belongs in prose at all.** Irreversible → hook. Prose is the weakest
   instrument available; when you use it, say so.
2. **Imperative, never permission.** `先查它。` not `你可以查。` And never write a sentence
   that authorises skipping.
3. **The trigger must be mechanically decidable** — "when the spec names an AC id", not
   "when relevant".
4. **Table > list > paragraph.** In a recorded incident the losing rule was prose and the
   winning one a table.
5. **State the cost, in the opening block.** No enforcement? Write "this one is on you" —
   an honestly-labelled weak rule beats a fake strong one.
6. **Delete the superseded version.** Annotating it as obsolete is not enough.
7. **Never name a command that is not there.** A node told to run something that returns
   nothing will report having checked, and it will have checked nothing.
