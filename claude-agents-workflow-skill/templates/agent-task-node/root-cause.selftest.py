#!/usr/bin/env python3
"""換角色的價值全在「輸入被切掉」—— 所以要驗的正是它拿不到那些東西。

    python3 root-cause.selftest.py

## 為什麼有這一格

同一個實作者重試兩次,第二次帶著第一次的推理一起進來。如果第一次錯在**理解錯了**,
那份推理正是要被丟掉的東西 —— 而重試把它保留了下來。

2026-08-11 實測的 HOLD 判定就是這個形狀:PM 說「連續兩輪產出零執行證據」、
「不要重做程式碼」。它診斷出的是跑法錯了不是程式錯了,而流程當時能做的只有升級給人。

借自 cc-sdd 的 Debugger role(實作者 BLOCKED 或審查連退兩輪時觸發,在乾淨脈絡裡查根因、
產出修復計畫、交給新的實作者)。這支釘住那把刀真的有切下去,以及查不出來時不會硬掰。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_SERVER_START", "1")

try:
    from server import prompt_root_cause, SCHEMAS, PROMPTS
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


# 每一樣「不該進這一格」的東西各埋一個可辨識字串。worker 送過來的 payload 會把整包
# 流程變數 merge 進去,所以它們**確實在 payload 裡** —— 切在提示詞這一層,與盲審同理。
PAYLOAD = {
    "prUrl": "https://github.com/o/r/pull/9",
    "testReport": '{"allPass":false,"blockingReasons":["TESTREPORT-KEEP 4 個案例 0 通過"]}',
    "testAttempts": 2,
    "pr": '{"prUrl":"https://github.com/o/r/pull/9","summary":"SUMMARY-POISON 全部照 SRS 做完了"}',
    "pmReview": '{"verdict":"NOGO","feedback":"PMREVIEW-POISON 上一輪的判定"}',
    "srs": "SRS-POISON 這份規格洋洋灑灑地說明了設計理念",
    "sdd": "SDD-POISON 架構圖與分層說明",
    "uiuxSpec": "UIUX-POISON 視覺規範",
    "rework_feedback": "REWORK-POISON 上一輪要你修的東西",
}

pr = prompt_root_cause(PAYLOAD)

# ── 這一刀真的切下去了嗎 ──────────────────────────────────────────────────
for token, what in (("SUMMARY-POISON", "實作者的摘要"),
                    ("PMREVIEW-POISON", "上一輪的 PM 判定"),
                    ("SRS-POISON", "SRS 散文"), ("SDD-POISON", "SDD"),
                    ("UIUX-POISON", "UI/UX 規範"),
                    ("REWORK-POISON", "上一輪的返工說明")):
    check("查根因拿不到%s" % what, token not in pr,
          "「%s」出現在提示詞裡 —— 那把刀沒切下去,這一格就只是第三次重試" % what)

# 它該拿到的:機器產出的判定 + PR(自己去 diff)
check("拿得到測試報告(機器產出的判定)", "TESTREPORT-KEEP" in pr)
check("拿得到 PR,並被要求自己 gh pr diff", "gh pr diff" in pr and "pull/9" in pr)
check("被告知已經失敗了幾輪", "2 輪" in pr)

# ── 不要預設答案是 code ──────────────────────────────────────────────────
check("先問「錯在哪一層」而不是直接問怎麼修", "layer" in pr)
check("明講不要預設是 code", "不要預設是 code" in pr,
      "少了這句,答案會落在實作者已經試過兩次的那一層")
check("要求列出排除掉的方向", "notTheProblem" in pr)

# ── 查不出來要說查不出來 ────────────────────────────────────────────────
check("查不出來時要求填 usable:false", "查不出來就填" in pr)
check("明說猜一個聽起來合理的原因才是失敗", "猜一個聽起來合理的原因" in pr,
      "沒有這句,模型會傾向交出一個好看的答案 —— 而流程會照著它再燒一整輪")

# ── schema 與登記表 ─────────────────────────────────────────────────────
sch = SCHEMAS.get("root-cause") or {}
req = sch.get("required") or []
check("usable 是節點自己宣告的必填欄位", "usable" in req,
      "由閘去推論「這份計畫看起來夠不夠具體」會讓兩個讀者對同一份產出各說各話")
check("evidence 必填", "evidence" in req,
      "指不出位置的推測,與「我覺得」分不出來")
check("layer 是列舉而不是自由文字",
      "enum" in (sch.get("properties") or {}).get("layer", {}))
check("登記在 PROMPTS 裡(server.py 自己的守衛會擋)", "root-cause" in PROMPTS)

# ── 對照組:把摘要放回去,第一項必須立刻紅 ──────────────────────────────
# 沒有這一格,上面那六個 ✓ 只是在描述現況,不是在守什麼。
leaked = prompt_root_cause({**PAYLOAD, "testReport": PAYLOAD["testReport"] + PAYLOAD["pr"]})
check("對照組:摘要混進報告時偵測得到", "SUMMARY-POISON" in leaked,
      "連刻意漏進去都偵測不到,那前面幾項就不是在驗切線")

print()
print("  pass —— 那把刀切下去了:查根因看不到敘述,只看得到證據,而查不出來時不硬掰"
      if bad == 0 else "  gap —— %d 項不符" % bad)
sys.exit(1 if bad else 0)
