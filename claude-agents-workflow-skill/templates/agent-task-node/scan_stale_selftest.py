#!/usr/bin/env python3
"""scan-stale 改成不用 AI(2026-09-14)—— 跑法:python3 scan_stale_selftest.py

案例取自 AI 版自己的判斷(09-13 13:08 那一輪):#346 開、#348 已有流程不重開、#347 還在跑不開;
09-14 那一輪:#387 紅但沒落後 main 不開、#384 草稿不開。另外驗 AI 版沒有的那條:同一組 head+base 只開一次。
不打網路:gh 和引擎都換成假的。SERVER_PY 可指向別份 server.py(bluesea 部署那份也跑同一套)。
"""
import importlib.util, json, os, sys, tempfile
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
os.environ["UNSTICK_SCAN_STATE"] = os.path.join(tempfile.mkdtemp(), "state.json")
SRV = os.environ.get("SERVER_PY", os.path.join(D, "server.py"))
spec = importlib.util.spec_from_file_location("atn_server", SRV); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

FAILED = {"__typename": "StatusContext", "state": "FAILURE"}
PASSED = {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"}
RUNNING = {"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": ""}
def pr(n, state="DIRTY", checks=(FAILED, PASSED), draft=False, head=None):
    return {"number": n, "url": "https://github.com/jrjohn/arcana-ai-bpm/pull/%d" % n, "isDraft": draft,
            "mergeStateStatus": state, "headRefOid": head or ("h%d" % n), "baseRefName": "main",
            "statusCheckRollup": list(checks)}

class World:
    def __init__(self, prs, behind, active=(), engine_down=False, post_code=201, gh_down=False):
        self.prs, self.behind, self.active = prs, behind, list(active)
        self.engine_down, self.post_code, self.gh_down = engine_down, post_code, gh_down
        self.posts = []
    def gh(self, args):
        if self.gh_down: raise RuntimeError("gh: bad credentials")
        if args[:2] == ["pr", "list"]: return self.prs
        if args[0] == "api" and "/compare/" in args[1]:
            head = args[1].rsplit("...", 1)[1]
            n = next(p["number"] for p in self.prs if p["headRefOid"] == head)
            return {"behind_by": self.behind.get(n, 0), "base_commit": {"sha": "base1"}}
        raise AssertionError(args)
    def engine(self, method, path, body=None):
        if self.engine_down: raise OSError("connection refused")
        if method == "GET": return 200, [{"prUrl": u} for u in self.active]
        self.posts.append(body); return self.post_code, {}
def scan(w):
    return m.scan_stale({}, gh=w.gh, engine=w.engine)
def reset_state():
    if os.path.exists(os.environ["UNSTICK_SCAN_STATE"]): os.remove(os.environ["UNSTICK_SCAN_STATE"])

print("\n════ 09-13 那一輪:判斷要跟 AI 一樣 ════")
reset_state()
w = World([pr(346), pr(347, "UNSTABLE", (RUNNING, RUNNING)), pr(348)], {346: 1, 347: 1, 348: 1},
          active=["https://github.com/jrjohn/arcana-ai-bpm/pull/348"])
r = scan(w)
check("#346(DIRTY、落後、紅、沒在跑)→ 開一個", r["started"] == 1 and [b["prUrl"][-3:] for b in w.posts] == ["346"])
check("#348 已有 unstick-flow → 不重開", "#348 skip: unstick-flow already active" in r["reason"])
check("#347 檢查還在跑 → 不開", "#347 skip: no failing check" in r["reason"])
check("subject 跟 AI 版同格式", w.posts[0]["subject"] == "unstick arcana-ai-bpm#346")

print("\n════ 09-14 那一輪 ════")
reset_state()
w = World([pr(387, "UNSTABLE"), pr(384, draft=True), pr(388, "CLEAN", (PASSED,))], {387: 0, 388: 0})
r = scan(w)
check("#387 紅但沒落後 main(真的程式問題)→ 不開", "#387 skip: up to date with base" in r["reason"])
check("#384 草稿 → 不開", "#384 skip: draft" in r["reason"])
check("整輪 0 個,沒有 POST", r["started"] == 0 and w.posts == [])
w = World([pr(390, "CLEAN", (FAILED,))], {390: 2})
check("mergeState CLEAN 就不當成卡住", scan(w)["started"] == 0)
w = World([pr(391, "BLOCKED", (FAILED, RUNNING))], {391: 2})
check("有紅也有還在跑 → 等跑完再說", "checks still running" in scan(w)["reason"])

print("\n════ AI 版沒有的:同一組 head+base 只開一次(不再迴圈)════")
reset_state()
w = World([pr(346)], {346: 1})
check("第一次 → 開", scan(w)["started"] == 1)
r = scan(w)
check("流程結束後還是卡著、head/base 沒變 → 不再開", r["started"] == 0 and "already tried" in r["reason"])
w.prs = [pr(346, head="h346-new")]
check("PR 推了新 commit → 可以再開一次", scan(w)["started"] == 1)

print("\n════ 上限與故障 ════")
reset_state()
w = World([pr(1), pr(2), pr(3)], {1: 1, 2: 1, 3: 1})
r = scan(w)
check("一輪最多開 %d 個" % m.UNSTICK_MAX_START, r["started"] == m.UNSTICK_MAX_START and "per-scan cap" in r["reason"])
reset_state()
w = World([pr(346)], {346: 1}, engine_down=True)
r = scan(w)
check("問不到引擎(不知道誰在跑)→ 一個都不開", r["started"] == 0 and w.posts == [] and "engine unreachable" in r["reason"])
w = World([pr(346)], {346: 1}, post_code=500)
r = scan(w)
check("引擎開流程失敗 → 不記成開過,錯誤要講出來", r["started"] == 0 and "HTTP 500" in r["reason"])
w.post_code = 201
check("  ……所以下一輪會再試", scan(w)["started"] == 1)
w = World([], {}, gh_down=True)
r = scan(w)
check("gh 壞掉 → 不丟例外、錯誤寫進 reason", r["started"] == 0 and "bad credentials" in r["reason"])

src = open(SRV, encoding="utf-8").read()
print("\n════ 接線 ════")
check("do_POST 真的走 scan_stale(payload)", "result = scan_stale(payload)" in src)
check("舊的 AI 提示詞已經拿掉(不會兩條路並存)", "prompt_scan_stale" not in src)

print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
