#!/usr/bin/env python3
"""S8 信心門檻 / 反思模式的自驗 —— 跑法:python3 confidence_selftest.py

四個對照組是這支腳本的重點,不是附帶:政策驗證若不能對著壞政策變紅,
它就只是一段沒有人會發現失效的程式碼。特別是「self_report 不得 escalate」——
那條規則是整個設計的支點,所以它必須被證明會擋。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, json, os, sys, types

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")

spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except SystemExit as e:
    print("  import 觸發 SystemExit:", e); raise
print("  server.py import 成功(_check_confidence_policies 在 import 時已跑過)")

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)

print("\n════ A. 政策驗證(含對照組) ════")
# 正向:現有政策通過
m._check_confidence_policies()
check("現有政策通過驗證", True)

# 對照組 1:self_report + escalate 必須被拒
saved = dict(m.CONFIDENCE_POLICY)
m.CONFIDENCE_POLICY["bad"] = {"min": 0.7, "source": "self_report",
                              "onBelow": "escalate", "maxRounds": 1}
try:
    m._check_confidence_policies(); rejected = False
except AssertionError as e:
    rejected = "self_report" in str(e)
check("對照組:self_report+escalate 被拒絕(這條規則若不擋,整個設計就是裝飾)", rejected)
m.CONFIDENCE_POLICY.clear(); m.CONFIDENCE_POLICY.update(saved)

# 對照組 2:min 超出範圍
m.CONFIDENCE_POLICY["bad2"] = {"min": 1.7, "source": "judge", "onBelow": "escalate"}
try:
    m._check_confidence_policies(); rejected2 = False
except AssertionError:
    rejected2 = True
check("對照組:min=1.7 被拒絕", rejected2)
m.CONFIDENCE_POLICY.clear(); m.CONFIDENCE_POLICY.update(saved)

# 對照組 3:onBelow 打錯字
m.CONFIDENCE_POLICY["bad3"] = {"min": 0.7, "source": "judge", "onBelow": "reflec"}
try:
    m._check_confidence_policies(); rejected3 = False
except AssertionError:
    rejected3 = True
check("對照組:onBelow 打錯字被拒絕(否則它會靜默地永遠不觸發)", rejected3)
m.CONFIDENCE_POLICY.clear(); m.CONFIDENCE_POLICY.update(saved)

print("\n════ B. schema 注入 ════")
base = json.dumps({"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]})
got = json.loads(m._schema_with_confidence(base))
check("confidence 被加為必填", "confidence" in got["required"])
check("confidenceRationale 被加為必填", "confidenceRationale" in got["required"])
check("原有欄位保留", "x" in got["required"] and "x" in got["properties"])
check("非 object schema 原樣返回",
      m._schema_with_confidence('{"type":"string"}') == '{"type":"string"}')

print("\n════ C. 三態判定 ════")
pol = {"min": 0.7}
check("0.9 → pass",    m._confidence_verdict(0.9, pol) == "pass")
check("0.5 → below",   m._confidence_verdict(0.5, pol) == "below")
check("None → missing(與 below 分開,處置不同)", m._confidence_verdict(None, pol) == "missing")
check("無政策 → notApplicable(不是 pass)", m._confidence_verdict(0.9, None) == "notApplicable")

print("\n════ D. 反思迴圈(替換掉真正的 Claude 呼叫) ════")
calls = []
def fake_once(prompt, schema, payload, wall, cwd=None):
    calls.append(prompt)
    # 第一次低信心,第二次才提高 —— 用來看迴圈有沒有真的再跑一輪
    return {"result": "r%d" % len(calls),
            "confidence": 0.4 if len(calls) == 1 else 0.85,
            "confidenceRationale": "不確定 X"}
m._invoke_claude_once = fake_once

out = m._invoke_claude("原始提示", base, {"_node": "intakeReview"}, 60)
check("低信心觸發了第二輪", len(calls) == 2)
check("第二輪的提示含反思段落", "反思重做" in calls[1])
check("反思提示帶入模型自己說的不確定處", "不確定 X" in calls[1])
check("最終 verdict=pass", out["_confidence"]["verdict"] == "pass")
check("rounds=1", out["_confidence"]["rounds"] == 1)
check("self_report 被標為 second-class", out["_confidence"]["tier"] == "second-class")
check("self_report 不得產生 escalate", "disposition" not in out)

print("\n════ E. maxRounds 是上限,不是建議 ════")
calls.clear()
def always_low(prompt, schema, payload, wall, cwd=None):
    calls.append(prompt)
    return {"confidence": 0.1, "confidenceRationale": "就是不確定"}
m._invoke_claude_once = always_low
out = m._invoke_claude("p", base, {"_node": "intakeReview"}, 60)
check("永遠低信心時只重做 maxRounds(1)次,共 2 次呼叫", len(calls) == 2)
check("仍回報 below,不假裝過關", out["_confidence"]["verdict"] == "below")

print("\n════ F. judge 模式才可以擋 ════")
m.CONFIDENCE_POLICY["judgeNode"] = {"min": 0.7, "source": "judge",
                                    "onBelow": "escalate", "maxRounds": 0}
m._check_confidence_policies()
calls.clear()
out = m._invoke_claude("p", base, {"_node": "judgeNode"}, 60)
check("judge + 低信心 → disposition=escalate", out.get("disposition") == "escalate")
check("judge 標為 gating(非次等)", out["_confidence"]["tier"] == "gating")
check("maxRounds=0 時不重做", len(calls) == 1)

print("\n════ G. 沒有政策的節點 ════")
calls.clear()
out = m._invoke_claude("p", base, {"_node": "someUngatedNode"}, 60)
check("回報 notApplicable 而不是 pass", out["_confidence"]["verdict"] == "notApplicable")
check("沒有政策時不注入、不重做", len(calls) == 1)

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
