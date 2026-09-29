#!/usr/bin/env python3
"""流程被中止後,implement 不可以再推 commit / 開 PR —— 跑法:python3 orphan_guard_selftest.py

中止流程實例不會停掉 agent 手上的工作;implement 做完照樣推、照樣開 PR,留下沒有流程在管的遺孤。
  09-24 4a2ace83 中止後冒出 #451;09-25 d6fdedfd 是手動找 pid 停掉才沒冒。

  A 組:_instance_state 讀狀態(注入假的查詢)
  B 組:_refuse_if_instance_gone 的判準 —— **只有確定中止/結束才擋,查不到照做**
  C 組:檢查真的排在 push 與開 PR 之前
  D 組:修之前(2665bee)的 implement_flow → C 組判紅
  E 組:用真的 Data Index 查 d6fdedfd(09-25 真的被中止的那一輪)→ 必須擋
        (連不到 Data Index 時明說沒跑,不算通過)

注意:arcana-skills 沒有 CI,這支不會自動跑。
"""
import importlib.util, inspect, os, subprocess, sys

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

def q_state(st):
    return lambda q: {"data": {"ProcessInstances": [{"state": st}]}}
def q_empty(q): return {"data": {"ProcessInstances": []}}
def q_boom(q): raise OSError("connection refused")

print("A 組 —— 讀狀態")
check("ABORTED 讀得到", m._instance_state("x", q_state("ABORTED")) == "ABORTED")
check("ACTIVE 讀得到", m._instance_state("x", q_state("ACTIVE")) == "ACTIVE")
check("查無此實例 → None", m._instance_state("x", q_empty) is None)
check("連線失敗 → None(不是例外)", m._instance_state("x", q_boom) is None)
check("沒有 piid → None,而且不去查", m._instance_state("", q_boom) is None)

print("B 組 —— 判準")
P = {"_piid": "d6fdedfd-5702-4ab0-b58b-76ca6d872410"}
r = m._refuse_if_instance_gone(P, "pushing b", q_state("ABORTED"))
check("已中止 → 擋,並說出狀態", isinstance(r, dict) and r.get("instanceGone") == "ABORTED" and "pushing b" in r["error"])
check("已結束(COMPLETED)→ 擋", (m._refuse_if_instance_gone(P, "x", q_state("COMPLETED")) or {}).get("instanceGone") == "COMPLETED")
check("還在跑 → 照做", m._refuse_if_instance_gone(P, "x", q_state("ACTIVE")) is None)
check("ERROR(實例還在,只是出錯)→ 照做", m._refuse_if_instance_gone(P, "x", q_state("ERROR")) is None)
check("**查不到 → 照做**(不能因為自己讀不到就擋掉正常工作)", m._refuse_if_instance_gone(P, "x", q_boom) is None)
check("沒有 _piid(直接呼叫,不屬於流程)→ 照做", m._refuse_if_instance_gone({}, "x", q_boom) is None)

def guarded(src):
    g = src.find("_refuse_if_instance_gone(payload")
    g2 = src.find("_refuse_if_instance_gone(payload", g + 1)
    push = src.find('_git("push"')
    pr = src.find('"gh", "pr", "create"')
    return g != -1 and g2 != -1 and push != -1 and pr != -1 and g < push and g2 < pr

print("C 組 —— 檢查排在留下痕跡的動作之前")
check("implement_flow:push 前、開 PR 前各有一道", guarded(inspect.getsource(m.implement_flow)))

print("D 組 —— 修之前必須判紅")
try:
    old = subprocess.run(["git", "-C", D, "show", "2665bee:claude-agents-workflow-skill/templates/agent-task-node/server.py"],
                         capture_output=True, text=True, timeout=30).stdout
    a = old.find("def implement_flow(payload):"); b = old.find("\ndef ", a + 10)
    if a < 0:
        print("  ? 取不到修之前的版本 —— D 組沒跑,不是通過"); fail += 1
    else:
        check("修之前(2665bee)的 implement_flow 沒有這道檢查 → 判紅", not guarded(old[a:b]))
except Exception as e:
    print("  ? D 組沒跑:%s" % e); fail += 1

print("E 組 —— 真的 Data Index")
for url in (os.environ.get("DATA_INDEX_URL"), "http://localhost:8180", "http://aaf-data-index:8080"):
    if not url:
        continue
    os.environ["DATA_INDEX_URL"] = url
    st = m._instance_state("d6fdedfd-5702-4ab0-b58b-76ca6d872410")
    if st is not None:
        check("%s 上 d6fdedfd 是 %s → 擋" % (url, st),
              (m._refuse_if_instance_gone(P, "opening a PR") or {}).get("instanceGone") == "ABORTED")
        break
else:
    print("  ? 連不到 Data Index —— E 組沒跑,不是通過")

print("\n  %d 過 / %d 失敗" % (ok, fail))
sys.exit(1 if fail else 0)
