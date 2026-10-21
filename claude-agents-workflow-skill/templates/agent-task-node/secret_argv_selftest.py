#!/usr/bin/env python3
"""測試容器逾時,報告裡不能有 token(2026-10-21)—— 跑法:python3 secret_argv_selftest.py

事件:test_flow 用 `-e CLAUDE_CODE_OAUTH_TOKEN=<值>`、`-e GH_TOKEN=<值>` 起 runner 容器。
runner 跑滿 2400 秒逾時,`str(TimeoutExpired)` 帶出**整條指令**,寫進 testReport.reason ——
也就是寫進流程變數、Data Index,PM 也可能引用。10-15 有一輪就這樣存下了當時在用的 token。

這支真的走一遍 test_flow(外部依賴全換成假的),讓 docker run 丟 TimeoutExpired,檢查:
  1. 指令列裡沒有祕密的值,但祕密的**名字**還在(runner 仍然拿得到 token)
  2. 回傳的 reason 裡沒有祕密的值
  3. 原始碼裡沒有「-e 祕密名=值」的寫法(含 uiux 稽核那一處)—— 掃描器自己先用一行舊寫法驗過
SERVER_PY 可指向別份 server.py;指向修之前那份應該紅(對照組)。不打網路、不需要 docker。
"""
import importlib.util, json, os, re, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
FAKE = {"CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat01-SELFTEST-not-a-real-token-0001",
        "GH_TOKEN": "ghp_SELFTESTnotarealtoken0002"}
os.environ.update(FAKE)
SRV = os.environ.get("SERVER_PY", os.path.join(D, "server.py"))
spec = importlib.util.spec_from_file_location("atn_server", SRV); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

def leaks(text):
    return [k for k, v in FAKE.items() if v in (text or "")]

# ── 3. 靜態:原始碼裡不能有「-e 祕密名=」。掃描器先對一行舊寫法驗過,證明它不是瞎的。
SECRET_ARG = re.compile(r'"-e",\s*"(CLAUDE_CODE_OAUTH_TOKEN|GH_TOKEN|GITHUB_TOKEN|ANTHROPIC_API_KEY)=')
print("靜態掃描")
check("掃描器認得舊寫法(對照)",
      bool(SECRET_ARG.search('"-e", "GH_TOKEN=" + os.environ.get("GH_TOKEN", "")')))
src = open(SRV, encoding="utf-8").read()
found = ["%d: %s" % (src.count("\n", 0, mt.start()) + 1, mt.group(1)) for mt in SECRET_ARG.finditer(src)]
check("server.py 沒有「-e 祕密名=值」(找到:%s)" % (found or "無"), not found)

# ── 1、2. 真的走一遍 test_flow,讓 runner 逾時
print("test_flow:runner 逾時")
m._start_pr_backend = lambda repo, branch, base, piid, net: (None, lambda: None)
m._scenario_autofill = lambda p: {"ran": False}
m._load_profile = lambda p: {"app": {}, "run": {}, "auth": {}, "nav": {}, "flow": {}}
m._gen_testcases = lambda p: ""
m._resolve_testcases = lambda gen, path: ("", "none")
m._testcases_cache_path = lambda p: "/nonexistent"
m._sdd_files = lambda p: []
m._gen_journeys = lambda p: ""
m._gen_api_checks = lambda p: ""
m._arch_qube = lambda p: {"applicable": False}
m._sonar = lambda p: {"applicable": False}
seen = []
_real_run = subprocess.run
def fake_run(cmd, *a, **k):
    if isinstance(cmd, list) and cmd[:2] == ["docker", "run"]:
        seen.append(list(cmd))
        raise subprocess.TimeoutExpired(cmd, k.get("timeout") or 2400)
    return _real_run(cmd, *a, **k)
subprocess.run = fake_run
payload = {"repo": "jrjohn/arcana-ai-bpm", "slug": "selftest", "_piid": "selftest",
           "prUrl": json.dumps({"prUrl": "https://github.com/jrjohn/arcana-ai-bpm/pull/1", "branch": "feat/selftest"})}
try:
    rep = m.test_flow(payload)
finally:
    subprocess.run = _real_run
reason = (rep or {}).get("reason", "")
check("走到了 runner 逾時那條路(reason 說 timed out)", "timed out" in reason)
check("有起 runner 容器(攔到 docker run)", len(seen) == 1)
argv = " ".join(seen[0]) if seen else ""
check("docker run 的指令列沒有祕密的值(漏:%s)" % (leaks(argv) or "無"), seen and not leaks(argv))
check("token 仍以名字傳給 runner(-e CLAUDE_CODE_OAUTH_TOKEN)", "-e CLAUDE_CODE_OAUTH_TOKEN " in argv + " ")
check("PR 分支那條路仍以名字傳 GH_TOKEN(-e GH_TOKEN)", "-e GH_TOKEN " in argv + " ")
check("回傳的 reason 沒有祕密的值(漏:%s)" % (leaks(reason) or "無"), not leaks(reason))

# ── 第二層:就算哪天又有東西把值帶出來,寫進報告前也會被遮掉
print("_redact_secrets")
red = getattr(m, "_redact_secrets", None)
check("有 _redact_secrets", callable(red))
if callable(red):
    s = red("x %s y %s z" % (FAKE["CLAUDE_CODE_OAUTH_TOKEN"], FAKE["GH_TOKEN"]))
    check("兩個值都被遮掉", not leaks(s))
    check("遮掉後看得出是哪一個(<名字 redacted>)", "<CLAUDE_CODE_OAUTH_TOKEN redacted>" in s and "<GH_TOKEN redacted>" in s)
    check("沒有祕密的字串原樣通過", red("plain text") == "plain text")

print("\n%s —— %d 過 / %d 不過" % ("pass" if not fail else "FAIL", ok, fail))
sys.exit(1 if fail else 0)
