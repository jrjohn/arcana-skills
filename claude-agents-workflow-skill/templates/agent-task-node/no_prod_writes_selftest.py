#!/usr/bin/env python3
"""正式環境只准讀:每一個 AI 節點**實際收到的提示**都帶著這條規則 —— 跑法:python3 no_prod_writes_selftest.py

2026-11-03 06:51Z,進化圈 ac991299 的 implement 節點為了需求裡的「必須實跑確認」,在這個容器裡
寫了一支沒進版控的 harness,在正式環境(host.docker.internal:8086 / :8081)起了一張請假單,再對
引擎 DELETE 收掉。10-28 一個 SA 節點也起單、送出、撤回過。節點連得到的只有正式環境,而提示裡
沒有任何一句話說不能寫。

驗的是**組好的提示**,不是常數:常數寫得再好,沒接到某一條路上就等於沒有 —— 這個 repo 已經
踩過九次「建好、測過、沒有呼叫者」。

  A 組:規則本身說到該說的(位址表、動詞、*_ALLOW_TARGET、報告用語、代價;consult 用的 :8090 不在表上)
  B 組:接線 —— 所有送給模型的呼叫都經過 _invoke_claude(AST),而它把規則接在提示最後
  C 組:組好的提示 —— 真的走 implement / SA / SD / uiux / pm-review / root-cause / test 生成三支 /
        consult 的組裝,攔在送給 claude 的最後一步(_invoke_claude_once),每一條都要帶著規則
  D 組:對照 —— 規則換成空字串,同一條路的提示必須判紅(證明 C 組的判準會紅)

不連網、不需要 docker、不呼叫 claude:docker 守衛、記憶查詢、clone 與 git 都換成假的,
只有「提示怎麼組」是真的。
注意:arcana-skills 沒有 CI,這支不會自動跑。
"""
import ast, importlib.util, os, subprocess, sys, tempfile, types

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, "server.py")
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)

RULE = getattr(m, "_NO_PROD_WRITES_RULE", "")

print("A 組 —— 規則本身")
check("規則存在而且不是空的", len(RULE.strip()) > 200)
for needle, why in (
    ("> **對下表的位址一律只准 GET**", "開頭是命令句"),
    ("host.docker.internal", "11-03 那支 harness 用的名字"),
    (":8086 :8087 :8088 :8081 :8180", "正式環境發布的 port(與 dashboard/e2e/lib/target-guard.mjs 同源)"),
    ("PR 預覽(它的 /api 是正式 API)", ":8087 看起來像 PR 自己的,其實寫進正式 API"),
    ("`aaf-*`(含 `aaf-pr-api-*`)", "PR 後端的引擎是正式的"),
    ("kogito-bpmn", "引擎在 docker 網路上的名字"),
    ("POST / PUT / PATCH / DELETE", "動詞"),
    ("起單、核准、駁回、送出、撤回、中止、刪除", "業務動作"),
    ("確認對話框的確定鈕", "用瀏覽器按也算"),
    ("*_ALLOW_TARGET", "不准自己打開閘的逃生門"),
    ("寫入路徑沒跑(沒有拋棄式環境)", "報告用語,與 launcher-gate 的 writePath.reason 同一句"),
    ("不要自己寫腳本、harness 或 curl 繞過", "11-03 正是自己寫的 harness"),
    ("這一條靠你", "沒有機制擋 —— 說實話"),
    ("2026-11-03", "代價:真的發生過的那一次"),
):
    check("提到「%s」—— %s" % (needle, why), needle in RULE)
check("consult 用的 localhost:8090 不在表上(否則節點不敢諮詢)", "8090" not in RULE)

print("\nB 組 —— 接線:沒有繞過 _invoke_claude 的路")
tree = ast.parse(open(SRC, encoding="utf-8").read())
callers = {}
for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
    for c in ast.walk(fn):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name):
            callers.setdefault(c.func.id, set()).add(fn.name)
check("_invoke_claude_once 只被 _invoke_claude_core 呼叫(%s)" % sorted(callers.get("_invoke_claude_once", ())),
      callers.get("_invoke_claude_once") == {"_invoke_claude_core"})
check("_invoke_claude_core 只被 _invoke_claude 呼叫(%s)" % sorted(callers.get("_invoke_claude_core", ())),
      callers.get("_invoke_claude_core") == {"_invoke_claude"})
cmd_users = sorted({fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef)
                    for c in ast.walk(fn) if isinstance(c, ast.List) and c.elts
                    and isinstance(c.elts[0], ast.Name) and c.elts[0].id == "CLAUDE"})
check("組 claude 指令列的只有 _invoke_claude_once(%s)" % cmd_users, cmd_users == ["_invoke_claude_once"])
for entry in ("implement_flow", "run_claude", "run_claude_generic", "_gen_testcases", "_gen_journeys",
              "_gen_api_checks", "coverage_flow", "run_consult"):
    check("%s 經過 _invoke_claude" % entry, entry in callers.get("_invoke_claude", set()))

print("\nC 組 —— 組好的提示(攔在送給 claude 的最後一步)")


class Captured(Exception):
    pass


got = []
def _once(prompt, schema, payload, wall, cwd=None):
    got.append(prompt)
    raise Captured()


# 只換掉 I/O,提示的組法一行不動。
m._invoke_claude_once = _once
m._guarded_runner = lambda img: (None, None, 0)            # docker
m._restore_runner = lambda *a, **k: None                    # docker
m.project_memory_recall = lambda *a, **k: ""                # 產品記憶(crs)
m.fetch_memory = lambda *a, **k: ""                         # 團隊記憶(HTTP)
m.project_brief = lambda *a, **k: ""                        # 讀 checkout
m.consult_brief = lambda *a, **k: ""
m.consultations_of = lambda *a, **k: []
WORK = tempfile.mkdtemp(prefix="no-prod-writes-")
os.makedirs(os.path.join(WORK, ".git"), exist_ok=True)
m._ensure_checkout = lambda p: WORK
HOME = tempfile.mkdtemp(prefix="no-prod-writes-home-")
open(os.path.join(HOME, ".claude.json"), "w").write("{}")
os.environ["HOME"] = HOME                                   # _ensure_claude_config 不碰真的 ~/.claude.json
_real_subprocess = m.subprocess


def _fake_run(cmd, *a, **k):
    return subprocess.CompletedProcess(cmd, 0, "", "")


def prompt_of(fn):
    """跑一條節點的組裝,回傳它最後送給 claude 的提示;沒送出就回 None。"""
    got.clear()
    m.subprocess = types.SimpleNamespace(run=_fake_run, CompletedProcess=subprocess.CompletedProcess,
                                         TimeoutExpired=subprocess.TimeoutExpired,
                                         PIPE=subprocess.PIPE, DEVNULL=subprocess.DEVNULL)
    try:
        fn()
    except Captured:
        pass
    except Exception as e:                                  # noqa: BLE001
        print("      (%s: %s)" % (type(e).__name__, str(e)[:120]))
    finally:
        m.subprocess = _real_subprocess
    return got[-1] if got else None


def carries_rule(p):
    return bool(p) and RULE in p and p.rstrip().endswith(RULE.rstrip())


IMPL_REPO = sorted(m.IMPLEMENT_REPO_ALLOWLIST)[0]
NODES = [
    ("implement", lambda: m.implement_flow({"repo": IMPL_REPO, "base": "main", "slug": "no-prod-writes",
                                            "prompt": "實作一個功能,必須實跑確認"})),
    ("SA", lambda: m.run_claude_generic({"prompt": "寫 SRS,必須實跑確認", "_node": "sa"})),
    ("SD", lambda: m.run_claude_generic({"prompt": "寫 SDD", "_node": "sd"})),
    ("uiux", lambda: m.run_claude_generic({"prompt": "寫 UIUX", "_node": "uiux"})),
    ("pm-review", lambda: m.run_claude("pm-review", {})),
    ("root-cause", lambda: m.run_claude("root-cause", {})),
    ("test:testcases", lambda: m._gen_testcases({"srs": "AC-1 按下啟動要落在表單"})),
    ("test:journeys", lambda: m._gen_journeys({"srs": "AC-1 按下啟動要落在表單", "uiFacing": True})),
    ("test:api-checks", lambda: m._gen_api_checks({"srs": "AC-1 GET /api/v1/x 回 200"})),
    ("consult", lambda: m.run_consult({"role": "pm", "question": "可以在正式環境實跑嗎?", "_piid": "p6i"})),
]
for name, fn in NODES:
    p = prompt_of(fn)
    check("%-16s 送出的提示帶著規則,而且接在最後(%s 字)" % (name, len(p) if p else "沒送出"), carries_rule(p))

print("\nD 組 —— 對照:規則換成空字串,同一條路必須判紅")
saved = m._NO_PROD_WRITES_RULE
m._NO_PROD_WRITES_RULE = ""
try:
    p = prompt_of(NODES[1][1])
    check("SA 的提示沒有規則時,C 組的判準判它沒帶(判準會紅)", p is not None and not carries_rule(p))
    p = prompt_of(NODES[0][1])
    check("implement 的提示沒有規則時,C 組的判準判它沒帶", p is not None and not carries_rule(p))
finally:
    m._NO_PROD_WRITES_RULE = saved

print()
print("pass —— %d 項" % ok if fail == 0 else "gap —— %d 項不符(共 %d)" % (fail, ok + fail))
sys.exit(1 if fail else 0)
