#!/usr/bin/env python3
"""task-boundary 的界線來自 SDD 的 `files`。這一支釘住那條線真的取得到。

    python3 sdd-files.selftest.py

## 為什麼要有這一支

`task-boundary.mjs` 的判定是集合比較,那部分有它自己的對照組。但它比的是
**傳進去的那份清單**,而清單是在這裡從 `sdd` 抽出來的。抽不到就是空清單,
空清單在 runner 端會變成 `notRun` —— 這個閘於是永遠擋著,而看起來像是
「SD 沒有宣告範圍」,不像是「抽取壞了」。兩者分不出來,正是這條管線反覆出的病。

所以真正要釘的是:**真實形狀的 SDD 抽得到,而抽不到的時候回空而不是回半份。**
回半份最糟 —— 沒被抽到的檔案會被判成「超界」,那是假紅。

`SDD_REAL_SHAPE` 取自 2026-07-30 實例 e7dfd560 真正產出的那份 SDD 的形狀與
它的三個路徑(全文在 aaf repo 的 `sdd-that-declares-inputs-sufficient.json`)。
這是一份縮減,不是全文 —— 它證明的是形狀對得上,不是所有欄位都試過。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_SERVER_START", "1")

try:
    from server import _sdd_declared_files
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


REAL_FILES = ["dashboard/e2e/uiux-review.mjs",
              "dashboard/e2e/uiux-redirect-classify.mjs",
              "dashboard/e2e/uiux-overlap-classify.mjs"]
SDD_REAL_SHAPE = {
    "approach": "## 進場自檢\n\n`srs` 完整(18 條 AC、20 條 REQ)。**輸入充足,不需 INPUT_INCOMPLETE。**",
    "files": REAL_FILES,
    "steps": ["S1 [C1] 新增 dashboard/e2e/uiux-redirect-classify.mjs:匯出純函式 classifyRedirect"],
}

# ── 真實形狀:字串、巢狀於 data、以及已經是 dict 的三種到法 ──────────────────
check("SDD 是 JSON 字串 → 抽得到那三個路徑",
      _sdd_declared_files({"sdd": json.dumps(SDD_REAL_SHAPE, ensure_ascii=False)}) == REAL_FILES)
check("SDD 已是 dict → 抽得到",
      _sdd_declared_files({"sdd": SDD_REAL_SHAPE}) == REAL_FILES)
# do_execute 把每個流程變數塞在 `data` 底下,do_implement 放頂層 —— 只讀一邊等於
# 對另一邊靜默失效,而那正是 `_pv` 存在的理由。
check("SDD 巢狀在 data 底下 → 也抽得到(_pv 的那個坑)",
      _sdd_declared_files({"data": {"sdd": json.dumps(SDD_REAL_SHAPE, ensure_ascii=False)}}) == REAL_FILES)
check("SDD 被 ``` 包起來 → 剝掉圍籬後仍抽得到",
      _sdd_declared_files({"sdd": "```json\n%s\n```"
                                  % json.dumps(SDD_REAL_SHAPE, ensure_ascii=False)}) == REAL_FILES)

# ── 抽不到的時候要回空(→ notRun),不得回半份(→ 假紅) ─────────────────────
check("沒有 sdd → 空清單", _sdd_declared_files({}) == [])
check("sdd 是散文(不是 JSON)→ 空清單,不從散文裡撈路徑",
      _sdd_declared_files({"sdd": "## 設計\n改 dashboard/e2e/uiux-review.mjs 與其他幾個檔"}) == [],
      "撈出半份清單會讓沒撈到的檔案被判成超界 —— 假紅")
check("sdd 有結構但沒有 files → 空清單",
      _sdd_declared_files({"sdd": json.dumps({"approach": "x", "steps": []})}) == [])
check("files 不是陣列 → 空清單",
      _sdd_declared_files({"sdd": json.dumps({"files": "a.ts"})}) == [])
check("files 裡的空白項被丟掉,其餘保留",
      _sdd_declared_files({"sdd": json.dumps({"files": ["  a.ts ", "", "   ", "b.ts"]})}) == ["a.ts", "b.ts"])

# ── 對照組:這幾項必須是「會紅的輸入」,否則上面那些只是在描述現況 ──────────
# 若哪天有人改成「從 steps 的散文裡也撈路徑」,第 6 項會立刻紅 —— 那是刻意的。
check("對照組:形狀對但 files 為空,不得被當成「有宣告」",
      _sdd_declared_files({"sdd": json.dumps({**SDD_REAL_SHAPE, "files": []})}) == [],
      "空的 files 若回非空,界線就是編出來的")

print()
print("  pass —— 真實形狀抽得到,而抽不到時回空(→ notRun),不回半份(→ 假紅)"
      if bad == 0 else "  gap —— %d 項不符" % bad)
sys.exit(1 if bad else 0)
