#!/usr/bin/env python3
"""PM 第四態 BLOCKED 的自驗 —— 跑法:python3 pm_blocked_selftest.py
BLOCKED = 流水線驗不到(CI 沒跑、測試閘跑不起來),不是產品缺陷(NOGO)也不是要人裁決(HOLD)。
這裡驗三件事:schema 收得下、dispose 認得且說的是「環境」、prompt 不再把 notRun 教成 HOLD。"""
import importlib.util, json, os, sys, subprocess
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)
check("pm-review schema 的 verdict enum 含 BLOCKED", "BLOCKED" in m.SCHEMAS["pm-review"]["properties"]["verdict"]["enum"] if hasattr(m, "SCHEMAS") else "BLOCKED" in open(os.path.join(D, "server.py"), encoding="utf-8").read().split('"pm-review": {')[1].split("enum")[1][:80])
CALLS = []
orig = subprocess.run
def patched(cmd, *a, **k):
    c = cmd if isinstance(cmd, list) else [str(cmd)]
    class R: returncode = 0; stdout = ""; stderr = ""
    if c[0] == "gh": CALLS.append(c)
    return R()
subprocess.run = patched
try:
    r = m.dispose_pr({"pmReview": json.dumps({"verdict": "BLOCKED", "reasonCode": "PR_CI_NOT_RUN", "feedback": "CI never ran"}),
                      "pr": json.dumps({"prUrl": "https://github.com/x/y/pull/9"}), "slug": "s", "_piid": "i"})
finally:
    subprocess.run = orig
check("BLOCKED → 轉草稿(不是關掉)", r.get("action") == "converted to draft" and r.get("verdict") == "BLOCKED")
comment = next((c for c in CALLS if c[1:3] == ["pr", "comment"]), None)
check("留言說的是「流水線 / 環境」,不是「等裁決」", comment is not None and "流水線" in comment[comment.index("--body") + 1] and "環境" in comment[comment.index("--body") + 1])
check("留言裡有 PM 的 reason", comment is not None and "CI never ran" in comment[comment.index("--body") + 1])
src = open(os.path.join(D, "server.py"), encoding="utf-8").read()
pm = src.split("def prompt_pm_review(p):")[1].split("\ndef ")[0]
check("prompt:notRun → BLOCKED,不再教成 HOLD", "`verdict=notRun` -> **BLOCKED**" in pm and "`verdict=notRun` -> HOLD" not in pm)
check("prompt:disposition=escalate → BLOCKED", "disposition=escalate" in pm and "BLOCKED" in pm)
check("prompt:紅的證據仍是 NOGO(不能把 BLOCKED 當逃生口)", "NEVER BLOCKED when evidence exists and is red" in pm)
skill = open(os.path.join(D, "..", "..", "..", "arcana-pm-skill", "SKILL.md"), encoding="utf-8").read()
check("SKILL.md 有 BLOCKED 的定義與 blockedAttempts 說明", "**BLOCKED**" in skill and "blockedAttempts" in skill)
print("\n  通過 %d,失敗 %d" % (ok, fail)); sys.exit(1 if fail else 0)
