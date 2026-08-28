#!/usr/bin/env python3
"""SA / SD 拿得到既有規格的自驗 —— 跑法:python3 existing_specs_selftest.py

## 為什麼需要這個

`_memory_brief` 只到 intake / implement / pm-review —— **SA、SD、uiux、test 什麼都
拿不到**(`_write_workspace_claude_md` 的 docstring 自己記著這件事)。後果是 SA 和 SD
各自跑完一整個節點,一次都沒問過前幾輪決定了什麼,於是產出的 SRS 讀起來像一個獨立
工具的規格,而不是這個產品的第 N 個功能。

重點是 C 組:**「問不到」與「目前沒有」必須是兩句話**。
`None`(沒有工作目錄可讀)和 `[]`(讀了,而這個 repo 還沒有規格)在下游是不同的意思;
合併就是這一整條工作在對抗的那種錯 —— 下游會把「還沒有」當成「我沒看到」。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, os, shutil, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("  server.py import 成功")

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)


def repo_with(specs):
    """造一個假 repo,docs/specs/<slug>/<name>.md 各放一份。"""
    d = tempfile.mkdtemp()
    for slug, name, body in specs:
        p = os.path.join(d, "docs", "specs", slug)
        os.makedirs(p, exist_ok=True)
        open(os.path.join(p, name), "w", encoding="utf-8").write(body)
    return d

SRS_BODY = """# SRS —— stage-drawer-resizable

## 文件資訊

| 項目 | 內容 |
|---|---|
| 功能代號 | `stage-drawer-resizable` |

---

## 1. 問題陳述

右欄寬度寫死為 420px,不論螢幕多寬。1600px 螢幕上表單一行只放得下五六個字。
"""

print("\n════ A. 讀得到既有規格 ════")
d = repo_with([("stage-drawer-resizable", "SRS.md", SRS_BODY)])
got = m._existing_specs(d)
check("回的是 list", isinstance(got, list))
check("找到 1 份", isinstance(got, list) and len(got) == 1)
if got:
    r = got[0]
    check("path 指得出檔案", r["path"] == "docs/specs/stage-drawer-resizable/SRS.md")
    check("認得出是哪個功能", r["feature"] == "stage-drawer-resizable")
    check("認得出是 SRS 還是 SDD", r["kind"] == "SRS")
    check("摘要是第一個實質段落,不是標題或表格線",
          "420px" in r["gist"] and not r["gist"].startswith(("#", "|", "-")))

print("\n════ B. 多個功能、多份文件都收得到 ════")
d2 = repo_with([
    ("feat-a", "SRS.md", "# A\n\n## 1. 問題\n\nA 的問題。\n"),
    ("feat-a", "SDD.md", "# A\n\n## 1. 設計\n\nA 的設計。\n"),
    ("feat-b", "SRS.md", "# B\n\n## 1. 問題\n\nB 的問題。\n"),
])
g2 = m._existing_specs(d2)
check("三份都收到", len(g2) == 3)
check("同一個功能的兩份都在",
      len([x for x in g2 if x["feature"] == "feat-a"]) == 2)
check("非 .md 不會被收",
      all(x["path"].endswith(".md") for x in g2))

print("\n════ C. 「問不到」與「目前沒有」是兩句話 ════")
check("沒有工作目錄 → None(問不到)", m._existing_specs(None) is None)
check("空字串也是 None", m._existing_specs("") is None)
empty = m._existing_specs(tempfile.mkdtemp())
check("有工作目錄但沒有 docs/specs → [](讀了,沒有規格)", empty == [])
check("None 與 [] 不可混為一談", m._existing_specs(None) is not empty)

print("\n════ D. 接進 project_context,而且缺席時說得出來 ════")
ctx = m.project_context({}, d)
check("existingSpecs 有進 context",
      "existingSpecs" in (ctx.get("context") or {}))
ctx_none = m.project_context({}, None)
miss = " ".join(ctx_none.get("unavailable") or [])
check("沒有工作目錄時列進 unavailable", "既有規格清單" in miss)
ctx_empty = m.project_context({}, tempfile.mkdtemp())
check("空 repo 不謊報為 unavailable(那是事實,不是查不到)",
      "既有規格清單" not in " ".join(ctx_empty.get("unavailable") or []))

print("\n════ E. 提示詞裡看得到,而且告訴節點去讀檔 ════")
brief = m.project_brief({}, d)
check("brief 帶出既有規格", "stage-drawer-resizable" in brief)
check("brief 告訴節點可以直接讀那個檔", "docs/specs/" in brief)

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
