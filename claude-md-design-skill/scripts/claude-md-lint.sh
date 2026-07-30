#!/usr/bin/env bash
# claude-md-lint — does this CLAUDE.md say things a model will actually do?
#
# WHY THIS EXISTS
#
# On 2026-07-30 the same capability was offered to pipeline nodes two ways. Written as one
# imperative sentence it was used 15 times. Written as a 783-character section that said
# "你可以主動查" (you may query this) and "不是每次都要" (not every time), it was used ZERO
# times across four nodes and 1.7 MB of transcript. The instruction was verified to have been
# delivered. It was read and not acted on.
#
# Every check below comes from an incident, and each one is a question a script can answer.
# The ones a script cannot answer are deliberately absent: a linter that guesses is a linter
# whose findings get ignored, and an ignored gate is the failure this whole tool is about.
#
# THREE-VALUED, NOT TWO
#
#   exit 0  clean          — checked, nothing above baseline
#   exit 1  findings       — checked, found `bad` findings
#   exit 2  notRun         — could NOT check (missing file, unreadable, no awk)
#
# "could not check" is never reported as "checked and fine". That conflation is the exact
# defect this repo has spent a week removing from its own gates.
#
# SEVERITY
#
#   bad   the rule will be skipped, or points at something that does not exist → blocks
#   sad   costs attention or clarity → reported, never blocks
#
# Everything defaults to `bad` only when the incident behind it actually cost a run.
#
# Usage:
#   claude-md-lint.sh <file> [<file>...]      lint one or more CLAUDE.md
#   claude-md-lint.sh --selftest              prove the checks can both fire and stay silent
#   claude-md-lint.sh --json <file>           machine-readable
#   claude-md-lint.sh --baseline <bl> <file>  freeze existing debt; only new findings block
#   claude-md-lint.sh --update-baseline <bl> <file>
set -uo pipefail

JSON=0; BASELINE=""; UPDATE_BL=""; IN_DOCKER=""; AS_RULES=0; FILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --selftest) SELFTEST=1; shift ;;
    --json) JSON=1; shift ;;
    # Where the RULE will run, which is not always where the linter runs. A workspace
    # CLAUDE.md naming /root/bin/crs-sqlite is correct inside the agent container and absent
    # on the host; checking the wrong filesystem turns a good rule into a finding. The flag
    # is explicit rather than inferred — guessing the target is how a check starts lying.
    --in-docker) IN_DOCKER="${2:-}"; shift 2 ;;
    # Treat the file as the rules themselves even when it is not called CLAUDE.md.
    --as-rules) AS_RULES=1; shift ;;
    --baseline) BASELINE="${2:-}"; shift 2 ;;
    --update-baseline) UPDATE_BL="${2:-}"; BASELINE="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) FILES+=("$1"); shift ;;
  esac
done

command -v awk >/dev/null 2>&1 || { echo "claude-md-lint: no awk — cannot check" >&2; exit 2; }

# ---------------------------------------------------------------------------------------
# The checker. Prose checks run OUTSIDE fenced blocks; capability checks run INSIDE them.
#
# That split is not tidiness — it is how this tool avoids the bug it was written to catch.
# A guide that documents bad wording must quote it, and matching the quote would flag the
# document teaching the rule. Today a refusal-detector matched the word INPUT_INCOMPLETE
# inside the sentence "no INPUT_INCOMPLETE needed" and stopped a healthy pipeline. Asking
# "is the string present" instead of "is this an instruction" is the same mistake.
# ---------------------------------------------------------------------------------------
lint_one() {
  local f="$1"
  [ -f "$f" ] || { echo "notRun|0|missing|cannot read $f"; return 2; }
  [ -r "$f" ] || { echo "notRun|0|unreadable|cannot read $f"; return 2; }

  local base; base=$(basename "$f")
  local asrules=0
  case "$base" in CLAUDE.md|CLAUDE.MD|claude.md|AGENTS.md|agents.md) asrules=1 ;; esac
  [ "$AS_RULES" = "1" ] && asrules=1
  awk -v FNAME="$f" -v ASRULES="$asrules" '
    function emit(sev, kind, line, msg) { printf "%s|%d|%s|%s\n", sev, line, kind, msg }

    # A line that TEACHES a rule by showing the wrong version is not itself the wrong version.
    function is_negative_example(s) {
      return (s ~ /❌/ || s ~ /不要寫成/ || s ~ /反例/ || s ~ /錯:/ || s ~ /WRONG:/ || s ~ /BAD:/)
    }

    # Use versus mention. A phrase inside backticks or quotation marks is being CITED — by a
    # table listing the patterns this very linter matches, by a description of the tool, by a
    # guide teaching the rule. Matching it flags the document that explains the rule, which is
    # how a check stops being usable in its own domain.
    #
    # This function is the whole reason the tool can lint itself, and its absence was a real
    # defect: the first version reported 12 findings across its own SKILL.md and README, every
    # one of them a quotation. That is precisely the failure it exists to catch — asking "is
    # the string present" instead of "is this an instruction" — committed by the checker.
    function strip_citations(s) {
      gsub(/`[^`]*`/, " ", s)      # inline code
      gsub(/"[^"]*"/, " ", s)      # ASCII quotes
      gsub(/「[^」]*」/, " ", s)   # CJK corner brackets
      gsub(/“[^”]*”/, " ", s)      # CJK double quotes
      return s
    }

    BEGIN { infence=0; heading_count=0; top_block=1; consequence=0; bytes=0; lines=0; fm=0 }

    # YAML frontmatter is metadata about the file, not instruction inside it. A skill
    # description that names the patterns it detects is doing its job.
    NR==1 && /^---[[:space:]]*$/ { fm=1; next }
    fm && /^---[[:space:]]*$/    { fm=0; next }
    fm                          { next }

    { lines++; bytes += length($0) + 1 }

    # ---- fence tracking -----------------------------------------------------------------
    /^[[:space:]]*```/ {
      if (infence) { infence=0 } else { infence=1; fence_info=$0 }
      next
    }

    # ---- headings: the top block is everything before the second heading -----------------
    # `!infence` is load-bearing. Without it a shell comment inside a ```bash block ("# 例:")
    # counts as a markdown heading: it produced a phantom duplicate-section finding against a
    # real file and, worse, closed the top block early — so the window in which a stated
    # consequence counts would end at the first code comment, and a document that DOES state
    # its cost after an example would be told it does not.
    #
    # Found by running this tool on a real global CLAUDE.md. A checker that has only been run
    # against its own fixtures has not been tested, it has been rehearsed.
    !infence && /^#/ {
      heading_count++
      if (heading_count >= 2) top_block=0
      h=$0; sub(/^#+[[:space:]]*/, "", h)
      if (h in seen_heading) emit("sad", "duplicate-section", NR, "heading repeated: \"" h "\" — two generations of one rule can coexist, and the more specific one wins regardless of which is current")
      seen_heading[h]=1
      next
    }

    # =======================================================================================
    # PROSE CHECKS — outside fences only
    # =======================================================================================
    !infence {
      s=$0
      if (is_negative_example(s)) next
      if (s ~ /^[[:space:]]*$/) next
      raw=s
      s=strip_citations(s)
      if (s ~ /^[[:space:]|-]*$/) next   # nothing left but table scaffolding

      # --- bad: a sentence that authorises skipping ---------------------------------------
      # "不是每次都要" was measured at zero uses. A rule carrying its own exemption is a
      # suggestion, and a suggestion loses to whatever concrete task the model already has.
      if (s ~ /不是每次都要/ || s ~ /視情況/ || s ~ /必要時/ || s ~ /有需要再/ || s ~ /有需要時/ ||
          s ~ /依你判斷/ || s ~ /自行斟酌/ || s ~ /酌情/ ||
          s ~ /[Aa]s needed/ || s ~ /[Ii]f appropriate/ || s ~ /[Ww]hen appropriate/ ||
          s ~ /[Aa]t your discretion/ || s ~ /[Ii]f you think/ || s ~ /[Ww]here relevant/)
        { emit("bad", "self-exempting", NR, "authorises skipping — the rule carries its own exemption: " substr(s,1,70)); next }

      # --- bad: the trigger is decided by whoever is executing -----------------------------
      # A criterion only the executor can apply is not a criterion. The rule it replaced was
      # deleted for exactly this: "what counts as drill-down" was decided in the moment, and
      # the answer drifted.
      if (s ~ /相關時/ || s ~ /重要的時候/ || s ~ /適當時/ || s ~ /覺得有必要/ ||
          s ~ /你認為.*就/ || s ~ /如果覺得/ ||
          s ~ /[Ww]hen relevant/ || s ~ /[Ii]f important/ || s ~ /[Aa]s you see fit/)
        { emit("bad", "executor-judged-trigger", NR, "trigger decided in the moment by the executor, so it is not a trigger: " substr(s,1,70)); next }

      # --- sad: permission grammar where a rule belongs -----------------------------------
      # Measured 0 uses against 15 for the imperative form of the same capability.
      if (s ~ /你可以/ || s ~ /可以主動/ || s ~ /建議你/ || s ~ /值得(查|做|試)/ || s ~ /不妨/ ||
          s ~ /[Yy]ou (can|may) / || s ~ /[Ff]eel free/ || s ~ /[Cc]onsider (using|running|checking)/ ||
          s ~ /[Oo]ptionally/)
        { emit("sad", "permission-not-instruction", NR, "permission grammar — say what to do, not what is allowed: " substr(s,1,70)); next }

      # --- consequence anywhere in the top block ------------------------------------------
      if (top_block && (s ~ /違反/ || s ~ /代價/ || s ~ /會擋/ || s ~ /會被 ?reject/ ||
                        s ~ /[Rr]ejected/ || s ~ /[Bb]locked/ || s ~ /[Ww]ill fail/ || s ~ /hook/))
        consequence=1
    }

    # =======================================================================================
    # CAPABILITY CHECKS — inside fenced blocks only
    #
    # Five capabilities on one stack went dark for one missing variable each, and every
    # failure was silent. An instruction pointing at something absent is worse than none:
    # the node reports having consulted history when it consulted an empty file.
    # =======================================================================================
    infence && fence_info ~ /(bash|sh|shell|console)/ {
      n=split($0, tok, /[[:space:]]+/)
      for (i=1; i<=n; i++) {
        t=tok[i]
        if (t ~ /^\//) {                                  # absolute path
          gsub(/[",;)`]+$/, "", t)
          # Placeholders are not claims about the filesystem. `path/to` and `…` are the two
          # conventions a usage example actually uses; anything else is treated as real.
          if (t ~ /[<>$*]/) continue
          if (t ~ /path\/to/ || t ~ /\.\.\./ || t ~ /…/) continue
          print "CHECKPATH|" NR "|" t
        }
      }
    }

    END {
      # Only a file that IS the rules is asked to state a cost. A README or a skill doc
      # *about* the rules has no opening rule to attach one to, and demanding it there is a
      # category error that would train people to ignore the finding. Decided by filename,
      # or by an explicit flag — never by reading the document and judging its genre.
      if (ASRULES && !consequence)
        emit("bad", "no-consequence", 1, "the opening rule never says what happens if it is broken — a rule without a cost is a suggestion")
      if (bytes > 40000)
        emit("sad", "size", lines, "‾" int(bytes/1000) " KB reloaded every turn — it competes with the task for attention")
      printf "STAT|%d|%d\n", lines, bytes
    }
  ' "$f"
}

# Path existence is resolved in the shell, not awk: awk cannot see the filesystem the rule
# will actually run against, and a path that exists only on the author's machine is the
# failure mode, not a passing check.
resolve_paths() {
  while IFS='|' read -r tag line path; do
    [ "$tag" = "CHECKPATH" ] || { echo "$tag|$line|$path"; continue; }
    if [ -n "$IN_DOCKER" ]; then
      if docker exec "$IN_DOCKER" test -e "$path" >/dev/null 2>&1; then continue; fi
      # A container that is not running is "could not check", never "checked and absent".
      if ! docker inspect -f '{{.State.Running}}' "$IN_DOCKER" 2>/dev/null | grep -q true; then
        echo "notRun|$line|target-unavailable|container '$IN_DOCKER' is not running — nothing was checked"
        continue
      fi
      echo "bad|$line|absent-capability|the rule points at \`$path\`, absent inside '$IN_DOCKER' — a node told to run it will report having checked, and it will have checked nothing"
      continue
    fi
    if [ -e "$path" ]; then
      continue
    fi
    echo "bad|$line|absent-capability|the rule points at \`$path\`, which does not exist here — a node told to run it will report having checked, and it will have checked nothing"
  done
}

# ---------------------------------------------------------------------------------------
# Selftest: every check must be able to FIRE and to STAY SILENT. A check that has never
# been observed failing is a check nobody has reason to trust.
# ---------------------------------------------------------------------------------------
if [ "${SELFTEST:-0}" = "1" ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  fail=0
  expect() { # expect <label> <file> <kind> <should-fire:1|0>
    local label="$1" file="$2" kind="$3" want="$4"
    local got; got=$(lint_one "$file" | resolve_paths | grep -c "|$kind|" || true)
    local fired=0; [ "$got" -gt 0 ] && fired=1
    if [ "$fired" = "$want" ]; then printf '  ✅ %s\n' "$label"
    else printf '  ❌ %s (kind=%s fired=%s want=%s)\n' "$label" "$kind" "$fired" "$want"; fail=1; fi
  }

  # One finding per line, most severe first — so each pattern gets its own line here, or the
  # test would be asserting the reporting policy instead of the patterns.
  cat > "$tmp/bad.md" <<'EOF'
# 規則
> 動工前先查歷史。違反這條 = hook 會擋下你的第一個 tool call。
這個能力你可以主動查。
不是每次都要。
相關時再用即可。
EOF
  cat > "$tmp/good.md" <<'EOF'
# 🚨 最高優先 — 動工前先問歷史
> **在你要重做任何事之前,先查它。**
> 違反這條 = 第一個 tool call 被 hook reject。
## 什麼時候一定要查
| 情況 | 先查什麼 |
|---|---|
| 你在重做上一輪失敗的事 | 上一輪為什麼沒過 |
EOF
  cat > "$tmp/teaches.md" <<'EOF'
# 寫法指引
> 一律用命令句。違反的代價是規則被跳過。
- ✅ 「先查它。」
- ❌ 「你可以主動查。」
- ❌❌ 「不是每次都要。」 ← 這句直接授權跳過
不要寫成「相關時再查」。
EOF
  # Use versus mention: a table cataloguing the patterns, a description naming them, and a
  # placeholder path. None of these instructs anybody to do anything.
  cat > "$tmp/mentions.md" <<'EOF'
---
name: some-skill
description: Flags rules that say 不是每次都要 or as needed, and triggers like when relevant.
---
# 檢查器說明
> 用它。違反 = PR 被擋。
| kind | 會抓什麼 |
|---|---|
| self-exempting | `不是每次都要`、`視情況`、`as needed` |
| executor-judged | 「相關時」、"when relevant" |
```bash
lint.sh /path/to/CLAUDE.md
```
EOF
  # ...but a rule that USES the pattern, with the same words unquoted, must still fire.
  cat > "$tmp/uses.md" <<'EOF'
# 規則
> 先查。違反 = 被擋。
這個查詢視情況做即可。
EOF

  # A shell comment inside a fenced block is not a markdown heading. Two of them are not a
  # duplicate section, and neither of them closes the top block.
  mkdir -p "$tmp/fence"
  cat > "$tmp/fence/CLAUDE.md" <<'EOF'
# 🚨 規則
> **先查它。**
```bash
# 例:
osearch 'a'
```
```bash
# 例:
osearch 'b'
```
違反這條 = 第一個 tool call 被 hook reject。
EOF

  cat > "$tmp/absent.md" <<'EOF'
# 規則
> 先查。違反 = 被擋。
```bash
/definitely/not/here/crs vsearch '<問題>'
```
EOF
  mkdir -p "$tmp/nc" "$tmp/ok"
  cat > "$tmp/nc/CLAUDE.md" <<'EOF'
# 規則
> 動工前先查歷史。
EOF
  cp "$tmp/good.md" "$tmp/ok/CLAUDE.md"

  echo "claude-md-lint --selftest"
  expect "self-exempting 抓得到「不是每次都要」"          "$tmp/bad.md"      self-exempting          1
  expect "executor-judged-trigger 抓得到「相關時」"        "$tmp/bad.md"      executor-judged-trigger 1
  expect "permission 抓得到「你可以」"                     "$tmp/bad.md"      permission-not-instruction 1
  expect "一份好文件不被誤報(self-exempting)"            "$tmp/good.md"     self-exempting          0
  expect "一份好文件不被誤報(permission)"                "$tmp/good.md"     permission-not-instruction 0
  expect "教學用的反例不被當成違規 ← 今天的假紅"          "$tmp/teaches.md"  self-exempting          0
  expect "教學用的反例不被當成違規(permission)"          "$tmp/teaches.md"  permission-not-instruction 0
  expect "指向不存在的路徑會紅"                            "$tmp/absent.md"   absent-capability       1
  expect "存在的路徑不會紅"                                "$tmp/good.md"     absent-capability       0
  expect "叫 CLAUDE.md 而沒寫代價會紅"                     "$tmp/nc/CLAUDE.md" no-consequence         1
  expect "叫 CLAUDE.md 且有寫代價不會紅"                   "$tmp/ok/CLAUDE.md" no-consequence         0
  expect "講規則的文件(非 CLAUDE.md)不被要求寫代價"      "$tmp/teaches.md"   no-consequence         0
  expect "引用不觸發:表格列舉 pattern"                    "$tmp/mentions.md" self-exempting          0
  expect "引用不觸發:表格列舉 trigger"                    "$tmp/mentions.md" executor-judged-trigger 0
  expect "引用不觸發:frontmatter 描述"                    "$tmp/mentions.md" permission-not-instruction 0
  expect "引用不觸發:/path/to/ 佔位符"                    "$tmp/mentions.md" absent-capability       0
  expect "但同樣的字未加引號當指令用,仍要紅"              "$tmp/uses.md"     self-exempting          1
  expect "fence 內的 # 註解不是標題(不報重複節)"          "$tmp/fence/CLAUDE.md" duplicate-section   0
  expect "fence 內的 # 註解不提前關掉 top block"           "$tmp/fence/CLAUDE.md" no-consequence      0
  echo
  if [ "$fail" = "0" ]; then echo "selftest: PASS"; exit 0; else echo "selftest: FAIL"; exit 1; fi
fi

[ ${#FILES[@]} -gt 0 ] || { echo "usage: $0 <CLAUDE.md> [...] | --selftest" >&2; exit 2; }

# ---------------------------------------------------------------------------------------
declare -a ALL_BAD=() ALL_SAD=()
NOTRUN=0
for f in "${FILES[@]}"; do
  out=$(lint_one "$f" | resolve_paths) || true
  stat_line=$(printf '%s\n' "$out" | grep '^STAT|' | head -1)
  body=$(printf '%s\n' "$out" | grep -v '^STAT|' || true)

  if printf '%s\n' "$body" | grep -q '^notRun|'; then
    NOTRUN=1
    [ "$JSON" = "1" ] || echo "$f: notRun — $(printf '%s\n' "$body" | sed -n 's/^notRun|[0-9]*|[a-z-]*|//p')"
    continue
  fi

  [ "$JSON" = "1" ] || {
    lines=$(printf '%s' "$stat_line" | cut -d'|' -f2); bytes=$(printf '%s' "$stat_line" | cut -d'|' -f3)
    echo "$f  (${lines:-?} 行 / ${bytes:-?} bytes)"
  }
  while IFS='|' read -r sev line kind msg; do
    [ -n "${sev:-}" ] || continue
    case "$sev" in
      bad) ALL_BAD+=("$f:$line|$kind|$msg") ;;
      sad) ALL_SAD+=("$f:$line|$kind|$msg") ;;
    esac
    [ "$JSON" = "1" ] || printf '  %-4s %s:%s  %s\n       %s\n' "[$sev]" "$f" "$line" "$kind" "$msg"
  done <<< "$body"
done

nbad=${#ALL_BAD[@]}; nsad=${#ALL_SAD[@]}

# Baseline: inherited debt stays visible and stops blocking; new debt blocks. A check that
# floods on first run against an untouched document gets switched off — that has already
# happened twice in this repo, and both times the check was right.
BL_BAD=0
if [ -n "$BASELINE" ] && [ -f "$BASELINE" ]; then
  BL_BAD=$(grep '^bad=' "$BASELINE" 2>/dev/null | cut -d= -f2 || echo 0)
  BL_BAD=${BL_BAD:-0}
fi
if [ -n "$UPDATE_BL" ]; then
  printf 'bad=%d\nsad=%d\n' "$nbad" "$nsad" > "$UPDATE_BL"
  echo "baseline written: $UPDATE_BL (bad=$nbad sad=$nsad)"
  exit 0
fi

if [ "$NOTRUN" = "1" ] && [ "$nbad" = "0" ]; then verdict="notRun"
elif [ "$nbad" -gt "$BL_BAD" ]; then verdict="findings"
else verdict="pass"; fi

if [ "$JSON" = "1" ]; then
  printf '{"verdict":"%s","bad":%d,"sad":%d,"baselineBad":%d,"findings":[' "$verdict" "$nbad" "$nsad" "$BL_BAD"
  sep=""
  for x in "${ALL_BAD[@]:-}" ; do [ -n "$x" ] || continue
    printf '%s{"severity":"bad","at":"%s","kind":"%s"}' "$sep" "${x%%|*}" "$(printf '%s' "$x" | cut -d'|' -f2)"; sep=","; done
  for x in "${ALL_SAD[@]:-}" ; do [ -n "$x" ] || continue
    printf '%s{"severity":"sad","at":"%s","kind":"%s"}' "$sep" "${x%%|*}" "$(printf '%s' "$x" | cut -d'|' -f2)"; sep=","; done
  printf ']}\n'
else
  echo
  echo "verdict=$verdict  bad=$nbad (baseline $BL_BAD)  sad=$nsad"
  [ "$verdict" = "notRun" ] && echo "  notRun is NOT a pass — nothing was checked."
fi

case "$verdict" in
  pass) exit 0 ;;
  findings) exit 1 ;;
  *) exit 2 ;;
esac
