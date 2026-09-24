#!/usr/bin/env python3
"""Gemini 安全把關的自驗 —— 跑法:python3 security_gate_selftest.py

守的是一句話:**只有「最新一次」審查「明確」標出安全疑慮時才擋;其餘一律放行。**

背景(2026-09-23):merge-flow 以前只看「所有檢查都綠」就合併,沒有任何東西讀
PR Agent(Gemini)的審查內容。而那個 PR Agent 從 2026-02-27 之後就沒成功審過一次
(金鑰無效 + 模型下架),job 卻一直報成功 —— 綠燈不代表有人看過程式。

把關刻意設計成 fail-open:沒審查(Renovate / release PR 本來就跳過)、審查失敗、
審查比最新 commit 舊、人工加了覆寫標籤,都放行。它擋錯的代價(卡住合併)比漏擋高,
所以只在證據最強的那一種情況擋。

判準是 pr-agent 自己的輸出字串(convert_to_markdown_v2):
  沒有疑慮 → "No security concerns identified"
  有疑慮   → "Security concerns" + 內容
不交給模型解讀。

對照組是重點:每一個「必須擋」的案例,都要能對著「永遠放行」的壞版本變紅 ——
這支腳本最後會自己跑一次那個壞版本,確認測試真的會抓到。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。
"""
import importlib.util
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")

spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("  server.py import 成功")

# 真實 pr-agent 審查裡的那一列(取自 arcana-cloud-rust#122, 2026-09-23)
CLEAN = ("## PR Reviewer Guide 🔍\n<table>\n"
         "<tr><td>⏱️&nbsp;<strong>Estimated effort to review</strong>: 1 🔵⚪⚪⚪⚪</td></tr>\n"
         "<tr><td>🔒&nbsp;<strong>No security concerns identified</strong></td></tr>\n</table>")
CONCERN = CLEAN.replace("<strong>No security concerns identified</strong>",
                        "<strong>Security concerns</strong><br><br>\n\n"
                        "<strong>Hardcoded secret:</strong> API key committed in config.py")
BOT = "github-actions[bot]"
HEAD = "2026-09-23T10:00:00Z"

CASES = [
    # (名稱, comments, labels, head_time, 期望放行)
    ("沒有任何審查(Renovate/release 被跳過)", [], set(), HEAD, True),
    ("審查失敗,只有 Failed 留言",
     [{"login": BOT, "body": "Failed to review PR", "updated_at": "2026-09-23T11:00:00Z"}], set(), HEAD, True),
    ("最新審查:沒有安全疑慮",
     [{"login": BOT, "body": CLEAN, "updated_at": "2026-09-23T11:00:00Z"}], set(), HEAD, True),
    ("最新審查:有安全疑慮 → 必須擋",
     [{"login": BOT, "body": CONCERN, "updated_at": "2026-09-23T11:00:00Z"}], set(), HEAD, False),
    ("有疑慮但審查比最新 commit 舊 → 放行",
     [{"login": BOT, "body": CONCERN, "updated_at": "2026-09-23T09:00:00Z"}], set(), HEAD, True),
    ("有疑慮但人工加了 security-reviewed → 放行",
     [{"login": BOT, "body": CONCERN, "updated_at": "2026-09-23T11:00:00Z"}], {"security-reviewed"}, HEAD, True),
    ("舊的有疑慮、新的乾淨 → 以最新為準放行",
     [{"login": BOT, "body": CONCERN, "updated_at": "2026-09-23T10:30:00Z"},
      {"login": BOT, "body": CLEAN, "updated_at": "2026-09-23T11:30:00Z"}], set(), HEAD, True),
    ("舊的乾淨、新的有疑慮 → 以最新為準擋",
     [{"login": BOT, "body": CLEAN, "updated_at": "2026-09-23T10:30:00Z"},
      {"login": BOT, "body": CONCERN, "updated_at": "2026-09-23T11:30:00Z"}], set(), HEAD, False),
    ("人類留言寫 Security concerns 不算數",
     [{"login": "jrjohn", "body": "Reviewer Guide ... Security concerns?", "updated_at": "2026-09-23T11:00:00Z"}],
     set(), HEAD, True),
]


def run(fn, label):
    fails = 0
    for name, cm, lb, ht, exp in CASES:
        allow, why = fn(cm, lb, ht)
        ok = allow == exp
        fails += not ok
        if label == "real":
            print("  %s 期望%s | %s | %s" % ("PASS" if ok else "FAIL", "放行" if exp else "擋下", name, why))
    return fails


fails = run(m.evaluate_security_gate, "real")
print("\n  %d / %d 通過" % (len(CASES) - fails, len(CASES)))

# 對照組:永遠放行的壞版本,必須讓「必須擋」的案例變紅
broken = run(lambda cm, lb, ht: (True, "broken"), "broken")
must_block = sum(1 for c in CASES if not c[4])
print("  對照組(永遠放行):%d 個案例變紅,應為 %d" % (broken, must_block))

if fails or broken != must_block:
    print("FAIL")
    sys.exit(1)
print("OK")
