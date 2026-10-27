#!/usr/bin/env python3
"""agent 的即時 console 不能寫進 token(2026-10-27)—— 跑法:python3 console_redact_selftest.py

事件:一個 merge-flow 的 Merge 節點,agent 為了找 PR 跑了 `env | grep -iE 'pr|repo|gh_'`,
GH_TOKEN 原樣寫進 CONSOLE_DIR/<piid>__Merge.jsonl —— 那個檔由 read-API 的
/workflows/processes/:id/console/:node 提供給畫面(當時還不用登入就讀得到)。

這支真的走一遍 _invoke_claude_once 的 console 路徑(claude 換成假的 Popen,吐出含 token 的
stream-json),檢查:
  1. console 檔裡沒有任何祕密的值(env 裡的、和不在 env 裡但長得像 token 的)
  2. 遮罩不弄壞 JSON —— 每一行仍然 json.loads 得了,結果事件仍然解析得到
  3. 回傳的 structured_output 照舊(遮罩只動寫到磁碟的那一份)
SERVER_PY 可指向別份 server.py;指向修之前那份應該紅(對照組)。不打網路、不需要 docker / claude。
"""
import importlib.util, io, json, os, subprocess, sys, tempfile
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
FAKE = {"GH_TOKEN": "gho_SELFTESTnotarealtoken000000000000000001",
        "CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat01-SELFTEST-not-a-real-token-0001"}
NOT_IN_ENV = "ghp_SELFTESTsecondaccount0000000000000000002"
os.environ.update(FAKE)
CON = tempfile.mkdtemp(prefix="console-selftest-")
os.environ["CONSOLE_DIR"] = CON
SRV = os.environ.get("SERVER_PY", os.path.join(D, "server.py"))
spec = importlib.util.spec_from_file_location("atn_server", SRV); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

tool_out = "GH_TOKEN=%s\nOTHER=%s\nCLAUDE_CODE_OAUTH_TOKEN=%s" % (FAKE["GH_TOKEN"], NOT_IN_ENV, FAKE["CLAUDE_CODE_OAUTH_TOKEN"])
LINES = [
    json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "input": {"command": "env | grep gh_"}}]}}),
    json.dumps({"type": "user", "message": {"content": [{"type": "tool_result", "content": tool_out}]}}),
    json.dumps({"type": "result", "structured_output": {"merged": False, "reason": "no PR"},
                "usage": {"input_tokens": 1, "output_tokens": 1}, "session_id": "s"}),
]

class FakeProc:
    def __init__(self, *a, **k):
        self.stdout = io.StringIO("".join(l + "\n" for l in LINES))
        self.stderr = io.StringIO("")
        self.returncode = 0
    def wait(self, timeout=None): return 0
    def kill(self): pass

real = subprocess.Popen
subprocess.Popen = FakeProc
m._workspace = lambda p: None
m._instance_claude_config = lambda piid: None
err = None
try:
    out = m._invoke_claude_once("prompt", "{}", {"_piid": "selftest-piid", "_node": "Merge"}, 30)
except Exception as e:  # noqa: BLE001
    out, err = None, e
finally:
    subprocess.Popen = real

path = os.path.join(CON, "selftest-piid__Merge.jsonl")
print("console 路徑")
check("呼叫沒丟例外(%s)" % (err or "無"), err is None)
check("console 檔寫出來了", os.path.exists(path))
text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
leaked = [k for k, v in FAKE.items() if v in text] + (["(不在 env 的 ghp_)"] if NOT_IN_ENV in text else [])
check("console 檔沒有任何 token(漏:%s)" % (leaked or "無"), text and not leaked)
check("遮罩記號在(證明真的有東西被遮,不是根本沒寫)", "redacted>" in text)
parsed = []
for l in text.splitlines():
    try: parsed.append(json.loads(l))
    except ValueError: parsed.append(None)
check("每一行仍是合法 JSON", parsed and all(p is not None for p in parsed))
check("回傳的 structured_output 照舊", isinstance(out, dict) and out.get("merged") is False)

print("\n%s —— %d 過 / %d 不過" % ("pass" if not fail else "FAIL", ok, fail))
sys.exit(1 if fail else 0)
