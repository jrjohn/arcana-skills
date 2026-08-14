#!/usr/bin/env python3
"""PR 建置閘的自驗 —— 跑法:python3 ci_gate_selftest.py

守的是一句話:**流程必須看得見自己 PR 的建置結果,而缺席不是綠。**

2026-08-14 在 arcana-ai-bpm #212 觀察到:Jenkins 兩次把該分支判 FAILURE
(`designers.spec.ts`「form designer mounts the form-js editor」—— 一支在 main 上
三個瀏覽器全過的既有測試,在這個 PR 上 20 秒找不到 `app-form-editor`;第一輪 6 個
失敗,第二輪變 9 個),而流程從頭到尾沒有提過這件事:

  · `testReport` 有 101 個欄位,無一攜帶 CI / build 狀態
  · `pmReview` 全文提及 Jenkins / CI / build 各 0 次
  · Implement 因此重做兩輪都不知道建置是紅的,第二輪還把它弄得更糟

Implement 修得動壞掉的建置。沒有人告訴它有這回事。

對照組是這支腳本的重點。三個容易寫錯的方向,每一個都要能對著「舊的寫法」變紅:

  (1) 只數失敗 → 清單空的時候讀成「沒有紅」→ 綠。這正是 #212 推新 commit 後
      Jenkins 三個 context 從清單**消失**(不是 pending)的那段時間會發生的事。
  (2) 把「沒有 CI 的 repo」也擋下來 → 每個不用 CI 的產品都永遠過不了。
  (3) 把 red 與 notRun 併成同一種阻擋 → PM 分不出「改程式」與「等建置」,
      於是叫 Implement 去修一個根本沒建起來的 PR,白燒一輪。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
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

ok = fail = 0


def check(label, cond):
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {label}")
    else:
        fail += 1
        print(f"  ✗ {label}")


def C(name, state):
    return {"name": name, "state": state, "detail": "", "url": ""}


# ── 1. 判定:四種狀態各自成立 ──────────────────────────────────
print("\n[1] _ci_verdict 的四個狀態")

v, reds = m._ci_verdict([C("ci/angular", "red"), C("ci/rust", "green")], base_has_ci=True)
check("有紅 → red,且點名紅的那一項", v == "red" and [c["name"] for c in reds] == ["ci/angular"])

v, _ = m._ci_verdict([C("ci/angular", "green"), C("ci/rust", "green")], base_has_ci=True)
check("全綠 → green", v == "green")

v, _ = m._ci_verdict([], base_has_ci=True)
check("清單空 + base 有 CI → notRun(不是 green)", v == "notRun")

v, _ = m._ci_verdict([], base_has_ci=False)
check("清單空 + base 沒 CI → notApplicable(不擋沒有 CI 的產品)", v == "notApplicable")

v, _ = m._ci_verdict([C("ci/angular", "pending")], base_has_ci=True)
check("還有 pending → notRun(未落地不算過)", v == "notRun")

v, _ = m._ci_verdict([C("a", "green"), C("b", "pending")], base_has_ci=True)
check("部分綠 + 部分未完成 → notRun(部分清單不是完整清單)", v == "notRun")


# ── 2. 對照組:三種寫錯的方向都必須被判出來 ───────────────────
print("\n[2] 對照組 —— 舊的/天真的寫法會怎麼錯")

# (1) 只數失敗數
naive_count_only = lambda checks: "red" if any(c["state"] == "red" for c in checks) else "green"
check("對照:只數失敗會把『空清單』讀成 green,本實作讀成 notRun",
      naive_count_only([]) == "green" and m._ci_verdict([], True)[0] == "notRun")

# (2) 一律要求有 CI
naive_always_required = lambda checks: "red" if not checks else "green"
check("對照:一律要求會把『沒有 CI 的 repo』判紅,本實作判 notApplicable",
      naive_always_required([]) == "red" and m._ci_verdict([], False)[0] == "notApplicable")

# (3) red 與 notRun 併成同一種
red_note = m._fold_ci({}, {"verdict": "red", "summary": "ci/angular — E2E gap"})["blockingReasons"][0]["note"]
nr_note = m._fold_ci({}, {"verdict": "notRun", "summary": "等了 1800 秒"})["blockingReasons"][0]["note"]
check("red 的說明要說『修得動』", "修得動" in red_note)
check("notRun 的說明要說『不要為它改程式』", "不要為它改程式" in nr_note)
check("兩者說明不同(PM 才分得出 NOGO 與 HOLD)", red_note != nr_note)


# ── 3. 折進報告:判定要與其他閘出自同一個物件 ─────────────────
print("\n[3] _fold_ci 折進 testReport")

rep = {"allPass": True, "blockingReasons": []}
m._fold_ci(rep, {"verdict": "red", "summary": "ci/angular — E2E gap"})
check("red 會把 allPass 打成 False", rep["allPass"] is False)
check("red 會進 blockingReasons,gate=prCi",
      any(b.get("gate") == "prCi" for b in rep["blockingReasons"]))
check("summary 原文有帶進去(Implement 要看得到是哪一項)",
      "ci/angular" in rep["blockingReasons"][0]["note"])

rep = {"allPass": True, "blockingReasons": []}
m._fold_ci(rep, {"verdict": "notRun", "summary": "沒有任何檢查回報"})
check("notRun 也會擋(缺席不等於通過)", rep["allPass"] is False)

rep = {"allPass": True, "blockingReasons": []}
m._fold_ci(rep, {"verdict": "green", "summary": "4 項檢查全綠"})
check("green 不動 allPass", rep["allPass"] is True and rep["blockingReasons"] == [])

rep = {"allPass": True, "blockingReasons": []}
m._fold_ci(rep, {"verdict": "notApplicable", "summary": ""})
check("notApplicable 不動 allPass", rep["allPass"] is True and rep["blockingReasons"] == [])

rep = {"allPass": True}          # runner 沒給 blockingReasons 的舊報告
m._fold_ci(rep, {"verdict": "red", "summary": "x"})
check("報告沒有 blockingReasons 欄位時不會爆", rep["blockingReasons"][0]["gate"] == "prCi")

check("prCi 一定會被寫進報告(即使是綠的,PM 要看得到它跑過)",
      m._fold_ci({}, {"verdict": "green"}).get("prCi", {}).get("verdict") == "green")


# ── 4. 不讀自己貼的那一格 ────────────────────────────────────
print("\n[4] 不能拿自己的成績當證據")

check("自己的 context 名字有定義", m._CI_SELF_CONTEXT == "arcana/sdlc-test")
src = open(os.path.join(D, "server.py"), encoding="utf-8").read()
seg = src[src.index("def _ci_checks_for"):src.index("def _gh_json")]
check("_ci_checks_for 兩個來源都會濾掉自己那一格", seg.count("_CI_SELF_CONTEXT") == 2)
check("兩個 GitHub 來源都讀(statuses 與 check-runs 各一)",
      "/status" in seg and "/check-runs" in seg)


# ── 5. 沒有 PR / 被關閉時不得誤擋 ────────────────────────────
print("\n[5] 邊界")

check("沒有 repo/branch → notApplicable", m._pr_ci("", "")["verdict"] == "notApplicable")
os.environ["PR_CI_GATE"] = "0"
check("PR_CI_GATE=0 → notApplicable(可關,但預設是開)",
      m._pr_ci("a/b", "feat/x")["verdict"] == "notApplicable")
os.environ.pop("PR_CI_GATE")


# ── 6. PM 收到的指示要說得出四種狀態的差別 ───────────────────
print("\n[6] PM 的裁決指示")

pm = m.prompt_pm_review({"prUrl": "https://github.com/x/y/pull/1", "_piid": "x"})
check("PM 被告知 prCi 不是選配", "prCi" in pm and "NOT optional" in pm)
check("PM 被告知 red → NOGO", "verdict=red" in pm and "NOGO" in pm)
check("PM 被告知 notRun → HOLD 而不是 NOGO", "notRun" in pm and "HOLD, NOT NOGO" in pm)
check("『缺席不是綠』有寫進去", "Absent is not green" in pm)
check("舊的『CI 只是輔助、不必理會』那句已經不在",
      "CI check-rollup / SonarQube is CONFIRMATORY but NOT required" not in pm)


print(f"\n通過 {ok} / 失敗 {fail}")
sys.exit(1 if fail else 0)
