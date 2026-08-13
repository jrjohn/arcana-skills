#!/usr/bin/env python3
"""合併裁決 prompt 的自驗 —— 跑法:python3 merge_gate_selftest.py

守的是一句話:**缺席的檢查不是通過的檢查。**

2026-08-13 在 arcana-ai-bpm #207 觀察到:`gh pr checks` 只列出
`mvn package (BPMN codegen)`(綠),三個 Jenkins context 完全沒有出現 ——
不是紅、不是 pending,是沒有那一行。而 GitHub 的 mergeStateStatus 仍是 CLEAN,
因為它也只秤有回報的那些。

原本的 prompt 說「EVERY status check listed by `gh pr checks` is green」。
那句話對上面那個 PR **是成立的** —— 清單上唯一那一行確實是綠的。
規則沒有錯,它只是問錯了問題:它問「列出來的都綠嗎」,而該問的是
「該來的都來了嗎,而且都綠嗎」。

原本也已經有一條「空清單不算全綠」,但那擋不住這個情況 —— 部分清單不是空清單。

對照組是這支腳本的重點:一條讀不出「缺席」兩個字的政策,擋不住下一次的缺席。
所以每一項都要能對著「舊的寫法」變紅。

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


# ── 兩段受測文字 ────────────────────────────────────────────────
verdict = m.prompt_merge_verdict("https://github.com/x/y/pull/1") \
    if hasattr(m, "prompt_merge_verdict") else None
if verdict is None:
    # 名稱可能不同 —— 找出所有含 CHECK 2 的 prompt 產生器,取其輸出。
    verdict = ""
    for name in dir(m):
        if not name.startswith("prompt_"):
            continue
        fn = getattr(m, name)
        if not callable(fn):
            continue
        for args in (("https://github.com/x/y/pull/1",), ({},), ()):
            try:
                out = fn(*args)
            except Exception:
                continue
            if isinstance(out, str) and "CHECK 2" in out:
                verdict = out
            break
policy = ""
for name in dir(m):
    if not name.startswith("prompt_"):
        continue
    fn = getattr(m, name)
    if not callable(fn):
        continue
    for args in (({},), ("x",), ()):
        try:
            out = fn(*args)
        except Exception:
            continue
        if isinstance(out, str) and "Autonomous-merge policy" in out:
            policy = out
        break

print("\n【裁決 prompt(CHECK 2)】")
check("找得到 CHECK 2 那段", "CHECK 2" in verdict)
check("要求 PRESENT,不只是 green", "PRESENT" in verdict)
check("明說 ABSENT 不等於 green", "ABSENT IS NOT GREEN" in verdict)
check("點名預期的兩個 context", "ci/rust" in verdict and "ci/angular" in verdict)
check("缺席要判 PENDING 而不是 APPROVED",
      "Expected-but-missing" in verdict and "PENDING" in verdict)
check("禁止對沒看過的 context 給 APPROVED",
      "Never APPROVED on a context you never saw" in verdict)
check("說明預期集合會隨改動範圍變動(不能數行數)",
      "counting rows" in verdict and "kogito-bpmn" in verdict)

print("\n【自主合併政策】")
check("找得到政策那段", "Autonomous-merge policy" in policy)
check("保留原本的『空清單不算全綠』", "empty check list is not 'all green'" in policy)
check("新增『缺席不是通過』", "ABSENT IS NOT A CHECK THAT PASSED" in policy)
check("明說部分清單不是空清單", "PARTIAL list is not empty" in policy)
check("要求先列出預期的 context 再逐一確認",
      "name the contexts you EXPECT" in policy and "PRESENT" in policy)

# ── 對照組:舊寫法必須被判不足 ──────────────────────────────────
print("\n【對照組 —— 舊的寫法必須讀成『擋不住缺席』】")
OLD_VERDICT = (
    "CHECK 2 — `gh pr checks 1`: EVERY per-pipeline status context must be green. "
    "For arcana-ai-bpm that means BOTH `ci/rust` AND `ci/angular`. "
    "If any required check is still pending -> PENDING."
)
OLD_POLICY = (
    "Autonomous-merge policy: EVERY status check listed by `gh pr checks` is green/passing. "
    "For repos with no checks configured, an empty check list is not 'all green'."
)
check("舊裁決文字讀不出『缺席』的要求(所以擋不住 #207)",
      "PRESENT" not in OLD_VERDICT and "ABSENT IS NOT GREEN" not in OLD_VERDICT)
check("舊政策文字只擋空清單,擋不住部分清單",
      "empty check list" in OLD_POLICY and "PARTIAL list is not empty" not in OLD_POLICY)
check("舊文字點名了 context 卻沒要求它們必須出現 —— 這正是空真的來源",
      "ci/rust" in OLD_VERDICT and "PRESENT" not in OLD_VERDICT)



# ── ① 疊在尚未合併的工作之上,不得靜默 ──────────────────────────
print("\n【publish:PR 夾帶不屬於本輪的 commit 時要說出來】")
src = open(os.path.join(D, "server.py"), encoding="utf-8").read()

check("publish 會去數 base..HEAD 的 commit",
      'origin/%s..HEAD' in src and '"log", "--oneline"' in src)
check("本輪自己那一個不算進『夾帶』", "stacked[1:]" in src)
check("夾帶時 PR 內文要出現警告", "疊在尚未合併的工作之上" in src)
check("警告要列出是哪幾個 commit", 'inherited' in src and '"\\n".join' in src)
check("回傳值帶 stackedOn(PM 節點與流程變數看得到)", src.count('"stackedOn": inherited') == 3)
check("沒有夾帶時不加任何噪音(stack_note 預設空字串)", 'stack_note = ""' in src)

# 對照組:把判準拿掉,必須讀不出這件事
OLD_PUBLISH = (
    'body = ("AI-implemented feature `%s`.\\n\\n"\n'
    '        "This is a **GATED** PR ..."\n'
    '        "Local build gate: %s\\n\\nSummary: %s\\n")'
)
check("對照組:舊的 body 組法讀不出『夾帶』的概念",
      "疊在尚未合併的工作之上" not in OLD_PUBLISH and "stackedOn" not in OLD_PUBLISH)

print(f"\n{ok} 通過, {fail} 失敗")
sys.exit(1 if fail else 0)
