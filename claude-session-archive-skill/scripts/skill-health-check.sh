#!/usr/bin/env bash
# skill-health-check.sh — 抓「有知識卻永遠不會被載入」的 skill。
#
# 為什麼存在(2026-09-18):
#   ~/.claude/skills/inap-release-manager/ 有完整的 instructions.md + references/
#   (含踩坑換來的 CR 更新規則),但缺 SKILL.md。Claude Code 只靠 SKILL.md 發現
#   skill,所以它自建立起從未被載入過一次 —— 目錄在、內容完整、沒有任何錯誤訊息。
#   每次都重頭做一遍,因為那份知識是隱形的。這種壞法完全靜默,只能靠掃描抓。
#
# ── 判準的由來(第一版寫錯,這裡記下來免得改回去)────────────────────────
#   第一版把「SKILL.md 沒有 frontmatter」判成 BAD,結果一次噴出 8 個 —— 但其中
#   luminous-skill / mis-management-skill / somnics-cloud-report / doc-indexer-skill
#   全都好端端地在可用清單裡。實測 luminous-skill/SKILL.md 確實沒有 frontmatter,
#   它以第一個 H1 標題當描述被載入。
#   → Claude Code 會 fallback 到標題。缺 frontmatter 不是「壞掉」,是「觸發力弱」。
#   → 誤判的方向永遠是「把常規寫法判成缺陷」。所以嚴重度分三級,只有真的隱形才擋。
#
#   BAD  = 有 .md 知識(深度 ≤2)卻完全沒有 SKILL.md  → 永遠不會被載入,必須修
#   SAD  = 有 SKILL.md 但沒有 frontmatter description → 會載入,但退化成用標題當
#                                                       觸發詞,命中率差。值得修,不擋
#   INFO = 空目錄 / slash-command 包 / 快取目錄        → 本來就不是 skill,不該報
#
# 用法:  bash skill-health-check.sh [skills-dir]
# 結束碼: 0=pass(可含 SAD/INFO)  1=findings(有 BAD)  2=notRun(掃不到目錄)

set -u
SKILLS_DIR="${1:-$HOME/.claude/skills}"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "notRun: 找不到 skills 目錄 $SKILLS_DIR"
  exit 2
fi

bad=0; sad=0; info=0; checked=0
bad_lines=""; sad_lines=""; info_lines=""

# frontmatter 取值:只看檔案開頭的 --- 區塊;沒有區塊就回空字串
fm_get() {
  awk -v key="$2" '
    NR==1 && $0 != "---" { exit }
    NR==1 { next }
    $0 == "---" { exit }
    index($0, key ":") == 1 { sub(/^[^:]*:[[:space:]]*/, ""); print; exit }
  ' "$1" 2>/dev/null
}

for dir in "$SKILLS_DIR"/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  checked=$((checked + 1))
  skill_md="$dir/SKILL.md"

  if [ -f "$skill_md" ]; then
    fm_desc=$(fm_get "$skill_md" "description")
    fm_name=$(fm_get "$skill_md" "name")

    if [ -z "$fm_desc" ]; then
      sad_lines="${sad_lines}  SAD  $name — SKILL.md 無 frontmatter description,退化成用標題當觸發詞\n"
      sad=$((sad + 1))
    elif [ -n "$fm_name" ] && [ "$fm_name" != "$name" ]; then
      # 目錄名才是清單顯示的名字,不致命
      sad_lines="${sad_lines}  SAD  $name — frontmatter name='$fm_name' 與目錄名不符(以目錄名為準)\n"
      sad=$((sad + 1))
    fi
    continue
  fi

  # 沒有 SKILL.md —— 分辨「隱形的知識」與「本來就不是 skill」
  if [ -z "$(find -L "$dir" -type f -print -quit 2>/dev/null)" ]; then
    info_lines="${info_lines}  INFO $name — 空目錄,無害(可刪)\n"
    info=$((info + 1)); continue
  fi
  if [ -d "$dir/commands" ]; then
    info_lines="${info_lines}  INFO $name — slash-command 包(有 commands/),非 skill\n"
    info=$((info + 1)); continue
  fi

  # 只看深度 ≤2 的 .md:真正的 skill 知識放在根或 references/,
  # 埋在更深 UUID 目錄裡的是同步快取(如 synced/)
  shallow_md=$(find -L "$dir" -maxdepth 2 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
  if [ "$shallow_md" -eq 0 ]; then
    info_lines="${info_lines}  INFO $name — 淺層無 .md(快取/資料目錄),非 skill\n"
    info=$((info + 1))
  else
    bad_lines="${bad_lines}  BAD  $name — 有 $shallow_md 個 .md 但缺 SKILL.md → 這些知識永遠不會被載入\n"
    bad=$((bad + 1))
  fi
done

echo "skill-health-check: $SKILLS_DIR  (檢查 $checked 個目錄)"
[ -n "$bad_lines" ]  && printf "%b" "$bad_lines"
[ -n "$sad_lines" ]  && printf "%b" "$sad_lines"
[ -n "$info_lines" ] && printf "%b" "$info_lines"

if [ "$bad" -gt 0 ]; then
  echo "verdict=findings  bad=$bad  sad=$sad  info=$info"
  exit 1
fi
echo "verdict=pass  bad=0  sad=$sad  info=$info"
exit 0
