#!/usr/bin/env python3
"""規格要渲染成**真的 Markdown** 的自驗 —— 跑法:python3 spec_markdown_selftest.py

## 為什麼需要這支

2026-08-28,`_pv` 補上 `design` 那一層之後,規格終於落進版控了(PR #290)。
量一下寫出去的東西:

    SRS.md   19787 位元組   Markdown 標題 0 個   有 `## 文件資訊` = 否

副檔名是 `.md`,內容是一整包 `json.dumps`。也就是說「規格進了版控」達成了,
而「規格拿得出來當文件」沒有 —— 而且前者過了會讓後者**看起來也過了**。

後果是可量的:把那份檔丟給 md-to-docx,`parseDocumentStructure` 因為找不到
`## 文件資訊` 會一直停在 cover 段,轉出來的 .docx 只有封面與目錄,
**而且它仍然回報 `Created (14 KB)`**。實測 356 字 vs 11515 字。

所以這支問的是三件事,而不是「有沒有呼叫渲染器」:
  · 渲染出來的是不是真 Markdown(有標題、有 `## 文件資訊`)
  · **有沒有漏欄位** —— 不認得的鍵也必須印出來
  · 內容有沒有在轉換中掉字

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, json, os, re, subprocess, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
notrun = []
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)
def skip(label, why):
    notrun.append(label); print("  ⊘ %s —— %s(這是「沒檢查」,不是「通過」)" % (label, why))

# SA / SD 真實產出的形狀(2026-08-28 從實例 48c6d365 量的):
# 平鋪的 dict,值不是 str 就是 list[str]。
SRS = {
    "problem": "右欄寬度寫死 420px,1600px 螢幕上一行只放得下五六個字。",
    "requirements": ["**R1** 抽屜要可以加寬。", "**R2** 再按一次要回到原寬度。"],
    "acceptance": ["**AC-1** Given 抽屜開著,When 按下切換,Then 量到的寬度 > 600px。"],
    "edgeCases": ["視窗小於 900px 時不提供加寬。"],
    "_confidence": {"policy": "none", "verdict": "notApplicable"},
}

print("\n════ A. 產出的是真 Markdown ════")
md = m._spec_markdown("srs", "stage-drawer-resizable", SRS)
heads = [l for l in md.split("\n") if l.startswith("#")]
check("有 Markdown 標題(%d 個)" % len(heads), len(heads) >= 4)
check("有 `## 文件資訊` —— md-to-docx 靠它離開 cover 段", "## 文件資訊" in md)
check("開頭是 H1 標題", md.lstrip().startswith("# "))
check("功能代號寫進文件資訊", "`stage-drawer-resizable`" in md)
check("不是 JSON 傾印", not md.split("---")[-1].strip().startswith("{"))

print("\n════ B. 章節命名與排序 ════")
check("problem → 問題陳述", "## 1. 問題陳述" in md)
check("requirements → 需求項目", "## 2. 需求項目" in md)
check("acceptance → 驗收條件", "## 3. 驗收條件" in md)
check("edgeCases → 邊界情況", "## 4. 邊界情況" in md)
sdd = m._spec_markdown("sdd", "x", {"approach": "A", "files": ["f"], "steps": ["s"]})
check("SDD 用自己的章節名", "## 1. 設計取向" in sdd and "## 2. 影響的檔案" in sdd)

print("\n════ C. 不認得的欄位不可以被丟掉 ════")
# 這一組是這支的重點。少印一個欄位,下游就少看見一段需求,而且沒有人會發現:
# 文件看起來是完整的 —— 這正是這條流水線反覆出現的那個病。
extra = dict(SRS)
extra["riskRegister"] = ["RK-1 使用者可能找不到切換鈕。"]
extra["openQuestions"] = "門檻要不要跟著螢幕寬度走?"
md2 = m._spec_markdown("srs", "x", extra)
check("未知欄位 riskRegister 有印出來", "riskRegister" in md2 and "RK-1" in md2)
check("未知欄位 openQuestions 有印出來", "openQuestions" in md2 and "門檻要不要" in md2)
check("_confidence 這種簿記欄位也不丟", "_confidence" in md2)

print("\n════ D. 內容一個字都不能掉 ════")
def strings_of(v):
    if isinstance(v, str): return [v]
    if isinstance(v, list): return [x for i in v for x in strings_of(i)]
    if isinstance(v, dict): return [x for i in v.values() for x in strings_of(i)]
    return []
miss = [s for s in strings_of(extra) if s.strip() and s.strip() not in md2]
check("原始字串 %d 條全在(缺 %d 條)" % (len(strings_of(extra)), len(miss)), not miss)
multi = m._spec_markdown("srs", "x", {"requirements": ["第一行\n第二行\n第三行"]})
check("多行條目的續行仍屬於同一個清單項", "- 第一行" in multi and "\n  第二行" in multi)

print("\n════ E. 空的規格不寫空殼 ════")
# 一份空的 SDD 比沒有 SDD 更糟:它讓覆蓋率的分母看起來有東西。
for empty in (None, "", {}, []):
    d = tempfile.mkdtemp()
    got = m.write_specs(d, "x", {"design": {"srs": empty}})
    if got: break
check("srs 是空的(None/空字串/空 dict/空 list)時完全不寫檔", not got)

print("\n════ F2. 節點拿到的是 JSON **字串**,不是 dict ════")
# 這一組的存在理由,是這支自驗第一版全綠而真跑失敗(實例 7d88a7f0 / PR #292)。
# BPMN 把 srs/sdd/uiuxSpec 宣告成 `_strItem`(structureRef="String"),引擎存的是
# JSON 字串;Data Index 的 `variables` 會幫忙解析成物件 —— 我照那個樣子設計並測試,
# 於是渲染器從來沒收過 dict,而自驗一路綠燈。
#
# 教訓寫成判準:**測試資料要取自節點真正收到的那一端**,不是取自顯示層。
as_string = json.dumps(SRS, ensure_ascii=False)
md_s = m._spec_markdown("srs", "x", as_string)
check("JSON 字串會被解開後渲染(行首標題 %d 個)"
      % sum(1 for l in md_s.split("\n") if l.startswith("#")),
      sum(1 for l in md_s.split("\n") if l.startswith("#")) >= 4)
check("字串輸入與物件輸入產出相同", md_s == m._spec_markdown("srs", "x", SRS))
check("解不開的字串不會被丟掉", "只是一段白話" in m._spec_markdown("srs", "x", "只是一段白話"))
check("字串 \"null\" 視同沒有", m._spec_markdown("srs", "x", "null") == "")

# 直通條件必須問**形狀**,不是問字眼。
# 這正是 PR #292 的失效點:那份 SRS 在**討論** `## 文件資訊` 這個字串,
# 於是「內文含 ## 文件資訊」成立,整包 JSON 被原封不動當成文件送出去。
talks_about = json.dumps(
    {"problem": "驗收要看有沒有 `## 文件資訊`,不能只看檔案大小。"}, ensure_ascii=False)
md_t = m._spec_markdown("srs", "x", talks_about)
check("只是「提到」## 文件資訊 的 JSON 不會被當成 Markdown 直通",
      md_t.lstrip().startswith("# ") and not md_t.lstrip().startswith("{"))

print("\n════ F. 已經是 Markdown 的字串原樣採用 ════")
already = "# 我自己寫的\n\n## 文件資訊\n\n| a | b |\n\n## 1. 內容\n\n正文。\n"
out = m._spec_markdown("srs", "x", already)
check("不二次包裝", out.count("## 文件資訊") == 1 and out.startswith("# 我自己寫的"))
plain = m._spec_markdown("srs", "x", "只是一段白話,沒有標題。")
check("純文字會補上文件資訊", "## 文件資訊" in plain and "只是一段白話" in plain)

print("\n════ G. 端到端:轉成 .docx 之後真的有內文 ════")
JS = os.path.expanduser("~/.claude/skills/app-requirements-skill/md-to-docx.js")
if not os.path.isfile(JS):
    skip("md-to-docx 端到端", "找不到 %s" % JS)
elif subprocess.run(["which", "node"], capture_output=True).returncode != 0:
    skip("md-to-docx 端到端", "這台沒有 node")
else:
    t = tempfile.mkdtemp()
    def docx_text(text):
        """轉成 .docx 再把內文抽回來。回 None 代表**轉不出來**(問不到),不是「空的」。"""
        p_md = os.path.join(t, "x.md"); p_dx = os.path.join(t, "x.docx")
        open(p_md, "w", encoding="utf-8").write(text)
        if os.path.exists(p_dx): os.remove(p_dx)
        subprocess.run(["node", JS, p_md, p_dx], capture_output=True, timeout=120)
        if not os.path.exists(p_dx): return None
        import zipfile
        with zipfile.ZipFile(p_dx) as z:
            return re.sub(r"<[^>]+>", "", z.read("word/document.xml").decode("utf-8"))

    t_new = docx_text(md)
    t_old = docx_text(json.dumps(SRS, ensure_ascii=False, indent=2))
    if t_new is None or t_old is None:
        skip("md-to-docx 端到端", "轉檔沒有產出檔案")
    else:
        # 判準是**內文在不在**,不是位元組數。門檻會隨樣本大小飄,而「AC-1 這句話
        # 有沒有出現在 .docx 裡」不會 —— 它正是使用者打開檔案時要看到的東西。
        # 兩邊都量:只證明新的過得去不算數,舊的必須紅,否則這一組沒有分辨力。
        needles = ["420px", "AC-1", "問題陳述", "驗收條件"]
        old_hits = [n for n in needles if n in t_old]
        new_hits = [n for n in needles if n in t_new]
        check("舊做法(JSON 傾印)轉出來是空殼:%d/%d 句都不在(%d 字)"
              % (len(needles) - len(old_hits), len(needles), len(t_old)), not old_hits)
        check("新做法:%d/%d 句都在 .docx 裡(%d 字)"
              % (len(new_hits), len(needles), len(t_new)), len(new_hits) == len(needles))
        check("新的比舊的多出真內文", len(t_new) > len(t_old))

print("\n" + "═" * 46)
if notrun:
    print("  未檢查 %d 項:%s" % (len(notrun), ", ".join(notrun)))
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
