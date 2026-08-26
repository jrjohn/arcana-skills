#!/usr/bin/env python3
"""UI/UX 稽核去重的自驗 —— 跑法:python3 uiux_dedup_selftest.py

這支的重點是 C 組。A、B 只證明新寫法會過,而「會過」從來不是問題所在:
舊寫法也一直在跑、一直回報 skipped,只是它比對的欄位**已經被流程改掉了**,
所以一次都沒攔下來。C 組把舊寫法拿回來對著同一份真實資料跑,證明它會漏。

一個判準若不能對著壞版本變紅,它就不是判準,是一段沒有人會發現失效的程式碼。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, os, sys

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

# 2026-08-26 從引擎實際讀到的兩條在跑的實例。slug 欄位是流程改寫**之後**的值 ——
# 這正是舊寫法看到的東西,也正是它為什麼比不中。
LIVE = [
    {"slug": "workflow-page-i18n-zhtw",
     "feature_request": "[UI/UX 自動稽核] /workflow — 狀態標籤、篩選頁籤中英夾雜。"
                        "請依 app-uiux-designer rubric 修正此問題。\n\n〔稽核識別:uiux-workflow-i18n〕"},
    {"slug": "workflow-failure-reason-panel",
     "feature_request": "[UI/UX 自動稽核] /workflow — 詳情面板空白未顯示失敗原因。"
                        "請依 app-uiux-designer rubric 修正此問題。\n\n〔稽核識別:uiux-workflow-empty-state〕"},
]

def collect_new(instances):
    """現在的寫法:slug 與 feature_request 裡的識別碼都收。"""
    s = set()
    for v in instances:
        if v.get("slug"):
            s.add(v["slug"])
        s |= m._audit_markers_in(v.get("feature_request"))
    return s

def collect_old(instances):
    """2026-08-26 之前的寫法,原封不動搬過來當對照組。"""
    s = set()
    for v in instances:
        if v.get("slug"):
            s.add(v["slug"])
    return s

print("\n════ A. 識別碼寫得出、也讀得回 ════")
mk = m._audit_marker("uiux-workflow-i18n")
check("標記帶得出 slug", "uiux-workflow-i18n" in mk)
check("讀得回同一個", m._audit_markers_in("需求內文" + mk) == {"uiux-workflow-i18n"})
check("空 slug 不留下半個標記", m._audit_marker("") == "" and m._audit_marker(None) == "")
check("沒有標記回空集合,不是 None", m._audit_markers_in("一段普通的需求") == set())
check("不是字串也回空集合(別讓 None 炸掉整輪稽核)", m._audit_markers_in(None) == set())
check("一段文字帶兩個識別碼要兩個都收",
      m._audit_markers_in(m._audit_marker("uiux-a") + m._audit_marker("uiux-b")) == {"uiux-a", "uiux-b"})

print("\n════ B. 新寫法:攔得下重複的單 ════")
seen = collect_new(LIVE)
check("uiux-workflow-i18n 被認出在飛", "uiux-workflow-i18n" in seen)
check("uiux-workflow-empty-state 被認出在飛", "uiux-workflow-empty-state" in seen)
check("沒開過的發現照樣放行(不能全部擋死)", "uiux-org-contrast" not in seen)
check("改寫後的 slug 也一起收著", "workflow-page-i18n-zhtw" in seen)

print("\n════ C. 對照組:舊寫法對著同一份資料必須漏 ════")
old = collect_old(LIVE)
check("舊寫法看不到 uiux-workflow-i18n(這就是重複開 8 次的原因)",
      "uiux-workflow-i18n" not in old)
check("舊寫法看不到 uiux-workflow-empty-state",
      "uiux-workflow-empty-state" not in old)
check("舊寫法收到的只有被改寫後的名字",
      old == {"workflow-page-i18n-zhtw", "workflow-failure-reason-panel"})

print("\n════ D. 人手動刪掉標記 → 去重失效,但不能崩 ════")
tampered = [{"slug": "workflow-page-i18n-zhtw",
             "feature_request": "[UI/UX 自動稽核] /workflow — 有人把識別碼刪了。"}]
t = collect_new(tampered)
check("不炸", isinstance(t, set))
check("擋不住是預期的(人刻意改的,不替他決定)", "uiux-workflow-i18n" not in t)

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
