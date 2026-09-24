#!/usr/bin/env python3
"""品質收斂指標的自驗 —— 跑法:python3 quality_metrics_selftest.py

這支釘住的是**一個已經發生過的缺陷**,不是假想的風險。

第一版 `_quality_metrics` 的 Data Index 那段回了 `gateBlockedRounds: null`,
而 Data Index 當時活得好好的(POST :8180/graphql → 200,容器 Up 6 days)。
真因有兩個,而且兩個都被同一個過寬的 `except Exception` 蓋住:

  1. `urllib.request` 沒 import(本檔慣例是在函式**內部** import,我漏了)→ NameError
  2. Data Index 的 `variables` 回的是**一串 JSON 文字**,不是字典。
     對字串呼叫 `.get("testReport")` → AttributeError

兩個 bug,外觀完全一樣:一個誠實的「讀不到」。

**真正的教訓不是「記得 import」**,是:
> 「我的程式壞了」和「對方掛了」如果長得一模一樣,這個指標就不能用來做決定 ——
> 因為這兩件事要修的地方完全不同。所以 **None 一定要附理由(diError)**。

C 組是這支的重點:它把**修好之前**的寫法拿回來,對著同一份真實形狀的資料跑,
證明那個寫法真的會爆。一個判準若不能對著壞版本變紅,它就不是判準。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, json, os, sys

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


# ── 真實形狀:Data Index 把 variables 當**字串**回來(2026-09-23 從 :8180 實際觀察) ──
NOW = m.datetime.datetime.now(m.datetime.timezone.utc).isoformat()

def _pi(blocking):
    """一條在窗內、有 testReport 的實例。variables 是字串 —— 這是引擎真的回的形狀。"""
    v = {"testReport": json.dumps({"blockingReasons": (["uiux"] if blocking else [])})}
    return {"start": NOW, "variables": json.dumps(v)}

ROWS = [_pi(True), _pi(True), _pi(False)]   # 3 輪有報告,其中 2 輪被擋


class _R:
    def __init__(self, out): self.returncode = 0; self.stdout = out; self.stderr = ""


def _run_with(di_stdout, gh=None):
    """把 curl 與 gh 都換成罐頭,讓這支不需要網路也不需要跑著的服務。"""
    real_run, real_gh = m.subprocess.run, m._gh
    m.subprocess.run = lambda *a, **k: _R(di_stdout)
    m._gh = gh or (lambda args: (1, "", "stubbed"))   # gh 不存在 → GitHub 那幾項回 None
    try:
        return m._quality_metrics("owner/repo", "http://di.invalid")
    finally:
        m.subprocess.run, m._gh = real_run, real_gh


# ── A 組:正常路徑 —— variables 是字串也要數得對 ──────────────────────
a = _run_with(json.dumps({"data": {"ProcessInstances": ROWS}}))
check("A1 有報告的輪數 = 3", a["roundsWithReport"] == 3)
check("A2 被擋的輪數 = 2", a["gateBlockedRounds"] == 2)
check("A3 一切正常時 diError 必須是 None(不能留殘字)", a["diError"] is None)


# ── B 組:讀不到 —— 必須是 None,而且**必須講出理由** ────────────────
b = _run_with("")                       # curl 回空 → ProcessInstances 缺席
check("B1 讀不到 → gateBlockedRounds 是 None(不是 0)", b["gateBlockedRounds"] is None)
check("B2 讀不到 → roundsWithReport 是 None(不是 0)", b["roundsWithReport"] is None)
check("B3 **None 一定附理由** diError 非空", bool(b["diError"]))

b2 = _run_with(json.dumps({"errors": [{"message": "boom"}]}))
check("B4 GraphQL 回 errors 也算讀不到 + 附理由",
      b2["gateBlockedRounds"] is None and bool(b2["diError"]))


# ── C 組(重點):把修好之前的兩個寫法拿回來,證明它們真的會爆 ─────────
def _old_shape_string_variables(rows):
    """修好之前:直接把 variables 當字典。"""
    for pi in rows:
        (pi.get("variables") or {}).get("testReport")      # 字串 → AttributeError

try:
    _old_shape_string_variables(ROWS)
    check("C1 舊寫法(把 variables 當字典)會爆 —— 對照組", False)
except AttributeError:
    check("C1 舊寫法(把 variables 當字典)會爆 —— 對照組", True)

def _old_shape_no_reason(_rows):
    """修好之前:except 只寫 None,不留理由。"""
    try:
        raise NameError("name 'urllib' is not defined")     # 當時真正發生的例外
    except Exception:
        return {"gateBlockedRounds": None}                  # ← 沒有 diError

old = _old_shape_no_reason(ROWS)
check("C2 舊寫法把 NameError 偽裝成『讀不到』,且無從分辨 —— 對照組",
      old["gateBlockedRounds"] is None and "diError" not in old)


# ── D 組:缺來源回 None,不是 0(免得「0 個人工發現」被讀成已經不用人顧) ──
check("D1 gh 不在 → humanFound 是 None", a["humanFound"] is None)
check("D2 humanFoundMeasured 要誠實說沒量到", a["humanFoundMeasured"] is False)
check("D3 gh 不在 → gateCoverage 是 None(不是 0 個閘)", a["gateCoverage"] is None)


print("\n  %d 過 / %d 失敗" % (ok, fail))
sys.exit(1 if fail else 0)
