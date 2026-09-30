#!/usr/bin/env python3
"""task-boundary 拿得到 SD 宣告的檔案清單嗎 —— 跑法:python3 sdd_files_selftest.py

2026-09-30 查到:run-test.sh 等著 SDD_FILES_B64,agent 從沒給 → task-boundary 每一輪 notRun 並擋。

  A 組:_sdd_files 讀各種形狀(物件 / JSON 字串 / data 底下 / 項目是字串或 {path})
  B 組:test_flow 真的把它放進 runner 的環境變數(不是寫好卻沒人呼叫)
  C 組:對 Data Index 最近一輪真的 sdd 讀得出清單(連不到明說沒跑,不算通過)

注意:arcana-skills 沒有 CI,這支不會自動跑。
"""
import importlib.util, inspect, json, os, sys, urllib.request

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)

print("A 組 —— 讀清單")
F = ["dashboard/src/a.ts", "dashboard/e2e/aaf/a.spec.ts"]
check("物件", m._sdd_files({"sdd": {"files": F}}) == F)
check("JSON 字串", m._sdd_files({"sdd": json.dumps({"files": F})}) == F)
check("放在 data 底下", m._sdd_files({"data": {"sdd": {"files": F}}}) == F)
check("項目是 {path}", m._sdd_files({"sdd": {"files": [{"path": F[0]}, {"file": F[1]}, "", None]}}) == F)
check("沒有 sdd → []", m._sdd_files({}) == [])
check("壞掉的 JSON → []", m._sdd_files({"sdd": "{not json"}) == [])

print("B 組 —— 真的接進 runner")
src = inspect.getsource(m.test_flow)
check("test_flow 呼叫 _sdd_files 並設 SDD_FILES_B64",
      "_sdd_files(payload)" in src and '"SDD_FILES_B64="' in src)

print("C 組 —— 對 Data Index 最近一輪真的 sdd")
try:
    q = {"query": '{ ProcessInstances(where:{processId:{equal:"sdlc-code-flow"}}, orderBy:{start:DESC}, pagination:{limit:1}){ id variables } }'}
    req = urllib.request.Request("http://localhost:8180/graphql", data=json.dumps(q).encode(),
                                 headers={"Content-Type": "application/json"})
    pi = json.load(urllib.request.urlopen(req, timeout=15))["data"]["ProcessInstances"][0]
    v = json.loads(pi["variables"]) if isinstance(pi["variables"], str) else pi["variables"]
    got = m._sdd_files({"data": v})
    print("     %s:%d 個檔案,例:%s" % (pi["id"][:8], len(got), got[:2]))
    check("最近一輪讀得出非空的清單", len(got) > 0)
except Exception as e:
    print("  ? 連不到 Data Index(%s)—— C 組沒跑,不算通過" % e); fail += 1

print()
print("  %d 過 / %d 失敗" % (ok, fail))
sys.exit(1 if fail else 0)
