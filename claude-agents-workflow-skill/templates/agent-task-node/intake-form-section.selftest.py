#!/usr/bin/env python3
"""使用者填的東西,到得了讀它的那個節點嗎?

    python3 intake-form-section.selftest.py

## 為什麼

2026-08-10 實測的一條完整失敗鏈,四個環節各自看起來都正常:

  1. 表單有 11 個欄位,使用者填完送出 → 端點回 `advanced: true`
  2. 流程只宣告了 `feature_request` 一個對得上的變數 → 其餘九個被 Kogito 丟掉
  3. `intakeForm` 這個 userTask 只有一個 dataOutput(`out`)→ 退回再填時連
     `feature_request` 都寫不回去
  4. 補上逐欄位映射後欄位確實進了流程(`pm_answers` 1883 字),但
     `_intake_form_section` 只讀 `p["intakeForm"]` 這個 blob → **仍然讀不到**

結果:第二輪的 blocking 追問,問的正是使用者上一輪逐條回答過的事。
從外面看流程一切正常 —— 它只是顯得「AI 問題很多」。

這支釘住最後一哩:**不管上游用 blob 還是具名欄位,填答都必須出現在提示詞裡。**
中間那幾層由 BPMN 側的檢查守,這裡守的是讀的那一端。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_SERVER_START", "1")

try:
    from server import _intake_form_section
except Exception as e:  # pragma: no cover - import 失敗就是沒量到
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


ANSWER = "1. 註冊表已有 repo 欄位,不需要 schema 變更。"

# ── 具名欄位(BPMN 補上逐欄位 dataOutputAssociation 之後的實際形狀)────────────
out = _intake_form_section({
    "intakeRound": 1,
    "feature_request": "啟動時要能選專案",
    "pm_answers": ANSWER,
    "out_of_scope": "不做管理介面",
})
check("具名欄位:回覆必須出現在提示詞裡", ANSWER in out,
      "這是 2026-08-10 那次的實際形狀 —— 少了它,節點會重問已經回答過的事")
check("具名欄位:其他欄位也要在", "不做管理介面" in out and "啟動時要能選專案" in out)
check("具名欄位:標籤用人看得懂的字", "對上輪追問的回覆" in out, out[:120])

# ── 巢狀在 data 底下(do_intake 帶 data 之後的形狀)────────────────────────
# dispatcher 有兩種擺法:do_implement 放頂層,do_execute 放 `data` 底下。只讀頂層的程式碼
# 對 implement 有效、對設計節點靜默失效 —— 這個 repo 為此寫過 `_pv`,而這裡必須用它。
out = _intake_form_section({
    "intakeRound": 1,
    "data": {"pm_answers": ANSWER, "acceptance": "選 second-product 時 repo 必須是那一個"},
})
check("巢狀在 data 底下的回覆也要讀得到", ANSWER in out,
      "worker 改成帶 data 之後,只讀頂層會讓這件事再靜默失效一次")
check("巢狀在 data 底下的其他欄位也要在", "選 second-product 時 repo 必須是那一個" in out)

# ── blob(原本預期的形狀)必須維持可用 ──────────────────────────────────────
out = _intake_form_section({
    "intakeRound": 1,
    "intakeForm": json.dumps({"pm_answers": ANSWER}, ensure_ascii=False),
})
check("blob 形狀仍然可讀", ANSWER in out, "改動不得把原本能用的那條路弄壞")

# ── 兩者並存時,blob 優先,具名欄位補洞 ────────────────────────────────────
out = _intake_form_section({
    "intakeRound": 1,
    "intakeForm": json.dumps({"pm_answers": "來自 blob"}, ensure_ascii=False),
    "pm_answers": "來自具名欄位",
    "placement": "只有具名欄位有這個",
})
check("並存時 blob 不被具名欄位覆蓋", "來自 blob" in out and "來自具名欄位" not in out)
check("並存時 blob 沒有的欄位由具名欄位補上", "只有具名欄位有這個" in out)

# ── out 是決議字串,不是表單 —— 不得炸掉,也不得被讀成有填答 ────────────────
out = _intake_form_section({"intakeRound": 1, "intakeForm": "approve"})
check("intakeForm 是決議字串時不炸、且視為未填",
      "尚無填答內容" in out,
      "BPMN 的 intakeForm 綁的正是 out;把 'approve' 當表單會讓 items() 拋例外")

# ── 真的什麼都沒有 → 說「沒有」,不得假裝有 ────────────────────────────────
out = _intake_form_section({"intakeRound": 0})
check("完全沒有填答時要明說", "尚無填答內容" in out)

print()
if bad == 0:
    print("  pass —— 兩種上游形狀的填答都到得了節點,而沒有填答不會被讀成有")
else:
    print("  gap —— %d 項不符:使用者填的東西到不了讀它的地方" % bad)
sys.exit(1 if bad else 0)
