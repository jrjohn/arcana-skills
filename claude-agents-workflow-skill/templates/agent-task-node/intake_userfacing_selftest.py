#!/usr/bin/env python3
"""IntakeReview 必須回答 userFacing —— 跑法:python3 intake_userfacing_selftest.py

2026-09-07 量到:47 個 sdlc-code-flow 實例、38 個開單時 uiFacing="true",而 uiux 節點跑過 **0 次**。
機制:BPMN 宣告 IntakeReview 有 uiFacing 這個輸出,worker 由 userFacing.value 推導 —— 而這個 schema
沒有 userFacing,所以永遠推不出來;Kogito 對「宣告了卻沒交回」的輸出寫 null,把開單時的 true 洗掉,
uiGate 就走預設邊跳過 uiux。一個宣告了、接好線、從來沒有執行過的關卡。
"""
import importlib.util, json, os, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

sch = m.SCHEMAS["intake"]
check("schema 有 userFacing", "userFacing" in sch["properties"])
check("userFacing 是 required(可選欄位會在最不確定時消失,而那正是唯一需要它的時候)", "userFacing" in sch["required"])
check("userFacing.value 是 boolean 且必填", sch["properties"]["userFacing"]["properties"]["value"]["type"] == "boolean"
      and "value" in sch["properties"]["userFacing"]["required"])
check("why 也在(要說得出依據)", "why" in sch["properties"]["userFacing"]["properties"])
# 對照組:舊 schema(沒有 userFacing)無法讓 worker 推導出 uiFacing —— 那正是這次的缺陷
old_props = {k: v for k, v in sch["properties"].items() if k != "userFacing"}
check("對照組:少了 userFacing 時,結果裡就沒有 worker 要讀的 /userFacing/value", "userFacing" not in old_props)

t = m.prompt_intake({"feature_request": "把治理告警移到最下面", "uiFacing": "true", "_piid": "i"})
check("prompt 明說 userFacing 必答", "userFacing" in t and "必答" in t)
check("prompt 帶入開單時的 uiFacing(讓它知道提交者初判什麼)", "uiFacing=true" in t)
check("prompt 說明不確定時傾向 true", "傾向 true" in t)
t2 = m.prompt_intake({"feature_request": "x", "_piid": "i"})
check("開單沒帶 uiFacing 時,prompt 說「未提供」而不是假裝有值", "(未提供)" in t2)
print("\n  通過 %d,失敗 %d" % (ok, fail)); sys.exit(1 if fail else 0)
