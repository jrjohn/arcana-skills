#!/usr/bin/env python3
"""(f) GO 自動 un-draft、(g) rework 沿用上一輪測試案例 —— 跑法:python3 go_undraft_reuse_selftest.py"""
import importlib.util, json, os, sys, subprocess, tempfile
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

print("\n════ (g) 測試案例:生成 → 存;失敗 → 沿用;都沒有 → 回歸 ════")
tmp = tempfile.mkdtemp(); os.environ["TESTCASES_CACHE_DIR"] = tmp
path = m._testcases_cache_path({"_piid": "6775540d-b8f8"})
check("快取路徑以實例 id 為鍵、在 TESTCASES_CACHE_DIR 下", path.startswith(tmp) and "6775540d-b8f8" in path)
check("沒有實例 id → 沒有快取路徑(不會跨實例沿用)", m._testcases_cache_path({}) == "")
MOD = "export const testcases = [ { id: 'FEAT-01', name: 'x', run: async () => {} } ];"
g, src = m._resolve_testcases(MOD, path)
check("第一輪生成成功 → generated,且存了檔", src == "generated" and g == MOD and open(path).read() == MOD)
g, src = m._resolve_testcases(None, path)
check("第二輪生成失敗 → reused,內容是上一輪的", src == "reused" and g == MOD)
g, src = m._resolve_testcases(None, m._testcases_cache_path({"_piid": "nothing-saved"}))
check("沒有上一輪 → regression(None)", src == "regression" and g is None)
open(path, "w").write("garbage without a module")
g, src = m._resolve_testcases(None, path)
check("快取不是模組 → 不沿用,退回 regression", src == "regression" and g is None)
g, src = m._resolve_testcases(None, "")
check("沒有快取路徑 → regression", src == "regression")
src_code = open(os.path.join(D, "server.py"), encoding="utf-8").read()
check("test_flow 把 testcasesSource 寫進 testReport", 'rep["testcasesSource"] = tc_source' in src_code)

print("\n════ (f) pr-ready:只在 OPEN 且草稿時 gh pr ready ════")
CALLS = []
def runner(view_json, ready_rc=0, view_rc=0):
    def patched(cmd, *a, **k):
        c = cmd if isinstance(cmd, list) else [str(cmd)]
        class R: returncode = 0; stdout = ""; stderr = ""
        r = R()
        if c[:3] == ["gh", "pr", "view"]:
            r.returncode = view_rc; r.stdout = json.dumps(view_json); r.stderr = "boom" if view_rc else ""
        elif c[:3] == ["gh", "pr", "ready"]:
            CALLS.append(c); r.returncode = ready_rc; r.stderr = "nope" if ready_rc else ""
        return r
    return patched
def run(payload, **kw):
    CALLS.clear(); orig = subprocess.run; subprocess.run = runner(**kw)
    try: return m.pr_ready(payload)
    finally: subprocess.run = orig
r = run({"prUrl": "https://github.com/x/y/pull/7"}, view_json={"state": "OPEN", "isDraft": True})
check("草稿 → 呼叫 gh pr ready,ready=true wasDraft=true", r["ready"] and r["wasDraft"] and len(CALLS) == 1)
r = run({"prUrl": "https://github.com/x/y/pull/7"}, view_json={"state": "OPEN", "isDraft": False})
check("不是草稿 → 不呼叫,ready=true wasDraft=false", r["ready"] and r["wasDraft"] is False and not CALLS)
r = run({"prUrl": "https://github.com/x/y/pull/7"}, view_json={"state": "MERGED", "isDraft": False})
check("不是 OPEN → ready=false 且說原因", not r["ready"] and "not open" in r["reason"] and not CALLS)
r = run({"prUrl": "https://github.com/x/y/pull/7"}, view_json={"state": "OPEN", "isDraft": True}, ready_rc=1)
check("gh pr ready 失敗 → ready=false 且帶錯誤", not r["ready"] and "failed" in r["reason"])
r = run({"pr": json.dumps({"ran": False, "response": json.dumps({"prUrl": "https://github.com/x/y/pull/8"})})}, view_json={"state": "OPEN", "isDraft": False})
check("prUrl 藏在 pr 變數深處也掃得到", r.get("pr") == "https://github.com/x/y/pull/8")
r = run({}, view_json={})
check("沒有 PR → ready=false", not r["ready"] and "no PR" in r["reason"])
print("\n  通過 %d,失敗 %d" % (ok, fail)); sys.exit(1 if fail else 0)
