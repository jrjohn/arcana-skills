#!/usr/bin/env python3
"""有 PR 卻沒分支名時,測試步驟不准默默改測本機站(2026-10-27)—— 跑法:python3 pr_branch_recover_selftest.py

事件(#750,10-22):實作節點那一輪回 "no structured_output",worker 只把舊的 prUrl 帶下去、沒有分支名。
test_flow 拿到 branch="" → 走「回歸測試」那條路,測的是本機正在跑的站,報告卻看起來像測過這個 PR。
PM 最後判 BLOCKED 是對的,但那是 PM 自己讀出來的,測試步驟什麼也沒說。

這支真的走一遍 test_flow(GitHub 與 docker 換成假的),檢查:
  1. 分支名有帶 → 照舊測 PR,不打 GitHub
  2. 只有 PR 網址(#750 的形狀)→ 向 GitHub 問到分支,照樣測 PR
  3. GitHub 也問不到 → 不跑 runner、回報沒測到、disposition=escalate
  4. 完全沒有 PR(手動回歸)→ 照舊測本機站,不打 GitHub
  5. 只拿網址的呼叫者(recover 預設關)→ 行為不變,不打 GitHub
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

URL = "https://github.com/jrjohn/arcana-ai-bpm/pull/750"
gh = {"answer": "feat/sonar-debt-bugs-vulns-duplication", "calls": []}
def fake_gh_json(args, timeout=90):
    gh["calls"].append(list(args))
    if args[:2] == ["pr", "view"] and gh["answer"]:
        return {"headRefName": gh["answer"]}
    raise RuntimeError("gh: could not resolve")
m._gh_json = fake_gh_json

runs = []
_real_run = subprocess.run
def fake_run(cmd, *a, **k):
    if isinstance(cmd, list) and cmd[:2] == ["docker", "run"]:
        runs.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, 'TESTREPORT:{"allPass": true, "total": 1, "passed": 1}\n', "")
    if isinstance(cmd, list) and cmd[:2] == ["docker", "rm"]:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return _real_run(cmd, *a, **k)

def run_test(pr_url_var, answer):
    runs.clear(); gh["calls"].clear(); gh["answer"] = answer
    subprocess.run = fake_run
    try:
        res = m.test_flow({"repo": "jrjohn/arcana-ai-bpm", "slug": "selftest", "_piid": "95430b19-4d18",
                           "prUrl": pr_url_var})
    finally:
        subprocess.run = _real_run
    return res

def env_of(cmd, name):
    return next((c.split("=", 1)[1] for c in cmd if c.startswith(name + "=")), None)

def report_of(res):
    tr = (res or {}).get("testReport")
    try:
        return json.loads(tr) if isinstance(tr, str) else (tr or {})
    except ValueError:
        return {}

# 10-22 #750 實例的 pr 變數形狀:有 prUrl、有 error、沒有 branch(carried forward)
SHAPE_750 = json.dumps({"ran": False, "error": "implement failed: no structured_output in claude result: {...}",
                        "prUrl": URL, "prUrlCarriedForward": True})

print("1. 分支名有帶")
run_test(json.dumps({"prUrl": URL, "branch": "feat/selftest"}), "feat/should-not-be-asked")
check("runner 拿到 BRANCH=feat/selftest", runs and env_of(runs[0], "BRANCH") == "feat/selftest")
check("沒有去問 GitHub", not gh["calls"])

print("2. 只有 PR 網址(#750 的形狀)")
run_test(SHAPE_750, "feat/sonar-debt-bugs-vulns-duplication")
check("向 GitHub 問了這個 PR 的分支", any(c[:3] == ["pr", "view", URL] for c in gh["calls"]))
check("runner 拿到問回來的 BRANCH", runs and env_of(runs[0], "BRANCH") == "feat/sonar-debt-bugs-vulns-duplication")
check("沒有改測本機站(沒有 TARGET_URL)", runs and env_of(runs[0], "TARGET_URL") is None)

print("3. GitHub 也問不到")
res = run_test(SHAPE_750, "")
rep = report_of(res)
check("沒有跑任何 runner(不測錯東西)", not runs)
check("allPass 是 false、total 是 0", rep.get("allPass") is False and rep.get("total") == 0)
check("disposition=escalate(閘跑不起來,交給 PM 判環境)", rep.get("disposition") == "escalate")
check("blockingReasons 點名 prBranchUnknown 與那個 PR",
      any(b.get("field") == "prBranchUnknown" and b.get("value") == URL for b in rep.get("blockingReasons") or []))

print("4. 完全沒有 PR(手動回歸)")
run_test("", "feat/should-not-be-asked")
check("照舊測本機站(有 TARGET_URL、沒有 BRANCH)",
      runs and env_of(runs[0], "TARGET_URL") is not None and env_of(runs[0], "BRANCH") is None)
check("沒有去問 GitHub", not gh["calls"])

print("5. 只拿網址的呼叫者")
gh["calls"].clear(); gh["answer"] = "feat/should-not-be-asked"
url, br = m._pr_url_and_branch({"prUrl": SHAPE_750})
check("recover 預設關:分支照舊是空的(得到 %r)" % br, br == "")
check("網址照舊讀得到", url == URL)
check("沒有去問 GitHub", not gh["calls"])

print("\n%s —— %d 過 / %d 不過" % ("pass" if not fail else "FAIL", ok, fail))
sys.exit(1 if fail else 0)
