#!/usr/bin/env python3
"""盲審的價值全在「輸入被切掉」—— 所以要驗的正是它拿不到那些東西。

    python3 pm-blind.selftest.py

## 為什麼有這一刀

PM 節點今天拿到的第一樣東西是 `pr` 變數 —— 4000 字,由 **implement 自己寫的摘要**。
然後才是 SRS / SDD / uiuxSpec / siblings / 前幾輪的對話。

而 AI 實作者的失敗模式恰好是:**產出一份很有說服力的摘要,而摘要與 diff 不符。**
2026-08-11 實測:implement 的摘要寫「Implemented … end-to-end (Rust backend + Angular
frontend), per SRS/SDD, with unit tests」,而 Test 節點跑出來是 **4 個測試案例 0 個通過**。

借自 cc-sdd 的 per-task 獨立 reviewer。這支釘住那把刀真的有切下去。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_SERVER_START", "1")

try:
    from server import prompt_pm_blind, prompt_pm_review, SCHEMAS
except Exception as e:  # pragma: no cover
    print("  notRun —— 匯入 server.py 失敗:%s" % e)
    sys.exit(2)

bad = 0


def check(label, ok, detail=""):
    global bad
    print("  %s %s" % ("✓" if ok else "✗", label))
    if not ok:
        bad += 1
        if detail:
            print("      %s" % detail)


POISON = "IMPLEMENTER-SUMMARY-POISON-TOKEN"
PAYLOAD = {
    "prUrl": "https://github.com/o/r/pull/1",
    "acceptance": "AC1 啟動頁出現專案選單\nAC2 送出時帶 projectId",
    # 以下每一樣都是「不該進盲審」的東西,各埋一個可辨識的字串。
    "pr": '{"prUrl":"https://github.com/o/r/pull/1","summary":"%s 全部做完了"}' % POISON,
    "srs": "SRS-POISON 這份規格洋洋灑灑地說明了設計理念",
    "sdd": "SDD-POISON 架構圖與分層說明",
    "uiuxSpec": "UIUX-POISON 視覺規範",
    "siblings": "SIBLINGS-POISON 其他 feature 的判定",
    "testReport": '{"allPass":false,"POISON":"TESTREPORT-POISON"}',
    "job": "subject",
}

blind = prompt_pm_blind(PAYLOAD)

# ── 這一刀真的切下去了嗎 ──────────────────────────────────────────────────
for token, what in ((POISON, "實作者的摘要"), ("SRS-POISON", "SRS 散文"),
                    ("SDD-POISON", "SDD"), ("UIUX-POISON", "UI/UX 規範"),
                    ("SIBLINGS-POISON", "sibling 判定"),
                    ("TESTREPORT-POISON", "測試報告")):
    check("盲審拿不到%s" % what, token not in blind,
          "「%s」出現在盲審提示詞裡 —— 那把刀沒切下去" % what)

# 它該拿到的兩樣
check("盲審拿得到可驗收條目", "AC1 啟動頁出現專案選單" in blind)
check("盲審拿得到 PR(要自己 gh pr diff)", "gh pr diff" in blind and "pull/1" in blind)

# ── file:line 是硬約束,不是建議 ─────────────────────────────────────────
check("要求 file:line 當證據", "file:line" in blind)
check("指不出位置就必須 done:false", "done: false" in blind or "done: false" in blind)
check("答不了的放 notAssessable 而不是猜", "notAssessable" in blind and "不要猜" in blind)

sch = SCHEMAS.get("pm-blind") or {}
props = (sch.get("properties") or {}).get("checks", {}).get("items", {})
req = props.get("required") or []
check("schema 逼出證據(evidence 必填)", "evidence" in req,
      "evidence 不是必填 —— 一句「有做到」沒有位置,與「我覺得應該有做」分不出來")

# ── 第二問要看得到盲審的結果,而且沒跑成時不得讀成通過 ──────────────────
full_with = prompt_pm_review({**PAYLOAD, "_blind": {"checks": [
    {"ac": "AC1", "done": False, "evidence": "-", "why": "diff 裡找不到選單"}]}})
check("七維判定看得到盲審結果", "diff 裡找不到選單" in full_with)
check("分歧要被點名", "不一致" in full_with or "落差" in full_with)

full_without = prompt_pm_review({**PAYLOAD, "_blindNotRun": "呼叫失敗"})
check("盲審沒跑成時,明說不得讀成「都做到了」",
      "不得把它讀成" in full_without,
      "沒有那句話,缺席會被讀成通過 —— 這正是這一整套要防的病")

print()
print("  pass —— 那把刀切下去了:盲審看不到敘述,而第二問看得到盲審"
      if bad == 0 else "  gap —— %d 項不符:盲審不盲,或分歧沒有被看見" % bad)
sys.exit(1 if bad else 0)
