#!/usr/bin/env python3
"""AI 對話的圖片直接交給 Claude(2026-10-28)—— 跑法:python3 image_input_selftest.py

John 選 A:上傳的圖片由後端放在 payload["images"],agent 把它跟文字提示放進同一則使用者訊息
(`--input-format stream-json`)。實測 claude 2.1.311 可與 --json-schema、--resume 並用。

這支真的走 _invoke_claude_once(claude 換成假的 subprocess),檢查:
  A. 沒有圖片 → 指令與 stdin 跟改之前一模一樣(對照:不能因為這個功能改到所有節點)
  B. 有圖片、非串流 → 帶 --input-format stream-json + stream-json 輸出;stdin 是一則 JSONL 使用者訊息,
     文字在前、圖片在後;從輸出裡取 result 事件的 structured_output
  C. 有圖片、串流(有 console)→ 一樣帶 --input-format;寫進提示檔的是 JSONL;console 沒有 base64
  D. 不合格的圖片整批拒絕(格式、張數、空資料、過大),不默默略過
SERVER_PY 可指向別份 server.py;指向修之前那份應該紅(對照組)。不打網路、不需要 docker / claude。
"""
import importlib.util, io, json, os, subprocess, sys, tempfile, types
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
CON = tempfile.mkdtemp(prefix="img-selftest-")
os.environ["CONSOLE_DIR"] = CON
SRV = os.environ.get("SERVER_PY", os.path.join(D, "server.py"))
spec = importlib.util.spec_from_file_location("atn_server", SRV); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

m._workspace = lambda p: None
m._instance_claude_config = lambda piid: None
PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
SCHEMA = json.dumps({"type": "object", "properties": {"reply": {"type": "string"}}, "required": ["reply"]})
RESULT = {"type": "result", "subtype": "success", "is_error": False, "structured_output": {"reply": "看到了"},
          "usage": {"input_tokens": 1, "output_tokens": 1}, "session_id": "s1"}

seen = {}
def fake_run(cmd, input=None, **k):
    seen["cmd"], seen["stdin"] = list(cmd), input
    if "--input-format" in cmd:
        out = "\n".join(json.dumps(e) for e in ({"type": "system", "subtype": "init"}, RESULT)) + "\n"
    else:
        out = json.dumps(RESULT)
    return types.SimpleNamespace(returncode=0, stdout=out, stderr="")

real_run, real_popen = subprocess.run, subprocess.Popen
subprocess.run = fake_run

def call(payload):
    seen.clear()
    try:
        return m._invoke_claude_once("請照圖片填表", SCHEMA, payload, 30), None
    except Exception as e:  # noqa: BLE001
        return None, e

print("A 組 —— 沒有圖片:跟改之前一樣")
r, e = call({})
check("沒丟例外(%s)" % (e or "無"), e is None)
check("指令沒有 --input-format、輸出是 json", "--input-format" not in seen.get("cmd", []) and
      seen["cmd"][seen["cmd"].index("--output-format") + 1] == "json")
check("stdin 就是純文字提示", seen.get("stdin") == "請照圖片填表")
check("結果照舊", isinstance(r, dict) and r.get("reply") == "看到了")

print("B 組 —— 有圖片、非串流")
r, e = call({"images": [{"media_type": "image/png", "data": PNG, "name": "a.png"}]})
cmd = seen.get("cmd", [])
check("沒丟例外(%s)" % (e or "無"), e is None)
check("帶 --input-format stream-json", "--input-format" in cmd and cmd[cmd.index("--input-format") + 1] == "stream-json")
check("輸出改 stream-json 並帶 --verbose(stream-json 輸入只能配它)",
      cmd[cmd.index("--output-format") + 1] == "stream-json" and "--verbose" in cmd)
check("仍帶 --json-schema", "--json-schema" in cmd)
try:
    msg = json.loads(seen.get("stdin") or "")
except ValueError:
    msg = {}
content = ((msg.get("message") or {}).get("content")) or []
check("stdin 是一則使用者訊息", msg.get("type") == "user" and (msg.get("message") or {}).get("role") == "user")
check("文字在前、圖片在後", [c.get("type") for c in content] == ["text", "image"] and content[0].get("text") == "請照圖片填表")
src = (content[1].get("source") if len(content) > 1 else {}) or {}
check("圖片是 base64、格式與資料原樣", src.get("type") == "base64" and src.get("media_type") == "image/png" and src.get("data") == PNG)
check("從 stream-json 輸出取到 structured_output", isinstance(r, dict) and r.get("reply") == "看到了")
check("--resume 照常帶(接續對話)", call({"images": [{"media_type": "image/png", "data": PNG}], "sid": "abc"})[1] is None
      and "--resume" in seen.get("cmd", []))

print("C 組 —— 有圖片、串流(有 console)")
class FakePopen:
    def __init__(self, cmd, stdin=None, **k):
        seen["cmd"] = list(cmd); seen["stdin"] = stdin.read() if stdin else None
        self.stdout = io.StringIO("\n".join(json.dumps(e) for e in ({"type": "system", "subtype": "init"}, RESULT)) + "\n")
        self.stderr = io.StringIO(""); self.returncode = 0
    def wait(self, timeout=None): return 0
    def kill(self): pass
subprocess.Popen = FakePopen
seen.clear()
try:
    r = m._invoke_claude_once("請照圖片填表", SCHEMA,
                              {"_piid": "img-piid", "_node": "Chat", "images": [{"media_type": "image/jpeg", "data": PNG}]}, 30)
    e = None
except Exception as ex:  # noqa: BLE001
    r, e = None, ex
subprocess.Popen = real_popen
cmd = seen.get("cmd", [])
check("沒丟例外(%s)" % (e or "無"), e is None)
check("串流指令也帶 --input-format stream-json", "--input-format" in cmd)
try:
    smsg = json.loads(seen.get("stdin") or "")
except ValueError:
    smsg = {}
check("寫進提示檔的是 JSONL 使用者訊息(含圖片)",
      [c.get("type") for c in ((smsg.get("message") or {}).get("content") or [])] == ["text", "image"])
con = os.path.join(CON, "img-piid__Chat.jsonl")
check("console 沒有圖片的 base64", os.path.exists(con) and PNG not in open(con, encoding="utf-8").read())

print("D 組 —— 不合格的圖片整批拒絕")
for label, imgs in (("格式不支援(image/bmp)", [{"media_type": "image/bmp", "data": PNG}]),
                    ("超過 5 張", [{"media_type": "image/png", "data": PNG}] * 6),
                    ("資料是空的", [{"media_type": "image/png", "data": ""}]),
                    ("過大", [{"media_type": "image/png", "data": "A" * 7_000_001}])):
    r, e = call({"images": imgs})
    check("%s → 拒絕且沒有呼叫 claude" % label, isinstance(e, ValueError) and not seen.get("cmd"))

subprocess.run = real_run
print("\n%s —— %d 過 / %d 不過" % ("pass" if not fail else "FAIL", ok, fail))
sys.exit(1 if fail else 0)
