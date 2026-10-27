#!/usr/bin/env python3
"""runner 逾時要把容器收掉(2026-10-22)—— 跑法:python3 runner_timeout_cleanup_selftest.py

事件:`subprocess.run(["docker","run","--rm",...], timeout=2400)` 逾時只殺掉 docker CLI,**容器照跑**。
10-21 晚 Mac swap 幾乎滿時,一個逾時留下的孤兒 runner 又跑了 40 分鐘,跟進化圈的正式測試搶記憶體,
下一個測試也逾時 —— 越滾越糟。

這支真的走一遍 test_flow 與 uiux_audit_flow(外部依賴換成假的),檢查:
  1. runner 容器有固定的 --name(含實例編號,查得到是誰的)
  2. 逾時後用**同一個名字** `docker rm -f` 收掉
  3. 正常跑完不多此一舉(--rm 本來就會收)
  4. 同一個實例測兩次,名字不撞(上次沒收乾淨的孤兒不會讓這次起不來)
SERVER_PY 可指向別份 server.py;指向修之前那份應該紅(對照組)。不打網路、不需要 docker。
"""
import importlib.util, json, os, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
SRV = os.environ.get("SERVER_PY", os.path.join(D, "server.py"))
spec = importlib.util.spec_from_file_location("atn_server", SRV); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

for f, v in {"_start_pr_backend": lambda repo, branch, base, piid, net: (None, lambda: None),
             "_scenario_autofill": lambda p: {"ran": False},
             "_load_profile": lambda p: {"app": {}, "run": {}, "auth": {}, "nav": {}, "flow": {}},
             "_gen_testcases": lambda p: "", "_resolve_testcases": lambda gen, path: ("", "none"),
             "_testcases_cache_path": lambda p: "/nonexistent", "_sdd_files": lambda p: [],
             "_gen_journeys": lambda p: "", "_gen_api_checks": lambda p: "",
             "_arch_qube": lambda p: {"applicable": False}, "_sonar": lambda p: {"applicable": False},
             "_fold_ci": lambda rep, ci: None, "_pr_ci": lambda *a: {}, "_post_commit_status": lambda *a: None}.items():
    setattr(m, f, v)

calls = []
mode = {"run": "timeout"}
_real_run = subprocess.run
def fake_run(cmd, *a, **k):
    if isinstance(cmd, list) and cmd[:2] == ["docker", "run"]:
        calls.append(("run", list(cmd)))
        if mode["run"] == "timeout":
            raise subprocess.TimeoutExpired(cmd, k.get("timeout") or 2400)
        return subprocess.CompletedProcess(cmd, 0, 'TESTREPORT:{"allPass": true, "total": 1, "passed": 1}\n', "")
    if isinstance(cmd, list) and cmd[:2] == ["docker", "rm"]:
        calls.append(("rm", list(cmd)))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return _real_run(cmd, *a, **k)

def name_of(cmd):
    return cmd[cmd.index("--name") + 1] if "--name" in cmd and cmd.index("--name") + 1 < len(cmd) else None

PAYLOAD = {"repo": "jrjohn/arcana-ai-bpm", "slug": "selftest", "_piid": "6835f30f-b853-44f3",
           "prUrl": json.dumps({"prUrl": "https://github.com/jrjohn/arcana-ai-bpm/pull/1", "branch": "feat/selftest"})}

def run(fn, payload, how):
    calls.clear(); mode["run"] = how
    subprocess.run = fake_run
    try:
        return fn(payload)
    finally:
        subprocess.run = _real_run

print("test_flow:runner 逾時")
rep = run(m.test_flow, PAYLOAD, "timeout")
runs = [c for k, c in calls if k == "run"]; rms = [c for k, c in calls if k == "rm"]
name = name_of(runs[0]) if runs else None
check("走到逾時那條路", "timed out" in (rep or {}).get("reason", ""))
check("runner 有 --name(得到:%s)" % name, bool(name))
check("名字查得到是哪個實例(含 _piid 開頭)", bool(name) and "6835f30f" in name)
check("逾時後用同一個名字 docker rm -f", any(c[:3] == ["docker", "rm", "-f"] and name and c[3] == name for c in rms))

print("test_flow:正常跑完")
run(m.test_flow, PAYLOAD, "ok")
check("正常跑完不多做 docker rm(--rm 會收)", not [c for k, c in calls if k == "rm"])

print("test_flow:同一實例測兩次")
run(m.test_flow, PAYLOAD, "timeout"); n1 = name_of([c for k, c in calls if k == "run"][0])
run(m.test_flow, PAYLOAD, "timeout"); n2 = name_of([c for k, c in calls if k == "run"][0])
check("兩次的名字不撞(%s / %s)" % (n1, n2), bool(n1) and bool(n2) and n1 != n2)

print("uiux_audit_flow:runner 逾時")
res = run(m.uiux_audit_flow, {}, "timeout")
runs = [c for k, c in calls if k == "run"]; rms = [c for k, c in calls if k == "rm"]
uname = name_of(runs[0]) if runs else None
check("走到逾時那條路", "timed out" in json.dumps(res or {}))
check("稽核的 runner 也有 --name(得到:%s)" % uname, bool(uname))
check("逾時後用同一個名字 docker rm -f", any(c[:3] == ["docker", "rm", "-f"] and uname and c[3] == uname for c in rms))

print("\n%s —— %d 過 / %d 不過" % ("pass" if not fail else "FAIL", ok, fail))
sys.exit(1 if fail else 0)
