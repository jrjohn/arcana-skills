#!/usr/bin/env python3
"""`_intake_form_section` 的自驗 —— 跑法:python3 intake_form_section_selftest.py

重點是 B 組。

A 組(值在頂層)一直都是綠的 —— 這個函式從來沒有在那個擺法上壞過。
壞的是 B 組:`do_execute`(驅動 SA / SD / uiux / IntakeReview)把每一個實例變數
塞在 `data` 底下,而這個函式讀的是頂層。2026-08-28 實測:使用者逐條答完、
`pm_answers` 1697 字確實寫進流程變數,而 IntakeReview 把同樣三題原封不動再問一次,
還明寫「此題在第 1 輪已問過且未獲回覆」。

從外面看流程一切正常 —— 它只是顯得「AI 問題很多」。
那正是人機迴圈會因為「很煩」被拿掉的死法,而它不是煩,是壞了。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, os, sys

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

ANS = "【Q1】上一輪不是被否決,是 implement 的 NameError 弄壞的。"
NONE_MSG = "尚無填答內容"

print("\n════ A. 值在頂層(do_implement 的擺法) ════")
top = m._intake_form_section({"pm_answers": ANS, "intakeRound": 2})
check("讀得到 pm_answers", ANS[:12] in top)
check("不再說「尚無填答內容」", NONE_MSG not in top)

print("\n════ B. 值在 data 底下(do_execute 的擺法)—— 這是壞掉的那一半 ════")
nested = m._intake_form_section({"data": {"pm_answers": ANS, "intakeRound": 2}})
check("讀得到 pm_answers", ANS[:12] in nested)
check("不再說「尚無填答內容」", NONE_MSG not in nested)
check("兩種擺法給出同樣的內容(答案在哪個容器裡是上游的實作細節)",
      (ANS[:12] in top) and (ANS[:12] in nested))

print("\n════ C. 真的沒填時仍要說「沒填」—— 不能為了讓 B 綠就永遠不說 ════")
# 沒有這一組,上面那些可能只是把「尚無填答」整句刪掉了。
empty = m._intake_form_section({})
check("兩邊都空 → 說得出尚無填答", NONE_MSG in empty)
empty2 = m._intake_form_section({"data": {}})
check("data 是空字典 → 一樣說得出", NONE_MSG in empty2)
empty3 = m._intake_form_section({"pm_answers": "", "data": {"pm_answers": None}})
check("空字串與 None 都不算填過", NONE_MSG in empty3)

print("\n════ D. intakeForm 這個容器本身也要兩邊都找 ════")
blob = m._intake_form_section({"data": {"intakeForm": '{"feature_request": "右側視窗要能拉寬"}'}})
check("data 裡的 intakeForm 解析得出來", "右側視窗要能拉寬" in blob)
check("解析得出時不說「尚無填答」", NONE_MSG not in blob)

print("\n════ E. 不是物件的 intakeForm 不得冒充填答 ════")
# `intakeForm` 綁在 userTask 的 out,而 out 是決議字串("approve")。
# 把它當填答塞進提示詞比沒有更糟:節點看到像填答的東西就不會說「尚無填答」,
# 而它實際上什麼都沒讀到。
d = m._intake_form_section({"data": {"intakeForm": "approve"}})
check("決議字串不被當成填答(仍說尚無填答)", NONE_MSG in d)

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
