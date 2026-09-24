#!/usr/bin/env python3
"""用量紀錄帶上 CLI 自己算的花費 —— 跑法:python3 usage_cost_selftest.py

這支釘住的是 2026-09-24 量到的缺陷:
  `_usage.input` = 一般輸入 + 快取讀取 + 快取寫入,而讀取端拿它 × 原價估錢。
  快取讀取只收一成,agent 的一次呼叫大多是快取讀取 → 同一段時間讀取端算出 $68.82,
  CLI 自己回報 $15.53(4.4 倍)。loop 驅動器的週預算煞車讀的就是灌水的那個,
  於是在預算內的輪次被擋下。

修法:`_usage` 帶上 CLI 的 `total_cost_usd`(`cost_usd`),讀取端有就直接用。

  A 組:`_cost_usd` 的判準(真實形狀 + 壞值)
  B 組:它**真的被接進** `_invoke_claude_once` 產生的 `_usage` —— 一個寫好、測過、
        卻沒有任何呼叫者的函式,在這個 repo 出現過九次
  C 組:把**修之前**的原始碼餵給 B 組的檢查,必須變紅。不能對著壞版本變紅的檢查不算檢查。

注意:arcana-skills 沒有 CI,這支不會自動跑。
"""
import importlib.util, inspect, os, re, subprocess, sys

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

print("A 組 —— _cost_usd")
# 4a2ace83 的 IntakeReview(Opus 5.5 1M)真實回報值
check("真實的回報值原樣帶出", m._cost_usd({"total_cost_usd": 0.5625}) == 0.5625)
check("整數也收", m._cost_usd({"total_cost_usd": 2}) == 2.0)
check("0 是合法值(不可被當壞值丟掉)", m._cost_usd({"total_cost_usd": 0}) == 0.0)
check("沒有這個鍵 → None(不是 0)", m._cost_usd({}) is None)
check("null → None", m._cost_usd({"total_cost_usd": None}) is None)
check("負數 → None", m._cost_usd({"total_cost_usd": -1}) is None)
check("字串 → None", m._cost_usd({"total_cost_usd": "abc"}) is None)
check("NaN → None", m._cost_usd({"total_cost_usd": float("nan")}) is None)
check("無限大 → None", m._cost_usd({"total_cost_usd": float("inf")}) is None)
check("布林 → None(True 不是 $1)", m._cost_usd({"total_cost_usd": True}) is None)

WIRE = re.compile(r'"_usage"\]\s*=\s*\{[^}]*"cost_usd"\s*:\s*_cost_usd\(env\)', re.S)
def wired(src):
    return bool(WIRE.search(src))

print("B 組 —— 真的接上了")
check("_invoke_claude_once 產生的 _usage 帶 cost_usd",
      wired(inspect.getsource(m._invoke_claude_once)))

print("C 組 —— 修之前的原始碼必須讓 B 組變紅")
try:
    old = subprocess.run(["git", "-C", D, "show", "ee39184:claude-agents-workflow-skill/templates/agent-task-node/server.py"],
                         capture_output=True, text=True, timeout=30)
    if old.returncode != 0 or "_invoke_claude_once" not in old.stdout:
        print("  ? 取不到修之前的版本(%s)—— C 組沒跑,不是通過" % (old.stderr.strip()[:80] or "空"))
        fail += 1
    else:
        check("修之前(ee39184)的 _usage 沒帶 cost_usd → 檢查判紅", not wired(old.stdout))
except Exception as e:
    print("  ? C 組沒跑:%s" % e); fail += 1

print("\n  %d 過 / %d 失敗" % (ok, fail))
sys.exit(1 if fail else 0)
